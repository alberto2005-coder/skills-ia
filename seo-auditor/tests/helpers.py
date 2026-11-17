# -*- coding: utf-8 -*-
"""Utilidades compartidas por los tests (no contiene casos de prueba)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import analyze, perf
from scripts.indexcheck import parse_robots
from scripts.page import parse_file

FIXTURES = Path(__file__).resolve().parent / "fixtures"
URL = "https://example.com/guia"
HEADERS = {
    "content-type": "text/html; charset=utf-8",
    "content-encoding": "gzip",
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "content-security-policy": "default-src 'self'; frame-ancestors 'self'",
    "x-frame-options": "SAMEORIGIN",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "geolocation=()",
}
ROBOTS = "User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n"


def build_result():
    """Pipeline completo sobre el fixture bueno, sin red."""
    page = parse_file(str(FIXTURES / "page_full.html"))
    robots = parse_robots(ROBOTS)
    checks, data = analyze.document_checks(
        page, url=URL, page_url=URL, headers=HEADERS, robots=robots,
        sitemap_urls=["https://example.com/sitemap.xml"],
        page_map={URL: page.hreflangs}, llms_status=True, http_llms_status=True)
    perf_checks, perf_data = perf.analyze(HEADERS, page.html_bytes, 180, 260,
                                          page, url=URL)
    checks.extend(perf_checks)
    data["perf"] = perf_data
    return {"mode": "page", "target": URL, "pages_scanned": 1,
            "checks": checks, "findings": analyze.to_findings(checks),
            "data": data,
            "crawl": {"max_pages": 1, "max_depth": 0, "requests_per_second": 1.0,
                      "robots_respected": True, "pages_fetched": 1}}
