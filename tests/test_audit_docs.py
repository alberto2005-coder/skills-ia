"""Tests de la auditoría de documentación: detecta lo que debe y calla el resto."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

import audit_docs  # noqa: E402

INDEX = {
    "format": "skills-ia-index",
    "version": "5.0.0",
    "skills_total": 3,
    "packages": [
        {
            "name": "demo",
            "path": "demo",
            "version": "1.0.0",
            "manifest": "demo/skills.json",
            "skill_count": 2,
            "skills": ["demo", "demo-sub"],
        },
        {
            "name": "otro",
            "path": "otro",
            "version": "1.0.0",
            "manifest": "otro/skills.json",
            "skill_count": 1,
            "skills": ["otro"],
        },
    ],
}

README = """# Repo

| Módulo | Propósito | Skills |
| :--- | :--- | ---: |
| **[`demo`](demo/)** | Paquete de demo. | 2 |
| **[`otro`](otro/)** | Otro paquete. | 1 |

#### `demo` — maestro + 1 sub-skill

```bash
py demo/scripts/x.py --json
```
"""

DOC_INDEX = """# Índice

| Paquete | Skills | Maestro | Sub-skills |
|---|---:|---|---|
| `demo` | 2 | `demo` | `demo-sub` |
| `otro` | 1 | `otro` | — |

Ver `skills.json` y `docs/demo.md`.
"""

DEMO = """# Demo

**Paquete de 2 skills:** maestro + 1 sub-skill.

```bash
py demo/scripts/x.py --json
```
"""


def build_repo(root: Path) -> None:
    """Repo mínimo: dos paquetes, su tabla, sus guías y un script con un flag."""
    (root / "skills.json").write_text(json.dumps(INDEX, indent=2), encoding="utf-8")
    (root / "README.md").write_text(README, encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "index.md").write_text(DOC_INDEX, encoding="utf-8")
    (root / "docs" / "demo.md").write_text(DEMO, encoding="utf-8")
    (root / "docs" / "otro.md").write_text("# Otro\n", encoding="utf-8")
    for name, skills in (("demo", 2), ("otro", 1)):
        package = root / name
        (package / "scripts").mkdir(parents=True)
        (package / "skills.json").write_text(json.dumps({"name": name, "version": "1.0.0"}), encoding="utf-8")
        (package / "scripts" / "x.py").write_text(
            'import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument("--json")\n',
            encoding="utf-8",
        )


class AuditDocsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        build_repo(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def problems(self) -> dict[str, list[str]]:
        return audit_docs.audit(self.root)

    def append(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")

    def test_clean_repo_has_no_drift(self):
        self.assertEqual({title: found for title, found in self.problems().items() if found}, {})
        self.assertEqual(audit_docs.main(["--root", str(self.root)]), 0)

    def test_missing_repo_path_is_reported(self):
        self.append("docs/demo.md", "\nVer `scripts/nope.py`.\n")

        found = self.problems()["Rutas citadas que no existen"]
        self.assertEqual(len(found), 1)
        self.assertIn("scripts/nope.py", found[0])
        self.assertEqual(audit_docs.main(["--root", str(self.root)]), 1)

    def test_package_relative_path_is_accepted(self):
        self.append("docs/demo.md", "\nVer `scripts/x.py`.\n")

        self.assertEqual(self.problems()["Rutas citadas que no existen"], [])

    def test_unknown_flag_is_reported(self):
        self.append("docs/demo.md", "\nUsa `--inventado`.\n")

        found = self.problems()["Flags documentadas que no existen"]
        self.assertEqual(len(found), 1)
        self.assertIn("--inventado", found[0])

    def test_known_flag_passes(self):
        self.append("docs/demo.md", "\nUsa `--json`.\n")

        self.assertEqual(self.problems()["Flags documentadas que no existen"], [])

    def test_table_count_is_checked(self):
        readme = self.root / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8").replace("| 2 |", "| 3 |"), encoding="utf-8")

        found = self.problems()["Tablas de paquetes"]
        self.assertEqual(len(found), 1)
        self.assertIn("«demo»", found[0])

    def test_master_heading_is_checked(self):
        readme = self.root / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace("maestro + 1 sub-skill", "maestro + 5 sub-skills"),
            encoding="utf-8",
        )

        found = self.problems()["Cabeceras «maestro + N»"]
        self.assertEqual(len(found), 1)
        self.assertIn("maestro + 5", found[0])

    def test_skill_claim_is_checked(self):
        # Sin el recuento correcto en la guía, el que declara debe ser el del manifiesto.
        (self.root / "docs" / "demo.md").write_text("# Demo\n\nSon 7 skills.\n", encoding="utf-8")

        found = self.problems()["Recuentos de skills por guía"]
        self.assertEqual(len(found), 1)
        self.assertIn("7", found[0])

    def test_anchor_must_match_a_heading(self):
        self.append("docs/demo.md", "\n[Ir](#no-existe).\n")

        found = self.problems()["Enlaces internos"]
        self.assertEqual(len(found), 1)
        self.assertIn("#no-existe", found[0])

    def test_slug_matches_github_behaviour(self):
        self.assertEqual(audit_docs.slug("🇪🇸 Español"), "-español")
        self.assertEqual(audit_docs.slug("Contratos y `--flags`"), "contratos-y---flags")
        self.assertEqual(
            audit_docs.anchors_of("## Tests\n\n## Tests\n\n## Tests\n"),
            {"tests", "tests-1", "tests-2"},
        )

    def test_main_rejects_a_root_without_index(self):
        empty = self.root / "vacio"
        empty.mkdir()
        buffer = io.StringIO()

        with redirect_stdout(io.StringIO()), redirect_stderr(buffer):
            self.assertEqual(audit_docs.main(["--root", str(empty)]), 2)
        self.assertIn("no parece la raíz", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
