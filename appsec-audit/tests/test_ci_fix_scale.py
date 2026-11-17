"""Tests de las fases 3-5: CI y agentes, remediación y escala."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from config import SKILL_ROOT

SCRIPT_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import validate_findings  # noqa: E402


def run(script, *args, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


DANGEROUS_WORKFLOW = """name: ci
on:
  pull_request_target:
permissions:
  contents: write
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
      - run: echo "${{ github.event.pull_request.title }}"
      - uses: some/action@main
"""

SAFE_WORKFLOW = """name: ci
on:
  pull_request:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@0123456789abcdef0123456789abcdef01234567
"""


def sarif_run(results, rules=None, version="2.1.0"):
    return {
        "version": version,
        "runs": [{
            "tool": {"driver": {"name": "Semgrep", "rules": rules or []}},
            "results": results,
        }],
    }


def sarif_result(rule_id="py.sql-injection", line=42, message="SQL injection", uri="app/api.py"):
    return {
        "ruleId": rule_id,
        "level": "error",
        "message": {"text": message},
        "locations": [{"physicalLocation": {
            "artifactLocation": {"uri": uri},
            "region": {"startLine": line},
        }}],
    }


SQL_RULE = {
    "id": "py.sql-injection",
    "properties": {"tags": ["CWE-89: SQL Injection"], "security-severity": "8.0"},
    "defaultConfiguration": {"level": "error"},
}


class CiFixScaleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
        return path


class TestDetectTools(CiFixScaleTest):
    def test_reports_the_no_execution_policy(self):
        result = run("detect_tools.py", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("no se instalan ni se ejecutan", report["policy"])
        self.assertGreaterEqual(len(report["tools"]), 10)

    def test_detects_a_binary_from_path_without_running_it(self):
        binaries = self.root / "bin"
        binaries.mkdir()
        for name in ("semgrep", "semgrep.exe"):
            candidate = binaries / name
            candidate.write_text("@echo off\n", encoding="utf-8")
            candidate.chmod(0o755)
        env = {**os.environ, "PATH": str(binaries)}

        result = run("detect_tools.py", "--require", "semgrep", "--json", env=env)

        report = json.loads(result.stdout)
        self.assertEqual(report["required_missing"], [])
        semgrep = next(tool for tool in report["tools"] if tool["name"] == "semgrep")
        self.assertTrue(semgrep["available"])
        self.assertIn(str(binaries), semgrep["path"])

    def test_missing_required_tool_exits_one(self):
        result = run("detect_tools.py", "--require", "herramienta-inexistente-xyz")

        self.assertEqual(result.returncode, 1)
        self.assertIn("herramienta-inexistente-xyz", result.stderr)

    def test_workflow_with_pull_request_target_and_write_is_critical(self):
        workflow = self.write("ci.yml", DANGEROUS_WORKFLOW)
        result = run("detect_tools.py", "--workflow", workflow, "--json")

        findings = json.loads(result.stdout)["workflow"]["findings"]
        critical = {item["rule"] for item in findings if item["severity"] == "critica"}
        self.assertIn("CI-PRTARGET", critical)
        self.assertIn("CI-WRITE-TOKEN", critical)
        self.assertIn("CI-UNTRUSTED-CHECKOUT", critical)
        self.assertEqual(result.returncode, 0)

    def test_fail_on_critical_gate(self):
        workflow = self.write("ci.yml", DANGEROUS_WORKFLOW)

        self.assertEqual(
            run("detect_tools.py", "--workflow", workflow, "--fail-on-critical").returncode,
            1,
        )

    def test_safe_workflow_has_no_critical(self):
        workflow = self.write("ci.yml", SAFE_WORKFLOW)
        result = run("detect_tools.py", "--workflow", workflow, "--fail-on-critical", "--json")

        report = json.loads(result.stdout)
        self.assertEqual(report["workflow"]["critical"], 0)
        self.assertEqual(result.returncode, 0)

    def test_missing_workflow_exits_one(self):
        self.assertEqual(run("detect_tools.py", "--workflow", self.root / "no.yml").returncode, 1)


class TestNormalizeSarif(CiFixScaleTest):
    def test_imports_sarif_as_needs_validation(self):
        sarif = self.write("semgrep.sarif", sarif_run([sarif_result()], [SQL_RULE]))
        out = self.root / "findings.json"

        result = run("normalize_sarif.py", sarif, "--output", out, "--target", "demo")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(payload["target"], "demo")
        finding = payload["findings"][0]
        self.assertEqual(finding["id"], "F-001")
        self.assertEqual(finding["verdict"], "needs_validation")
        self.assertEqual(finding["confidence"], 5)
        self.assertEqual(finding["cwe"], "CWE-89")
        self.assertEqual(finding["location"], {"file": "app/api.py", "line": 42})
        self.assertNotIn("severity", finding)
        self.assertEqual(validate_findings.validate_payload(payload), [])

    def test_results_without_location_are_counted_not_imported(self):
        orphan = {"ruleId": "x", "message": {"text": "sin ubicación"}, "locations": []}
        sarif = self.write("s.sarif", sarif_run([sarif_result(), orphan]))

        result = run("normalize_sarif.py", sarif)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 hallazgo(s) importado(s)", result.stdout)
        self.assertIn("1 sin ubicación", result.stdout)

    def test_fail_on_high_triggers_on_security_severity(self):
        sarif = self.write("s.sarif", sarif_run([sarif_result()], [SQL_RULE]))

        result = run("normalize_sarif.py", sarif, "--fail-on", "high")

        self.assertEqual(result.returncode, 1)

    def test_fail_on_critical_does_not_trigger_on_high(self):
        sarif = self.write("s.sarif", sarif_run([sarif_result()], [SQL_RULE]))

        self.assertEqual(run("normalize_sarif.py", sarif, "--fail-on", "critical").returncode, 0)

    def test_upload_check_accepts_a_clean_sarif(self):
        sarif = self.write("ok.sarif", sarif_run([sarif_result()], [SQL_RULE]))

        result = run("normalize_sarif.py", sarif, "--check")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("apto para upload-sarif", result.stdout)

    def test_upload_check_rejects_bad_version(self):
        sarif = self.write("old.sarif", sarif_run([sarif_result()], [SQL_RULE], version="2.0.0"))

        result = run("normalize_sarif.py", sarif, "--check")

        self.assertEqual(result.returncode, 1)
        self.assertIn("2.1.0", result.stdout)

    def test_missing_file_exits_two(self):
        self.assertEqual(run("normalize_sarif.py", self.root / "no.sarif").returncode, 2)


PATCH = """--- a/app.py
+++ b/app.py
@@ -1,3 +1,3 @@
 import os
-x = 1
+x = 2
 print(x)
"""

BROKEN_PATCH = """--- a/app.py
+++ b/app.py
@@ -1,3 +1,3 @@
 import os
-y = 9
+y = 10
 print(x)
"""

ORIGINAL = "import os\nx = 1\nprint(x)\n"


class TestApplyPatch(CiFixScaleTest):
    def setUp(self):
        super().setUp()
        self.file = self.write("app.py", ORIGINAL)
        self.patch = self.write("fix.diff", PATCH)
        self.broken = self.write("broken.diff", BROKEN_PATCH)

    def content(self):
        return self.file.read_text(encoding="utf-8")

    def test_dry_run_does_not_write(self):
        result = run("apply_patch.py", self.file, "--diff", self.patch)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DRY-RUN", result.stdout)
        self.assertEqual(self.content(), ORIGINAL)
        self.assertFalse(self.file.with_suffix(".py.orig").exists())

    def test_apply_without_confirmation_is_refused(self):
        result = run("apply_patch.py", self.file, "--diff", self.patch, "--apply")

        self.assertEqual(result.returncode, 1)
        self.assertIn("--yes", result.stderr)
        self.assertEqual(self.content(), ORIGINAL)

    def test_apply_with_confirmation_writes_and_keeps_a_backup(self):
        result = run("apply_patch.py", self.file, "--diff", self.patch, "--apply", "--yes")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("x = 2", self.content())
        self.assertEqual(self.file.with_suffix(".py.orig").read_text(encoding="utf-8"), ORIGINAL)

    def test_mismatched_context_is_refused(self):
        result = run("apply_patch.py", self.file, "--diff", self.broken, "--apply", "--yes")

        self.assertEqual(result.returncode, 1)
        self.assertIn("contexto no coincide", result.stdout)
        self.assertEqual(self.content(), ORIGINAL)

    def test_verification_without_sandbox_is_refused(self):
        result = run(
            "apply_patch.py", self.file, "--diff", self.patch,
            "--apply", "--yes", "--verify", "echo ok",
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("sandbox", result.stderr)
        self.assertEqual(self.content(), ORIGINAL)

    def test_verification_runs_only_with_declared_sandbox(self):
        result = run(
            "apply_patch.py", self.file, "--diff", self.patch,
            "--apply", "--yes", "--sandbox", "contenedor-auditoria", "--verify", "echo ok",
            "--json",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "applied")
        self.assertEqual(report["verification"]["sandbox"], "contenedor-auditoria")
        self.assertEqual(report["verification"]["returncode"], 0)
        self.assertIn("ok", report["verification"]["output"])

    def test_missing_diff_exits_two(self):
        self.assertEqual(
            run("apply_patch.py", self.file, "--diff", self.root / "no.diff").returncode,
            2,
        )


class TestScaleReport(CiFixScaleTest):
    def repo(self, name, confirmed=1, gaps=1):
        path = self.root / name
        audit = path / ".appsec-audit"
        audit.mkdir(parents=True)
        (audit / "findings.json").write_text(json.dumps({
            "audit_id": f"audit-{name}",
            "target": name,
            "findings": [
                {
                    "id": f"F-{index + 1:03d}",
                    "title": "fallo",
                    "verdict": "confirmed" if index < confirmed else "needs_validation",
                    "confidence": 8,
                    "severity": "alta",
                    "cwe": "CWE-89",
                    "location": {"file": "app.py", "line": index + 1},
                    "evidence": "evidencia",
                    "fingerprint": f"sha256:{index:032x}",
                }
                for index in range(confirmed + 1)
            ],
        }), encoding="utf-8")
        (audit / "coverage-ledger.json").write_text(json.dumps({
            "audit_id": f"audit-{name}",
            "target": name,
            "units": [
                {"id": f"U-{index + 1:03d}", "surface": "POST /x", "subsystem": "api",
                 "attack_class": "injection",
                 "status": "planned" if index < gaps else "covered",
                 "updated_at": "2026-01-01T00:00:00Z"}
                for index in range(gaps + 1)
            ],
        }), encoding="utf-8")
        return path

    def test_reports_topology_and_cost_per_phase(self):
        api, web = self.repo("api", confirmed=2), self.repo("web", confirmed=1)
        vendor = self.write("terceros.json", {"vendors": [
            {"name": "stripe", "service": "pagos", "data": "pii", "repos": ["api"]},
            {"name": "sentry", "service": "errores", "data": "logs", "repos": []},
        ]})
        cost = self.write("tarifa.json", {"hourly": 100, "currency": "USD"})

        result = run(
            "scale_report.py", "--repos", f"api={api},web={web}",
            "--vendor", vendor, "--profile", "deep", "--cost", cost, "--json",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["system"], {"repos": 2, "vendors": 2, "profile": "deep"})
        self.assertEqual(report["cost"]["currency"], "USD")
        self.assertEqual(report["cost"]["phases"][0]["phase"], "recon")
        self.assertEqual(report["cost"]["total_cost"], round(report["cost"]["total_hours"] * 100, 2))
        self.assertEqual(report["cost"]["total_hours"], sum(p["hours"] for p in report["cost"]["phases"]))
        self.assertIn({"from": "repo:api", "to": "vendor:stripe", "data": "pii"},
                      report["topology"]["edges"])
        self.assertEqual(report["topology"]["vendors_without_repo"], ["sentry"])
        confirmed = sum(repo["findings"]["confirmed"] for repo in report["repos"])
        self.assertEqual(confirmed, 3)

    def test_repo_without_artifacts_is_pending(self):
        empty = self.root / "vacio"
        empty.mkdir()

        report = json.loads(run("scale_report.py", "--repos", f"vacio={empty}", "--json").stdout)

        self.assertFalse(report["repos"][0]["artifacts"]["findings"])
        self.assertTrue(any("superficie" in note for note in report["repos"][0]["notes"]))

    def test_missing_repo_exits_two(self):
        self.assertEqual(
            run("scale_report.py", "--repos", f"x={self.root / 'no'}").returncode,
            2,
        )


class TestPhaseDocuments(unittest.TestCase):
    def test_agent_hardening_reference_covers_the_rules(self):
        text = (SKILL_ROOT / "references" / "agent-hardening.md").read_text(encoding="utf-8").lower()

        for needle in ("pull_request_target", "sha", "security-events: write",
                       "contenido hostil", "needs_validation"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_remediation_reference_declares_the_sandbox(self):
        text = (SKILL_ROOT / "references" / "remediation.md").read_text(encoding="utf-8")

        for needle in ("Contenedor efímero", "Sin datos de producción", ".orig", "variante"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_pr_comment_template_has_the_gate(self):
        text = (SKILL_ROOT / "templates" / "pr-comment.md").read_text(encoding="utf-8")

        for needle in ("bloquea", "Frente al baseline", "Límites", "upload-sarif"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
