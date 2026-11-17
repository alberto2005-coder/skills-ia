# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import schema_audit
from scripts.page import parse_file

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def status(checks, check_id):
    for rec in checks:
        if rec["id"] == check_id:
            return rec["status"]
    return None


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.page = parse_file(str(FIXTURES / "page_full.html"))
        self.checks, self.data = schema_audit.analyze(
            self.page, "https://example.com/guia")

    def test_inventory_of_types(self):
        types = self.data["types"]
        for expected in ("Article", "Organization", "Product", "FAQPage",
                         "Offer", "AggregateRating"):
            self.assertIn(expected, types)
        self.assertEqual(self.data["invalid_blocks"], [])

    def test_rich_checks_pass(self):
        self.assertEqual(status(self.checks, "SCHEMA-PRODUCT-001"), "pass")
        self.assertEqual(status(self.checks, "SCHEMA-RATING-001"), "pass")
        self.assertEqual(status(self.checks, "SCHEMA-FAQ-001"), "pass")

    def test_rich_preview_contains_visible_data(self):
        blocks = schema_audit.blocks_from_page(self.page)
        html_text = schema_audit.rich_preview(blocks, "https://example.com/guia")
        self.assertIn("Rich preview", html_text)
        self.assertIn("Curso de auditoría SEO", html_text)
        self.assertIn("4.8", html_text)
        self.assertIn("99.00", html_text)
        self.assertIn("FAQPage", html_text)
        self.assertNotIn("<script src=", html_text)

    def test_rich_preview_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocks = schema_audit.blocks_from_page(self.page)
            path = schema_audit.write_rich_preview(blocks, tmp)
            self.assertTrue(Path(path).exists())
            self.assertIn("Rich preview", Path(path).read_text(encoding="utf-8"))

    def test_invalid_jsonld(self):
        page = parse_file(str(FIXTURES / "page_bad.html"))
        checks, data = schema_audit.analyze(page, "bad.html")
        self.assertEqual(status(checks, "SCHEMA-JSONLD-001"), "fail")
        self.assertEqual(data["invalid_blocks"], [1])

    def test_missing_required_properties(self):
        blocks = [{"valid_json": True, "data": {
            "@context": "https://schema.org", "@type": "Product",
            "name": "Solo nombre"}, "types": ["Product"], "block": 1}]
        html_text = schema_audit.rich_preview(blocks)
        self.assertIn("Falta para Product", html_text)
        self.assertIn("image", html_text)
        self.assertIn("offers", html_text)

    def test_legacy_inspect_html(self):
        blocks = schema_audit.inspect_html(str(FIXTURES / "page_full.html"))
        self.assertEqual(len(blocks), 4)
        self.assertTrue(all(block["valid_json"] for block in blocks))
        self.assertIn("Product", blocks[2]["types"])


if __name__ == "__main__":
    unittest.main()
