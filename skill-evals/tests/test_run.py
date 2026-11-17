import json
import sys
import tempfile
import unittest
from pathlib import Path

from config import PHRASES, SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import evalkit  # noqa: E402
import run  # noqa: E402


class TestRun(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.phrases = json.loads(PHRASES.read_text(encoding="utf-8"))
        cls.document = evalkit.build_cases(cls.phrases)
        _, cls.router = evalkit.load_router(SKILL_ROOT.parent)
        cls.result = evalkit.evaluate(cls.router, cls.document)

    def test_every_case_passes_on_the_current_catalog(self):
        self.assertEqual(self.result["failures"], [])
        self.assertEqual(self.result["metrics"]["precision"], 1.0)
        self.assertEqual(self.result["metrics"]["recall"], 1.0)

    def test_metrics_shape(self):
        metrics = self.result["metrics"]
        self.assertEqual(metrics["cases"], len(self.document["cases"]))
        self.assertIn("mrr", metrics)
        self.assertEqual(set(metrics["by_kind"]), set(evalkit.KINDS))
        self.assertEqual(set(metrics["by_split"]), set(evalkit.SPLITS))

    def test_budget_is_reported(self):
        budget = self.result["budget"]
        self.assertEqual(budget["skills"], len(self.router.names))
        self.assertEqual(len(budget["heaviest"]), 5)
        self.assertEqual(budget["over_budget"], [])

    def test_collisions_have_threshold(self):
        for item in self.result["collisions"]:
            self.assertGreaterEqual(item["jaccard"], evalkit.COLLISION_JACCARD)

    def test_gates_parse(self):
        self.assertEqual(evalkit.parse_gates(["precision=0.95", "recall=0.98"]),
                         {"precision": 0.95, "recall": 0.98})
        with self.assertRaises(ValueError):
            evalkit.parse_gates(["precision"])
        with self.assertRaises(ValueError):
            evalkit.parse_gates(["precision=1.5"])
        with self.assertRaises(ValueError):
            evalkit.parse_gates(["velocidad=0.9"])

    def _cases_file(self, tmp: str) -> Path:
        path = Path(tmp) / "cases.json"
        path.write_text(json.dumps(self.document, ensure_ascii=False), encoding="utf-8")
        return path

    def test_cli_passes_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = self._cases_file(tmp)
            out = Path(tmp) / "run.json"
            code = run.main(["--cases", str(cases), "--out", str(out),
                             "--fail-under", "precision=0.95", "--json"])
            self.assertEqual(code, 0)
            written = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(written["gate"]["verdict"], "pass")

    def test_cli_fails_an_impossible_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = self._cases_file(tmp)
            self.assertEqual(
                run.main(["--cases", str(cases), "--fail-under", "precision=1.01"]),
                2,
            )

    def test_cli_detects_regressions_against_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            baseline = json.loads(json.dumps(self.result))
            baseline["cases"][0]["passed"] = True
            base_path = Path(tmp) / "baseline.json"
            base_path.write_text(json.dumps(baseline, ensure_ascii=False), encoding="utf-8")

            document = json.loads(json.dumps(self.document))
            target = next(case for case in document["cases"]
                          if case["kind"] == "positive" and case["expect"] == "eval-run")
            target["expect"] = "appsec-recon"
            tampered = Path(tmp) / "cases.json"
            tampered.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")

            code = run.main(["--cases", str(tampered), "--baseline", str(base_path),
                             "--fail-on-regression"])
            self.assertEqual(code, 1)

    def test_cli_rejects_invalid_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('{"format": "skill-evals-cases", "cases": []}', encoding="utf-8")
            self.assertEqual(run.main(["--cases", str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
