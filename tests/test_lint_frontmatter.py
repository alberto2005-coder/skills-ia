"""Tests del linter de frontmatter que corre en CI."""

import sys
import tempfile
import unittest
from pathlib import Path

import lint_frontmatter

ROOT = Path(__file__).resolve().parent.parent

# `description` con dos puntos y espacio dentro de un escalar plano: un parser
# YAML real rechaza el bloque entero (`mapping values are not allowed here`).
INVALID_YAML_SKILL = """---
name: demo
description: Describe el paquete y su uso. English: describe the package and its scope.
---

# Demo
"""

FOLDED_DESCRIPTION_SKILL = """---
name: demo
description: >
  Describe el paquete y su uso con una frase suficientemente larga.
---

# Demo
"""


class TestLintFrontmatter(unittest.TestCase):
    def test_repository_is_clean(self):
        problems = lint_frontmatter.lint_repository(ROOT)

        self.assertEqual(problems, {}, f"lint con problemas: {sorted(problems)[:5]}")

    def test_missing_description_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "paquete" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo\ndescription:\n---\n\n# Demo\n", encoding="utf-8"
            )

            problems = lint_frontmatter.lint_repository(root)

        self.assertIn("paquete/demo/SKILL.md", problems)
        self.assertTrue(any("description" in item for item in problems["paquete/demo/SKILL.md"]))

    def test_name_must_match_the_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "paquete" / "otra"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Una descripción suficientemente larga.\n---\n\n# Demo\n",
                encoding="utf-8",
            )

            problems = lint_frontmatter.lint_repository(root)

        self.assertIn("paquete/otra/SKILL.md", problems)
        self.assertTrue(any("carpeta" in item for item in problems["paquete/otra/SKILL.md"]))

    def test_invalid_yaml_description_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "paquete" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(INVALID_YAML_SKILL, encoding="utf-8")

            problems = lint_frontmatter.lint_repository(root)

        self.assertIn("paquete/demo/SKILL.md", problems)
        self.assertTrue(any("YAML" in item for item in problems["paquete/demo/SKILL.md"]))

    def test_folded_description_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "paquete" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(FOLDED_DESCRIPTION_SKILL, encoding="utf-8")

            problems = lint_frontmatter.lint_repository(root)

        self.assertEqual(problems, {})

    def test_manifest_points_to_a_real_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "paquete"
            package.mkdir()
            (package / "skills.json").write_text(
                '{"skills": [{"name": "fantasma", "path": "fantasma/SKILL.md"}]}',
                encoding="utf-8",
            )

            problems = lint_frontmatter.lint_repository(root)

        self.assertIn("paquete/skills.json", problems)
        self.assertTrue(any("inexistente" in item for item in problems["paquete/skills.json"]))

    def test_tests_directories_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = root / "paquete" / "tests" / "fixtures" / "rota"
            fixture.mkdir(parents=True)
            (fixture / "SKILL.md").write_text("sin frontmatter", encoding="utf-8")

            self.assertEqual(lint_frontmatter.lint_repository(root), {})

    def test_cli_exit_codes(self):
        import subprocess

        clean = subprocess.run(
            [sys.executable, str(ROOT / "tests" / "lint_frontmatter.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)


if __name__ == "__main__":
    unittest.main()
