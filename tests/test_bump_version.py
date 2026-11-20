"""Tests del subidor de versiones: los cuatro sitios, y lo que debe rechazar."""

from __future__ import annotations

import datetime
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import bump_version  # noqa: E402

SKILL = """---
name: %s
description: Skill de prueba con descripción suficientemente larga. Úsala cuando
  haga falta probar el subidor de versiones. English: test the version bumper.
metadata:
  package: demo
  version: "%s"
---

# %s
"""


def write_skill(path: Path, name: str, version: str, newline: str = "\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (SKILL % (name, version, name)).replace("\n", newline)
    path.write_bytes(text.encode("utf-8"))


def write_repo(root: Path, newline: str = "\n") -> None:
    """Repo mínimo con un paquete, dos skills, un fixture y los dos índices."""
    package = root / "demo"
    package.mkdir(parents=True, exist_ok=True)
    manifest = {
        "format": "skills-ia-package",
        "name": "demo",
        "version": "1.0.0",
        "skills": [
            {"name": "demo", "path": "SKILL.md"},
            {"name": "demo-sub", "path": "demo-sub/SKILL.md"},
        ],
    }
    (package / "skills.json").write_bytes(
        (json.dumps(manifest, indent=2) + "\n").replace("\n", newline).encode("utf-8")
    )
    write_skill(package / "SKILL.md", "demo", "1.0.0", newline)
    write_skill(package / "demo-sub" / "SKILL.md", "demo-sub", "1.0.0", newline)
    fixture = package / "tests" / "fixtures" / "vieja" / "SKILL.md"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_bytes(b"---\nname: vieja\ndescription: fixture\n---\n")

    index = {
        "format": "skills-ia-index",
        "version": "5.0.0",
        "updated": "2026-01-01",
        "packages": [
            {
                "name": "demo",
                "path": "demo",
                "version": "1.0.0",
                "manifest": "demo/skills.json",
                "skill_count": 2,
                "skills": ["demo", "demo-sub"],
            }
        ],
    }
    (root / "skills.json").write_bytes(
        (json.dumps(index, indent=2) + "\n").replace("\n", newline).encode("utf-8")
    )

    marketplace = {
        "name": "demo-market",
        "owner": {"name": "quien-sea"},
        "version": "5.0.0",
        "plugins": [{"name": "demo", "source": "./demo", "version": "1.0.0", "skills": ["."]}],
    }
    market_path = root / ".claude-plugin" / "marketplace.json"
    market_path.parent.mkdir(parents=True, exist_ok=True)
    market_path.write_bytes(
        (json.dumps(marketplace, indent=2) + "\n").replace("\n", newline).encode("utf-8")
    )


def run(root: Path, *extra: str) -> tuple[int, str, str]:
    """Ejecuta el CLI y devuelve (código, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = bump_version.main(["--root", str(root), *extra])
    return code, out.getvalue(), err.getvalue()


class BumpVersionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        write_repo(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def json_of(self, relative: str) -> dict:
        return json.loads((self.root / relative).read_text(encoding="utf-8"))

    def test_updates_every_place_the_version_is_declared(self):
        code, _, err = run(self.root, "demo", "1.0.1")

        self.assertEqual(code, 0, err)
        self.assertEqual(self.json_of("demo/skills.json")["version"], "1.0.1")
        index = self.json_of("skills.json")
        self.assertEqual(index["packages"][0]["version"], "1.0.1")
        self.assertEqual(index["version"], "5.0.1")
        self.assertEqual(index["updated"], datetime.date.today().isoformat())
        market = self.json_of(".claude-plugin/marketplace.json")
        self.assertEqual(market["plugins"][0]["version"], "1.0.1")
        self.assertEqual(market["version"], "5.0.1")
        for relative in ("demo/SKILL.md", "demo/demo-sub/SKILL.md"):
            text = (self.root / relative).read_text(encoding="utf-8")
            self.assertIn('  version: "1.0.1"', text)

    def test_leaves_test_fixtures_alone(self):
        run(self.root, "demo", "1.0.1")
        fixture = self.root / "demo" / "tests" / "fixtures" / "vieja" / "SKILL.md"

        self.assertEqual(fixture.read_bytes(), b"---\nname: vieja\ndescription: fixture\n---\n")

    def test_rejects_a_version_that_does_not_go_up(self):
        for version in ("1.0.0", "0.9.9"):
            with self.subTest(version=version):
                code, _, err = run(self.root, "demo", version)
                self.assertEqual(code, 1)
                self.assertIn("debe ser mayor", err)
        self.assertEqual(self.json_of("demo/skills.json")["version"], "1.0.0")

    def test_rejects_a_version_that_is_not_semver(self):
        code, _, err = run(self.root, "demo", "1.0")

        self.assertEqual(code, 1)
        self.assertIn("X.Y.Z", err)

    def test_rejects_a_package_without_manifest(self):
        code, _, err = run(self.root, "fantasma", "1.0.1")

        self.assertEqual(code, 1)
        self.assertIn("no existe el paquete", err)

    def test_no_bundle_keeps_the_index_version(self):
        code, out, err = run(self.root, "demo", "1.0.1", "--no-bundle")

        self.assertEqual(code, 0, err)
        self.assertEqual(self.json_of("skills.json")["version"], "5.0.0")
        self.assertEqual(self.json_of("demo/skills.json")["version"], "1.0.1")
        self.assertNotIn("bundle", out)

    def test_dry_run_changes_nothing(self):
        before = (self.root / "demo" / "skills.json").read_bytes()
        code, out, _ = run(self.root, "demo", "1.0.1", "--dry-run")

        self.assertEqual(code, 0)
        self.assertIn("cambiaría demo/skills.json", out)
        self.assertEqual((self.root / "demo" / "skills.json").read_bytes(), before)

    def test_keeps_crlf_endings(self):
        self.tearDown()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        write_repo(self.root, newline="\r\n")

        code, _, err = run(self.root, "demo", "1.0.1")

        self.assertEqual(code, 0, err)
        for relative in ("demo/skills.json", "skills.json", ".claude-plugin/marketplace.json"):
            raw = (self.root / relative).read_bytes()
            self.assertGreater(raw.count(b"\r\n"), 0, relative)
            self.assertEqual(raw.count(b"\n"), raw.count(b"\r\n"), relative)


if __name__ == "__main__":
    unittest.main()
