import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from config import FIXTURES, SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import grade  # noqa: E402
import map_flows  # noqa: E402
import scan_secrets  # noqa: E402

SCRIPT_DIR = SKILL_ROOT / "scripts"


class TestScanSecrets(unittest.TestCase):

    def test_finds_known_secret_shapes(self):
        findings = scan_secrets.scan(FIXTURES / "vuln_app")
        kinds = {item["kind"] for item in findings}

        self.assertIn("aws_access_key", kinds)
        self.assertIn("github_token", kinds)
        self.assertIn("private_key", kinds)

    def test_never_returns_the_full_secret(self):
        findings = scan_secrets.scan(FIXTURES / "vuln_app")

        for item in findings:
            with self.subTest(kind=item["kind"]):
                self.assertIn("…", item["preview"])
                self.assertNotIn("AKIAIOSFODNN7EXAMPLE", item["preview"])
                self.assertNotIn("ghp_0123456789abcdefghijABCDEFGHIJ0123", item["preview"])

    def test_clean_directory_reports_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "app.py").write_text("print('hola')\n", encoding="utf-8", errors="replace")

            self.assertEqual(scan_secrets.scan(Path(tmp)), [])

    def test_cli_strict_exit_code(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "scan_secrets.py"), str(FIXTURES / "vuln_app"), "--strict"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("aws_access_key", result.stdout)


class TestMapFlows(unittest.TestCase):

    def test_finds_source_to_sink_candidates(self):
        findings = map_flows.scan(FIXTURES / "vuln_app" / "app.py")
        candidates = [item for item in findings if item["source_nearby"]]
        sinks = {item["sink"] for item in candidates}

        self.assertIn("sql", sinks)
        self.assertIn("command", sinks)

    def test_sink_without_source_is_not_a_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clean.py"
            path.write_text("def f():\n    print('ok')\n", encoding="utf-8", errors="replace")

            self.assertEqual(map_flows.scan(path), [])

    def test_cli_reports_counts(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "map_flows.py"), str(FIXTURES / "vuln_app"), "--json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        payload = json.loads(result.stdout)

        self.assertGreaterEqual(payload["candidates"], 2)
        self.assertEqual(result.returncode, 0)


class TestGrade(unittest.TestCase):

    def test_clean_project_gets_an_a(self):
        result = grade.grade_findings([])

        self.assertEqual(result["score"], 100)
        self.assertEqual(result["letter"], "A")

    def test_penalties_and_letters(self):
        high = grade.grade_findings([{"severity": "alta", "confidence": 9}])
        critical = grade.grade_findings([{"severity": "critical", "confidence": 10}])

        self.assertEqual(high["score"], 90)
        self.assertEqual(high["letter"], "A")
        self.assertEqual(critical["score"], 75)
        self.assertEqual(critical["letter"], "C")

    def test_low_confidence_is_discarded(self):
        result = grade.grade_findings([
            {"id": "F1", "severity": "critica", "confidence": 6},
            {"id": "F2", "severity": "media", "confidence": 8},
        ])

        self.assertEqual(result["accepted"], 1)
        self.assertEqual(len(result["discarded"]), 1)
        self.assertEqual(result["discarded"][0]["id"], "F1")
        self.assertEqual(result["score"], 97)

    def test_unknown_severity_is_discarded(self):
        result = grade.grade_findings([{"id": "X", "severity": "urgente", "confidence": 9}])

        self.assertEqual(result["accepted"], 0)
        self.assertEqual(result["letter"], "A")

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "ok.json"
            good.write_text(json.dumps({"findings": [{"severity": "baja", "confidence": 9}]}), encoding="utf-8", errors="replace")
            broken = Path(tmp) / "broken.json"
            broken.write_text("{no json", encoding="utf-8", errors="replace")

            ok = subprocess.run([sys.executable, str(SCRIPT_DIR / "grade.py"), str(good)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
            bad = subprocess.run([sys.executable, str(SCRIPT_DIR / "grade.py"), str(broken)],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace")

        self.assertEqual(ok.returncode, 0)
        self.assertIn("Nota: A", ok.stdout)
        self.assertEqual(bad.returncode, 2)


if __name__ == "__main__":
    unittest.main()
