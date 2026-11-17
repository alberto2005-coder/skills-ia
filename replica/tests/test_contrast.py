"""Tests de replica/scripts/contrast.py (WCAG AA/AAA y parseo de colores)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import support
import contrast


class ContrastTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def tokens(self, colors, pairs=None, name="tokens.json"):
        data = {"colors": colors}
        if pairs is not None:
            data["pairs"] = pairs
        return support.write_text(os.path.join(self.dir, name), json.dumps(data))

    def test_blanco_sobre_negro_pasa(self):
        path = self.tokens({"text": "#FFFFFF", "background": "#000000"}, [["text", "background"]])
        code, out, _ = support.run_capture(contrast.main, [path])
        self.assertEqual(code, 0)
        self.assertIn("21.00", out)
        self.assertIn("cumplen AA", out)

    def test_gris_medio_falla_aa(self):
        path = self.tokens({"text": "#777777", "background": "#FFFFFF"}, [["text", "background"]])
        code, out, _ = support.run_capture(contrast.main, [path])
        self.assertEqual(code, 1)
        self.assertIn("4.48", out)
        self.assertIn("no cumplen AA", out)

    def test_texto_grande_usa_umbral_3(self):
        path = self.tokens(
            {"text": "#777777", "background": "#FFFFFF"}, [["text", "background", "large"]]
        )
        code, _, _ = support.run_capture(contrast.main, [path])
        self.assertEqual(code, 0)

    def test_json_incluye_aa_y_aaa(self):
        path = self.tokens({"text": "#000000", "background": "#FFFFFF"}, [["text", "background"]])
        code, out, _ = support.run_capture(contrast.main, [path, "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["failures"], 0)
        par = data["pairs"][0]
        self.assertTrue(par["aa"])
        self.assertTrue(par["aaa"])
        self.assertEqual(par["ratio"], 21.0)

    def test_min_propio(self):
        path = self.tokens({"text": "#000000", "background": "#FFFFFF"}, [["text", "background"]])
        code, _, _ = support.run_capture(contrast.main, [path, "--min", "22"])
        self.assertEqual(code, 1)

    def test_pares_por_defecto(self):
        path = self.tokens({"text": "#000000", "background": "#FFFFFF", "muted": "#AAAAAA"})
        code, out, _ = support.run_capture(contrast.main, [path, "--json"])
        data = json.loads(out)
        pares = {(p["foreground"], p["background"]) for p in data["pairs"]}
        self.assertIn(("text", "background"), pares)
        self.assertIn(("muted", "background"), pares)
        self.assertEqual(code, 1)  # #AAAAAA sobre blanco no llega a 4.5

    def test_parse_color_variantes(self):
        self.assertEqual(contrast.parse_color("#FFF"), (255, 255, 255))
        self.assertEqual(contrast.parse_color("#11223344"), (17, 34, 51))
        self.assertEqual(contrast.parse_color("rgb(1, 2, 3)"), (1, 2, 3))
        self.assertEqual(contrast.parse_color("rgba(1, 2, 3, 0.5)"), (1, 2, 3))
        self.assertEqual(contrast.parse_color("white"), (255, 255, 255))
        with self.assertRaises(ValueError):
            contrast.parse_color("azul")

    def test_fichero_inexistente(self):
        code, _, err = support.run_capture(contrast.main, [os.path.join(self.dir, "no.json")])
        self.assertEqual(code, 2)
        self.assertIn("No se pudo leer", err)

    def test_menos_de_dos_colores(self):
        path = self.tokens({"text": "#FFFFFF"})
        code, _, err = support.run_capture(contrast.main, [path])
        self.assertEqual(code, 2)
        self.assertIn("al menos dos colores", err)

    def test_color_desconocido_en_par_se_ignora(self):
        path = self.tokens(
            {"text": "#000000", "background": "#FFFFFF"}, [["text", "fantasma"]]
        )
        code, _, err = support.run_capture(contrast.main, [path, "--json"])
        self.assertEqual(code, 0)
        self.assertIn("Par ignorado", err)

    def test_ayuda_argparse(self):
        with self.assertRaises(SystemExit) as ctx:
            support.run_capture(contrast.main, ["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
