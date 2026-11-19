"""Contrato entre el workflow de tags y los workflows de release."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"


def load(name: str) -> dict:
    """Workflow como dict; en YAML 1.1 la clave `on` se parsea como True."""
    data = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    if "on" not in data and True in data:
        data["on"] = data[True]
    return data


def plan_script() -> str:
    steps = load("tag-release.yml")["jobs"]["plan"]["steps"]
    for step in steps:
        if step.get("id") == "plan":
            return step["run"]
    raise AssertionError("tag-release.yml no tiene un paso con id=plan")


class TagReleaseContractTests(unittest.TestCase):
    def test_bundle_output_carries_the_version_not_the_tag(self):
        script = plan_script()

        self.assertIn(".bundle.version", script)
        self.assertNotIn(".bundle.tag", script)

    def test_bundle_release_prefixes_the_tag_only_once(self):
        call = load("tag-release.yml")["jobs"]["release-bundle"]["with"]

        self.assertEqual(call["version"], "${{ needs.plan.outputs.bundle }}")
        self.assertEqual(call["tag"], "bundle-v${{ needs.plan.outputs.bundle }}")
        self.assertNotIn("bundle-v", call["version"])

    def test_release_bundle_declares_the_inputs_the_caller_passes(self):
        inputs = load("release-bundle.yml")["on"]["workflow_call"]["inputs"]
        call = load("tag-release.yml")["jobs"]["release-bundle"]["with"]

        self.assertEqual(sorted(inputs), ["tag", "version"])
        self.assertEqual(sorted(call), sorted(inputs))

    def test_package_release_passes_the_three_inputs_it_declares(self):
        inputs = load("release-package.yml")["on"]["workflow_call"]["inputs"]
        call = load("tag-release.yml")["jobs"]["release-packages"]["with"]

        self.assertEqual(sorted(inputs), ["package", "tag", "version"])
        self.assertEqual(sorted(call), sorted(inputs))


if __name__ == "__main__":
    unittest.main()
