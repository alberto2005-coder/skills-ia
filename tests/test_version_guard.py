"""Tests de la guardia de versiones: tocar un paquete exige subir su manifiesto."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import version_guard

GIT = [
    "git",
    "-c", "user.name=tests",
    "-c", "user.email=tests@example.com",
    "-c", "commit.gpgsign=false",
    "-c", "core.autocrlf=false",
]


def run_git(root: Path, *args: str) -> None:
    subprocess.run(
        GIT + list(args), cwd=str(root), capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=True,
    )


def write_package(root: Path, version: str) -> None:
    package = root / "demo"
    package.mkdir(exist_ok=True)
    manifest = {"format": "skills-ia-package", "name": "demo", "version": version, "skills": []}
    (package / "skills.json").write_text(json.dumps(manifest), encoding="utf-8")
    (package / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Paquete de prueba suficientemente largo.\n"
        'metadata:\n  package: demo\n  version: "%s"\n---\n\n# Demo\n' % version,
        encoding="utf-8",
    )


class VersionGuardTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        run_git(self.root, "init", "-q")
        write_package(self.root, "1.0.0")
        (self.root / "skills.json").write_text('{"version": "1.0.0", "packages": []}', encoding="utf-8")
        run_git(self.root, "add", "-A")
        run_git(self.root, "commit", "-qm", "base")

    def tearDown(self):
        self._tmp.cleanup()

    def commit_change(self, path: str, text: str, version: str | None = None) -> None:
        if version is not None:
            write_package(self.root, version)
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        run_git(self.root, "add", "-A")
        run_git(self.root, "commit", "-qm", "change")

    def test_change_without_bump_is_reported(self):
        self.commit_change("demo/scripts/tool.py", "print('hola')\n")

        problems = version_guard.lint_changes(self.root, "HEAD~1")

        self.assertEqual(len(problems), 1)
        self.assertIn("demo", problems[0])
        self.assertIn("1.0.0", problems[0])

    def test_change_with_bump_passes(self):
        self.commit_change("demo/scripts/tool.py", "print('hola')\n", version="1.1.0")

        self.assertEqual(version_guard.lint_changes(self.root, "HEAD~1"), [])

    def test_change_outside_packages_is_ignored(self):
        self.commit_change("docs/guia.md", "# Guia\n")

        self.assertEqual(version_guard.lint_changes(self.root, "HEAD~1"), [])

    def test_bumped_packages_reports_old_and_new_version(self):
        self.commit_change("demo/scripts/tool.py", "print('hola')\n", version="1.2.0")

        self.assertEqual(
            version_guard.bumped_packages(self.root, "HEAD~1"),
            {"demo": ("1.0.0", "1.2.0")},
        )

    def test_new_package_needs_no_bump(self):
        package = self.root / "nuevo"
        package.mkdir()
        (package / "skills.json").write_text(
            '{"name": "nuevo", "version": "0.1.0"}', encoding="utf-8"
        )
        run_git(self.root, "add", "-A")
        run_git(self.root, "commit", "-qm", "nuevo")

        self.assertEqual(version_guard.lint_changes(self.root, "HEAD~1"), [])

    def test_release_plan_lists_packages_and_tags(self):
        self.commit_change("demo/scripts/tool.py", "print('hola')\n", version="1.2.0")

        plan = version_guard.release_plan(self.root, "HEAD~1")

        self.assertEqual(
            plan["packages"],
            [{"package": "demo", "version": "1.2.0", "tag": "demo-v1.2.0"}],
        )
        self.assertIsNone(plan["bundle"])

    def test_release_plan_detects_a_bundle_change(self):
        (self.root / "skills.json").write_text('{"version": "5.1.0", "packages": []}', encoding="utf-8")
        run_git(self.root, "add", "-A")
        run_git(self.root, "commit", "-qm", "bundle")

        plan = version_guard.release_plan(self.root, "HEAD~1")

        self.assertEqual(plan["packages"], [])
        self.assertEqual(plan["bundle"], {"version": "5.1.0", "tag": "bundle-v5.1.0"})
        self.assertNotIn("bundle-v", plan["bundle"]["version"])  # el tag se construye una vez

    def test_release_plan_is_empty_without_changes(self):
        self.commit_change("docs/guia.md", "# Guia\n")

        self.assertEqual(
            version_guard.release_plan(self.root, "HEAD~1"), {"packages": [], "bundle": None}
        )

    def test_non_semver_version_is_reported(self):
        self.commit_change("demo/scripts/tool.py", "print('hola')\n", version="v1.3")

        problems = version_guard.lint_changes(self.root, "HEAD~1")

        self.assertEqual(len(problems), 1)
        self.assertIn("X.Y.Z", problems[0])


if __name__ == "__main__":
    unittest.main()
