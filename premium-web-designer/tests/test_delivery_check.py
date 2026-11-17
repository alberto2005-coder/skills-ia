import contextlib
import io
import subprocess
import sys
import unittest
from pathlib import Path

from config import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import delivery_check as dc

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run(target: Path) -> dc.Result:
    result = dc.Result()
    dc.check_page(target, result)
    dc.check_css(target, result)
    dc.check_files(target, result)
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
