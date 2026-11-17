# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import security
from scripts.page import parse_file, parse_html

FIXTURES = Path(__file__).resolve().parent / "fixtures"

FULL = {
    "strict-transport-security": "max-age=31536000; includeSubDomains; preload",
    "content-security-policy": "default-src 'self'; frame-ancestors 'none'",
    "x-frame-options": "DENY",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "geolocation=()",
}


def status(checks, check_id):
    for rec in checks:
        if rec["id"] == check_id:
            return rec["status"]
    return None


class HeaderScoreTests(unittest.TestCase):
    def test_full_headers_score_100(self):
        checks, data = security.audit_headers(FULL, url="https://example.com")
        self.assertEqual(data["score"], 100)
        for rec in checks:
            if rec["id"].startswith("SEC-") and rec["id"] != "SEC-MIXED-001":
                self.assertEqual(rec["status"], "pass", rec["id"])

    def test_no_headers_gives_no_score(self):
        checks, data = security.audit_headers({})
        self.assertIsNone(data["score"])
        self.assertTrue(all(rec["status"] == "skip" for rec in checks))

    def test_missing_headers_reduce_score(self):
        checks, data = security.audit_headers(
            {"content-security-policy": "default-src 'self'"}, url="https://example.com")
        self.assertEqual(data["score"], 25)
        self.assertEqual(status(checks, "SEC-HSTS-001"), "fail")
        self.assertEqual(status(checks, "SEC-CSP-001"), "pass")

    def test_hsts_max_age_zero_is_invalid(self):
        self.assertFalse(security.hsts_ok("max-age=0")[0])
        self.assertTrue(security.hsts_ok("max-age=86400")[0])

    def test_xfo_covered_by_csp(self):
        ok, _detail = security.xfo_ok("", "default-src 'self'; frame-ancestors 'self'")
        self.assertTrue(ok)

    def test_mixed_content_lowers_score(self):
        page = parse_file(str(FIXTURES / "page_bad.html"))
        checks, data = security.audit_headers(
            FULL, page=page, url="https://example.com/bad",
            page_url="https://example.com/bad")
        self.assertEqual(status(checks, "SEC-MIXED-001"), "fail")
        self.assertEqual(len(data["mixed_content"]), 1)
        self.assertEqual(data["score"], 80)

    def test_https_page_without_mixed_content(self):
        page = parse_html('<html><body><img src="/img/a.png"></body></html>')
        checks, data = security.audit_headers(FULL, page=page,
                                              page_url="https://example.com/a")
        self.assertEqual(status(checks, "SEC-MIXED-001"), "pass")
        self.assertEqual(data["score"], 100)


if __name__ == "__main__":
    unittest.main()
