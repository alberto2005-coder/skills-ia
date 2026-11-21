import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import review_order  # noqa: E402
from pr_review_util import parse_diff  # noqa: E402


def analyze():
    files = parse_diff((FIXTURES / "orden.patch").read_text(encoding="utf-8"))
    return review_order.analyze(FIXTURES / "repo_orden", files)


class OrderTests(unittest.TestCase):
    def test_waves_put_the_base_before_its_consumers(self):
        payload = analyze()
        waves = [item["files"] for item in payload["waves"]]
        position = {path: index for index, wave in enumerate(waves) for path in wave}
        self.assertEqual(position["base.py"], 0)
        self.assertLess(position["base.py"], position["medio.py"])
        self.assertLess(position["medio.py"], position["alto.py"])
        self.assertEqual(position["alto.py"], 2)

    def test_edges_point_from_importer_to_dependency(self):
        payload = analyze()
        self.assertIn(["medio.py", "base.py"], payload["edges"])
        self.assertIn(["alto.py", "medio.py"], payload["edges"])

    def test_cycle_is_reported_as_high(self):
        payload = analyze()
        cycles = [item for item in payload["findings"] if item["rule"] == "ciclo-dependencias"]
        self.assertEqual({item["file"] for item in cycles}, {"ciclo_a.py", "ciclo_b.py"})
        self.assertTrue(all(item["severity"] == "high" for item in cycles))

    def test_standalone_markdown_is_not_an_orphan(self):
        payload = analyze()
        self.assertNotIn("notas.md", [item["file"] for item in payload["findings"] if item["rule"] == "huerfano"])

    def test_cycle_members_share_the_last_wave(self):
        payload = analyze()
        last = payload["waves"][-1]["files"]
        self.assertIn("ciclo_a.py", last)
        self.assertIn("ciclo_b.py", last)

    def test_markdown_is_flagged_without_a_graph(self):
        payload = analyze()
        rules = {item["file"]: item["rule"] for item in payload["findings"]}
        self.assertEqual(rules.get("notas.md"), "sin-grafo")

    def test_standalone_file_is_an_orphan(self):
        payload = analyze()
        orphans = [item["file"] for item in payload["findings"] if item["rule"] == "huerfano"]
        self.assertEqual(orphans, ["suelto.py"])

    def test_every_changed_file_lands_in_a_wave(self):
        payload = analyze()
        placed = {path for wave in payload["waves"] for path in wave["files"]}
        self.assertEqual(placed, {item["path"] for item in parse_diff((FIXTURES / "orden.patch").read_text(encoding="utf-8"))})

    def test_plan_is_deterministic(self):
        self.assertEqual(analyze(), analyze())

    def test_missing_root_exits_two(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = review_order.main(["--diff", str(FIXTURES / "orden.patch"), "--root", "no-existe"])
        self.assertEqual(code, 2)

    def test_unreadable_diff_exits_two(self):
        code = review_order.main(["--diff", "no-existe.patch", "--root", str(FIXTURES / "repo_orden")])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
