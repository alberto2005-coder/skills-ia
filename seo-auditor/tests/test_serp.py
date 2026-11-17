# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import serp
from scripts.page import parse_file

FIXTURES = Path(__file__).resolve().parent / "fixtures"
URL = "https://example.com/guia"


def status(checks, check_id):
    for rec in checks:
        if rec["id"] == check_id:
            return rec["status"]
    return None


class SerpTests(unittest.TestCase):
    def setUp(self):
        self.page = parse_file(str(FIXTURES / "page_full.html"))

    def test_preview_is_self_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, metrics = serp.write(self.page, URL, tmp)
            text = Path(path).read_text(encoding="utf-8")
            self.assertIn("Google — escritorio", text)
            self.assertIn("Google — móvil", text)
            self.assertIn("Bing", text)
            self.assertIn("WhatsApp", text)
            self.assertIn("Facebook", text)
            self.assertIn("LinkedIn", text)
            self.assertIn("X (Twitter)", text)
            self.assertNotIn("<script src=", text)
            self.assertNotIn("http-equiv=\"refresh\"", text)
            self.assertEqual(metrics["title_chars"], len(self.page.title))

    def test_long_title_truncates(self):
        long_title = "T" * 100
        checks, metrics = serp.analyze(self.page, URL, title=long_title)
        self.assertTrue(metrics["title_truncated"])
        self.assertGreater(metrics["title_px"], serp.MAX_TITLE_PX)
        self.assertEqual(status(checks, "SERP-TITLE-001"), "fail")

    def test_override_title_and_description(self):
        html_text, metrics = serp.build(
            self.page, URL, title="Título corto", description="Descripción breve")
        self.assertIn("Título corto", html_text)
        self.assertIn("Descripción breve", html_text)
        self.assertFalse(metrics["title_truncated"])
        self.assertTrue(metrics["title_overridden"])

    def test_og_missing_is_reported(self):
        page = parse_file(str(FIXTURES / "page_bad.html"))
        checks, metrics = serp.analyze(page, URL)
        self.assertEqual(status(checks, "SERP-OG-001"), "fail")
        self.assertIn("og:image", metrics["og_missing"])
        self.assertEqual(status(checks, "SERP-TW-001"), "fail")

    def test_measure_is_marked_estimate(self):
        _checks, metrics = serp.analyze(self.page, URL)
        self.assertIn("estimate", metrics["measure"])


if __name__ == "__main__":
    unittest.main()
