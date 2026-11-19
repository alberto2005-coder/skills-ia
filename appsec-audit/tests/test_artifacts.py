"""Tests de los artefactos de auditoría: init, findings.json y ledger."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from appsec_config import SKILL_ROOT

SCRIPT_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import validate_findings  # noqa: E402

FINDINGS = validate_findings.fingerprint


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
        "severity": "critical",
        "cwe": cwe,
        "location": {"file": file, "line": 42},
        "root_cause": cause,
        "evidence": 'cursor.execute("SELECT * FROM users WHERE id = " + user_id)',
        "exploit": ["abrir /users?id=1'", "inyectar UNION SELECT", "leer la tabla users"],
        "patch": "- execute(sql + user_id)\n+ execute(sql, (user_id,))",
        "fingerprint": FINDINGS(cwe, file, cause),
    }
    data.update(overrides)
    return data


def needs_validation(**overrides):
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
        "unresolved": "si el middleware aplica filtro por tenant",
        "fingerprint": FINDINGS(cwe, file, cause),
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
        "reason": "el motor de plantillas escapa por defecto; no hay sink",
        "fingerprint": FINDINGS(cwe, file, cause),
    }
    data.update(overrides)
    return data


def payload(*items, **overrides):
    data = {"audit_id": "audit-demo", "target": "demo", "findings": list(items)}
    data.update(overrides)
    return data


class ArtifactTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.audit = self.root / ".appsec-audit"

    def write_json(self, data, name="findings.json"):
        path = self.root / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def read_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))


class TestInitAudit(ArtifactTest):
    def test_creates_the_three_artifacts(self):
        result = run("init_audit.py", self.root, "--id", "audit-demo", "--now", "2026-01-01T00:00:00Z")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in ("findings.json", "coverage-ledger.json", "architecture.md"):
            with self.subTest(name=name):
                self.assertTrue((self.audit / name).is_file())
        self.assertIn("audit-demo", result.stdout)

    def test_created_artifacts_pass_their_validators(self):
        run("init_audit.py", self.root, "--id", "audit-demo")

        findings = run("validate_findings.py", self.audit / "findings.json")
        ledger = run("ledger.py", "validate", self.audit / "coverage-ledger.json")

        self.assertEqual(findings.returncode, 0, findings.stdout)
        self.assertIn("OK", findings.stdout)
        self.assertEqual(ledger.returncode, 0, ledger.stdout)

    def test_refuses_to_overwrite_without_force(self):
        run("init_audit.py", self.root, "--id", "audit-demo")
        second = run("init_audit.py", self.root, "--id", "otra")

        self.assertEqual(second.returncode, 1)
        self.assertIn("--force", second.stderr)
        self.assertEqual(self.read_json(self.audit / "findings.json")["audit_id"], "audit-demo")

    def test_force_overwrites(self):
        run("init_audit.py", self.root, "--id", "audit-demo")
        forced = run("init_audit.py", self.root, "--id", "audit-nueva", "--force")

        self.assertEqual(forced.returncode, 0)
        self.assertEqual(self.read_json(self.audit / "findings.json")["audit_id"], "audit-nueva")

    def test_rejects_a_missing_target(self):
        result = run("init_audit.py", self.root / "no-existe")

        self.assertEqual(result.returncode, 2)

    def test_default_id_comes_from_the_target_name(self):
        target = self.root / "mi-servicio"
        target.mkdir()

        run("init_audit.py", target)

        self.assertEqual(
            self.read_json(target / ".appsec-audit" / "findings.json")["audit_id"],
            "audit-mi-servicio",
        )


class TestValidateFindings(ArtifactTest):
    def test_accepts_one_finding_per_verdict(self):
        path = self.write_json(payload(confirmed(), needs_validation(), rejected()))
        result = run("validate_findings.py", path)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("confirmed 1", result.stdout)

    def test_confirmed_requires_severity(self):
        item = confirmed()
        item.pop("severity")
        result = run("validate_findings.py", self.write_json(payload(item)))

        self.assertEqual(result.returncode, 1)
        self.assertIn("severity", result.stdout)

    def test_confirmed_requires_confidence_of_seven(self):
        result = run("validate_findings.py", self.write_json(payload(confirmed(confidence=6))))

        self.assertEqual(result.returncode, 1)
        self.assertIn("confidence", result.stdout)

    def test_confirmed_requires_exploit_and_patch(self):
        item = confirmed()
        item.pop("exploit")
        item.pop("patch")
        result = run("validate_findings.py", self.write_json(payload(item)))

        self.assertEqual(result.returncode, 1)
        self.assertIn("exploit", result.stdout)
        self.assertIn("patch", result.stdout)

    def test_needs_validation_rejects_severity(self):
        result = run(
            "validate_findings.py",
            self.write_json(payload(needs_validation(severity="high"))),
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("severity", result.stdout)

    def test_needs_validation_requires_unresolved(self):
        item = needs_validation()
        item.pop("unresolved")
        result = run("validate_findings.py", self.write_json(payload(item)))

        self.assertEqual(result.returncode, 1)
        self.assertIn("unresolved", result.stdout)

    def test_rejected_requires_reason(self):
        item = rejected()
        item.pop("reason")
        result = run("validate_findings.py", self.write_json(payload(item)))

        self.assertEqual(result.returncode, 1)
        self.assertIn("reason", result.stdout)

    def test_duplicate_ids_are_rejected(self):
        second = confirmed(
            title="SQL injection en /admin",
            location={"file": "app/admin.py", "line": 7},
            fingerprint=FINDINGS("CWE-89", "app/admin.py", "user_id se concatena en la consulta sql"),
        )
        result = run("validate_findings.py", self.write_json(payload(confirmed(), second)))

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicado", result.stdout)

    def test_duplicate_fingerprints_are_rejected(self):
        second = confirmed(id="F-002", location={"file": "app/api.py", "line": 77})
        result = run("validate_findings.py", self.write_json(payload(confirmed(), second)))

        self.assertEqual(result.returncode, 1)
        self.assertIn("fingerprint duplicado", result.stdout)
        self.assertIn("F-001", result.stdout)

    def test_distinct_root_causes_are_not_duplicates(self):
        other = confirmed(
            id="F-002",
            root_cause="otra causa distinta",
            fingerprint=FINDINGS("CWE-89", "app/api.py", "otra causa distinta"),
        )
        result = run("validate_findings.py", self.write_json(payload(confirmed(), other)))

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_tampered_fingerprint_is_rejected(self):
        item = confirmed(root_cause="otra causa distinta")
        result = run("validate_findings.py", self.write_json(payload(item)))

        self.assertEqual(result.returncode, 1)
        self.assertIn("fingerprint", result.stdout)

    def test_unknown_fields_are_rejected(self):
        result = run("validate_findings.py", self.write_json(payload(confirmed(inventado=True))))

        self.assertEqual(result.returncode, 1)
        self.assertIn("no permitido", result.stdout)

    def test_source_unit_must_exist_in_the_ledger(self):
        item = confirmed(source_unit="U-004")
        path = self.write_json(payload(item))
        ledger_path = self.write_json({"audit_id": "a", "target": "t", "units": []}, "ledger.json")

        missing = run("validate_findings.py", path, "--ledger", ledger_path)
        ledger_path.write_text(
            json.dumps({
                "audit_id": "a",
                "target": "t",
                "units": [{"id": "U-004"}],
            }),
            encoding="utf-8",
        )
        present = run("validate_findings.py", path, "--ledger", ledger_path)

        self.assertEqual(missing.returncode, 1)
        self.assertIn("source_unit", missing.stdout)
        self.assertEqual(present.returncode, 0, present.stdout)

    def test_broken_json_exits_two(self):
        path = self.root / "roto.json"
        path.write_text("{no json", encoding="utf-8")

        self.assertEqual(run("validate_findings.py", path).returncode, 2)


class TestLedger(ArtifactTest):
    def init(self):
        run("init_audit.py", self.root, "--id", "audit-demo")
        return self.audit / "coverage-ledger.json"

    def add_unit(self, path, surface="POST /login", attack_class="auth"):
        return run(
            "ledger.py", "add", path,
            "--surface", surface,
            "--subsystem", "auth",
            "--class", attack_class,
            "--owner", "appsec-code",
        )

    def test_add_assigns_sequential_ids(self):
        path = self.init()

        first = self.add_unit(path)
        second = self.add_unit(path, surface="GET /orders", attack_class="access-control")

        units = self.read_json(path)["units"]
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual([unit["id"] for unit in units], ["U-001", "U-002"])
        self.assertEqual(units[0]["status"], "planned")

    def test_covered_requires_a_check(self):
        path = self.init()
        self.add_unit(path)

        without = run("ledger.py", "update", path, "--id", "U-001", "--status", "covered")
        with_check = run(
            "ledger.py", "update", path, "--id", "U-001",
            "--status", "covered", "--check", "trazado fuente→sumidero",
            "--finding", "F-001",
        )

        self.assertEqual(without.returncode, 1)
        self.assertIn("checks", without.stderr)
        self.assertEqual(with_check.returncode, 0, with_check.stdout + with_check.stderr)
        unit = self.read_json(path)["units"][0]
        self.assertEqual(unit["status"], "covered")
        self.assertEqual(unit["findings"], ["F-001"])

    def test_skipped_requires_a_reason(self):
        path = self.init()
        self.add_unit(path)

        result = run("ledger.py", "update", path, "--id", "U-001", "--status", "skipped")

        self.assertEqual(result.returncode, 1)
        self.assertIn("skip_reason", result.stderr)

    def test_gaps_lists_planned_and_hunting_only(self):
        path = self.init()
        self.add_unit(path)
        self.add_unit(path, surface="GET /orders", attack_class="access-control")
        run("ledger.py", "update", path, "--id", "U-001", "--status", "covered", "--check", "revisado")

        result = run("ledger.py", "gaps", path)

        self.assertEqual(result.returncode, 0)
        self.assertIn("U-002", result.stdout)
        self.assertNotIn("U-001", result.stdout)

    def test_gaps_strict_fails_while_work_remains(self):
        path = self.init()
        self.add_unit(path)

        remaining = run("ledger.py", "gaps", path, "--strict")
        run("ledger.py", "update", path, "--id", "U-001", "--status", "covered", "--check", "revisado")
        done = run("ledger.py", "gaps", path, "--strict")

        self.assertEqual(remaining.returncode, 1)
        self.assertEqual(done.returncode, 0)

    def test_duplicate_ids_fail_validation(self):
        path = self.init()
        self.add_unit(path)
        data = self.read_json(path)
        data["units"].append(dict(data["units"][0]))
        path.write_text(json.dumps(data), encoding="utf-8")

        result = run("ledger.py", "validate", path)

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicado", result.stdout)

    def test_unknown_attack_class_is_refused(self):
        path = self.init()

        result = run(
            "ledger.py", "add", path,
            "--surface", "CRON",
            "--subsystem", "jobs",
            "--class", "inventada",
        )

        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
