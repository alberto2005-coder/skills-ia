# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.source_audit import audit_source

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def status(checks, check_id):
    for rec in checks:
        if rec["id"] == check_id:
            return rec["status"]
    return None


class SourceSiteTests(unittest.TestCase):
    def test_site_root_files_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text(
                (FIXTURES / "page_full.html").read_text(encoding="utf-8"),
                encoding="utf-8")
            (root / "robots.txt").write_text(
                "User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n",
                encoding="utf-8")
            (root / "sitemap.xml").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                '<url><loc>https://example.com/</loc></url></urlset>',
                encoding="utf-8")
            (root / "llms.txt").write_text("# Ejemplo\n", encoding="utf-8")
            (root / "llms-full.txt").write_text("# Ejemplo\n", encoding="utf-8")

            result = audit_source(tmp)
            self.assertEqual(result["files_scanned"], 1)
            self.assertTrue(result["data"]["llms_txt"])
            self.assertTrue(result["data"]["llms_full_txt"])
            self.assertEqual(status(result["checks"], "GEO-LLMS-001"), "pass")
            self.assertEqual(status(result["checks"], "GEO-LLMSFULL-001"), "pass")
            self.assertEqual(status(result["checks"], "IDX-SITEMAP-001"), "pass")
            self.assertEqual(status(result["checks"], "IDX-ROBOTS-001"), "pass")
            self.assertTrue(result["findings"])

    def test_missing_site_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text(
                (FIXTURES / "page_bad.html").read_text(encoding="utf-8"),
                encoding="utf-8")
            result = audit_source(tmp)
            self.assertEqual(status(result["checks"], "GEO-LLMS-001"), "fail")
            self.assertEqual(status(result["checks"], "IDX-SITEMAP-001"), "skip")
            self.assertEqual(status(result["checks"], "SRC-TITLE-001"), "fail")


if __name__ == "__main__":
    unittest.main()
