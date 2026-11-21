import json
import re
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
MASTER = PACKAGE / "SKILL.md"
SUB_SKILLS = ("pr-risk", "pr-order", "pr-routing", "pr-findings")
SCRIPTS = ("pr_review_util.py", "review_risk.py", "review_order.py", "review_routing.py", "review_findings.py")


def read(path):
    return Path(path).read_text(encoding="utf-8")


class StructureTests(unittest.TestCase):
    def test_manifest_lists_the_five_skills(self):
        manifest = json.loads(read(PACKAGE / "skills.json"))
        self.assertEqual([entry["name"] for entry in manifest["skills"]], ["pr-reviewer", *SUB_SKILLS])
        self.assertEqual(manifest["version"], "1.0.0")
        for entry in manifest["skills"]:
            self.assertTrue((PACKAGE / entry["path"]).is_file(), entry["path"])

    def test_every_skill_declares_version_one(self):
        for path in [MASTER] + [PACKAGE / name / "SKILL.md" for name in SUB_SKILLS]:
            with self.subTest(skill=path.parent.name):
                text = read(path)
                self.assertRegex(text, r'(?m)^  version: "1\.0\.0"$')
                self.assertRegex(text, r"(?m)^  package: pr-reviewer$")

    def test_sub_skills_declare_gate_and_handoff(self):
        for name in SUB_SKILLS:
            with self.subTest(skill=name):
                headings = re.findall(r"^##\s+(.+)$", read(PACKAGE / name / "SKILL.md"), re.M)
                self.assertIn("Gate de salida", headings)
                self.assertIn("Handoff", headings)

    def test_master_indexes_its_sub_skills(self):
        text = read(MASTER)
        for name in SUB_SKILLS:
            self.assertIn("`%s`" % name, text)

    def test_master_stays_compact(self):
        text = read(MASTER)
        self.assertLessEqual(len(text.splitlines()), 200)
        commands = [line for line in text.splitlines() if line.strip().startswith(("py ", "python3 "))]
        self.assertLessEqual(len(commands), 6)

    def test_scripts_and_assets_exist(self):
        for script in SCRIPTS:
            self.assertTrue((PACKAGE / "scripts" / script).is_file(), script)
        for reference in ("review-strategy.md", "risk-signals.md", "findings-contract.md", "routing-and-ownership.md"):
            self.assertTrue((PACKAGE / "references" / reference).is_file(), reference)
        for template in ("review-plan.md", "findings-merged.json", "review-report.md"):
            self.assertTrue((PACKAGE / "templates" / template).is_file(), template)

    def test_scripts_do_not_import_from_the_repository_root(self):
        for script in SCRIPTS:
            text = read(PACKAGE / "scripts" / script)
            with self.subTest(script=script):
                for forbidden in ("from contracts", "from tests", "import contracts", "import tests"):
                    self.assertNotIn(forbidden, text)

    def test_every_entry_point_declares_its_cli(self):
        for script in SCRIPTS[1:]:
            text = read(PACKAGE / "scripts" / script)
            with self.subTest(script=script):
                self.assertIn("pr_review_util", text)
                self.assertIn("ArgumentParser", text)


if __name__ == "__main__":
    unittest.main()
