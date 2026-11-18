"""Tests de las comprobaciones de enlaces relativos e índice del linter."""

import json
import tempfile
import unittest
from pathlib import Path

import lint_frontmatter

ROOT = Path(__file__).resolve().parent.parent


class TestLintLinks(unittest.TestCase):
    def test_repository_links_are_clean(self):
        self.assertEqual(lint_frontmatter.lint_links(ROOT), {})

    def test_broken_relative_link_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "guia.md").write_text(
                "Ver [la guía](otra.md) y [la web](https://example.com).\n", encoding="utf-8"
            )

            problems = lint_frontmatter.lint_links(root)

        self.assertIn("docs/guia.md", problems)
        self.assertEqual(len(problems["docs/guia.md"]), 1)
        self.assertIn("otra.md", problems["docs/guia.md"][0])

    def test_anchor_and_external_links_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "guia.md").write_text(
                "[sección](#indice) [web](https://example.com) [correo](mailto:a@b.c)\n",
                encoding="utf-8",
            )

            self.assertEqual(lint_frontmatter.lint_links(root), {})


class TestLintIndex(unittest.TestCase):
    def _repo(self, tmp, *, declared_total=2, skill_count=2):
        root = Path(tmp)
        (root / "paquete" / "demo").mkdir(parents=True)
        (root / "paquete" / "SKILL.md").write_text("---\nname: paquete\n---\n", encoding="utf-8")
        (root / "paquete" / "demo" / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
        (root / "paquete" / "skills.json").write_text(
            json.dumps({"skills": [
                {"name": "paquete", "path": "SKILL.md"},
                {"name": "demo", "path": "demo/SKILL.md"},
            ]}),
            encoding="utf-8",
        )
        (root / "skills.json").write_text(
            json.dumps({"skills_total": declared_total, "packages": [{
                "name": "paquete", "path": "paquete", "manifest": "paquete/skills.json",
                "skill_count": skill_count, "skills": ["paquete", "demo"],
            }]}),
            encoding="utf-8",
        )
        return root

    def test_consistent_index_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(lint_frontmatter.lint_index(self._repo(tmp)), [])

    def test_total_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            problems = lint_frontmatter.lint_index(self._repo(tmp, declared_total=9))

        self.assertTrue(any("skills_total" in item for item in problems))

    def test_skill_count_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            problems = lint_frontmatter.lint_index(self._repo(tmp, skill_count=4))

        self.assertTrue(any("skill_count" in item for item in problems))

    def test_missing_skill_file_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            (root / "paquete" / "demo" / "SKILL.md").unlink()

            problems = lint_frontmatter.lint_index(root)

        self.assertTrue(any("falta el SKILL.md" in item for item in problems))


class TestLintPackageDocs(unittest.TestCase):
    def _repo(self, tmp, *, guide=True, readme_link=True, index_link=True):
        root = Path(tmp)
        (root / "paquete" / "demo").mkdir(parents=True)
        (root / "paquete" / "SKILL.md").write_text("---\nname: paquete\n---\n", encoding="utf-8")
        (root / "paquete" / "demo" / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
        (root / "paquete" / "skills.json").write_text(
            json.dumps({"skills": [
                {"name": "paquete", "path": "SKILL.md"},
                {"name": "demo", "path": "demo/SKILL.md"},
            ]}),
            encoding="utf-8",
        )
        (root / "skills.json").write_text(
            json.dumps({"skills_total": 2, "packages": [{
                "name": "paquete", "path": "paquete", "manifest": "paquete/skills.json",
                "skill_count": 2, "skills": ["paquete", "demo"],
            }]}),
            encoding="utf-8",
        )
        (root / "docs").mkdir()
        if guide:
            (root / "docs" / "paquete.md").write_text("# Paquete\n", encoding="utf-8")
        readme = "- [Guía](docs/paquete.md)\n" if readme_link else "# Sin enlaces\n"
        (root / "README.md").write_text(readme, encoding="utf-8")
        index = "- [**Paquete**](paquete.md)\n" if index_link else "# Índice\n"
        (root / "docs" / "index.md").write_text(index, encoding="utf-8")
        return root

    def test_documented_package_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(lint_frontmatter.lint_package_docs(self._repo(tmp)), {})

    def test_missing_guide_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            problems = lint_frontmatter.lint_package_docs(self._repo(tmp, guide=False))

        self.assertIn("docs/", problems)
        self.assertIn("falta la guía docs/paquete.md", problems["docs/"])

    def test_missing_readme_link_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            problems = lint_frontmatter.lint_package_docs(self._repo(tmp, readme_link=False))

        self.assertIn("README.md", problems)
        self.assertIn("el paquete «paquete» no tiene enlace a su guía", problems["README.md"])

    def test_missing_index_link_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            problems = lint_frontmatter.lint_package_docs(self._repo(tmp, index_link=False))

        self.assertIn("docs/index.md", problems)

    def test_repository_packages_are_documented(self):
        self.assertEqual(lint_frontmatter.lint_package_docs(ROOT), {})


if __name__ == "__main__":
    unittest.main()
