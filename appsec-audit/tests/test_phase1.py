"""Tests de la fase 1: verificación independiente, SARIF, diff/PR y baseline."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from config import SKILL_ROOT

SCRIPT_DIR = SKILL_ROOT / "scripts"
REPO = SKILL_ROOT.parent
sys.path.insert(0, str(SCRIPT_DIR))

import validate_findings  # noqa: E402

FINGERPRINT = validate_findings.fingerprint


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def confirmed(**overrides):
    cwe, file = "CWE-89", "app/api.py"
    cause = "user_id se concatena en la consulta sql"
    data = {
        "id": "F-001",
        "title": "SQL injection en /users",
        "verdict": "confirmed",
        "confidence": 9,
        "severity": "critica",
        "cwe": cwe,
        "location": {"file": file, "line": 42},
        "root_cause": cause,
        "evidence": 'cursor.execute("SELECT * FROM users WHERE id = " + user_id)',
        "exploit": ["abrir /users?id=1'", "inyectar UNION SELECT"],
        "patch": "- execute(sql + user_id)\n+ execute(sql, (user_id,))",
        "fingerprint": FINGERPRINT(cwe, file, cause),
    }
    data.update(overrides)
    return data


def pending(**overrides):
    cwe, file = "CWE-639", "app/orders.py"
    cause = "no se comprueba el propietario del pedido"
    data = {
        "id": "F-002",
        "title": "Posible IDOR en /orders",
        "verdict": "needs_validation",
        "confidence": 5,
        "cwe": cwe,
        "location": {"file": file, "line": 88},
        "root_cause": cause,
        "evidence": "get_order(order_id) sin comprobar owner",
        "unresolved": "si el middleware filtra por tenant",
        "fingerprint": FINGERPRINT(cwe, file, cause),
    }
    data.update(overrides)
    return data


def rejected(**overrides):
    cwe, file = "CWE-79", "app/views.py"
    cause = "la plantilla escapa el comentario"
    data = {
        "id": "F-003",
        "title": "XSS en comentarios",
        "verdict": "rejected",
        "confidence": 3,
        "cwe": cwe,
        "location": {"file": file, "line": 12},
        "root_cause": cause,
        "evidence": "render_template con autoescape activo",
        "reason": "el motor de plantillas escapa por defecto",
        "fingerprint": FINGERPRINT(cwe, file, cause),
    }
    data.update(overrides)
    return data


def payload(*items, **overrides):
    data = {"audit_id": "audit-demo", "target": "demo", "findings": list(items)}
    data.update(overrides)
    return data


class Phase1Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, data, name):
        path = self.root / name
        if isinstance(data, str):
            path.write_text(data, encoding="utf-8")
        else:
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path


class TestVerificationTemplate(Phase1Test):
    def setUp(self):
        super().setUp()
        self.text = (SKILL_ROOT / "templates" / "verification.md").read_text(encoding="utf-8")

    def test_declares_the_isolation_rule(self):
        self.assertIn("Lo único que se entrega", self.text)
        self.assertIn("Lo que no se entrega", self.text)
        for leaked in ("Evidencia redactada", "veredicto", "confianza", "parche"):
            with self.subTest(term=leaked):
                self.assertIn(leaked, self.text)

    def test_covers_the_refutation_questions(self):
        for question in ("no ejecutable", "sumidero", "mitigación", "producción", "benigna"):
            with self.subTest(question=question):
                self.assertIn(question, self.text)

    def test_maps_every_verdict_to_its_required_fields(self):
        for verdict in ("confirmed", "needs_validation", "rejected"):
            with self.subTest(verdict=verdict):
                self.assertIn(f"`{verdict}`", self.text)


class TestSarif(Phase1Test):
    def export(self, data, *extra):
        path = self.write(data, "findings.json")
        result = run("export_sarif.py", path, *extra)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_minimal_sarif_contract(self):
        sarif = self.export(payload(confirmed()))

        self.assertEqual(sarif["version"], "2.1.0")
        self.assertIn("sarif-2.1.0", sarif["$schema"])
        driver = sarif["runs"][0]["tool"]["driver"]
        self.assertEqual(driver["name"], "appsec-audit")
        self.assertEqual(driver["rules"][0]["id"], "CWE-89")

    def test_only_confirmed_by_default(self):
        sarif = self.export(payload(confirmed(), pending(), rejected()))

        results = sarif["runs"][0]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["properties"]["verdict"], "confirmed")

    def test_pending_needs_the_flag_and_is_a_note(self):
        data = payload(confirmed(), pending())
        without = self.export(data)
        with_pending = self.export(data, "--include-pending")

        self.assertEqual(len(without["runs"][0]["results"]), 1)
        result = with_pending["runs"][0]["results"][1]
        self.assertEqual(result["level"], "note")
        self.assertEqual(result["properties"]["verdict"], "needs_validation")

    def test_severity_mapping(self):
        sarif = self.export(payload(
            confirmed(id="F-001"),
            confirmed(id="F-002", severity="alta"),
            confirmed(id="F-003", severity="media", cwe="CWE-79", location={"file": "a.py", "line": 1},
                      fingerprint=FINGERPRINT("CWE-79", "a.py", "user_id se concatena en la consulta sql")),
            confirmed(id="F-004", severity="baja", cwe="CWE-20", location={"file": "b.py", "line": 2},
                      fingerprint=FINGERPRINT("CWE-20", "b.py", "user_id se concatena en la consulta sql")),
        ))

        levels = [result["level"] for result in sarif["runs"][0]["results"]]
        self.assertEqual(levels, ["error", "error", "warning", "note"])

    def test_rules_are_deduplicated_by_cwe(self):
        second = confirmed(id="F-002", location={"file": "app/api.py", "line": 77})
        sarif = self.export(payload(confirmed(), second))

        run = sarif["runs"][0]
        self.assertEqual(len(run["tool"]["driver"]["rules"]), 1)
        self.assertEqual([result["ruleIndex"] for result in run["results"]], [0, 0])

    def test_location_and_fingerprint(self):
        sarif = self.export(payload(confirmed(location={"file": "app\\api.py", "line": 42})))

        result = sarif["runs"][0]["results"][0]
        physical = result["locations"][0]["physicalLocation"]
        self.assertEqual(physical["artifactLocation"]["uri"], "app/api.py")
        self.assertEqual(physical["region"]["startLine"], 42)
        self.assertTrue(result["partialFingerprints"]["appsecAuditFingerprint/v1"].startswith("sha256:"))

    def test_output_file_is_written(self):
        path = self.write(payload(confirmed()), "findings.json")
        out = self.root / "appsec.sarif"
        result = run("export_sarif.py", path, "--output", out)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["version"], "2.1.0")

    def test_invalid_report_exits_one(self):
        path = self.write({"audit_id": "x"}, "findings.json")

        self.assertEqual(run("export_sarif.py", path).returncode, 1)

    def test_missing_file_exits_two(self):
        self.assertEqual(run("export_sarif.py", self.root / "no.json").returncode, 2)


PATCH = """diff --git a/app/api.py b/app/api.py
--- a/app/api.py
+++ b/app/api.py
@@ -40,2 +40,3 @@ def users():
-    old()
+    new()
+    extra()
@@ -80,0 +84,2 @@ def admin():
+    admin_only()
+    more()
--- a/app/views.py
+++ b/app/views.py
@@ -10,0 +11,1 @@
+    render()
"""


class TestDiffScope(Phase1Test):
    def test_parses_added_ranges_from_a_patch(self):
        patch = self.write(PATCH, "cambios.patch")
        result = run("diff_scope.py", "--diff", patch, "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        scope = json.loads(result.stdout)
        self.assertEqual(scope["files"], {"app/api.py": [[40, 42], [84, 85]], "app/views.py": [[11, 11]]})
        self.assertEqual(scope["summary"], {"files": 2, "changed_lines": 6})

    def test_merges_adjacent_ranges(self):
        patch = self.write(
            "--- a/x.py\n+++ b/x.py\n@@ -1,0 +2,1 @@\n+a\n@@ -5,0 +3,1 @@\n+b\n",
            "p.patch",
        )
        scope = json.loads(run("diff_scope.py", "--diff", patch, "--json").stdout)

        self.assertEqual(scope["files"]["x.py"], [[2, 3]])

    def test_split_findings_inside_and_outside_the_diff(self):
        patch = self.write(PATCH, "cambios.patch")
        findings = self.write(payload(
            confirmed(location={"file": "app/api.py", "line": 41}),
            pending(location={"file": "app/api.py", "line": 90}),
            rejected(location={"file": "app/views.py", "line": 11}),
        ), "findings.json")
        scope = json.loads(
            run("diff_scope.py", "--diff", patch, "--findings", findings, "--json").stdout
        )

        self.assertEqual(scope["findings"]["in_scope"], ["F-001", "F-003"])
        self.assertEqual(scope["findings"]["out_of_scope"], ["F-002"])
        self.assertEqual(scope["findings"]["total"], 3)

    def test_writes_the_scope_file(self):
        patch = self.write(PATCH, "cambios.patch")
        out = self.root / "scope.json"
        result = run("diff_scope.py", "--diff", patch, "--output", out)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 fichero(s)", result.stdout)
        self.assertIn("app/api.py", json.loads(out.read_text(encoding="utf-8"))["files"])

    def test_git_base_with_no_changes_is_empty(self):
        if shutil.which("git") is None:
            self.skipTest("git no disponible")
        repo = self.root / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("x = 1\n", encoding="utf-8")
        for command in (
            ["git", "init", "-q"],
            ["git", "add", "a.py"],
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"],
        ):
            subprocess.run(command, cwd=repo, check=True, capture_output=True)

        result = run("diff_scope.py", "--repo", repo, "--base", "HEAD", "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["files"], {})

    def test_git_base_reports_added_lines(self):
        if shutil.which("git") is None:
            self.skipTest("git no disponible")
        repo = self.root / "repo2"
        repo.mkdir()
        (repo / "a.py").write_text("x = 1\n", encoding="utf-8")
        for command in (
            ["git", "init", "-q"],
            ["git", "add", "a.py"],
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"],
        ):
            subprocess.run(command, cwd=repo, check=True, capture_output=True)
        (repo / "a.py").write_text("x = 1\ny = 2\n", encoding="utf-8")

        scope = json.loads(run("diff_scope.py", "--repo", repo, "--base", "HEAD", "--json").stdout)

        self.assertEqual(scope["files"], {"a.py": [[2, 2]]})

    def test_missing_patch_exits_two(self):
        self.assertEqual(run("diff_scope.py", "--diff", self.root / "no.patch").returncode, 2)

    def test_findings_must_have_the_list(self):
        patch = self.write(PATCH, "cambios.patch")
        findings = self.write({"audit_id": "x"}, "findings.json")

        self.assertEqual(
            run("diff_scope.py", "--diff", patch, "--findings", findings).returncode,
            1,
        )


class TestReportBaseline(Phase1Test):
    def diff(self, baseline, current, *extra):
        base_path = self.write(baseline, "baseline.json")
        current_path = self.write(current, "current.json")
        return run("diff_reports.py", base_path, current_path, *extra)

    def test_classifies_new_fixed_changed_and_persisting(self):
        base = payload(confirmed(), pending(), rejected())
        current = payload(
            confirmed(),
            pending(verdict="confirmed", severity="alta", confidence=8, exploit=["a", "b"], patch="x"),
            confirmed(id="F-009", title="Command injection", location={"file": "app/run.py", "line": 3},
                      fingerprint=FINGERPRINT("CWE-89", "app/run.py", "user_id se concatena en la consulta sql")),
        )
        result = self.diff(base, current, "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual([item["id"] for item in data["new"]], ["F-009"])
        self.assertEqual([item["id"] for item in data["fixed"]], ["F-003"])
        self.assertEqual([item["id"] for item in data["changed"]], ["F-002"])
        self.assertEqual([item["id"] for item in data["persisting"]], ["F-001"])

    def test_gate_blocks_only_new_confirmed(self):
        base = payload(confirmed())
        clean = self.diff(base, payload(confirmed(), pending()), "--fail-on", "new")
        blocked = self.diff(
            base,
            payload(confirmed(), confirmed(id="F-009", location={"file": "a.py", "line": 2},
                                          fingerprint=FINGERPRINT("CWE-89", "a.py", "otra causa"))),
            "--fail-on", "new",
        )

        self.assertEqual(clean.returncode, 0, clean.stdout)
        self.assertEqual(blocked.returncode, 1)
        self.assertIn("BLOQUEADO", blocked.stdout)

    def test_human_summary_counts(self):
        result = self.diff(payload(confirmed()), payload(confirmed(), rejected()))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Nuevos 1", result.stdout)
        self.assertIn("Persistentes 1", result.stdout)

    def test_missing_baseline_exits_two(self):
        current = self.write(payload(confirmed()), "current.json")
        result = run("diff_reports.py", self.root / "no.json", current)

        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
