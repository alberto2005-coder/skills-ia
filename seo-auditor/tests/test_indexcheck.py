# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import indexcheck
from scripts.page import parse_html

ROBOTS_TEXT = """
User-agent: *
Disallow: /privado
Allow: /privado/publico
Crawl-delay: 2

User-agent: GPTBot
Disallow: /

Sitemap: https://example.com/sitemap.xml
"""


def status(checks, check_id):
    for rec in checks:
        if rec["id"] == check_id:
            return rec["status"]
    return None


class RobotsTests(unittest.TestCase):
    def setUp(self):
        self.robots = indexcheck.parse_robots(ROBOTS_TEXT)

    def test_parse_groups_and_sitemaps(self):
        self.assertEqual(len(self.robots["groups"]), 2)
        self.assertEqual(self.robots["sitemaps"], ["https://example.com/sitemap.xml"])
        self.assertEqual(self.robots["crawl_delays"], [2.0])

    def test_allow_and_disallow_longest_match(self):
        self.assertFalse(indexcheck.is_allowed(self.robots, "/privado/x", "Googlebot"))
        self.assertTrue(indexcheck.is_allowed(self.robots, "/privado/publico/x", "Googlebot"))
        self.assertTrue(indexcheck.is_allowed(self.robots, "/", "Googlebot"))

    def test_specific_agent(self):
        self.assertFalse(indexcheck.is_allowed(self.robots, "/", "GPTBot"))
        self.assertTrue(indexcheck.is_allowed(self.robots, "/", "OAI-SearchBot"))

    def test_global_disallow(self):
        self.assertFalse(indexcheck.global_disallow(self.robots))
        self.assertTrue(indexcheck.global_disallow(
            indexcheck.parse_robots("User-agent: *\nDisallow: /\n")))

    def test_wildcard_pattern(self):
        robots = indexcheck.parse_robots("User-agent: *\nDisallow: /*?s=\n")
        self.assertFalse(indexcheck.is_allowed(robots, "/buscar?s=test", "Googlebot"))
        self.assertTrue(indexcheck.is_allowed(robots, "/buscar", "Googlebot"))


class DirectiveCrossCheckTests(unittest.TestCase):
    def test_meta_header_conflict(self):
        page = parse_html('<html><head><meta name="robots" content="noindex"></head>'
                          '<body><h1>x</h1></body></html>')
        checks, data = indexcheck.analyze(
            page, "https://example.com/a", headers={"x-robots-tag": "index, follow"})
        self.assertEqual(status(checks, "IDX-META-001"), "fail")
        self.assertEqual(status(checks, "IDX-XROBOTS-001"), "pass")
        self.assertEqual(status(checks, "IDX-CONFLICT-001"), "fail")
        self.assertEqual(data["x_robots_tag"], "index, follow")

    def test_canonical_not_self_referential(self):
        page = parse_html('<html><head><link rel="canonical" href="https://example.com/otra">'
                          '</head><body></body></html>')
        checks, _ = indexcheck.analyze(page, "https://example.com/a")
        self.assertEqual(status(checks, "IDX-CANON-001"), "fail")

    def test_robots_blocks_url(self):
        page = parse_html("<html><body></body></html>")
        robots = indexcheck.parse_robots("User-agent: *\nDisallow: /blog\n")
        checks, data = indexcheck.analyze(page, "https://example.com/blog/post",
                                          robots=robots)
        self.assertEqual(status(checks, "IDX-ROBOTS-001"), "fail")
        self.assertFalse(data["robots_allows_url"])

    def test_ai_crawler_allowlist(self):
        page = parse_html("<html><body></body></html>")
        robots = indexcheck.parse_robots("User-agent: PerplexityBot\nDisallow: /\n")
        from scripts import geo
        checks, data = geo.analyze(robots, page, "https://example.com/")
        self.assertEqual(status(checks, "GEO-CRAWLERS-001"), "fail")
        blocked = [c["bot"] for c in data["crawlers"] if c["permitido"] is False]
        self.assertIn("PerplexityBot", blocked)


class PresenceTests(unittest.TestCase):
    def test_indirect_results_are_estimates(self):
        def fake_fetch(url, timeout):
            if "bing" in url:
                return '<a href="https://example.com/guia">resultado</a>'
            return "Please complete the captcha"

        results = indexcheck.check_presence(
            "https://example.com/guia", engines=["bing", "duckduckgo"],
            fetch=fake_fetch, delay=0)
        by_engine = {item["engine"]: item for item in results}
        self.assertEqual(by_engine["bing"]["status"], "found")
        self.assertEqual(by_engine["bing"]["results"], 1)
        self.assertEqual(by_engine["duckduckgo"]["status"], "thin")
        for item in results:
            self.assertTrue(item["indirect"])
            self.assertEqual(item["confidence"], "estimate")

    def test_requires_absolute_url(self):
        with self.assertRaises(ValueError):
            indexcheck.check_presence("sin-host", fetch=lambda u, t: "")


if __name__ == "__main__":
    unittest.main()
