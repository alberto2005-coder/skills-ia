"""Tests de replica/scripts/imgdiff.py con PNG generados por stdlib (zlib + struct)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import support
import imgdiff


class ImgDiffTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return os.path.join(self.dir, name)

    def png_misma(self, name):
        # Banda blanca horizontal en las filas 20-40: bordes marcados y estables.
        return support.write_png(
            self.path(name), 64, 64, support.band_pixel(set(range(20, 40)))
        )

    def png_banda_abajo(self, name):
        return support.write_png(
            self.path(name), 64, 64, support.band_pixel(set(range(40, 60)))
        )

    def test_identicas_dan_100(self):
        a = self.png_misma("a.png")
        b = self.png_misma("b.png")
        code, out, _ = support.run_capture(imgdiff.main, [a, b])
        self.assertEqual(code, 0)
        self.assertIn("100.0%", out)
        self.assertIn("structura practicamente identica", out)  # "Estructura", con mayuscula

    def test_layout_distinto_baja_la_similitud(self):
        a = self.png_misma("a.png")
        b = self.png_banda_abajo("b.png")
        code, out, _ = support.run_capture(imgdiff.main, [a, b, "--json"])
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertLess(data["similarity"], 100.0)
        self.assertTrue(data["regions"])
        self.assertEqual(data["grid"], "32x32")

    def test_umbral_falla(self):
        a = self.png_misma("a.png")
        b = self.png_banda_abajo("b.png")
        code, out, _ = support.run_capture(
            imgdiff.main, [a, b, "--min-similarity", "99.9"]
        )
        self.assertEqual(code, 1)
        self.assertIn("Por debajo del umbral", out)

    def test_umbral_pasa(self):
        a = self.png_misma("a.png")
        b = self.png_banda_abajo("b.png")
        code, _, _ = support.run_capture(
            imgdiff.main, [a, b, "--min-similarity", "0"]
        )
        self.assertEqual(code, 0)

    def test_mapa_de_calor_es_png_valido(self):
        a = self.png_misma("a.png")
        b = self.png_banda_abajo("b.png")
        out_png = self.path("diff.png")
        code, out, _ = support.run_capture(imgdiff.main, [a, b, "--out", out_png])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(out_png))
        self.assertIn("Mapa de calor", out)
        with open(out_png, "rb") as fh:
            self.assertEqual(fh.read(8), imgdiff.PNG_SIG)
        # El PNG de salida se puede volver a leer con el propio lector.
        width, height, bpp, pixels = imgdiff.read_png(out_png)
        self.assertEqual((width, height, bpp), (64, 64, 3))
        self.assertEqual(len(pixels), 64 * 64 * 3)

    def test_rgba_y_gris(self):
        a = support.write_png(
            self.path("rgba.png"), 64, 64,
            lambda x, y: (255, 255, 255, 255) if y in range(20, 40) else (0, 0, 0, 255),
            color_type=6,
        )
        b = support.write_png(
            self.path("gris.png"), 64, 64,
            lambda x, y: (255,) if y in range(20, 40) else (0,),
            color_type=0,
        )
        width, height, bpp, _ = imgdiff.read_png(a)
        self.assertEqual((width, bpp), (64, 4))
        code, out, _ = support.run_capture(imgdiff.main, [a, b, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["similarity"], 100.0)

    def test_no_es_png(self):
        path = support.write_text(self.path("falso.png"), "no soy un png")
        code, _, err = support.run_capture(imgdiff.main, [path, self.png_misma("a.png")])
        self.assertEqual(code, 2)
        self.assertIn("no es un PNG", err)

    def test_fichero_inexistente(self):
        code, _, err = support.run_capture(
            imgdiff.main, [self.path("nada.png"), self.png_misma("a.png")]
        )
        self.assertEqual(code, 2)
        self.assertIn("[x]", err)

    def test_grid_minimo(self):
        a = self.png_misma("a.png")
        with self.assertRaises(SystemExit) as ctx:
            support.run_capture(imgdiff.main, [a, a, "--grid", "3"])
        self.assertEqual(ctx.exception.code, 2)

    def test_png_entrelazado_no_soportado(self):
        import struct
        import zlib

        raw = bytearray()
        for _ in range(8):
            raw.append(0)
            raw.extend(b"\x00" * 8 * 3)

        def chunk(tag, payload):
            return (
                struct.pack(">I", len(payload))
                + tag
                + payload
                + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
            )

        data = (
            imgdiff.PNG_SIG
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 2, 0, 0, 1))
            + chunk(b"IDAT", zlib.compress(bytes(raw)))
            + chunk(b"IEND", b"")
        )
        path = self.path("entrelazado.png")
        with open(path, "wb") as fh:
            fh.write(data)
        code, _, err = support.run_capture(imgdiff.main, [path, path])
        self.assertEqual(code, 2)
        self.assertIn("entrelazado", err)

    def test_ayuda_argparse(self):
        with self.assertRaises(SystemExit) as ctx:
            support.run_capture(imgdiff.main, ["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
