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
import validate_findings  # noqa: E402

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
        return validate_findings.validate_payload(data)

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
                    self.assertEqual(validate_findings.main(argv), expected, threshold)

    def test_unreadable_input_and_invalid_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(validate_findings.main([str(Path(tmp) / "no-existe.json")]), 2)
            broken = Path(tmp) / "roto.json"
            broken.write_text("{", encoding="utf-8")
            self.assertEqual(validate_findings.main([str(broken)]), 2)


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
        self.assertEqual(validate_findings.validate_payload(emitted), [])
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
        self.assertEqual(validate_findings.validate_payload(emitted), [])
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


if __name__ == "__main__":
    unittest.main()
