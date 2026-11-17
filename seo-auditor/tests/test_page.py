# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.page import normalize_url, parse_file, parse_html

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load(name):
    return parse_file(str(FIXTURES / name))


class PageParserTests(unittest.TestCase):
    def test_metadata(self):
        page = load("page_full.html")
        self.assertIn("Auditoría SEO", page.title)
        self.assertGreater(len(page.description), 100)
        self.assertEqual(page.canonicals[0], "https://example.com/guia")
        self.assertEqual(page.html_lang, "es-ES")
        self.assertIn("index,follow", page.robots_meta)

    def test_headings_and_images(self):
        page = load("page_full.html")
        counts = page.heading_counts()
        self.assertEqual(counts["h1"], 1)
        self.assertEqual(counts["h2"], 2)
        self.assertEqual(counts["h3"], 2)
        self.assertEqual(counts["h4"], 1)
        self.assertEqual(len(page.images_without_alt()), 1)

    def test_hreflang_and_social(self):
        page = load("page_full.html")
        langs = [lang for lang, _href in page.hreflangs]
        self.assertIn("es-ES", langs)
        self.assertIn("en-GB", langs)
        self.assertIn("x-default", langs)
        self.assertIn("og:title", page.og)
        self.assertEqual(page.twitter.get("twitter:card"), "summary_large_image")

    def test_text_metrics(self):
        page = load("page_full.html")
        self.assertGreater(page.word_count, 100)
        self.assertGreater(page.ratio(), 0.1)
        self.assertLess(page.ratio(), 1.0)
        self.assertTrue(page.paragraphs)

    def test_script_text_is_not_content(self):
        page = parse_html("<html><body><script>var x = 1;</script><p>Hola mundo</p></body></html>")
        self.assertNotIn("var", page.text)
        self.assertIn("Hola mundo", page.text)

    def test_normalize_url(self):
        self.assertEqual(normalize_url("https://Example.com/a/"), "https://example.com/a")
        self.assertEqual(normalize_url("https://example.com"), "https://example.com/")

    def test_empty_alt_is_decorative(self):
        page = parse_html('<img src="a.png"><img src="b.png" alt="">')
        self.assertEqual([img["src"] for img in page.images_without_alt()], ["a.png"])

    def test_template_content_is_not_page_content(self):
        page = parse_html(
            '<h1>Visible</h1><template><h2>Plantilla</h2><img src="t.png"></template>'
            '<img src="real.png" alt="descriptivo">')
        self.assertEqual([img["src"] for img in page.images], ["real.png"])
        self.assertEqual(page.heading_counts()["h2"], 0)
        self.assertNotIn("Plantilla", page.text)

    def test_bad_fixture(self):
        page = load("page_bad.html")
        self.assertEqual(page.title, "")
        self.assertEqual(page.heading_counts()["h1"], 2)
        self.assertIn("noindex", page.robots_meta)
        self.assertEqual(len(page.jsonld), 1)


if __name__ == "__main__":
    unittest.main()
