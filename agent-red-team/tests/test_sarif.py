"""Tests del exportador SARIF de agent-red-team."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "scripts" / "export_sarif.py"


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def finding(**overrides):
    data = {
        "id": "SEC-01",
        "titulo": "Inyección de instrucciones en SKILL.md",
        "severidad": "high",
        "nivel": "normal",
        "categoria": "Prompt injection",
        "fichero": "SKILL.md",
        "linea": 12,
        "evidencia": "ignora las instrucciones anteriores",
        "verificacion": "confirmed",
        "justificacion_verificacion": "no es un fence ni un test",
        "recomendacion": "eliminar la instrucción",
    }
    data.update(overrides)
    return data


def report(findings, **overrides):
    data = {
        "herramienta": "agent-red-team",
        "version": "2.1.0",
        "target": "/tmp/skill",
        "fecha": "2026-11-17T00:00:00Z",
        "modo": "auditoria_completa",
        "veredicto": "PRECAUCION",
        "puntuacion_riesgo": 55,
        "rechazo": False,
        "findings": findings,
    }
    data.update(overrides)
    return data


class TestSarif(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, data, name="informe.json"):
        path = self.root / name
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def export(self, data, *extra):
        result = run(self.write(data), *extra)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_minimal_sarif_contract(self):
        sarif = self.export(report([finding()]))

        self.assertEqual(sarif["version"], "2.1.0")
        self.assertIn("sarif-2.1.0", sarif["$schema"])
        self.assertEqual(len(sarif["runs"]), 1)
        self.assertEqual(sarif["runs"][0]["tool"]["driver"]["name"], "agent-red-team")
        self.assertEqual(sarif["runs"][0]["tool"]["driver"]["version"], "2.1.0")

    def test_only_confirmed_is_exported_by_default(self):
        sarif = self.export(report([
            finding(id="SEC-01", verificacion="confirmed"),
            finding(id="SEC-02", verificacion="needs_validation", linea=3),
            finding(id="SEC-03", verificacion="rejected", linea=4),
        ]))

        results = sarif["runs"][0]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["partialFingerprints"]["agentRedTeamId/v1"], "SEC-01")

    def test_pending_needs_the_flag_and_becomes_a_note(self):
        data = report([finding(verificacion="needs_validation", severidad="critical")])
        without = self.export(data)
        with_pending = self.export(data, "--include-pending")

        self.assertEqual(without["runs"][0]["results"], [])
        result = with_pending["runs"][0]["results"][0]
        self.assertEqual(result["level"], "note")
        self.assertEqual(result["properties"]["verification"], "needs_validation")

    def test_severity_mapping(self):
        sarif = self.export(report([
            finding(id="SEC-01", severidad="critical"),
            finding(id="SEC-02", severidad="high"),
            finding(id="SEC-03", severidad="medium"),
            finding(id="SEC-04", severidad="low"),
        ]))

        levels = [result["level"] for result in sarif["runs"][0]["results"]]
        self.assertEqual(levels, ["error", "error", "warning", "note"])

    def test_reject_is_always_an_error(self):
        sarif = self.export(report([finding(severidad="low", nivel="REJECT")]))

        result = sarif["runs"][0]["results"][0]
        self.assertEqual(result["level"], "error")
        self.assertTrue(result["properties"]["reject"])

    def test_rules_are_deduplicated_by_category(self):
        sarif = self.export(report([
            finding(id="SEC-01", categoria="Prompt injection"),
            finding(id="SEC-02", categoria="Prompt injection", linea=20),
            finding(id="SEC-03", categoria="Exfiltración"),
        ]))

        run = sarif["runs"][0]
        self.assertEqual(len(run["tool"]["driver"]["rules"]), 2)
        self.assertEqual(
            [result["ruleIndex"] for result in run["results"]],
            [0, 0, 1],
        )
        self.assertEqual(run["results"][0]["ruleId"], "agent-red-team/prompt-injection")
        self.assertEqual(run["results"][2]["ruleId"], "agent-red-team/exfiltracion")

    def test_location_uses_forward_slashes_and_region(self):
        sarif = self.export(report([finding(fichero="scripts\\run.py", linea=7)]))

        location = sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
        self.assertEqual(location["artifactLocation"]["uri"], "scripts/run.py")
        self.assertEqual(location["region"]["startLine"], 7)

    def test_file_level_finding_has_no_region(self):
        sarif = self.export(report([finding(linea=0)]))

        location = sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
        self.assertNotIn("region", location)

    def test_run_properties_carry_the_verdict(self):
        sarif = self.export(report([finding()]))

        properties = sarif["runs"][0]["properties"]
        self.assertEqual(properties["veredicto"], "PRECAUCION")
        self.assertEqual(properties["puntuacion_riesgo"], 55)

    def test_output_file_is_written(self):
        path = self.write(report([finding()]))
        out = self.root / "salida.sarif"

        result = run(path, "--output", out)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(out.is_file())
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["version"], "2.1.0")

    def test_invalid_report_exits_one(self):
        path = self.write({"herramienta": "agent-red-team"})

        self.assertEqual(run(path).returncode, 1)

    def test_missing_file_exits_two(self):
        self.assertEqual(run(self.root / "no-existe.json").returncode, 2)


if __name__ == "__main__":
    unittest.main()
