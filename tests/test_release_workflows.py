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

    def test_no_job_level_if_uses_the_matrix_context(self):
        # `matrix` no existe en `jobs.<id>.if`: GitHub rechaza el workflow entero.
        for name, job in load("tag-release.yml")["jobs"].items():
            self.assertNotIn("matrix", str(job.get("if", "")), name)

    def test_the_matrix_comes_from_its_own_never_empty_output(self):
        job = load("tag-release.yml")["jobs"]["release-packages"]
        script = plan_script()

        self.assertEqual(
            job["strategy"]["matrix"]["include"],
            "${{ fromJson(needs.plan.outputs.matrix) }}",
        )
        self.assertIn("needs.plan.outputs.packages != '[]'", job["if"])
        self.assertEqual(
            load("tag-release.yml")["jobs"]["plan"]["outputs"]["matrix"],
            "${{ steps.plan.outputs.matrix }}",
        )
        self.assertIn('matrix=[{"package":"-"', script)


    def test_lint_job_validates_workflows_with_actionlint(self):
        steps = load("tests.yml")["jobs"]["lint"]["steps"]
        scripts = [step.get("run", "") for step in steps]

        install = [s for s in scripts if "actionlint" in s and "sha256sum -c -" in s]
        check = [s for s in scripts if s.strip() == "actionlint -color"]
        self.assertTrue(install, "falta el paso que instala actionlint con checksum")
        self.assertTrue(check, "falta el paso que ejecuta actionlint")

    def test_tag_step_sets_a_git_identity_the_runner_lacks(self):
        # El runner no trae user.name/user.email y `git tag -a` falla sin ellos.
        steps = load("tag-release.yml")["jobs"]["plan"]["steps"]
        script = next(
            step["run"]
            for step in steps
            if step.get("name") == "Create and push tags idempotently"
        )

        self.assertIn("git config user.name", script)
        self.assertIn("git config user.email", script)
        self.assertLess(script.index("git config user.name"), script.index('git tag -a "$tag"'))

    def test_manual_run_accepts_an_explicit_base(self):
        inputs = load("tag-release.yml")["on"]["workflow_dispatch"]["inputs"]
        steps = load("tag-release.yml")["jobs"]["plan"]["steps"]
        env = next(step["env"] for step in steps if step.get("id") == "plan")

        self.assertTrue(inputs["base"]["required"])
        self.assertEqual(env["BASE_SHA"], "${{ inputs.base || github.event.before }}")

    def test_tag_push_retries_and_checks_the_remote(self):
        # Un push rechazado no debe abortar el resto ni dejar el repo a medias.
        steps = load("tag-release.yml")["jobs"]["plan"]["steps"]
        script = next(
            step["run"]
            for step in steps
            if step.get("name") == "Create and push tags idempotently"
        )

        self.assertIn("for attempt in 1 2 3", script)
        self.assertIn("sleep $((attempt * 5))", script)
        self.assertIn("git ls-remote --exit-code --tags origin", script)
        self.assertIn("quedaron sin publicar", script)
    def test_releases_use_the_bilingual_notes(self):
        # La descripción de la release va en español e inglés.
        for name in ("release-package.yml", "release-bundle.yml"):
            with self.subTest(workflow=name):
                text = (WORKFLOWS / name).read_text(encoding="utf-8")

                self.assertIn("scripts/release_notes.py", text)
                self.assertNotIn("changelog_gen.py", text)

if __name__ == "__main__":
    unittest.main()
