import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from config import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import delivery_check as dc

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run(target: Path, public: bool = False) -> dc.Result:
    result = dc.Result()
    dc.check_page(target, result, public=public)
    dc.check_css(target, result)
    dc.check_files(target, result, public=public)
    dc.check_headers(target, result, public=public)
    return result


class TestDeliveryCheck(unittest.TestCase):

    def test_good_site_has_no_must_failures(self):
        result = run(FIXTURES / "site_ok")

        self.assertEqual(
            [item["id"] for item in result.must_failures()],
            [],
            "Unexpected must failures on the reference site.",
        )

    def test_good_site_passes_seo_and_resilience_checks(self):
        failed = {item["id"] for item in run(FIXTURES / "site_ok").failures}

        for check_id in [
            "HTML-003",
            "HTML-004",
            "HTML-007",
            "HTML-008",
            "HTML-011",
            "HTML-013",
            "HTML-014",
            "HTML-015",
            "CSS-001",
            "CSS-002",
            "CSS-003",
            "FILE-001",
            "FILE-002",
            "FILE-003",
        ]:
            with self.subTest(check=check_id):
                self.assertNotIn(check_id, failed)

    def test_bad_site_reports_the_known_defects(self):
        result = run(FIXTURES / "site_bad")
        failed = {item["id"] for item in result.failures}
        must = {item["id"] for item in result.must_failures()}

        for check_id in ["HTML-001", "HTML-006", "HTML-010", "HTML-012"]:
            with self.subTest(check=check_id, severity="must"):
                self.assertIn(check_id, must)

        for check_id in ["HTML-015", "CSS-003", "FILE-001", "FILE-003"]:
            with self.subTest(check=check_id, severity="should"):
                self.assertIn(check_id, failed)

    def test_local_site_passes_without_public_flag(self):
        result = run(FIXTURES / "site_local")

        self.assertEqual([item["id"] for item in result.must_failures()], [])

    def test_public_flag_promotes_the_publishing_requirements(self):
        local_must = {item["id"] for item in run(FIXTURES / "site_local").must_failures()}
        public_must = {item["id"] for item in run(FIXTURES / "site_local", public=True).must_failures()}

        self.assertEqual(local_must, set())
        self.assertEqual(public_must, {"HTML-007", "HTML-008", "FILE-001", "FILE-003"})

    def test_public_flag_keeps_the_complete_site_green(self):
        result = run(FIXTURES / "site_ok", public=True)

        self.assertEqual([item["id"] for item in result.must_failures()], [])

    def test_report_states_the_mode(self):
        self.assertIn("Modo: prototipo local", dc.render(FIXTURES / "site_local", run(FIXTURES / "site_local")))
        self.assertIn(
            "Modo: sitio publicado",
            dc.render(FIXTURES / "site_local", run(FIXTURES / "site_local", public=True), public=True),
        )

    def test_public_flag_cli_exit_codes(self):
        script = SKILL_ROOT / "scripts" / "delivery_check.py"

        def execute(*extra):
            return subprocess.run(
                [sys.executable, str(script), str(FIXTURES / "site_local"), *extra],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(execute().returncode, 0, execute().stdout)
        public = execute("--public")
        self.assertEqual(public.returncode, 1, public.stdout)
        self.assertIn("HTML-007", public.stdout)

    def test_headers_are_ignored_outside_public_mode(self):
        ids = {item["id"] for item in run(FIXTURES / "site_ok").items}

        self.assertFalse({check for check in ids if check.startswith("HDR-")})

    def test_public_site_without_headers_is_flagged(self):
        result = run(FIXTURES / "site_ok", public=True)
        failed = {item["id"] for item in result.failures}

        self.assertTrue({"HDR-001", "HDR-002", "HDR-003"} <= failed, failed)
        self.assertEqual([item["id"] for item in result.must_failures()], [])

    def test_public_site_with_headers_is_clean(self):
        result = run(FIXTURES / "site_public", public=True)
        failed = {item["id"] for item in result.failures}

        self.assertEqual([item["id"] for item in result.must_failures()], [])
        self.assertNotIn("HDR-002", failed)
        self.assertNotIn("HDR-003", failed)

    def test_headers_file_formats_are_detected(self):
        formats = {
            "_headers": """/*
  Content-Security-Policy: default-src 'self'
  Strict-Transport-Security: max-age=31536000
""",
            "netlify.toml": """[[headers]]
  for = "/*"
  [headers.values]
    Content-Security-Policy = "default-src 'self'"
    Strict-Transport-Security = "max-age=31536000"
""",
            "vercel.json": json.dumps(
                {
                    "headers": [
                        {
                            "source": "/(.*)",
                            "headers": [
                                {"key": "Content-Security-Policy", "value": "default-src 'self'"},
                                {"key": "Strict-Transport-Security", "value": "max-age=31536000"},
                            ],
                        }
                    ]
                }
            ),
        }

        for name, body in formats.items():
            with self.subTest(format=name), tempfile.TemporaryDirectory() as tmp:
                site = Path(tmp) / "site"
                shutil.copytree(FIXTURES / "site_local", site)
                (site / name).write_text(body, encoding="utf-8")

                result = run(site, public=True)
                failed = {item["id"] for item in result.failures}
                self.assertNotIn("HDR-001", failed)
                self.assertNotIn("HDR-002", failed)
                self.assertNotIn("HDR-003", failed)

    def test_hsts_without_max_age_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            site = Path(tmp) / "site"
            shutil.copytree(FIXTURES / "site_local", site)
            (site / "_headers").write_text(
                """/*
  Strict-Transport-Security: includeSubDomains
""",
                encoding="utf-8",
            )

            result = run(site, public=True)
            detail = {item["id"]: item["detail"] for item in result.failures}

            self.assertEqual(detail.get("HDR-003"), "sin max-age")

    def test_report_is_readable(self):
        text = dc.render(FIXTURES / "site_bad", run(FIXTURES / "site_bad"))

        self.assertIn("[FALLA]", text)
        self.assertIn("Resumen:", text)
        self.assertIn("Entrega bloqueada", text)

    def test_cli_exit_codes(self):
        script = SKILL_ROOT / "scripts" / "delivery_check.py"

        good = subprocess.run(
            [sys.executable, str(script), str(FIXTURES / "site_ok")],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        bad = subprocess.run(
            [sys.executable, str(script), str(FIXTURES / "site_bad")],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        missing = subprocess.run(
            [sys.executable, str(script), str(FIXTURES / "no-existe")],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(good.returncode, 0, good.stdout)
        self.assertEqual(bad.returncode, 1, bad.stdout)
        self.assertEqual(missing.returncode, 2)

    def test_json_output_parses(self):
        script = SKILL_ROOT / "scripts" / "delivery_check.py"
        output = subprocess.run(
            [sys.executable, str(script), str(FIXTURES / "site_ok"), "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        import json

        payload = json.loads(output.stdout)

        self.assertEqual(payload["must_failed"], 0)
        self.assertTrue(payload["items"])


if __name__ == "__main__":
    unittest.main()
