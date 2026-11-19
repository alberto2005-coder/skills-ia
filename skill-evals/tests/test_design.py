import json
import sys
import tempfile
import unittest
from pathlib import Path

from evals_config import PHRASES, SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import design  # noqa: E402
import evalkit  # noqa: E402


class TestDesign(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.phrases = json.loads(PHRASES.read_text(encoding="utf-8"))
        cls.document = evalkit.build_cases(cls.phrases)
        _, cls.router = evalkit.load_router(SKILL_ROOT.parent)

    def test_cases_are_valid_and_cover_the_catalog(self):
        self.assertEqual(evalkit.validate_cases(self.document, self.router.names), [])
        covered = {case["expect"] for case in self.document["cases"] if case.get("expect")}
        self.assertEqual(covered, self.router.names)

    def test_ids_are_unique_and_splits_stable(self):
        ids = [case["id"] for case in self.document["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for case in self.document["cases"]:
            self.assertEqual(case["split"], evalkit.split_for(case["id"]))

    def test_every_kind_is_present(self):
        kinds = {case["kind"] for case in self.document["cases"]}
        self.assertEqual(kinds, set(evalkit.KINDS))

    def test_negative_cases_name_a_winner_and_forbid(self):
        negatives = [case for case in self.document["cases"] if case["kind"] == "negative"]
        self.assertTrue(negatives)
        for case in negatives:
            self.assertTrue(case["expect"])
            self.assertTrue(case["forbid"])
            self.assertNotEqual(case["expect"], case["forbid"])

    def test_detects_skill_without_positives(self):
        broken = json.loads(json.dumps(self.document))
        broken["cases"] = [case for case in broken["cases"]
                           if not (case["kind"] == "positive" and case["expect"] == "eval-run")]
        problems = evalkit.validate_cases(broken, self.router.names)
        self.assertTrue(any("sin casos positivos" in item for item in problems), problems)

    def test_rejects_bad_ids_and_kinds(self):
        broken = json.loads(json.dumps(self.document))
        broken["cases"][0]["id"] = "repetido"
        broken["cases"][1]["id"] = "repetido"
        broken["cases"][2]["kind"] = "inventado"
        problems = evalkit.validate_cases(broken, self.router.names)
        self.assertTrue(any("repetido" in item for item in problems), problems)
        self.assertTrue(any("kind inválido" in item for item in problems), problems)

    def test_cli_writes_and_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "cases.json"
            self.assertEqual(
                design.main(["--from-phrases", str(PHRASES), "--out", str(out), "--json"]),
                0,
            )
            self.assertTrue(out.is_file())
            written = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(written["format"], evalkit.CASE_FORMAT)
            self.assertEqual(design.main(["--check", "--cases", str(out)]), 0)

    def test_cli_rejects_invalid_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bad.json"
            out.write_text('{"format": "otro", "cases": []}', encoding="utf-8")
            self.assertEqual(design.main(["--check", "--cases", str(out)]), 1)


if __name__ == "__main__":
    unittest.main()
