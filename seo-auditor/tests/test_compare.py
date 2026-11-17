# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import compare, report


def rec(check_id, status, severity="must"):
    return {"id": check_id, "status": status, "dimension": "tecnico",
            "severity": severity, "title": "Comprobación " + check_id,
            "citation": "https://developers.google.com/search/docs",
            "evidence": status, "url": "https://example.com"}


def payload(checks):
    return report.build_payload({"mode": "page", "target": "https://example.com",
                                 "checks": checks, "findings": [], "data": {}})


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.old = payload([rec("A", "fail"), rec("B", "pass"), rec("C", "fail")])
        self.new = payload([rec("A", "pass"), rec("B", "fail"), rec("D", "fail")])
        self.diff = compare.compare(self.old, self.new)

    def test_classification(self):
        counts = self.diff["counts"]
        self.assertEqual(counts["mejorado"], 1)
        self.assertEqual(counts["empeorado"], 1)
        self.assertEqual(counts["nuevo"], 1)
        self.assertEqual(counts["resuelto"], 1)

    def test_entries(self):
        kinds = {(entry["id"], entry["tipo"]) for entry in self.diff["entries"]}
        self.assertIn(("A", "mejorado"), kinds)
        self.assertIn(("B", "empeorado"), kinds)
        self.assertIn(("D", "nuevo"), kinds)
        self.assertIn(("C", "resuelto"), kinds)

    def test_new_must_failures_are_flagged(self):
        ids = {entry["id"] for entry in self.diff["new_must_fails"]}
        self.assertIn("B", ids)
        self.assertIn("D", ids)

    def test_score_delta_and_markdown(self):
        self.assertLess(abs(self.diff["score_delta"]), 0.1)
        markdown = compare.render_markdown(self.diff)
        self.assertIn("mejorado", markdown)
        self.assertIn("Resuelto", markdown)

    def test_write_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = compare.write(self.diff, tmp)
            self.assertTrue((Path(out) / "compare.json").exists())
            self.assertTrue((Path(out) / "compare.md").exists())

    def test_identical_audits(self):
        diff = compare.compare(self.old, self.old)
        self.assertEqual(diff["score_delta"], 0.0)
        self.assertEqual(diff["entries"], [])
        self.assertTrue(all(value == 0 for key, value in diff["counts"].items()
                            if key != "igual"))


if __name__ == "__main__":
    unittest.main()
