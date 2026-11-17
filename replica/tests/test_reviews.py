"""Tests de replica/scripts/reviews.py (temas, citas con URL y marca THIN)."""

from __future__ import annotations

import csv
import json
import os
import tempfile
import unittest

import support
import reviews

HEADER = ["source", "url", "rating", "text", "date"]


class ReviewsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write_csv(self, rows, name="reviews.csv"):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(HEADER)
            writer.writerows(rows)
        return path

    def write_themes(self, themes, name="themes.json"):
        return support.write_text(
            os.path.join(self.dir, name), json.dumps({"themes": themes})
        )

    def rows(self):
        return [
            ["App Store", "https://apps.apple.com/a", 2, "Me cobran por asiento y la factura se dispara.", "2026-01-01"],
            ["G2", "https://www.g2.com/b", 1, "Per seat pricing otra vez; es caro para un equipo.", "2026-01-02"],
            ["G2", "https://www.g2.com/c", 2, "Caro y por asiento, no lo recomiendo.", "2026-01-03"],
            ["Reddit", "", 3, "Texto suficientemente largo pero sin enlace.", "2026-01-04"],
            ["Reddit", "https://reddit.com/d", 5, "corto", "2026-01-05"],
            ["Trustpilot", "https://trustpilot.com/e", 1, "La app tarda mucho en abrir el calendario.", "2026-01-06"],
        ]

    def test_descarta_filas_sin_url_o_texto_corto(self):
        csv_path = self.write_csv(self.rows())
        valid, dropped = reviews.load_reviews(csv_path)
        self.assertEqual(len(valid), 4)
        self.assertEqual(dropped, 2)
        self.assertTrue(all(v["url"].startswith("https://") for v in valid))

    def test_tema_solido_y_tema_thin(self):
        csv_path = self.write_csv(self.rows())
        themes = self.write_themes(
            {"precio por asiento": ["per seat", "por asiento", "caro"], "sms": ["sms"]}
        )
        code, out, _ = support.run_capture(
            reviews.main, [csv_path, "--themes", themes, "--json"]
        )
        self.assertEqual(code, 0)
        data = json.loads(out)
        por_tema = {t["theme"]: t for t in data["themes"]}
        self.assertEqual(por_tema["precio por asiento"]["count"], 3)
        self.assertFalse(por_tema["precio por asiento"]["thin"])
        self.assertEqual(por_tema["sms"]["count"], 0)
        self.assertTrue(por_tema["sms"]["thin"])
        self.assertEqual(data["dropped"], 2)

    def test_citas_llevan_url_y_texto_literal(self):
        csv_path = self.write_csv(self.rows())
        themes = self.write_themes({"precio por asiento": ["por asiento"]})
        code, out, _ = support.run_capture(reviews.main, [csv_path, "--themes", themes, "--json"])
        data = json.loads(out)
        citas = data["themes"][0]["quotes"]
        self.assertTrue(citas)
        for cita in citas:
            self.assertTrue(cita["url"].startswith("https://"))
            self.assertIn("asiento", cita["text"])

    def test_una_sola_fuente_es_thin(self):
        rows = [
            ["App Store", "https://a/1", 2, "Es caro y lento, no lo uso.", "2026-01-01"],
            ["App Store", "https://a/2", 2, "Caro para lo que ofrece.", "2026-01-02"],
            ["App Store", "https://a/3", 1, "Caro y lento otra vez.", "2026-01-03"],
        ]
        csv_path = self.write_csv(rows)
        themes = self.write_themes({"precio": ["caro"]})
        code, out, _ = support.run_capture(reviews.main, [csv_path, "--themes", themes, "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["themes"][0]["count"], 3)
        self.assertTrue(data["themes"][0]["thin"])  # una sola fuente

    def test_markdown_marca_thin_y_se_escribe(self):
        csv_path = self.write_csv(self.rows())
        themes = self.write_themes({"sms": ["sms"], "precio": ["caro"]})
        out_path = os.path.join(self.dir, "themes.md")
        code, out, _ = support.run_capture(
            reviews.main, [csv_path, "--themes", themes, "--out", out_path]
        )
        self.assertEqual(code, 0)
        self.assertIn("Citas", out)
        with open(out_path, encoding="utf-8") as fh:
            texto = fh.read()
        self.assertIn("THIN", texto)
        self.assertIn("https://", texto)

    def test_plurales_y_sufijos(self):
        patron = reviews.keyword_pattern("seat")
        self.assertTrue(patron.search("per seats"))
        patron = reviews.keyword_pattern("cancel")
        self.assertTrue(patron.search("cancelar la suscripcion"))
        self.assertFalse(patron.search("cancelaciontotalmente"))

    def test_sin_resenas_validas(self):
        csv_path = self.write_csv([["X", "", 1, "texto largo sin enlace alguno", "2026-01-01"]])
        themes = self.write_themes({"x": ["y"]})
        code, _, err = support.run_capture(reviews.main, [csv_path, "--themes", themes])
        self.assertEqual(code, 2)
        self.assertIn("Ninguna resena con URL valida", err)

    def test_themes_inexistente(self):
        csv_path = self.write_csv(self.rows())
        code, _, err = support.run_capture(
            reviews.main, [csv_path, "--themes", os.path.join(self.dir, "no.json")]
        )
        self.assertEqual(code, 2)

    def test_tsv(self):
        path = os.path.join(self.dir, "reviews.tsv")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write("source\turl\trating\ttext\tdate\n")
            fh.write("G2\thttps://g2.com/1\t2\tNo hay recordatorio por SMS, mala.\t2026-01-01\n")
        valid, dropped = reviews.load_reviews(path)
        self.assertEqual(len(valid), 1)
        self.assertEqual(dropped, 0)
        self.assertEqual(valid[0]["source"], "G2")

    def test_ayuda_argparse(self):
        with self.assertRaises(SystemExit) as ctx:
            support.run_capture(reviews.main, ["--help"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
