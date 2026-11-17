# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import onpage
from scripts.page import parse_file, parse_html

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def status(checks, check_id):
    for rec in checks:
        if rec["id"] == check_id:
            return rec["status"]
    return None


class OnPageTests(unittest.TestCase):
    def test_multiple_h1_fails(self):
        page = parse_file(str(FIXTURES / "page_bad.html"))
        checks, data = onpage.analyze(page, "bad.html")
        self.assertEqual(status(checks, "ONP-H1-001"), "fail")
        self.assertIn("H1 duplicado", " ".join(data["headings"]["issues"]))

    def test_heading_jump_detected(self):
        page = parse_html("<html><body><h1>A</h1><h3>B</h3></body></html>")
        result = onpage.heading_hierarchy(page)
        self.assertTrue(any("Salto" in issue for issue in result["issues"]))
        self.assertEqual(result["counts"]["h1"], 1)

    def test_images_without_alt_lists_paths(self):
        page = parse_file(str(FIXTURES / "page_bad.html"))
        paths = onpage.images_without_alt(page)
        self.assertEqual(paths, ["http://example.com/img/foto.png"])
        # `alt=""` marca imagen decorativa: no es un alt ausente.
        self.assertNotIn("/img/otra.png", paths)

    def test_ratio_estimate(self):
        page = parse_file(str(FIXTURES / "page_full.html"))
        checks, data = onpage.analyze(page, "full.html")
        self.assertGreater(data["text_ratio"], 0.1)
        self.assertIn(status(checks, "ONP-RATIO-001"), ("pass", "fail"))
        ratio_check = [rec for rec in checks if rec["id"] == "ONP-RATIO-001"][0]
        self.assertEqual(ratio_check["note"], "estimate")

    def test_keyword_density_table(self):
        page = parse_file(str(FIXTURES / "page_full.html"))
        density = onpage.keyword_density(page, limit=5)
        self.assertLessEqual(len(density["filas"]), 5)
        self.assertGreater(density["total_terminos"], 10)
        densities = [row["densidad_pct"] for row in density["filas"]]
        self.assertEqual(densities, sorted(densities, reverse=True))
        for row in density["filas"]:
            self.assertNotIn(row["termino"], onpage.STOPWORDS)

    def test_density_check_is_informational(self):
        page = parse_file(str(FIXTURES / "page_full.html"))
        checks, _ = onpage.analyze(page, "full.html")
        # No debe sumar un "pass" gratis a la dimensión de contenido.
        self.assertEqual(status(checks, "ONP-KW-001"), "skip")
        rec = [c for c in checks if c["id"] == "ONP-KW-001"][0]
        self.assertIn("no es", rec["evidence"])
        self.assertEqual(rec["note"], "informativo")


if __name__ == "__main__":
    unittest.main()
