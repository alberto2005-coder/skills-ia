import json
import re
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
MASTER = PACKAGE / "SKILL.md"
SUB_SKILLS = ("test-plan", "test-flaky", "test-mutation", "test-contract")
SCRIPTS = ("plan_tests.py", "flaky_scan.py", "mutation_targets.py", "contract_fixtures.py", "testarch_util.py")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class StructureTests(unittest.TestCase):
    def test_manifest_lists_the_five_skills(self):
        manifest = json.loads(read(PACKAGE / "skills.json"))
        names = [entry["name"] for entry in manifest["skills"]]
        self.assertEqual(names, ["test-architect", *SUB_SKILLS])
        self.assertEqual(manifest["version"], "1.0.0")
        for entry in manifest["skills"]:
            self.assertTrue((PACKAGE / entry["path"]).is_file(), entry["path"])

    def test_every_skill_declares_version_one(self):
        for path in [MASTER] + [PACKAGE / name / "SKILL.md" for name in SUB_SKILLS]:
            with self.subTest(skill=path.parent.name):
                text = read(path)
                self.assertRegex(text, r'(?m)^  version: "1\.0\.0"$')
                self.assertRegex(text, r"(?m)^  package: test-architect$")

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
        lines = len(read(MASTER).splitlines())
        self.assertLessEqual(lines, 200)
        commands = [line for line in read(MASTER).splitlines() if line.strip().startswith(("py ", "python3 "))]
        self.assertLessEqual(len(commands), 6)

    def test_scripts_and_assets_exist(self):
        for script in SCRIPTS:
            self.assertTrue((PACKAGE / "scripts" / script).is_file(), script)
        for reference in ("test-strategy.md", "flaky-patterns.md", "mutation-operators.md", "contract-testing.md"):
            self.assertTrue((PACKAGE / "references" / reference).is_file(), reference)
        for template in ("test-plan.md", "coverage-ledger.json", "mutation-report.md"):
            self.assertTrue((PACKAGE / "templates" / template).is_file(), template)

    def test_scripts_do_not_import_from_the_repository_root(self):
        for script in SCRIPTS:
            text = read(PACKAGE / "scripts" / script)
            with self.subTest(script=script):
                self.assertNotIn("from contracts", text)
                self.assertNotIn("from tests", text)
                self.assertNotIn("import contracts", text)

    def test_every_script_declares_the_package_root(self):
        for script in ("plan_tests.py", "flaky_scan.py", "mutation_targets.py", "contract_fixtures.py"):
            text = read(PACKAGE / "scripts" / script)
            with self.subTest(script=script):
                self.assertIn("testarch_util", text)
                self.assertIn("ArgumentParser", text)


if __name__ == "__main__":
    unittest.main()
