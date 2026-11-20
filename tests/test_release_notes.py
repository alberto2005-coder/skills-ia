"""Tests de la descripción bilingüe de las releases."""

from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import release_notes  # noqa: E402

COMMITS = [
    "feat(db-sql-lint): flag the missing index",
    "fix(db-drift): keep the diff stable",
    "docs: explain the gate",
    "sin convención, pero no se pierde",
]


def write_bundle_root(root: Path, packages: int = 2, skills: int = 3) -> None:
    """Raíz mínima con el índice y el generador que reutiliza el script."""
    index = {
        "format": "skills-ia-index",
        "version": "5.1.2",
        "skills_total": skills,
        "packages": [{"name": "pkg-%d" % number, "version": "1.0.0"} for number in range(packages)],
    }
    (root / "skills.json").write_text(json.dumps(index), encoding="utf-8")
    target = root / "docs-sync-engine" / "scripts"
    target.mkdir(parents=True)
    shutil.copy(ROOT / "docs-sync-engine" / "scripts" / "changelog_gen.py", target)


class ReleaseNotesTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        write_bundle_root(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def test_package_notes_are_bilingual(self):
        document = release_notes.render(self.root, "2.1.1", COMMITS, "db-architect")

        self.assertIn("## db-architect v2.1.1", document)
        self.assertIn("**Instalación / Installation:** `/plugin install db-architect@skills-ia`", document)
        self.assertIn("cambios incluidos en este release", document)
        self.assertIn("changes shipped in this release", document)
        self.assertIn("sha256sum -c SHA256SUMS", document)

    def test_sections_carry_both_languages(self):
        document = release_notes.render(self.root, "2.1.1", COMMITS, "db-architect")

        self.assertIn("### Nuevo / New", document)
        self.assertIn("### Correcciones / Fixes", document)
        self.assertIn("### Documentación / Docs", document)
        self.assertIn("### Otros / Other", document)
        self.assertIn("- db-sql-lint: flag the missing index", document)

    def test_entries_are_sorted_and_not_duplicated(self):
        commits = ["feat(z): segundo", "feat(a): primero"]
        document = release_notes.render(self.root, "2.1.1", commits, "db-architect")

        self.assertEqual(document.count("primero"), 1)
        self.assertLess(document.index("primero"), document.index("segundo"))

    def test_bundle_notes_state_the_catalog_size(self):
        document = release_notes.render(self.root, "5.1.2", [], None)

        self.assertIn("## Catálogo completo v5.1.2 / Full catalog v5.1.2", document)
        self.assertIn("Los 2 paquetes del catálogo (3 skills)", document)
        self.assertIn("All 2 catalog packages (3 skills)", document)
        self.assertIn("/plugin marketplace add alberto2005-coder/skills-ia", document)

    def test_empty_release_says_so_in_both_languages(self):
        document = release_notes.render(self.root, "5.1.2", [], None)

        self.assertIn("_Sin cambios / No changes._", document)

    def test_cli_writes_the_file(self):
        source = self.root / "commits.txt"
        source.write_text("\n".join(COMMITS), encoding="utf-8")
        out = self.root / "notes.md"
        buffer = io.StringIO()

        with redirect_stdout(buffer):
            code = release_notes.main(
                [
                    "--root",
                    str(self.root),
                    "--version",
                    "2.1.1",
                    "--package",
                    "db-architect",
                    "--input",
                    str(source),
                    "--out",
                    str(out),
                ]
            )

        self.assertEqual(code, 0)
        self.assertIn("escrito %s" % out, buffer.getvalue())
        self.assertIn("## db-architect v2.1.1", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
