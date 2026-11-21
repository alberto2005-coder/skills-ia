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

import mutation_targets  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "app_riesgo"


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = mutation_targets.main(argv)
    return code, out.getvalue()


def report(argv=None):
    code, output = run(["--root", str(FIXTURES), "--json", "--min-mutants", "1"] + (argv or []))
    assert code == 0
    return json.loads(output)


def target(name, data):
    found = [item for item in data["targets"] if item["function"] == name]
    assert found, name
    return found[0]


class MutationTargetTests(unittest.TestCase):
    def test_charge_concentrates_operators(self):
        charge = target("charge", report())
        self.assertGreaterEqual(charge["mutants"], 5)
        self.assertEqual(charge["operators"]["condicional-negada"], 2)
        self.assertEqual(charge["operators"]["limite"], 1)
        self.assertEqual(charge["operators"]["retorno"], 2)

    def test_login_has_a_boolean_operator(self):
        login = target("login", report())
        self.assertEqual(login["operators"]["booleano"], 1)

    def test_untested_target_is_reported_and_tested_one_is_not(self):
        data = report()
        files = {item["file"] for item in data["findings"]}
        self.assertIn("payments.py", files)
        self.assertNotIn("utils.py", files)
        self.assertEqual({item["rule"] for item in data["findings"]}, {"objetivo-sin-test"})

    def test_targets_are_ranked_by_mutants(self):
        mutants = [item["mutants"] for item in report()["targets"]]
        self.assertEqual(mutants, sorted(mutants, reverse=True))

    def test_limit_cuts_targets_and_records_the_rest(self):
        data = report(["--limit", "1"])
        self.assertEqual(len(data["targets"]), 1)
        self.assertTrue(data["discarded"])

    def test_min_mutants_filters_trivial_functions(self):
        data = report(["--min-mutants", "4"])
        self.assertTrue(all(item["mutants"] >= 4 for item in data["targets"]))
        self.assertNotIn("verify", {item["function"] for item in data["targets"]})

    def test_budget_sums_planned_mutants(self):
        data = report(["--limit", "2"])
        self.assertEqual(data["budget"]["planned_mutants"], sum(item["mutants"] for item in data["targets"]))

    def test_report_shape_is_stable(self):
        data = report()
        self.assertEqual(data["source"], "mutation_targets")
        self.assertEqual(data["files"], 3)
        self.assertEqual(data["summary"]["total"], len(data["findings"]))

    def test_out_writes_the_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mutacion.json"
            code, _ = run(["--root", str(FIXTURES), "--out", str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["source"], "mutation_targets")

    def test_missing_root_exits_two(self):
        code, _ = run(["--root", str(FIXTURES / "no-existe")])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
