# -*- coding: utf-8 -*-
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.cli import build_parser, main

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class CliTests(unittest.TestCase):
    def test_parser_has_all_commands(self):
        parser = build_parser()
        for command in ("audit", "rescore", "compare", "serp", "perf", "headers",
                        "schema", "hreflang", "onpage", "index", "fix"):
            self.assertIn(command, parser._subparsers._group_actions[0].choices)

    def test_audit_page_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            main(["audit", str(FIXTURES / "page_full.html"),
                  "--mode", "page", "--output", tmp])
            audits = list(Path(tmp).glob("**/audit.json"))
            self.assertEqual(len(audits), 1)
            payload = json.loads(audits[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "seo-auditor/audit")
            self.assertIn("verdict_line", payload)
            self.assertTrue((audits[0].parent / "report.html").exists())

    def test_rescore_compare_and_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            main(["audit", str(FIXTURES / "page_full.html"),
                  "--mode", "page", "--output", tmp])
            audit = list(Path(tmp).glob("**/audit.json"))[0]

            main(["rescore", str(audit), "--output", str(Path(tmp) / "rescored")])
            rescored = Path(tmp) / "rescored" / "audit.rescored.json"
            self.assertTrue(rescored.exists())
            self.assertTrue(json.loads(rescored.read_text(encoding="utf-8"))
                            ["rescored_without_network"])

            main(["compare", str(audit), str(audit),
                  "--output", str(Path(tmp) / "cmp")])
            self.assertTrue((Path(tmp) / "cmp" / "compare.md").exists())

            main(["fix", "--input", str(audit), "--output", str(Path(tmp) / "fix")])
            self.assertTrue((Path(tmp) / "fix" / "robots.txt.draft").exists())
            self.assertTrue((Path(tmp) / "fix" / "PLAN.md").exists())

    def test_serp_command_creates_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            main(["serp", str(FIXTURES / "page_full.html"),
                  "--title", "Título de prueba", "--output", tmp])
            self.assertTrue((Path(tmp) / "serp" / "preview.html").exists())
            self.assertTrue((Path(tmp) / "report.html").exists())
            text = (Path(tmp) / "serp" / "preview.html").read_text(encoding="utf-8")
            self.assertIn("Título de prueba", text)

    def test_schema_and_onpage_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            main(["schema", str(FIXTURES / "page_full.html"), "--output", tmp])
            self.assertTrue((Path(tmp) / "schema" / "rich-preview.html").exists())
            main(["onpage", str(FIXTURES / "page_full.html"), "--output", tmp])
            self.assertTrue((Path(tmp) / "audit.md").exists())


if __name__ == "__main__":
    unittest.main()
