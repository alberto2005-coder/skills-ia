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
  Describe el paquete y su uso con una frase suficientemente larga. Úsala cuando
  haya que demostrar que la activación funciona. English: describe the package.
---

# Demo
"""


ALIGNED_SKILL = """---
name: demo
description: >
  Describe el paquete y su uso con una frase suficientemente larga. Úsala cuando
  haya que demostrar que la versión cuadra. English: describe the package.
metadata:
  package: demo
  version: "1.0.0"
---

# Demo
"""


NO_TRIGGER_SKILL = """---
name: demo
description: >
  Describe el paquete y su uso con una frase suficientemente larga, pero sin
  decir cuándo usarla ni repetirlo en otro idioma.
metadata:
  package: demo
  version: "1.0.0"
---

# Demo
"""


NO_BILINGUAL_SKILL = """---
name: demo
description: >
  Describe el paquete y su uso con una frase suficientemente larga. Úsala cuando
  haya que comprobar que falta la versión en inglés.
metadata:
  package: demo
  version: "1.0.0"
---

# Demo
"""


MARKETPLACE = '{"name": "demo-market", "owner": {"name": "demo"}, "plugins": [{"name": "demo", "source": "./demo", "version": "9.9.9", "skills": ["."]}]}'


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

    def test_description_without_trigger_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "demo"
            skill.mkdir()
            (skill / "SKILL.md").write_text(NO_TRIGGER_SKILL, encoding="utf-8")

            problems = lint_frontmatter.lint_repository(root)

        self.assertTrue(
            any("caso de uso" in item for item in problems.get("demo/SKILL.md", [])),
            problems,
        )

    def test_description_without_the_other_language_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "demo"
            skill.mkdir()
            (skill / "SKILL.md").write_text(NO_BILINGUAL_SKILL, encoding="utf-8")

            problems = lint_frontmatter.lint_repository(root)

        self.assertTrue(
            any("otra lengua" in item for item in problems.get("demo/SKILL.md", [])),
            problems,
        )

    def test_marketplace_version_must_match_the_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "demo"
            package.mkdir()
            (package / "skills.json").write_text(
                '{"version": "1.0.0", "skills": [{"name": "demo", "path": "SKILL.md"}]}',
                encoding="utf-8",
            )
            (package / "SKILL.md").write_text(ALIGNED_SKILL, encoding="utf-8")
            (root / "skills.json").write_text(
                '{"packages": [{"name": "demo", "path": "demo", "version": "1.0.0"}]}',
                encoding="utf-8",
            )
            marketplace = root / ".claude-plugin"
            marketplace.mkdir()
            (marketplace / "marketplace.json").write_text(MARKETPLACE, encoding="utf-8")

            problems = lint_frontmatter.lint_repository(root)

        self.assertIn(".claude-plugin/marketplace.json", problems)
        self.assertTrue(
            any("versión" in item for item in problems[".claude-plugin/marketplace.json"]),
            problems,
        )

    def test_index_version_must_match_the_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "demo"
            package.mkdir()
            (package / "skills.json").write_text(
                '{"name": "demo", "version": "1.0.0"}', encoding="utf-8"
            )
            (package / "SKILL.md").write_text(ALIGNED_SKILL, encoding="utf-8")
            (root / "skills.json").write_text(
                '{"packages": [{"name": "demo", "path": "demo", "version": "2.0.0"}]}',
                encoding="utf-8",
            )

            problems = lint_frontmatter.lint_repository(root)

        self.assertIn("skills.json", problems)
        self.assertTrue(any("índice declara" in item for item in problems["skills.json"]))

    def test_skill_version_must_match_the_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "demo"
            package.mkdir()
            (package / "skills.json").write_text(
                '{"name": "demo", "version": "1.1.0"}', encoding="utf-8"
            )
            (package / "SKILL.md").write_text(ALIGNED_SKILL, encoding="utf-8")
            (root / "skills.json").write_text(
                '{"packages": [{"name": "demo", "path": "demo", "version": "1.1.0"}]}',
                encoding="utf-8",
            )

            problems = lint_frontmatter.lint_repository(root)

        self.assertIn("demo/SKILL.md", problems)
        self.assertTrue(any("metadata.version" in item for item in problems["demo/SKILL.md"]))

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
