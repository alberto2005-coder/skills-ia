"""Tests de `appsec-threat` y `appsec-deps`: mapeos, catálogo, SBOM y alcanzabilidad."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from appsec_config import SKILL_ROOT

SCRIPT_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import ledger  # noqa: E402
import sbom  # noqa: E402


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


class TestThreatModelDocs(unittest.TestCase):
    def setUp(self):
        self.reference = (SKILL_ROOT / "references" / "threat-model.md").read_text(encoding="utf-8")
        self.catalog = (SKILL_ROOT / "references" / "attack-classes.md").read_text(encoding="utf-8")
        self.template = (SKILL_ROOT / "templates" / "threat-model.md").read_text(encoding="utf-8")

    def test_owasp_2025_is_complete(self):
        for identifier, name in (
            ("A01", "Broken Access Control"),
            ("A02", "Security Misconfiguration"),
            ("A03", "Software Supply Chain Failures"),
            ("A04", "Cryptographic Failures"),
            ("A05", "Injection"),
            ("A06", "Insecure Design"),
            ("A07", "Authentication Failures"),
            ("A08", "Software or Data Integrity Failures"),
            ("A09", "Security Logging and Alerting Failures"),
            ("A10", "Mishandling of Exceptional Conditions"),
        ):
            with self.subTest(identifier=identifier):
                self.assertRegex(self.reference, rf"\| {identifier} \| {name} \|")

    def test_asvs_chapters_are_complete(self):
        for chapter in range(1, 18):
            with self.subTest(chapter=chapter):
                self.assertRegex(self.reference, rf"\| V{chapter} \|")

    def test_template_maps_trust_boundaries_to_controls(self):
        for heading in ("Activos", "Actores", "Límites de confianza", "Casos de abuso", "Mapeo"):
            with self.subTest(heading=heading):
                self.assertIn(f"## {heading}", self.template)
        self.assertIn("ASVS 5.0", self.template)
        self.assertIn("attack-classes.md", self.template)

    def test_catalog_covers_every_ledger_class(self):
        for attack_class in ledger.ATTACK_CLASSES:
            with self.subTest(attack_class=attack_class):
                self.assertIn(f"`{attack_class}`", self.catalog)

    def test_catalog_rows_carry_owasp_and_asvs(self):
        rows = [line for line in self.catalog.splitlines() if line.startswith("| `")]
        self.assertGreaterEqual(len(rows), len(ledger.ATTACK_CLASSES))
        for row in rows:
            with self.subTest(row=row[:40]):
                self.assertRegex(row, r"\| A\d\d")
                self.assertRegex(row, r"\| V\d+")


class TestLedgerClasses(unittest.TestCase):
    def test_expanded_classes_are_accepted(self):
        for name in ("secrets", "dependencies", "ssrf", "file-handling", "logging-monitoring", "privacy"):
            with self.subTest(name=name):
                self.assertIn(name, ledger.ATTACK_CLASSES)

    def test_add_accepts_a_new_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "coverage-ledger.json"
            path.write_text(
                json.dumps({
                    "audit_id": "a",
                    "target": "t",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "units": [],
                }),
                encoding="utf-8",
            )
            result = run(
                "ledger.py", "add", path,
                "--surface", "GET /api/export",
                "--subsystem", "reporting",
                "--class", "privacy",
                "--now", "2026-01-01T00:00:00Z",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("privacy", path.read_text(encoding="utf-8"))


PROJECT = {
    "package.json": json.dumps({
        "name": "demo",
        "dependencies": {"lodash": "4.17.20", "express": "^4.18.0"},
        "devDependencies": {"jest": "29.0.0"},
    }),
    "requirements.txt": "flask==2.0.0\nrequests>=2.0\n# comentario\n",
    "pyproject.toml": '[project]\nname = "demo"\ndependencies = [\n  "django==3.2.0",\n]\n',
    "go.mod": "module demo\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.7.0\n\tgolang.org/x/text v0.3.0 // indirect\n)\n",
}

APP_PY = "import flask\nimport requests\n"
TEST_PY = "import django\n"


class DepsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        for name, content in PROJECT.items():
            (self.project / name).write_text(content, encoding="utf-8")
        (self.project / "app.py").write_text(APP_PY, encoding="utf-8")
        (self.project / "tests").mkdir()
        (self.project / "tests" / "test_models.py").write_text(TEST_PY, encoding="utf-8")

    def build(self):
        out = self.root / "sbom.cdx.json"
        result = run("sbom.py", "build", self.project, "--output", out, "--now", "2026-01-01T00:00:00Z")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return out

    def advisories(self, items):
        path = self.root / "avisos.json"
        path.write_text(json.dumps({"advisories": items}), encoding="utf-8")
        return path

    def audit(self, *extra):
        sbom_path = self.build()
        path = self.advisories([
            {"id": "CVE-2020-8203", "package": "lodash", "ecosystem": "npm", "affected": "<4.17.21",
             "severity": "high", "summary": "prototype pollution"},
            {"id": "CVE-2023-0001", "package": "flask", "ecosystem": "pypi", "affected": "<2.2.5",
             "severity": "high", "summary": "fallo de sesión"},
            {"id": "CVE-2023-0002", "package": "django", "ecosystem": "pypi", "affected": "<4.0",
             "severity": "critical", "summary": "solo en tests"},
            {"id": "CVE-2023-0003", "package": "express", "ecosystem": "npm", "affected": "<5.0",
             "severity": "low", "summary": "no importado"},
        ])
        return run("sbom.py", "audit", sbom_path, "--advisories", path, "--repo", self.project, *extra)


class TestSbomBuild(DepsTest):
    def test_builds_one_component_per_manifest_entry(self):
        out = self.build()
        bom = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(bom["bomFormat"], "CycloneDX")
        self.assertEqual(bom["specVersion"], "1.5")
        purls = {item["purl"] for item in bom["components"]}
        self.assertIn("pkg:npm/lodash@4.17.20", purls)
        self.assertIn("pkg:npm/jest@29.0.0", purls)
        self.assertIn("pkg:pypi/flask@2.0.0", purls)
        self.assertIn("pkg:pypi/django@3.2.0", purls)
        self.assertIn("pkg:golang/github.com/gin-gonic/gin@1.7.0", purls)

    def test_unpinned_versions_are_declared(self):
        bom = json.loads(self.build().read_text(encoding="utf-8"))
        requests = next(item for item in bom["components"] if item["name"] == "requests")

        self.assertEqual(requests["version"], "unpinned")
        self.assertEqual(requests["purl"], "pkg:pypi/requests")

    def test_serial_is_reproducible(self):
        first = json.loads(self.build().read_text(encoding="utf-8"))["serialNumber"]
        second = json.loads(self.build().read_text(encoding="utf-8"))["serialNumber"]

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("urn:uuid:"))

    def test_validate_accepts_the_generated_bom(self):
        result = run("sbom.py", "validate", self.build())

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("OK", result.stdout)

    def test_validate_rejects_a_duplicated_ref(self):
        bom = json.loads(self.build().read_text(encoding="utf-8"))
        bom["components"].append(dict(bom["components"][0]))
        path = self.root / "roto.json"
        path.write_text(json.dumps(bom), encoding="utf-8")

        result = run("sbom.py", "validate", path)

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicado", result.stdout)

    def test_build_without_manifests_exits_one(self):
        empty = self.root / "vacio"
        empty.mkdir()

        self.assertEqual(run("sbom.py", "build", empty).returncode, 1)

    def test_build_missing_directory_exits_two(self):
        self.assertEqual(run("sbom.py", "build", self.root / "no-existe").returncode, 2)


class TestSbomAudit(DepsTest):
    def test_matches_cves_and_classifies_reachability(self):
        result = self.audit("--json")

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        by_name = {group["name"]: group for group in report["vulnerable"]}
        states = {
            name: group["advisories"][0]["reachability"] for name, group in by_name.items()
        }
        self.assertEqual(states["lodash"], "not-imported")
        self.assertEqual(states["flask"], "reachable")
        self.assertEqual(states["django"], "test-only")
        self.assertEqual(states["express"], "not-imported")
        self.assertEqual(report["counts"]["reachable"], 1)
        self.assertTrue(report["gate"]["blocked"])

    def test_gate_can_be_disabled(self):
        result = self.audit("--fail-on", "none")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("reachable 1", result.stdout)

    def test_medium_reachable_does_not_block(self):
        sbom_path = self.build()
        advisories = self.advisories([
            {"id": "CVE-2023-0001", "package": "flask", "ecosystem": "pypi", "affected": "<2.2.5",
             "severity": "medium"},
        ])

        result = run("sbom.py", "audit", sbom_path, "--advisories", advisories, "--repo", self.project)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("BLOQUEADO", result.stdout)

    def test_ecosystem_mismatch_is_ignored(self):
        sbom_path = self.build()
        advisories = self.advisories([
            {"id": "CVE-2023-9999", "package": "flask", "ecosystem": "npm", "affected": "<99",
             "severity": "critical"},
        ])

        report = json.loads(
            run("sbom.py", "audit", sbom_path, "--advisories", advisories,
                "--repo", self.project, "--json").stdout
        )

        self.assertEqual(report["vulnerable"], [])

    def test_without_repo_reachability_is_unknown(self):
        sbom_path = self.build()
        advisories = self.advisories([
            {"id": "CVE-2023-0001", "package": "flask", "ecosystem": "pypi", "affected": "<2.2.5",
             "severity": "high"},
        ])

        report = json.loads(
            run("sbom.py", "audit", sbom_path, "--advisories", advisories, "--json").stdout
        )

        self.assertEqual(report["vulnerable"][0]["advisories"][0]["reachability"], "unknown")
        self.assertFalse(report["gate"]["blocked"])

    def test_unpinned_component_is_reported_as_unresolved(self):
        sbom_path = self.build()
        advisories = self.advisories([
            {"id": "CVE-2023-0004", "package": "requests", "ecosystem": "pypi", "affected": "<3",
             "severity": "high"},
        ])

        report = json.loads(
            run("sbom.py", "audit", sbom_path, "--advisories", advisories,
                "--repo", self.project, "--json").stdout
        )

        self.assertEqual(report["unresolved"][0]["reason"], "unpinned")
        self.assertEqual(report["vulnerable"], [])

    def test_version_range_boundaries(self):
        self.assertTrue(sbom.satisfies("4.17.20", "<4.17.21"))
        self.assertFalse(sbom.satisfies("4.17.21", "<4.17.21"))
        self.assertTrue(sbom.satisfies("1.10.0", ">1.9.3"))
        self.assertTrue(sbom.satisfies("2.5.0", ">=2.0 <3.0"))
        self.assertFalse(sbom.satisfies("3.0.0", ">=2.0 <3.0"))
        with self.assertRaises(ValueError):
            sbom.satisfies("1.0.0", "~1.2")

    def test_output_file_is_written(self):
        sbom_path = self.build()
        advisories = self.advisories([
            {"id": "CVE-2023-0001", "package": "flask", "ecosystem": "pypi", "affected": "<2.2.5",
             "severity": "low"},
        ])
        out = self.root / "deps.json"

        result = run("sbom.py", "audit", sbom_path, "--advisories", advisories,
                     "--repo", self.project, "--output", out)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["sbom"], str(sbom_path))

    def test_invalid_advisories_exit_two(self):
        sbom_path = self.build()
        broken = self.root / "avisos.json"
        broken.write_text("{}", encoding="utf-8")

        self.assertEqual(
            run("sbom.py", "audit", sbom_path, "--advisories", broken).returncode,
            2,
        )


if __name__ == "__main__":
    unittest.main()
