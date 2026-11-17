# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import hreflang
from scripts.page import parse_file, parse_html

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def status(checks, check_id):
    for rec in checks:
        if rec["id"] == check_id:
            return rec["status"]
    return None


def page_with_hreflang(entries, lang="es"):
    links = "".join('<link rel="alternate" hreflang="%s" href="%s">' % (code, href)
                    for code, href in entries)
    return parse_html('<html lang="%s"><head>%s</head><body></body></html>' % (lang, links))


class HreflangTests(unittest.TestCase):
    def test_good_page(self):
        page = parse_file(str(FIXTURES / "page_full.html"))
        url = "https://example.com/guia"
        other = "https://example.com/en/guide"
        page_map = {
            url: page.hreflangs,
            other: [("en-GB", other), ("es-ES", url), ("x-default", url)],
        }
        checks, data = hreflang.analyze(page, url, page_map=page_map, url=url)
        for check_id in ("HREF-LANG-001", "HREF-CODE-001", "HREF-SELF-001",
                         "HREF-XDEFAULT-001", "HREF-RETURN-001"):
            self.assertEqual(status(checks, check_id), "pass", check_id)
        self.assertEqual(data["html_lang"], "es-ES")

    def test_missing_x_default(self):
        page = page_with_hreflang([
            ("es", "https://example.com/es"), ("en", "https://example.com/en")])
        checks, _ = hreflang.analyze(page, "https://example.com/es", url="x")
        self.assertEqual(status(checks, "HREF-XDEFAULT-001"), "fail")

    def test_single_language_skips_x_default(self):
        page = page_with_hreflang([("es", "https://example.com/es")])
        checks, _ = hreflang.analyze(page, "https://example.com/es")
        self.assertEqual(status(checks, "HREF-XDEFAULT-001"), "skip")

    def test_invalid_code_and_lang(self):
        page = parse_html('<html><head>'
                          '<link rel="alternate" hreflang="español!" href="/x">'
                          '</head><body></body></html>')
        checks, _ = hreflang.analyze(page, "https://example.com/x")
        self.assertEqual(status(checks, "HREF-CODE-001"), "fail")
        self.assertEqual(status(checks, "HREF-LANG-001"), "fail")

    def test_self_reference_required(self):
        page = page_with_hreflang([("es", "https://example.com/otra")])
        checks, _ = hreflang.analyze(page, "https://example.com/actual")
        self.assertEqual(status(checks, "HREF-SELF-001"), "fail")

    def test_bidirectional_return(self):
        a = "https://example.com/es"
        b = "https://example.com/en"
        page = page_with_hreflang([("es", a), ("en", b)])
        page_map = {a: [("es", a), ("en", b)], b: [("en", b), ("es", a)]}
        checks, _ = hreflang.analyze(page, a, page_map=page_map)
        self.assertEqual(status(checks, "HREF-RETURN-001"), "pass")

        page_map_broken = {a: [("es", a), ("en", b)], b: [("en", b)]}
        checks, data = hreflang.analyze(page, a, page_map=page_map_broken)
        self.assertEqual(status(checks, "HREF-RETURN-001"), "fail")
        self.assertTrue(data["broken_returns"])

    def test_return_skipped_without_map(self):
        page = page_with_hreflang([("es", "https://example.com/es")])
        checks, _ = hreflang.analyze(page, "https://example.com/es")
        self.assertEqual(status(checks, "HREF-RETURN-001"), "skip")


if __name__ == "__main__":
    unittest.main()
