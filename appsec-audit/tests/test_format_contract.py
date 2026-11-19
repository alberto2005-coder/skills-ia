"""Contrato de versiones: el payload de findings y el SARIF las declaran."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

from appsec_config import SKILL_ROOT

SCRIPT_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import appsec_util  # noqa: E402
import export_sarif  # noqa: E402
import init_audit  # noqa: E402
import validate_findings  # noqa: E402


class FormatContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.target = Path(self.tmp.name) / "proyecto"
        self.target.mkdir()
        self.assertEqual(init_audit.main([str(self.target)]), 0)
        path = self.target / init_audit.OUTPUT_DIR / "findings.json"
        self.payload = json.loads(path.read_text(encoding="utf-8"))

    def test_payload_stays_inside_the_schema(self):
        schema = validate_findings.load_schema()
        # El esquema cierra la raíz (`additionalProperties: false`), así que toda
        # clave del payload tiene que estar declarada en `properties`.
        self.assertLessEqual(set(self.payload), set(schema["properties"]))
        self.assertLessEqual(set(schema["required"]), set(self.payload))
        self.assertEqual(self.payload["format_version"], appsec_util.FORMAT_VERSION)
        declared = schema["properties"]["format_version"]
        self.assertEqual(declared["type"], "string")
        self.assertIn(self.payload["format_version"], declared["examples"])
        self.assertEqual(validate_findings.validate_payload(self.payload), [])

    def test_sarif_exports_tool_and_format_versions(self):
        sarif = export_sarif.build_sarif(self.payload)
        run = sarif["runs"][0]
        self.assertEqual(run["tool"]["driver"]["name"], "appsec-audit")
        self.assertEqual(run["tool"]["driver"]["version"], appsec_util.TOOL_VERSION)
        self.assertEqual(run["properties"]["format_version"], appsec_util.FORMAT_VERSION)


if __name__ == "__main__":
    unittest.main()
