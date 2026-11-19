# -*- coding: utf-8 -*-
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import analyze, perf, report
from scripts.indexcheck import parse_robots
from scripts.page import parse_file

FIXTURES = Path(__file__).resolve().parent / "fixtures"

HEADERS = {
    "content-type": "text/html; charset=utf-8",
    "content-encoding": "gzip",
    "strict-transport-security": "max-age=31536000",
    "content-security-policy": "default-src 'self'",
    "x-frame-options": "SAMEORIGIN",
    "x-content-type-options": "nosniff",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "geolocation=()",
}
URL = "https://example.com/guia"


def build_result():
    page = parse_file(str(FIXTURES / "page_full.html"))
    robots = parse_robots("User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n")
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
            "data": data, "crawl": {"max_pages": 1, "max_depth": 0,
                                    "requests_per_second": 1.0,
                                    "robots_respected": True, "pages_fetched": 1}}


class ReportTests(unittest.TestCase):
    def test_writes_three_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = report.write_report(build_result(), tmp)
            for name in ("audit.json", "audit.md", "report.html"):
                self.assertTrue((Path(out) / name).exists(), name)
            payload = json.loads((Path(out) / "audit.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "seo-auditor/audit")
            self.assertEqual(payload["schema_version"], "2.0")
            self.assertIn(payload["verdict"], ("Not Ready", "Competitive", "Leading"))

    def test_markdown_has_verdict_rubric_and_citations(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = report.write_report(build_result(), tmp)
            markdown = (Path(out) / "audit.md").read_text(encoding="utf-8")
            self.assertIn("Veredicto", markdown)
            self.assertIn("Rúbrica 0–100 por dimensiones", markdown)
            self.assertIn("Dimensión", markdown)
            self.assertIn("Doc oficial", markdown)
            self.assertIn("🔴", markdown)
            self.assertIn("⚪", markdown)

    def test_html_is_printable_and_filterable(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = report.write_report(build_result(), tmp)
            html_text = (Path(out) / "report.html").read_text(encoding="utf-8")
            self.assertIn("Imprimir", html_text)
            self.assertIn('data-filter="must"', html_text)
            self.assertIn("data-status=", html_text)
            self.assertIn("@media print", html_text)
            self.assertNotIn("<script src=", html_text)

    def test_rescore_reproduces_score_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = report.write_report(build_result(), tmp)
            payload = json.loads((Path(out) / "audit.json").read_text(encoding="utf-8"))
            rescored = report.rescore(payload)
            self.assertEqual(rescored["score"], payload["score"])
            self.assertTrue(rescored["rescored_without_network"])
            self.assertEqual(rescored["verdict"], payload["verdict"])

    def test_rescore_rejects_payload_without_checks(self):
        with self.assertRaises(ValueError):
            report.rescore({"schema": "seo-auditor/audit"})

    def test_must_fail_caps_verdict(self):
        checks = [{"id": "P%d" % i, "status": "pass", "dimension": "tecnico",
                   "severity_level": "must", "title": "ok", "url": ""} for i in range(9)]
        checks.append({"id": "M1", "status": "fail", "dimension": "tecnico",
                       "severity_level": "must", "title": "bloqueo", "url": ""})
        rubric = report.checks_mod.compute_rubric(checks)
        self.assertEqual(rubric["total"], 90.0)
        self.assertEqual(rubric["verdict"], "Competitive")
        self.assertTrue(rubric["verdict_capped_by_must"])
        self.assertIn("bloqueo", rubric["verdict_line"])

    def test_rubric_dimensions_and_must_fails(self):
        payload = report.build_payload(build_result())
        self.assertEqual(set(payload["dimensions"].keys()),
                         set(("tecnico", "contenido", "schema", "geo",
                              "seguridad", "rendimiento")))
        self.assertIn("formula", payload["rubric"])
        self.assertGreater(payload["score"], 0)
        self.assertLessEqual(payload["score"], 100)


if __name__ == "__main__":
    unittest.main()
