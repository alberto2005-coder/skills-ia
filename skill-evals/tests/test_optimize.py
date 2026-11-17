import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from config import REPO_ROOT, SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import evalkit  # noqa: E402
import optimize  # noqa: E402

ALPHA = """---
name: alpha
description: >
  Analiza documentos y genera resúmenes ejecutivos.
license: MIT
metadata:
  package: demo
  version: "1.0.0"
---

# Alpha

Cuerpo de prueba.
"""

BETA = """---
name: beta
description: >
  Revisa contratos y detecta cláusulas de riesgo.
license: MIT
metadata:
  package: demo
  version: "1.0.0"
---

# Beta

Cuerpo de prueba.
"""


def cases() -> dict:
    return {
        "format": "skill-evals-cases",
        "version": "1.0",
        "threshold": 0.3,
        "cases": [
            {"id": "pos:alpha:1", "prompt": "audita la seguridad de la aplicación",
             "expect": "alpha", "kind": "positive", "split": "train"},
            {"id": "pos:alpha:2", "prompt": "audita la seguridad del servicio web",
             "expect": "alpha", "kind": "positive", "split": "test"},
            {"id": "pos:beta:1", "prompt": "revisa el contrato y sus cláusulas de riesgo",
             "expect": "beta", "kind": "positive", "split": "train"},
            {"id": "pos:beta:2", "prompt": "revisa el contrato y detecta cláusulas abusivas",
             "expect": "beta", "kind": "positive", "split": "test"},
        ],
    }


class TestOptimize(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "tests").mkdir()
        shutil.copyfile(REPO_ROOT / "tests" / "trigger_router.py",
                        self.root / "tests" / "trigger_router.py")
        for name, content in (("alpha", ALPHA), ("beta", BETA)):
            (self.root / name).mkdir()
            (self.root / name / "SKILL.md").write_text(content, encoding="utf-8")
        self.cases_path = self.root / "cases.json"
        self.cases_path.write_text(json.dumps(cases()), encoding="utf-8")
        self.tr, self.router = evalkit.load_router(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_rewrite_preserves_other_frontmatter(self):
        path = self.root / "alpha" / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        updated = optimize.rewrite_description(text, "Nueva descripción de prueba.")

        self.assertIn("name: alpha", updated)
        self.assertIn("license: MIT", updated)
        self.assertIn("  package: demo", updated)
        self.assertIn("description: >", updated)
        self.assertIn("  Nueva descripción de prueba.", updated)
        self.assertNotIn("resúmenes ejecutivos", updated)

    def test_candidates_add_missing_terms(self):
        terms = ["audita", "seguridad", "aplicacion"]
        built = optimize.candidate_descriptions("Analiza documentos.", terms)

        self.assertTrue(built)
        for candidate in built:
            self.assertTrue(set(candidate["terms"]) <= set(terms))
            self.assertIn("También cubre:", candidate["description"])
        self.assertEqual(built[-1]["terms"], terms)

    def test_plan_proposes_improvement_with_diff(self):
        result = optimize.plan(self.router, self.tr, cases(), "alpha")

        self.assertEqual(result["status"], "improved")
        self.assertIn("seguridad", result["chosen"]["terms"])
        self.assertGreater(result["chosen"]["test"]["precision"],
                           result["baseline"]["test"]["precision"])
        self.assertIn("+++", result["diff"])
        self.assertIn("seguridad", result["diff"])

    def test_plan_is_deterministic(self):
        first = optimize.plan(self.router, self.tr, cases(), "alpha")
        second = optimize.plan(self.router, self.tr, cases(), "alpha")

        self.assertEqual(first["diff"], second["diff"])
        self.assertEqual(first["chosen"]["terms"], second["chosen"]["terms"])

    def test_plan_without_failures_does_nothing(self):
        result = optimize.plan(self.router, self.tr, cases(), "beta")

        self.assertEqual(result["status"], "no_candidates")
        self.assertIsNone(result["chosen"])
        self.assertEqual(result["diff"], "")

    def test_cli_is_dry_run_by_default(self):
        before = (self.root / "alpha" / "SKILL.md").read_text(encoding="utf-8")
        code = optimize.main(["--repo", str(self.root), "--skill", "alpha",
                              "--cases", str(self.cases_path)])

        self.assertEqual(code, 0)
        after = (self.root / "alpha" / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_cli_apply_writes_and_stops_improving(self):
        code = optimize.main(["--repo", str(self.root), "--skill", "alpha",
                              "--cases", str(self.cases_path), "--apply", "--json"])
        self.assertEqual(code, 0)
        updated = (self.root / "alpha" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("También cubre:", updated)

        _, router = evalkit.load_router(self.root)
        again = optimize.plan(router, self.tr, cases(), "alpha")
        self.assertNotEqual(again["status"], "improved")

    def test_cli_fails_when_nothing_to_improve(self):
        code = optimize.main(["--repo", str(self.root), "--skill", "beta",
                              "--cases", str(self.cases_path)])
        self.assertEqual(code, 1)

    def test_cli_rejects_unknown_skill(self):
        code = optimize.main(["--repo", str(self.root), "--skill", "gamma",
                              "--cases", str(self.cases_path)])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
