"""Tests de replica/scripts/listing.py (limites de store, claims y keywords)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import support
import listing


def ios(**over):
    base = {
        "title": "Hueco - Reservas",
        "subtitle": "Precio plano",
        "promotional_text": "Sin coste por asiento.",
        "keywords": "calendario,citas,agenda",
        "description": "Comparte un enlace y deja que reserven.",
        "screenshots": 5,
    }
    base.update(over)
    return base


def android(**over):
    base = {
        "title": "Hueco - Reservas",
        "short_description": "Enlaces de reserva con precio plano.",
        "full_description": "Comparte un enlace y deja que reserven.",
        "screenshots": 6,
    }
    base.update(over)
    return base


class ListingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, data, name="listing.json"):
        return support.write_text(os.path.join(self.dir, name), json.dumps(data))

    def test_listing_valido(self):
        path = self.write({"platform": "both", "avoid": ["Otra App"], "ios": ios(), "android": android()})
        code, out, _ = support.run_capture(listing.main, [path])
        self.assertEqual(code, 0)
        self.assertIn("Limpio", out)
        self.assertIn("0 error(es)", out)

    def test_titulo_demasiado_largo(self):
        path = self.write({"platform": "ios", "ios": ios(title="H" * 31)})
        code, out, _ = support.run_capture(listing.main, [path])
        self.assertEqual(code, 1)
        self.assertIn("31/30", out)
        self.assertIn("te pasas 1", out)

    def test_titulo_casi_al_limite_avisa(self):
        path = self.write({"platform": "ios", "ios": ios(title="H" * 29)})
        code, out, _ = support.run_capture(listing.main, [path])
        self.assertEqual(code, 0)
        self.assertIn("muy al limite", out)

    def test_claim_de_ranking_avisa(self):
        path = self.write({"platform": "ios", "ios": ios(title="Hueco, el mejor")})
        code, out, _ = support.run_capture(listing.main, [path])
        self.assertEqual(code, 0)
        self.assertIn("claim de ranking", out)

    def test_nombre_del_original_es_error(self):
        path = self.write(
            {"platform": "ios", "avoid": ["Original App"], "ios": ios(description="Como Original App pero mejor.")}
        )
        code, out, _ = support.run_capture(listing.main, [path])
        self.assertEqual(code, 1)
        self.assertIn("rastro de la app original", out)

    def test_keywords_con_espacios_y_repetidas(self):
        path = self.write(
            {"platform": "ios", "ios": ios(keywords="calendario, citas,calendario,citas")}
        )
        code, out, _ = support.run_capture(listing.main, [path])
        self.assertEqual(code, 1)
        self.assertIn("espacios tras las comas", out)
        self.assertIn("Keywords repetidas", out)

    def test_keywords_solapan_con_titulo(self):
        path = self.write(
            {"platform": "ios", "ios": ios(title="Hueco reservas", keywords="hueco,citas,agenda")}
        )
        code, out, _ = support.run_capture(listing.main, [path])
        self.assertEqual(code, 0)
        self.assertIn("desperdician espacio", out)

    def test_capturas_fuera_de_rango(self):
        path = self.write({"platform": "android", "android": android(screenshots=1)})
        code, out, _ = support.run_capture(listing.main, [path])
        self.assertEqual(code, 0)
        self.assertIn("Capturas: 1", out)

    def test_campo_obligatorio_vacio(self):
        path = self.write({"platform": "android", "android": android(short_description="")})
        code, out, _ = support.run_capture(listing.main, [path])
        self.assertEqual(code, 1)
        self.assertIn("vacio", out)

    def test_json_resumen(self):
        path = self.write({"platform": "ios", "ios": ios(title="H" * 40)})
        code, out, _ = support.run_capture(listing.main, [path, "--json"])
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["errors"], 1)
        self.assertEqual(data["reports"][0]["platform"], "ios")

    def test_bloque_ausente(self):
        path = self.write({"platform": "ios"})
        code, _, err = support.run_capture(listing.main, [path])
        self.assertEqual(code, 2)
        self.assertIn("Falta el bloque", err)

    def test_json_invalido(self):
        path = support.write_text(os.path.join(self.dir, "roto.json"), "{no es json")
        code, _, err = support.run_capture(listing.main, [path])
        self.assertEqual(code, 2)
        self.assertIn("No se pudo leer", err)

    def test_ayuda_argparse(self):
        with self.assertRaises(SystemExit) as ctx:
            support.run_capture(listing.main, ["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
