import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import plan_tests  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "app_riesgo"


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = plan_tests.main(argv)
    return code, out.getvalue()


def report(argv=None):
    code, output = run(["--root", str(FIXTURES), "--json"] + (argv or []))
    assert code == 0
    return json.loads(output)


class PlanRiskTests(unittest.TestCase):
    def test_module_without_test_is_high_in_a_risky_domain(self):
        findings = report()["findings"]
        auth = [item for item in findings if item["file"] == "auth.py" and item["rule"] == "modulo-sin-tests"]
        self.assertTrue(auth)
        self.assertEqual(auth[0]["severity"], "high")

    def test_money_domain_is_flagged(self):
        rules = {
            (item["file"], item["rule"])
            for item in report()["findings"]
        }
        self.assertIn(("payments.py", "dominio-riesgoso"), rules)
        self.assertIn(("payments.py", "modulo-sin-tests"), rules)

    def test_covered_module_is_not_reported(self):
        files = {item["file"] for item in report()["findings"]}
        self.assertNotIn("utils.py", files)

    def test_plan_is_sorted_by_score(self):
        scores = [item["score"] for item in report()["plan"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_limit_cuts_the_plan_and_the_ledger_records_why(self):
        data = report(["--limit", "1"])
        self.assertEqual(len(data["plan"]), 1)
        self.assertTrue(data["ledger"])
        self.assertTrue(all(item["reason"] == "fuera del presupuesto" for item in data["ledger"]))

    def test_min_score_filters_modules(self):
        data = report(["--min-score", "20"])
        self.assertTrue(all(item["score"] >= 20 for item in data["plan"]))

    def test_report_shape_is_stable(self):
        data = report()
        self.assertEqual(data["source"], "plan_tests")
        self.assertEqual(data["files"], 3)
        self.assertEqual(data["summary"]["total"], len(data["findings"]))
        for item in data["findings"]:
            self.assertEqual(sorted(item), ["file", "fix", "line", "message", "rule", "severity"])

    def test_output_is_deterministic(self):
        self.assertEqual(report(), report())

    def test_out_writes_the_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "plan.json"
            code, _ = run(["--root", str(FIXTURES), "--out", str(target)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["source"], "plan_tests")

    def test_missing_root_exits_two(self):
        code, _ = run(["--root", str(FIXTURES / "no-existe")])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
