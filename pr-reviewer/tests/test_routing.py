import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import review_routing  # noqa: E402
from pr_review_util import parse_diff  # noqa: E402


def run(*args):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = review_routing.main(list(args))
    return code, buffer.getvalue()


def payload(owners):
    files = parse_diff((FIXTURES / "riesgo.patch").read_text(encoding="utf-8"))
    rules, error = review_routing.load_rules(FIXTURES / owners)
    assert error is None, error
    return review_routing.analyze(files, rules[0], rules[1])


class RoutingTests(unittest.TestCase):
    def test_specific_rule_wins_over_general(self):
        report = payload("owners.json")
        assigned = {item["path"]: item["reviewers"] for item in report["assignments"]}
        self.assertEqual(assigned["src/auth/session.py"], ["ana"])

    def test_general_rule_covers_the_rest(self):
        report = payload("owners.json")
        assigned = {item["path"]: item["reviewers"] for item in report["assignments"]}
        self.assertEqual(assigned["requirements.txt"], ["equipo"])
        self.assertEqual(assigned["README.md"], ["equipo"])

    def test_sensitive_path_with_one_reviewer_is_flagged(self):
        report = payload("owners.json")
        rules = {item["rule"] for item in report["findings"]}
        self.assertIn("sin-respaldo", rules)

    def test_without_rules_every_file_is_unowned(self):
        report = payload("owners_vacio.json")
        unowned = [item for item in report["findings"] if item["rule"] == "ruta-sin-dueno"]
        self.assertEqual(len(unowned), 5)
        self.assertTrue(all(item["severity"] == "high" for item in unowned))

    def test_unowned_file_fails_the_high_gate(self):
        code, _ = run("--diff", str(FIXTURES / "riesgo.patch"), "--owners", str(FIXTURES / "owners_vacio.json"))
        self.assertEqual(code, 1)

    def test_overloaded_reviewer_is_medium(self):
        report = payload("owners_pesado.json")
        overload = [item for item in report["findings"] if item["rule"] == "revisor-sobrecargado"]
        self.assertEqual(len(overload), 1)
        self.assertEqual(overload[0]["severity"], "medium")
        self.assertIn("solo", overload[0]["message"])

    def test_overload_fails_only_at_medium(self):
        base = ["--diff", str(FIXTURES / "riesgo.patch"), "--owners", str(FIXTURES / "owners_pesado.json")]
        self.assertEqual(run(*base)[0], 0)
        self.assertEqual(run(*base, "--fail-on", "medium")[0], 1)

    def test_load_counts_one_file_once_per_reviewer(self):
        report = payload("owners_pesado.json")
        self.assertEqual(report["load"], {"solo": 5})

    def test_unreadable_rules_exit_two(self):
        code, _ = run("--diff", str(FIXTURES / "riesgo.patch"), "--owners", "no-existe.json")
        self.assertEqual(code, 2)

    def test_clean_routing_passes_the_high_gate(self):
        code, _ = run("--diff", str(FIXTURES / "riesgo.patch"), "--owners", str(FIXTURES / "owners.json"))
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
