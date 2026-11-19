"""Tests del empaquetador: zip determinista, binarios rechazados y validación."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_package  # noqa: E402

SKILL_OK = """---
name: demo
description: Paquete de prueba con una descripción suficientemente larga.
metadata:
  package: demo
  version: "%s"
---

# Demo

Sin enlaces relativos, para que el lint del zip no dependa de otros ficheros.
"""


def write_package(root: Path, version: str = "1.0.0", skill_text: str | None = None) -> Path:
    package = root / "demo"
    package.mkdir(parents=True, exist_ok=True)
    manifest = {
        "format": "skills-ia-package",
        "name": "demo",
        "version": version,
        "skills": [{"name": "demo", "path": "SKILL.md"}],
    }
    (package / "skills.json").write_text(json.dumps(manifest), encoding="utf-8")
    (package / "SKILL.md").write_text(skill_text or SKILL_OK % version, encoding="utf-8")
    return package


class BuildPackageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.out = self.root / "dist"
        write_package(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def build(self, out: Path | None = None):
        return build_package.build_package(self.root, "demo", out or self.out, "test-commit")

    def test_archive_is_deterministic(self):
        first, digest_first = self.build()
        second, digest_second = self.build(self.root / "dist2")

        self.assertEqual(digest_first, digest_second)
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_manifest_is_inside_the_archive(self):
        zip_path, _ = self.build()

        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            data = json.loads(archive.read("manifest.json"))

        self.assertIn("demo/SKILL.md", names)
        self.assertIn("demo/skills.json", names)
        self.assertEqual(data["package"], "demo")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["commit"], "test-commit")
        self.assertEqual(data["skills"], ["demo"])
        self.assertEqual(names, sorted(names))

    def test_checksum_file_matches_the_archive(self):
        zip_path, digest = self.build()
        checksum = (self.out / (zip_path.name + ".sha256")).read_text(encoding="utf-8")

        self.assertEqual(checksum.strip(), "%s  %s" % (digest, zip_path.name))

    def test_excluded_directories_are_left_out(self):
        package = self.root / "demo"
        (package / "tests").mkdir()
        (package / "tests" / "test_demo.py").write_text("pass\n", encoding="utf-8")
        (package / "__pycache__").mkdir()
        (package / "__pycache__" / "x.pyc").write_text("cache\n", encoding="utf-8")
        (package / ".venv").mkdir()
        (package / ".venv" / "lib.py").write_text("x = 1\n", encoding="utf-8")

        zip_path, _ = self.build()

        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()

        self.assertFalse([name for name in names if "tests/" in name or "__pycache__" in name])
        self.assertFalse([name for name in names if ".venv" in name])

    def test_known_binary_suffix_is_left_out(self):
        package = self.root / "demo"
        (package / "logo.png").write_bytes(bytes([0x89, 0x50, 0x4E, 0x47, 0x00, 0x01]))

        zip_path, _ = self.build()

        with zipfile.ZipFile(zip_path) as archive:
            self.assertNotIn("demo/logo.png", archive.namelist())

    def test_binary_content_with_innocent_suffix_is_rejected(self):
        package = self.root / "demo"
        (package / "assets").mkdir()
        (package / "assets" / "datos.dat").write_bytes(bytes([0xFF, 0xFE, 0x00, 0x01]))

        with self.assertRaises(build_package.BuildError):
            self.build()

        self.assertEqual(list(self.out.glob("*")) if self.out.exists() else [], [])

    def test_package_that_fails_the_lint_leaves_no_zip(self):
        write_package(self.root, skill_text="---\nname: demo\ndescription: corto\n---\n\n# Demo\n")

        with self.assertRaises(build_package.BuildError):
            self.build()

        self.assertEqual(list(self.out.glob("*.zip")), [])

    def test_all_builds_every_package_of_the_index(self):
        (self.root / "skills.json").write_text(
            json.dumps({"packages": [{"name": "demo", "path": "demo", "version": "1.0.0"}]}),
            encoding="utf-8",
        )

        code = build_package.main(["--all", "--root", str(self.root), "--out", str(self.out)])

        self.assertEqual(code, 0)
        self.assertEqual([path.name for path in self.out.glob("*.zip")], ["demo-1.0.0.zip"])


if __name__ == "__main__":
    unittest.main()
