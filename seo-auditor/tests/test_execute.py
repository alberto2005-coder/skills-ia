# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from helpers import build_result
from scripts import execute, report


class ExecuteTests(unittest.TestCase):
    def setUp(self):
        self.payload = report.build_payload(build_result())

    def test_build_plan_creates_drafts(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = execute.build_plan(self.payload, tmp)
            names = {Path(path).name for path in plan["files"]}
            for expected in ("robots.txt.draft", "meta-tags.html.draft",
                             "jsonld.json.draft", "llms.txt.draft",
                             "llms-full.txt.draft", "PLAN.md"):
                self.assertIn(expected, names)
            robots = (Path(tmp) / "robots.txt.draft").read_text(encoding="utf-8")
            self.assertIn("OAI-SearchBot", robots)
            self.assertIn("GPTBot", robots)
            self.assertIn("DRAFT", robots)
            plan_md = (Path(tmp) / "PLAN.md").read_text(encoding="utf-8")
            self.assertIn("DRAFT", plan_md)
            self.assertIn("robots.txt", plan_md)
            self.assertIn("Doc oficial", plan_md)

    def test_apply_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            execute.build_plan(self.payload, tmp)
            with self.assertRaises(PermissionError):
                execute.apply_plan(tmp, Path(tmp) / "site", confirm=False)

    def test_apply_writes_and_backs_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            drafts = Path(tmp) / "drafts"
            dest = Path(tmp) / "site"
            dest.mkdir()
            (dest / "robots.txt").write_text("User-agent: *\nDisallow:\n", encoding="utf-8")
            execute.build_plan(self.payload, drafts)
            result = execute.apply_plan(drafts, dest, confirm=True)
            self.assertTrue((dest / "robots.txt").exists())
            self.assertTrue((dest / "robots.txt.bak").exists())
            self.assertTrue((dest / "llms.txt").exists())
            self.assertIn("meta-tags.html", result["skipped_snippets"])
            self.assertIn("jsonld.json", result["skipped_snippets"])
            self.assertTrue(any(path.endswith("robots.txt") for path in result["applied"]))

    def test_jsonld_draft_has_no_invented_prices(self):
        with tempfile.TemporaryDirectory() as tmp:
            execute.build_plan(self.payload, tmp)
            text = (Path(tmp) / "jsonld.json.draft").read_text(encoding="utf-8")
            self.assertIn("_nota", text)
            self.assertNotIn("ratingValue", text)


if __name__ == "__main__":
    unittest.main()
