# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import perf
from scripts.page import parse_file

FIXTURES = Path(__file__).resolve().parent / "fixtures"

HEADERS = {"content-type": "text/html", "content-encoding": "br"}


def status(checks, check_id):
    for rec in checks:
        if rec["id"] == check_id:
            return rec["status"]
    return None


class PerfTests(unittest.TestCase):
    def setUp(self):
        self.page = parse_file(str(FIXTURES / "page_full.html"))

    def test_measured_values(self):
        checks, data = perf.analyze(HEADERS, 4096, 150, 240, self.page,
                                    url="https://example.com/guia")
        self.assertEqual(status(checks, "PERF-TTFB-001"), "pass")
        self.assertEqual(status(checks, "PERF-WEIGHT-001"), "pass")
        self.assertEqual(status(checks, "PERF-COMPRESS-001"), "pass")
        self.assertEqual(status(checks, "PERF-RESOURCES-001"), "pass")
        self.assertEqual(data["ttfb_ms"], 150)
        self.assertEqual(data["html_bytes"], 4096)
        self.assertEqual(data["content_encoding"], "br")

    def test_slow_and_uncompressed(self):
        checks, _ = perf.analyze({}, 400_000, 1500, 2000, self.page, url="https://example.com")
        self.assertEqual(status(checks, "PERF-TTFB-001"), "fail")
        self.assertEqual(status(checks, "PERF-WEIGHT-001"), "fail")
        self.assertEqual(status(checks, "PERF-COMPRESS-001"), "fail")

    def test_cwv_requires_external_data(self):
        checks, data = perf.analyze(HEADERS, 4000, 100, 150, self.page,
                                    url="https://example.com")
        cwv = [rec for rec in checks if rec["id"] == "PERF-CWV-001"][0]
        self.assertEqual(cwv["status"], "skip")
        self.assertIn("estimate", cwv["note"])
        self.assertIsNone(data["cwv_estimate"]["lcp_ms"])

        checks, data = perf.analyze(
            HEADERS, 4000, 100, 150, self.page, url="https://example.com",
            external_cwv={"lcp_ms": 4200, "cls": 0.02, "tbt_ms": 120})
        self.assertEqual(status(checks, "PERF-CWV-001"), "fail")
        self.assertEqual(data["cwv_source"], "external")

    def test_tbt_estimate_is_labelled(self):
        estimate = perf.tbt_estimate(300_000, 12)
        self.assertIsNotNone(estimate)
        self.assertGreater(estimate, 0)
        self.assertIsNone(perf.tbt_estimate(None, 0))

    def test_psi_link_present(self):
        _checks, data = perf.analyze(HEADERS, 1000, 10, 20, self.page,
                                    url="https://example.com/guia")
        self.assertIn("example.com", data["psi_url"])
        self.assertIn("pagespeed.web.dev", data["psi_url"])


if __name__ == "__main__":
    unittest.main()
