import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "findings"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import review_findings  # noqa: E402


def run(*args):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = review_findings.main(list(args))
    return code, json.loads(buffer.getvalue()) if buffer.getvalue() else None


def report(**data):
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    handle.write(json.dumps(data))
    handle.close()
    return handle.name


class FindingsTests(unittest.TestCase):
    def setUp(self):
        self.security = FIXTURES / "seguridad.json"
        self.tests = FIXTURES / "pruebas.json"
        self.coverage = FIXTURES / "cobertura.json"

    def test_not_run_status_survives_the_merge(self):
        code, payload = run("--input", str(self.security), str(self.coverage), "--fail-on", "none")
        self.assertEqual(code, 0)
        checks = {item["check"]: item["status"] for item in payload["checks"]}
        self.assertEqual(checks["coverage"], "not_run")
        self.assertEqual(payload["not_run"], ["coverage"])

    def test_missing_status_is_not_run_never_clean(self):
        code, payload = run("--input", str(FIXTURES / "sin_estado.json"))
        self.assertEqual(code, 0)
        self.assertEqual(payload["checks"], [{"check": "lint", "status": "not_run"}])
        self.assertEqual(payload["summary"]["checks_ran"], 0)

    def test_duplicate_keeps_the_highest_severity(self):
        _, payload = run("--input", str(self.security), str(self.tests))
        duplicates = [item for item in payload["findings"] if item["duplicates"] > 1]
        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]["severity"], "high")
        self.assertEqual(duplicates[0]["duplicates"], 2)
        self.assertEqual(sorted(duplicates[0]["checks"]), ["security", "tests"])

    def test_required_check_that_did_not_run_fails(self):
        code, payload = run("--input", str(self.security), str(self.coverage), "--require", "coverage")
        self.assertEqual(code, 1)
        self.assertIn("check-no-ejecutado", [item["rule"] for item in payload["findings"]])

    def test_required_check_missing_entirely_fails(self):
        code, payload = run("--input", str(self.security), "--require", "mutation")
        self.assertEqual(code, 1)
        self.assertIn("no aparece en ningún informe", payload["findings"][0]["message"])

    def test_required_check_that_ran_passes(self):
        code, _ = run("--input", str(self.security), "--require", "security", "--fail-on", "none")
        self.assertEqual(code, 0)

    def test_summary_separates_ran_from_not_run(self):
        _, payload = run("--input", str(self.security), str(self.coverage))
        self.assertEqual(payload["summary"]["checks_ran"], 1)
        self.assertEqual(payload["summary"]["checks_not_run"], 1)

    def test_findings_are_sorted_by_severity(self):
        _, payload = run("--input", str(self.security))
        severities = [item["severity"] for item in payload["findings"]]
        self.assertEqual(severities, sorted(severities, key=lambda value: {"high": 0, "medium": 1, "low": 2}[value]))

    def test_unknown_severity_exits_two(self):
        path = report(check="raro", status="ran", findings=[{"file": "a.py", "line": 1, "rule": "x", "severity": "critico"}])
        code, _ = run("--input", path)
        self.assertEqual(code, 2)

    def test_unknown_status_exits_two(self):
        path = report(check="raro", status="quizas", findings=[])
        code, _ = run("--input", path)
        self.assertEqual(code, 2)

    def test_invalid_json_exits_two(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        handle.write("{no es json")
        handle.close()
        code, _ = run("--input", handle.name)
        self.assertEqual(code, 2)

    def test_not_run_alone_does_not_pass_as_clean(self):
        _, payload = run("--input", str(self.coverage), "--json")
        self.assertEqual(payload["summary"]["total"], 0)
        self.assertEqual(payload["checks"][0]["status"], "not_run")
        self.assertEqual(payload["not_run"], ["coverage"])


if __name__ == "__main__":
    unittest.main()
