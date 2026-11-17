"""Tests de replica/scripts/parity.py (score, gates y formatos)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import support
import parity

CSV_HEADER = "id,area,priority,feature,status,notes\n"


class ParityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def csv_path(self, *rows, name="features.csv"):
        return support.write_text(os.path.join(self.dir, name), CSV_HEADER + "".join(rows))

    def test_todos_los_must_done_pasa(self):
        path = self.csv_path(
            "f1,reservas,must,Ver huecos,done,\n",
            "f2,reservas,should,Recordatorio,partial,\n",
        )
        code, out, _ = support.run_capture(parity.main, [path])
        self.assertEqual(code, 0)
        self.assertIn("Score:", out)
        self.assertIn("Todos los must estan done", out)

    def test_must_parcial_no_es_desplegable(self):
        path = self.csv_path(
            "f1,reservas,must,Ver huecos,done,\n",
            "f2,reservas,must,Pagar,partial,\n",
        )
        code, out, _ = support.run_capture(parity.main, [path])
        self.assertEqual(code, 1)
        self.assertIn("NO desplegable", out)
        # (3*1 + 3*0.5) / 6 * 100 = 75.0
        self.assertIn("75.0%", out)

    def test_out_of_scope_sale_del_denominador(self):
        path = self.csv_path(
            "f1,x,must,Algo,done,\n",
            "f2,x,could,Extra,out_of_scope,No en v1\n",
        )
        result = parity.analyze(parity.load(path))
        self.assertEqual(result["score"], 100.0)
        self.assertEqual(result["in_scope"], 1)
        self.assertEqual(result["out_of_scope"], 1)
        self.assertTrue(result["shippable"])

    def test_json_resumen(self):
        path = self.csv_path("f1,x,must,Algo,done,\n")
        code, out, _ = support.run_capture(parity.main, [path, "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        for key in ("score", "must_gaps", "by_priority", "areas", "shippable"):
            self.assertIn(key, data)
        self.assertEqual(data["score"], 100.0)

    def test_markdown_a_fichero(self):
        path = self.csv_path("f1,x,must,Algo,missing,\n")
        out_path = os.path.join(self.dir, "sub", "parity.md")
        code, out, _ = support.run_capture(
            parity.main, [path, "--markdown", "--out", out_path, "--no-fail"]
        )
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(out_path))
        with open(out_path, encoding="utf-8") as fh:
            texto = fh.read()
        self.assertIn("# Paridad funcional", texto)
        self.assertIn("Must pendientes", texto)

    def test_no_fail_ignora_gate(self):
        path = self.csv_path("f1,x,must,Algo,missing,\n")
        code, _, _ = support.run_capture(parity.main, [path, "--no-fail"])
        self.assertEqual(code, 0)

    def test_fichero_inexistente(self):
        code, _, err = support.run_capture(
            parity.main, [os.path.join(self.dir, "no-existe.csv")]
        )
        self.assertEqual(code, 2)
        self.assertIn("No se pudo leer", err)

    def test_formato_no_soportado(self):
        path = support.write_text(os.path.join(self.dir, "features.txt"), "id,area\n")
        code, _, err = support.run_capture(parity.main, [path])
        self.assertEqual(code, 2)
        self.assertIn("Formato no soportado", err)

    def test_prioridades_estados_en_espanol(self):
        path = support.write_text(
            os.path.join(self.dir, "features.json"),
            json.dumps(
                {
                    "features": [
                        {"id": "a", "area": "x", "priority": "imprescindible", "status": "hecho"},
                        {"id": "b", "area": "x", "priority": "opcional", "status": "parcial"},
                        {"id": "c", "area": "x", "priority": "recomendado", "status": "fuera de alcance"},
                    ]
                }
            ),
        )
        rows = parity.load(path)
        self.assertEqual([r["priority"] for r in rows], ["must", "could", "should"])
        self.assertEqual([r["status"] for r in rows], ["done", "partial", "out_of_scope"])
        result = parity.analyze(rows)
        # must done = 3, could partial = 0.5 -> 3.5 / 4
        self.assertEqual(result["score"], 87.5)
        self.assertTrue(result["shippable"])

    def test_sin_must_no_es_desplegable(self):
        path = self.csv_path("f1,x,should,Algo,done,\n")
        code, out, _ = support.run_capture(parity.main, [path])
        self.assertEqual(code, 1)
        self.assertIn("Ningun feature marcado como must", out)

    def test_manifiesto_vacio(self):
        path = support.write_text(os.path.join(self.dir, "vacio.csv"), CSV_HEADER)
        code, _, err = support.run_capture(parity.main, [path])
        self.assertEqual(code, 2)
        self.assertIn("vacio", err)

    def test_ayuda_argparse(self):
        with self.assertRaises(SystemExit) as ctx:
            support.run_capture(parity.main, ["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
