import json
import sys
import tempfile
import unittest
from pathlib import Path

from evals_config import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import evalkit  # noqa: E402
import report  # noqa: E402


def sample_run() -> dict:
    return {
        "format": evalkit.RUN_FORMAT,
        "version": "1.0",
        "threshold": 0.3,
        "metrics": {
            "cases": 2,
            "passed": 1,
            "precision": 0.5,
            "recall": 0.5,
            "mrr": 0.5,
            "false_negatives": 1,
            "false_positives": 0,
            "collisions": 1,
            "negative_violations": 0,
            "by_kind": {kind: {"cases": 0, "passed": 0} for kind in evalkit.KINDS},
            "by_split": {split: {"cases": 0, "passed": 0} for split in evalkit.SPLITS},
        },
        "collisions": [{"a": "x", "b": "y", "jaccard": 0.75}],
        "budget": {
            "skills": 1,
            "catalog_tokens": 10,
            "catalog_limit": 6000,
            "catalog_ok": True,
            "body_token_limit": 5000,
            "body_line_limit": 500,
            "over_budget": [],
            "heaviest": [{"skill": "x", "description_tokens": 10,
                          "body_tokens": 20, "body_lines": 5}],
        },
        "failures": [{
            "id": "pos:x:1",
            "prompt": "<script>alert(1)</script>",
            "kind": "positive",
            "expect": "x",
            "best": "y",
            "score": 0.1,
            "sibling": "y",
        }],
        "cases": [{"id": "pos:x:1", "passed": False}, {"id": "pos:y:1", "passed": True}],
        "gate": {"checks": [], "regressions": [], "verdict": "fail"},
    }


class TestReport(unittest.TestCase):

    def test_markdown_has_verdict_and_failures(self):
        text = report.render_markdown(sample_run())

        self.assertIn("FAIL", text)
        self.assertIn("pos:x:1", text)
        self.assertIn("Colisiones", text)
        self.assertIn("Presupuesto", text)

    def test_markdown_reports_baseline_changes(self):
        diff = {"regressions": ["pos:x:1"], "fixes": [], "new": [], "removed": []}
        text = report.render_markdown(sample_run(), diff)

        self.assertIn("Regresiones", text)
        self.assertIn("pos:x:1", text)

    def test_html_escapes_case_text(self):
        text = report.render_html(sample_run())

        self.assertNotIn("<script>alert", text)
        self.assertIn("&lt;script&gt;", text)
        self.assertIn("<!DOCTYPE html>", text)
        self.assertNotIn("<script src", text)

    def test_render_is_deterministic(self):
        self.assertEqual(report.render_markdown(sample_run()), report.render_markdown(sample_run()))
        self.assertEqual(report.render_html(sample_run()), report.render_html(sample_run()))

    def test_cli_writes_both_formats(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_path = Path(tmp) / "run.json"
            run_path.write_text(json.dumps(sample_run(), ensure_ascii=False), encoding="utf-8")
            md_path = Path(tmp) / "informe.md"
            html_path = Path(tmp) / "informe.html"

            self.assertEqual(
                report.main(["--run", str(run_path), "--out", str(md_path)]), 0)
            self.assertEqual(
                report.main(["--run", str(run_path), "--format", "html", "--out", str(html_path)]), 0)
            self.assertIn("Informe de evaluación", md_path.read_text(encoding="utf-8"))
            self.assertIn("<!DOCTYPE html>", html_path.read_text(encoding="utf-8"))

    def test_cli_rejects_foreign_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "other.json"
            path.write_text('{"format": "otro"}', encoding="utf-8")
            self.assertEqual(report.main(["--run", str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
