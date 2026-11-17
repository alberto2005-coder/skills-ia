# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import analyze, perf
from scripts.indexcheck import parse_robots
from scripts.page import parse_file

FIXTURES = Path(__file__).resolve().parent / "fixtures"

HEADERS = {
    "content-type": "text/html; charset=utf-8",
    "content-encoding": "gzip",
    "strict-transport-security": "max-age=63072000; includeSubDomains; preload",
    "content-security-policy": "default-src 'self'; frame-ancestors 'self'",
    "x-frame-options": "SAMEORIGIN",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "geolocation=(), camera=()",
}

ROBOTS = parse_robots(
    "User-agent: *\nAllow: /\n\nSitemap: https://example.com/sitemap.xml\n"
)


def status(checks, check_id):
    for rec in checks:
        if rec["id"] == check_id:
            return rec["status"]
    return None


class DocumentPipelineTests(unittest.TestCase):
    def setUp(self):
        self.page = parse_file(str(FIXTURES / "page_full.html"))
        self.url = "https://example.com/guia"
        self.checks, self.data = analyze.document_checks(
            self.page, url=self.url, page_url=self.url, headers=HEADERS,
            robots=ROBOTS, sitemap_urls=["https://example.com/sitemap.xml"],
            page_map={self.url: self.page.hreflangs},
            llms_status=True, http_llms_status=True)

    def test_good_page_passes_core_checks(self):
        for check_id in ("SRC-TITLE-001", "SRC-META-001", "ONP-H1-001",
                         "HREF-LANG-001", "HREF-SELF-001", "HREF-XDEFAULT-001",
                         "SERP-OG-001", "SCHEMA-JSONLD-001", "SCHEMA-PRODUCT-001",
                         "SCHEMA-RATING-001", "SCHEMA-FAQ-001", "GEO-EAT-001",
                         "IDX-CANON-001", "IDX-SITEMAP-001", "GEO-LLMS-001"):
            self.assertEqual(status(self.checks, check_id), "pass", check_id)

    def test_answer_block_and_security(self):
        self.assertEqual(status(self.checks, "GEO-ANSWER-001"), "pass")
        self.assertEqual(self.data["security"]["score"], 100)
        self.assertTrue(self.data["page"]["title"])

    def test_bad_page_fails(self):
        page = parse_file(str(FIXTURES / "page_bad.html"))
        checks, data = analyze.document_checks(
            page, url="https://example.com/bad", page_url="https://example.com/bad",
            headers={"x-robots-tag": "noindex", "content-type": "text/html"})
        for check_id in ("SRC-TITLE-001", "SRC-META-001", "ONP-H1-001",
                         "SRC-CANON-001", "IDX-META-001", "SCHEMA-JSONLD-001",
                         "HREF-LANG-001", "SEC-MIXED-001"):
            self.assertEqual(status(checks, check_id), "fail", check_id)
        self.assertTrue(data["security"]["mixed_content"])

    def test_findings_carry_id_severity_and_citation(self):
        page = parse_file(str(FIXTURES / "page_bad.html"))
        checks, _ = analyze.document_checks(page, url="bad.html")
        findings = analyze.to_findings(checks)
        self.assertTrue(findings)
        for finding in findings:
            self.assertTrue(finding["id"])
            self.assertIn(finding["severity_level"], ("must", "should", "nice"))
            self.assertTrue(finding["citation"].startswith("http"))
            self.assertTrue(finding["recommendation"])

    def test_perf_is_merged(self):
        perf_checks, perf_data = perf.analyze(
            HEADERS, self.page.html_bytes, 180, 260, self.page, url=self.url)
        self.assertEqual(status(perf_checks, "PERF-TTFB-001"), "pass")
        self.assertEqual(status(perf_checks, "PERF-COMPRESS-001"), "pass")
        self.assertEqual(status(perf_checks, "PERF-CWV-001"), "skip")
        self.assertEqual(perf_data["cwv_source"], "estimate")
        self.assertIn("pagespeed.web.dev", perf_data["psi_url"])


if __name__ == "__main__":
    unittest.main()
