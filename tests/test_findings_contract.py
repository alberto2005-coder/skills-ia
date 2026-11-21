"""Tests del contrato común de hallazgos: esquema, validador, SARIF y adaptadores."""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT_DIR = ROOT / "contracts" / "findings"
sys.path.insert(0, str(CONTRACT_DIR))

import emit  # noqa: E402
import findings_contract as contract  # noqa: E402
import findings_to_sarif  # noqa: E402
import findings_validate  # noqa: E402

TOOL = {"package": "demo", "skill": "demo", "version": "1.2.3"}


def good_finding(**overrides):
    finding = contract.make_finding(
        "CWE-89",
        "high",
        "high",
        "Inyección SQL en get_user",
        "El id de la petición se concatena en la consulta",
        'cursor.execute("SELECT * FROM users WHERE id = " + user_id)',
        "Parametrizar la consulta con un marcador y una tupla",
        contract.make_location("file", "app/api.py", 42),
        [{"id": "CWE-89", "url": "https://cwe.mitre.org/data/definitions/89.html"}],
    )
    finding.update(overrides)
    return finding


def payload(findings=None, **kwargs):
    return contract.build_payload(TOOL, [good_finding()] if findings is None else findings, **kwargs)


class SchemaTests(unittest.TestCase):
    def test_schema_declares_the_contract(self):
        schema = json.loads(contract.SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0.0")
        self.assertEqual(
            set(schema["required"]), {"schema_version", "tool", "summary", "findings"}
        )
        finding = schema["$defs"]["finding"]
        self.assertEqual(
            set(finding["required"]),
            {
                "fingerprint", "rule_id", "severity", "confidence", "title",
                "message", "evidence", "remediation", "location",
            },
        )
        self.assertEqual(
            finding["properties"]["severity"]["enum"],
            ["critical", "high", "medium", "low", "info"],
        )
        self.assertEqual(
            finding["properties"]["confidence"]["enum"], ["high", "medium", "low"]
        )
        self.assertEqual(
            schema["$defs"]["location"]["properties"]["type"]["enum"],
            ["file", "url", "resource", "schema"],
        )


class FingerprintTests(unittest.TestCase):
    def test_line_does_not_change_the_fingerprint(self):
        first = contract.fingerprint("CWE-89", contract.make_location("file", "app.py", 10), "SQL")
        second = contract.fingerprint("CWE-89", contract.make_location("file", "app.py", 99), "SQL")
        self.assertEqual(first, second)

    def test_cause_and_target_do_change_it(self):
        base = contract.fingerprint("CWE-89", contract.make_location("file", "app.py", 10), "SQL")
        other_cause = contract.fingerprint("CWE-89", contract.make_location("file", "app.py", 10), "Otra")
        other_target = contract.fingerprint("CWE-89", contract.make_location("file", "otro.py", 10), "SQL")
        other_rule = contract.fingerprint("CWE-78", contract.make_location("file", "app.py", 10), "SQL")
        self.assertEqual(len({base, other_cause, other_target, other_rule}), 4)

    def test_windows_and_posix_paths_share_a_fingerprint(self):
        windows = contract.fingerprint("CWE-89", contract.make_location("file", "app\\api.py", 10), "SQL")
        posix = contract.fingerprint("CWE-89", contract.make_location("file", "app/api.py", 10), "SQL")
        self.assertEqual(windows, posix)
        self.assertEqual(contract.make_location("file", "app\\api.py")["target"], "app/api.py")

    def test_only_files_carry_lines(self):
        location = contract.make_location("url", "https://example.com/a", 12, 14)
        self.assertEqual(location, {"type": "url", "target": "https://example.com/a",
                                    "line": None, "end_line": None})


class ValidatorTests(unittest.TestCase):
    def errors(self, data):
        return findings_validate.validate_payload(data)

    def test_good_payload_is_valid(self):
        self.assertEqual(self.errors(payload(target="demo")), [])

    def test_summary_must_match_the_findings(self):
        data = payload()
        data["summary"]["total"] = 2
        self.assertTrue(any("summary.total" in error for error in self.errors(data)))
        data = payload()
        data["summary"]["by_severity"]["high"] = 0
        self.assertTrue(any("by_severity.high" in error for error in self.errors(data)))

    def test_lines_on_a_url_are_rejected(self):
        finding = good_finding(location={"type": "url", "target": "https://x.dev/a",
                                         "line": 10, "end_line": None})
        finding["fingerprint"] = contract.fingerprint("CWE-89", finding["location"], finding["title"])
        self.assertTrue(any("inventada" in error for error in self.errors(payload([finding]))))

    def test_fingerprint_is_recomputed(self):
        finding = good_finding(fingerprint="sha256:" + "0" * 32)
        self.assertTrue(any("fingerprint no coincide" in error for error in self.errors(payload([finding]))))

    def test_duplicates_are_rejected(self):
        self.assertTrue(any("duplicado" in error for error in self.errors(payload([good_finding(), good_finding()]))))

    def test_unknown_fields_are_rejected(self):
        finding = good_finding(extra="no permitido")
        self.assertTrue(any("no permitido" in error for error in self.errors(payload([finding]))))
        data = payload()
        data["extra"] = True
        self.assertTrue(any("no permitido" in error for error in self.errors(data)))

    def test_closed_enums(self):
        for field, value in (("severity", "warning"), ("confidence", "certain")):
            finding = good_finding(**{field: value})
            self.assertTrue(any(field in error for error in self.errors(payload([finding]))))

    def test_fail_on_returns_its_own_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "findings.json"
            path.write_text(contract.dump(payload([good_finding()])), encoding="utf-8")
            cases = ((None, 0), ("critical", 0), ("high", 3), ("medium", 3), ("info", 3))
            for threshold, expected in cases:
                argv = [str(path)] + (["--fail-on", threshold] if threshold else [])
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(findings_validate.main(argv), expected, threshold)

    def test_unreadable_input_and_invalid_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(findings_validate.main([str(Path(tmp) / "no-existe.json")]), 2)
            broken = Path(tmp) / "roto.json"
            broken.write_text("{", encoding="utf-8")
            self.assertEqual(findings_validate.main([str(broken)]), 2)


class SarifTests(unittest.TestCase):
    def sarif(self, findings, **kwargs):
        return findings_to_sarif.build_sarif(payload(findings, **kwargs))

    def test_levels_follow_the_contract(self):
        findings = [
            good_finding(rule_id="R-CRIT", severity="critical"),
            good_finding(rule_id="R-HIGH", severity="high"),
            good_finding(rule_id="R-MED", severity="medium"),
            good_finding(rule_id="R-LOW", severity="low"),
            good_finding(rule_id="R-INFO", severity="info"),
        ]
        run = self.sarif(findings)["runs"][0]
        levels = {result["ruleId"]: result["level"] for result in run["results"]}
        self.assertEqual(levels, {
            "R-CRIT": "error", "R-HIGH": "error", "R-MED": "warning", "R-LOW": "note", "R-INFO": "note",
        })

    def test_hybrid_locations_and_fingerprints(self):
        findings = [
            good_finding(),
            good_finding(rule_id="SEO-1", location={"type": "url", "target": "https://x.dev/a",
                                                    "line": None, "end_line": None}),
            good_finding(rule_id="DB-1", location={"type": "schema", "target": "public.users",
                                                   "line": None, "end_line": None}),
        ]
        run = self.sarif(findings, target="demo")["runs"][0]
        file_result, url_result, schema_result = run["results"]
        self.assertEqual(file_result["locations"][0]["physicalLocation"]["region"]["startLine"], 42)
        self.assertEqual(url_result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"], "https://x.dev/a")
        self.assertEqual(schema_result["locations"][0]["logicalLocations"][0]["fullyQualifiedName"], "public.users")
        for result in run["results"]:
            self.assertTrue(result["partialFingerprints"]["skillsIaFingerprint/v1"].startswith("sha256:"))

    def test_absolute_paths_under_the_target_become_relative(self):
        finding = good_finding(location=contract.make_location("file", "C:\\repo\\app\\api.py", 7))
        run = self.sarif([finding], target="C:\\repo")["runs"][0]
        uri = run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        self.assertEqual(uri, "app/api.py")

    def test_driver_uses_the_tool_metadata(self):
        run = self.sarif([good_finding()])["runs"][0]
        self.assertEqual(run["tool"]["driver"]["name"], "demo")
        self.assertEqual(run["tool"]["driver"]["version"], "1.2.3")
        self.assertEqual(run["tool"]["driver"]["rules"][0]["id"], "CWE-89")
        self.assertEqual(run["tool"]["driver"]["rules"][0]["helpUri"],
                         "https://cwe.mitre.org/data/definitions/89.html")


SEO_AUDIT = {
    "schema": "seo-auditor/audit",
    "tool": {"name": "seo-auditor", "version": "3.0.1"},
    "target": "https://example.com/",
    "score": 72.5,
    "verdict_line": "Competitive — hay margen claro.",
    "findings": [
        {
            "id": "SRC-TITLE-001", "title": "Falta la etiqueta <title>",
            "severity": "high", "severity_level": "must", "status": "fail",
            "evidence": "No se detectó <title>.", "url": "https://example.com/",
            "citation": "https://developers.google.com/search/docs/appearance/title-link",
            "recommendation": "Añade un <title> único y descriptivo.",
            "confidence": "high",
        },
        {
            "id": "ONP-ALT-001", "title": "Imágenes sin alt",
            "severity": "medium", "severity_level": "should", "status": "fail",
            "evidence": "2 de 5 imágenes sin alt.", "url": "index.html",
            "citation": "", "recommendation": "Añade alt descriptivo.",
            "confidence": "medium",
        },
        {
            "id": "SEC-CSP-001", "title": "Sin CSP",
            "severity": "medium", "severity_level": "should", "status": "pass",
            "evidence": "Cabecera presente.", "url": "https://example.com/",
            "citation": "", "recommendation": "", "confidence": "high",
        },
    ],
}

APPSEC_AUDIT = {
    "audit_id": "audit-demo",
    "target": "C:\\repo",
    "profile": "standard",
    "created_at": "2026-11-20T10:00:00Z",
    "findings": [
        {
            "id": "F-001", "title": "Inyección SQL", "verdict": "confirmed",
            "confidence": 9, "severity": "critical", "cwe": "CWE-89", "owasp": "A03",
            "location": {"file": "C:\\repo\\app.py", "line": 10},
            "root_cause": "El id se concatena en la consulta",
            "evidence": 'cursor.execute("..." + user_id)', "patch": "- a\n+ b",
            "exploit": ["id=1 OR 1=1", "devuelve todo"],
        },
        {
            "id": "F-002", "title": "Posible XSS", "verdict": "needs_validation",
            "confidence": 5, "cwe": "CWE-79",
            "location": {"file": "C:\\repo\\app.py", "line": 20},
            "evidence": "return '<div>' + body", "unresolved": "Falta revisar el middleware",
        },
    ],
}


class AdapterTests(unittest.TestCase):
    def test_seo_maps_failures_only(self):
        emitted = emit.from_seo(SEO_AUDIT, "seo-auditor", "3.0.1")
        self.assertEqual(findings_validate.validate_payload(emitted), [])
        self.assertEqual(emitted["summary"]["total"], 2)
        self.assertEqual(emitted["summary"]["by_severity"]["high"], 1)
        self.assertEqual(emitted["summary"]["score"], 72.5)
        self.assertEqual(emitted["summary"]["note"], "Competitive — hay margen claro.")
        first, second = emitted["findings"]
        self.assertEqual(first["location"]["type"], "url")
        self.assertEqual(second["location"], {"type": "file", "target": "index.html",
                                              "line": None, "end_line": None})
        self.assertEqual(first["references"][0]["id"], "developers.google.com")
        self.assertEqual(first["rule_id"], "SRC-TITLE-001")

    def test_appsec_keeps_only_confirmed(self):
        emitted = emit.from_appsec(APPSEC_AUDIT, "appsec-audit", "2.0.1")
        self.assertEqual(findings_validate.validate_payload(emitted), [])
        self.assertEqual(emitted["summary"]["total"], 1)
        finding = emitted["findings"][0]
        self.assertEqual(finding["confidence"], "high")
        self.assertEqual(finding["severity"], "critical")
        self.assertEqual(finding["rule_id"], "CWE-89")
        self.assertEqual(finding["location"]["line"], 10)
        self.assertEqual(finding["references"][0]["id"], "CWE-89")
        self.assertEqual(finding["remediation"], "- a\n+ b")
        self.assertEqual([reference["id"] for reference in finding["references"]], ["CWE-89", "OWASP A03"])

    def test_confidence_bands(self):
        for value, expected in ((10, "high"), (8, "high"), (7, "medium"), (5, "medium"), (4, "low"), (1, "low")):
            self.assertEqual(emit.confidence_for(value), expected, value)
        self.assertEqual(emit.confidence_for("medium"), "medium")


DB_REPORT = {
    "files": 3,
    "findings": [
        {
            "file": ".tmp/db/migrations/001.sql", "line": 1, "rule": "reescritura-de-tipo",
            "severity": "high", "message": "reescribir la tabla bloquea escrituras",
        },
        {
            "target": "users.age", "rule": "columna-solo-en-migraciones",
            "severity": "medium", "message": "users.age nace de las migraciones y no está en el esquema",
        },
        {
            "file": ".tmp/db/schema.sql", "line": 5, "rule": "fk-sin-indice", "severity": "warning",
            "message": "la clave foránea orders.user_id no tiene índice",
            "fix": "CREATE INDEX idx_orders_user ON orders (user_id);",
        },
        {
            "file": ".tmp/db/schema.sql", "line": 9, "rule": "regla-nueva",
            "severity": "low", "message": "algo que aún no tiene consejo propio",
        },
    ],
}

API_DIFF = {
    "version": "major",
    "changes": [
        {"level": "major", "path": "/legacy/export", "detail": "endpoint eliminado"},
        {"level": "patch", "path": "GET /users/{id}", "detail": "cambio de descripción"},
    ],
}

API_AUTH = {
    "findings": [
        {"rule": "ruta-sin-guarda", "severity": "high", "target": "GET /users/{id}",
         "message": "el contrato exige seguridad y read_user no lleva guarda",
         "file": "api/api.py", "line": 7},
        {"rule": "spec-sin-codigo", "severity": "low", "target": "POST /admin/purge",
         "message": "el contrato declara la operación y no hay ruta que la implemente"},
    ],
}

FINOPS_LLM = {
    "files": 1,
    "findings": [
        {"file": "app/assistant.py", "line": 7, "rule": "llm-sin-limite-tokens", "severity": "high",
         "message": "llamada create() sin max_tokens: la respuesta puede crecer sin tope"},
        {"file": "app/assistant.py", "line": 16, "rule": "llm-sin-limite-tokens", "severity": "high",
         "message": "llamada create() sin max_tokens: la respuesta puede crecer sin tope"},
        {"file": "app/assistant.py", "line": 15, "rule": "bucle-sin-tope", "severity": "high",
         "message": "bucle while True con llamadas al modelo y sin break"},
    ],
}


class DbAdapterTests(unittest.TestCase):
    def setUp(self):
        self.payload = emit.from_db(DB_REPORT, "db-architect", "2.1.1")

    def test_report_is_valid(self):
        self.assertEqual(findings_validate.validate_payload(self.payload), [])
        self.assertEqual(self.payload["tool"]["package"], "db-architect")
        self.assertEqual(self.payload["summary"]["total"], 4)

    def test_file_and_schema_locations(self):
        first, second = self.payload["findings"][0], self.payload["findings"][1]
        self.assertEqual(first["location"], {"type": "file", "target": ".tmp/db/migrations/001.sql",
                                             "line": 1, "end_line": None})
        self.assertEqual(second["location"], {"type": "schema", "target": "users.age",
                                              "line": None, "end_line": None})

    def test_warning_becomes_medium_and_fix_is_used(self):
        third = self.payload["findings"][2]
        self.assertEqual(third["severity"], "medium")
        self.assertEqual(third["remediation"], "CREATE INDEX idx_orders_user ON orders (user_id);")
        self.assertEqual(third["evidence"], "CREATE INDEX idx_orders_user ON orders (user_id);")

    def test_known_and_unknown_rules_get_a_fix(self):
        first, last = self.payload["findings"][0], self.payload["findings"][3]
        self.assertIn("expand/contract", first["remediation"])
        self.assertIn("docs/db-architect.md", last["remediation"])
        self.assertEqual(last["evidence"], ".tmp/db/schema.sql:9")


class ApiAdapterTests(unittest.TestCase):
    def test_changes_become_endpoint_urls(self):
        payload = emit.from_api(API_DIFF, "api-contract-guard", "1.2.0")
        self.assertEqual(findings_validate.validate_payload(payload), [])
        self.assertEqual(payload["summary"]["note"], "veredicto major")
        major, patch = payload["findings"]
        self.assertEqual(major["rule_id"], "contract-diff-major")
        self.assertEqual(major["severity"], "high")
        self.assertEqual(major["location"], {"type": "url", "target": "/legacy/export",
                                             "line": None, "end_line": None})
        self.assertEqual(patch["severity"], "low")

    def test_coverage_findings_use_code_or_endpoint(self):
        payload = emit.from_api(API_AUTH, "api-contract-guard", "1.2.0")
        self.assertEqual(findings_validate.validate_payload(payload), [])
        first, second = payload["findings"]
        self.assertEqual(first["location"]["type"], "file")
        self.assertEqual(first["location"]["line"], 7)
        self.assertEqual(second["location"], {"type": "url", "target": "POST /admin/purge",
                                              "line": None, "end_line": None})

    def test_endpoints_without_scheme_go_to_logical_locations(self):
        sarif = findings_to_sarif.build_sarif(emit.from_api(API_DIFF, "api-contract-guard", "1.2.0"))
        result = sarif["runs"][0]["results"][0]
        self.assertIn("logicalLocations", result["locations"][0])
        self.assertEqual(result["locations"][0]["logicalLocations"][0]["fullyQualifiedName"],
                         "/legacy/export")


class FinopsAdapterTests(unittest.TestCase):
    def test_merges_identical_sites(self):
        payload = emit.from_finops(FINOPS_LLM, "finops-auditor", "1.1.0")
        self.assertEqual(findings_validate.validate_payload(payload), [])
        self.assertEqual(payload["summary"]["total"], 2)
        merged = payload["findings"][0]
        self.assertEqual(merged["rule_id"], "llm-sin-limite-tokens")
        self.assertIn("app/assistant.py:7", merged["evidence"])
        self.assertIn("también en app/assistant.py:16", merged["evidence"])
        self.assertEqual(payload["findings"][1]["rule_id"], "bucle-sin-tope")


DOCS_PARITY = {
    "target": "skills-ia",
    "findings": [
        {"file": "README.md", "line": 0, "rule": "secciones-idioma", "severity": "high",
         "message": "faltan las mitades «## 🇪🇸 Español» y «## 🇬🇧 English»",
         "fix": "Añade ambas secciones antes de traducir nada."},
        {"file": "docs/index.md", "line": 12, "rule": "ancla-rota", "severity": "medium",
         "message": "EN: #no-existe no apunta a ningún encabezado"},
        {"file": "docs/appsec-audit.md", "line": 3, "rule": "regla-sin-consejo", "severity": "low",
         "message": "algo que aún no tiene consejo propio"},
        {"file": "docs/a.md", "line": 4, "rule": "cifras", "severity": "warning",
         "message": "ES declara 80 skills y EN 81"},
        {"rule": "forma-tablas", "severity": "medium", "message": "sin fichero: no se puede ubicar"},
    ],
}


class DocsAdapterTests(unittest.TestCase):
    def setUp(self):
        self.payload = emit.from_docs(DOCS_PARITY, "docs-parity", "1.3.0")

    def test_parity_report_is_valid(self):
        self.assertEqual(findings_validate.validate_payload(self.payload), [])
        self.assertEqual(self.payload["tool"]["package"], emit.PACKAGES["docs"])
        self.assertEqual(self.payload["tool"]["skill"], "docs-parity")
        self.assertEqual(self.payload["summary"]["total"], 4)

    def test_document_wide_drift_keeps_the_file_and_no_line(self):
        first = self.payload["findings"][0]
        self.assertEqual(first["rule_id"], "secciones-idioma")
        self.assertEqual(first["location"], {"type": "file", "target": "README.md",
                                             "line": None, "end_line": None})
        self.assertEqual(first["evidence"], "Añade ambas secciones antes de traducir nada.")
        self.assertEqual(self.payload["findings"][1]["location"]["line"], 12)

    def test_own_fix_wins_then_the_rule_table_then_the_guide(self):
        first, second, third = self.payload["findings"][:3]
        self.assertEqual(first["remediation"], "Añade ambas secciones antes de traducir nada.")
        self.assertEqual(second["remediation"], emit.DOCS_FIXES["ancla-rota"])
        self.assertIn("docs/docs-sync-engine.md", third["remediation"])
        self.assertIn("regla-sin-consejo", third["remediation"])

    def test_warning_reads_as_medium_and_findings_need_a_file(self):
        severities = [finding["severity"] for finding in self.payload["findings"]]
        self.assertEqual(severities, ["high", "medium", "low", "medium"])
        self.assertEqual(self.payload["findings"][1]["evidence"], "docs/index.md:12")
        self.assertNotIn("forma-tablas", [finding["rule_id"] for finding in self.payload["findings"]])
        self.assertIs(emit.ADAPTERS["docs"], emit.from_docs)


class EmitCliTests(unittest.TestCase):
    def test_cli_reads_the_package_version_and_writes_a_valid_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "finops-auditor").mkdir()
            manifest = {"name": "finops-auditor", "version": "1.4.2"}
            (root / "finops-auditor" / "skills.json").write_text(json.dumps(manifest), encoding="utf-8")
            native = root / "llm.json"
            native.write_text(json.dumps(FINOPS_LLM), encoding="utf-8")
            output = root / "findings.json"
            with redirect_stdout(io.StringIO()):
                code = emit.main(["finops", str(native), "--output", str(output), "--root", str(root)])
            self.assertEqual(code, 0)
            emitted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(emitted["tool"]["version"], "1.4.2")
            self.assertEqual(findings_validate.validate_payload(emitted), [])

    def test_cli_rejects_an_unknown_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            native = Path(tmp) / "raro.json"
            native.write_text(json.dumps({"resultados": []}), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(emit.main(["db", str(native)]), 1)


if __name__ == "__main__":
    unittest.main()
