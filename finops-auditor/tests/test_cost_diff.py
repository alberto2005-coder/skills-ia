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

import cost_diff  # noqa: E402

BEFORE = {
    "resources": [
        {"id": "api", "monthly_cost": 100.0},
        {"id": "worker", "monthly_cost": 50.0},
    ]
}

AFTER_STABLE = {
    "resources": [
        {"id": "api", "monthly_cost": 100.0},
        {"id": "worker", "monthly_cost": 50.0},
    ]
}

AFTER_GROWN = {
    "resources": [
        {"id": "api", "monthly_cost": 130.0},
        {"id": "worker", "monthly_cost": 50.0},
        {"id": "batch", "monthly_cost": 40.0},
    ]
}


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cost_diff.main(argv)
    return code, out.getvalue()


class TestCostDiff(unittest.TestCase):

    def _pair(self, tmp, before, after):
        root = Path(tmp)
        old = root / "before.json"
        new = root / "after.json"
        old.write_text(json.dumps(before), encoding="utf-8")
        new.write_text(json.dumps(after), encoding="utf-8")
        return str(old), str(new)

    def test_identical_inventories_are_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = self._pair(tmp, BEFORE, AFTER_STABLE)
            code, output = run(["--before", old, "--after", new, "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["delta"], 0)
            self.assertEqual(report["delta_percent"], 0)
            self.assertEqual(report["breaches"], [])

    def test_growth_is_reported_with_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = self._pair(tmp, BEFORE, AFTER_GROWN)
            code, output = run(["--before", old, "--after", new, "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["before_total"], 150.0)
            self.assertEqual(report["after_total"], 220.0)
            self.assertEqual(report["delta"], 70.0)
            self.assertEqual(report["resources"]["added"], [{"id": "batch", "cost": 40.0}])
            self.assertEqual(report["resources"]["changed"][0]["id"], "api")
            self.assertEqual(report["resources"]["changed"][0]["delta"], 30.0)

    def test_max_increase_breaks_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = self._pair(tmp, BEFORE, AFTER_GROWN)
            code, output = run(["--before", old, "--after", new, "--max-increase", "50", "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual([item["guardrail"] for item in report["breaches"]], ["max-increase"])
            self.assertEqual(report["breaches"][0]["actual"], 70.0)

    def test_max_percent_breaks_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = self._pair(tmp, BEFORE, AFTER_GROWN)
            code, output = run(["--before", old, "--after", new, "--max-percent", "10", "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["breaches"][0]["guardrail"], "max-percent")
            self.assertAlmostEqual(report["breaches"][0]["actual"], 46.67, places=2)

    def test_budget_applies_to_the_new_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = self._pair(tmp, BEFORE, AFTER_GROWN)
            code, output = run(["--before", old, "--after", new, "--budget", "200", "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["breaches"][0]["guardrail"], "budget")
            self.assertEqual(report["breaches"][0]["actual"], 220.0)

    def test_all_guardrails_can_break_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = self._pair(tmp, BEFORE, AFTER_GROWN)
            code, _ = run(["--before", old, "--after", new, "--max-increase", "10",
                           "--max-percent", "5", "--budget", "100"])
            self.assertEqual(code, 1)

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = self._pair(tmp, BEFORE, AFTER_GROWN)
            code, _ = run(["--before", old, "--after", new, "--budget", "10", "--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_missing_inventory_exits_two(self):
        code, _ = run(["--before", "no-existe.json", "--after", "tampoco.json"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
