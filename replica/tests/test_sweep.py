"""Tests de replica/scripts/sweep.py (marca, dominio, colores y exenciones)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import support
import sweep


class SweepTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def file(self, name, text):
        return support.write_text(os.path.join(self.dir, name), text)

    def test_directorio_limpio(self):
        self.file("app.py", "print('hola')\n")
        code, out, _ = support.run_capture(sweep.main, [self.dir, "--avoid", "Original App"])
        self.assertEqual(code, 0)
        self.assertIn("Limpio", out)

    def test_marca_con_variantes(self):
        self.file("vista.py", "class OriginalAppEmbed: pass\n")
        code, out, _ = support.run_capture(sweep.main, [self.dir, "--avoid", "Original App"])
        self.assertEqual(code, 1)
        self.assertIn("OriginalAppEmbed", out)
        self.assertIn("hallazgo", out)

    def test_json_marca_dominio(self):
        self.file("index.html", "<a href='https://originalapp.com/x'>ir</a>\n")
        code, out, _ = support.run_capture(
            sweep.main, [self.dir, "--avoid", "originalapp.com", "--json"]
        )
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertFalse(data["clean"])
        self.assertEqual(data["by_term"].get("originalapp.com"), 1)
        self.assertEqual(data["hits"][0]["line"], 1)

    def test_color_hex_y_rgb(self):
        self.file("tema.css", ".a{color:#1DB954}\n.b{background:rgb(29, 185, 84)}\n")
        code, out, _ = support.run_capture(
            sweep.main, [self.dir, "--color", "#1DB954", "--json"]
        )
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(len(data["hits"]), 2)
        self.assertEqual(data["by_term"].get("#1db954"), 2)

    def test_color_invalido_se_ignora(self):
        self.file("tema.css", ".a{color:#1DB954}\n")
        code, _, err = support.run_capture(sweep.main, [self.dir, "--color", "verde"])
        self.assertEqual(code, 0)
        self.assertIn("Color no valido", err)

    def test_exencion_por_linea(self):
        self.file("doc.md", "El original se llama Original App  <!-- sweep:ignore -->\n")
        code, out, _ = support.run_capture(sweep.main, [self.dir, "--avoid", "Original App"])
        self.assertEqual(code, 0)
        self.assertIn("Limpio", out)

    def test_exencion_por_fichero(self):
        self.file("limites.md", "sweep:ignore-file\n\n# Limites\nSe compara con Original App.\n")
        code, _, _ = support.run_capture(sweep.main, [self.dir, "--avoid", "Original App"])
        self.assertEqual(code, 0)

    def test_exencion_de_fichero_solo_en_cabecera(self):
        lineas = ["# doc\n"] * 6 + ["Original App\n"]
        self.file("tarde.md", "".join(lineas))
        code, _, _ = support.run_capture(sweep.main, [self.dir, "--avoid", "Original App"])
        self.assertEqual(code, 1)

    def test_excluir_directorio(self):
        os.makedirs(os.path.join(self.dir, "vendor"), exist_ok=True)
        self.file(os.path.join("vendor", "lib.js"), "var x = 'Original App';\n")
        self.file("app.js", "var y = 1;\n")
        code, _, _ = support.run_capture(
            sweep.main, [self.dir, "--avoid", "Original App", "--exclude", "vendor"]
        )
        self.assertEqual(code, 0)

    def test_ignora_binarios(self):
        path = os.path.join(self.dir, "logo.png")
        with open(path, "wb") as fh:
            fh.write(b"\x89PNG\r\n\x1a\n\x00\x00Original App\x00\x00")
        code, out, _ = support.run_capture(sweep.main, [self.dir, "--avoid", "Original App"])
        self.assertEqual(code, 0)
        self.assertIn("Limpio", out)

    def test_no_fail(self):
        self.file("app.py", "NOMBRE = 'Original App'\n")
        code, _, _ = support.run_capture(
            sweep.main, [self.dir, "--avoid", "Original App", "--no-fail"]
        )
        self.assertEqual(code, 0)

    def test_ruta_inexistente(self):
        code, _, err = support.run_capture(
            sweep.main, [os.path.join(self.dir, "nada"), "--avoid", "X"]
        )
        self.assertEqual(code, 2)
        self.assertIn("No existe", err)

    def test_sin_terminos_es_error_de_uso(self):
        with self.assertRaises(SystemExit) as ctx:
            support.run_capture(sweep.main, [self.dir])
        self.assertEqual(ctx.exception.code, 2)

    def test_fichero_suelto(self):
        path = self.file("solo.txt", "marca: Original App\n")
        code, out, _ = support.run_capture(sweep.main, [path, "--avoid", "Original App"])
        self.assertEqual(code, 1)
        self.assertIn("1 hallazgo", out)

    def test_ayuda_argparse(self):
        with self.assertRaises(SystemExit) as ctx:
            support.run_capture(sweep.main, ["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
