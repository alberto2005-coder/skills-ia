"""Valida que el ledger de cobertura y el esquema del informe son JSON coherentes."""

import json
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
TEMPLATES = RAIZ / "templates"


class TestPlantillasJSON(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = json.loads((TEMPLATES / "coverage-ledger.json").read_text(encoding="utf-8"))
        cls.esquema = json.loads((TEMPLATES / "report-schema.json").read_text(encoding="utf-8"))

    def test_ledger_es_valido(self):
        self.assertIn("entradas", self.ledger)
        self.assertGreaterEqual(len(self.ledger["entradas"]), 6)

    def test_entradas_del_ledger_tienen_los_campos(self):
        obligatorios = {"superficie", "ficheros", "checks", "estado", "notas"}
        for entrada in self.ledger["entradas"]:
            self.assertTrue(obligatorios.issubset(entrada.keys()), entrada)
            self.assertIn(entrada["estado"], {"covered", "partial", "missing"})
            self.assertIsInstance(entrada["ficheros"], list)
            self.assertIsInstance(entrada["checks"], list)

    def test_ledger_cubre_las_superficies_pedidas(self):
        superficies = " ".join(e["superficie"] for e in self.ledger["entradas"]).lower()
        for esperada in ("skill.md", "scripts", "hooks", "mcp", "templates", "references"):
            self.assertIn(esperada, superficies)

    def test_esquema_exige_los_campos_del_hallazgo(self):
        finding = self.esquema["definitions"]["finding"]
        for campo in (
            "id", "titulo", "severidad", "categoria", "fichero",
            "linea", "evidencia", "verificacion", "recomendacion",
        ):
            self.assertIn(campo, finding["required"])
            self.assertIn(campo, finding["properties"])

    def test_enumeraciones_del_esquema(self):
        finding = self.esquema["definitions"]["finding"]["properties"]
        self.assertEqual(finding["severidad"]["enum"], ["critical", "high", "medium", "low"])
        self.assertEqual(
            finding["verificacion"]["enum"], ["confirmed", "needs_validation", "rejected"]
        )

    def test_estados_de_cobertura_en_el_esquema(self):
        cobertura = self.esquema["definitions"]["cobertura"]["properties"]["estado"]
        self.assertEqual(cobertura["enum"], ["covered", "partial", "missing"])


if __name__ == "__main__":
    unittest.main()
