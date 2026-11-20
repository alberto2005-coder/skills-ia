import json
import re
import unittest

from evals_config import (
    MASTER_MAX_COMMANDS,
    MASTER_MAX_LINES,
    REQUIRED_FILES,
    SKILL_ROOT,
    SUB_SKILLS,
    read_file,
)


def frontmatter(text: str) -> str:
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    return match.group(1) if match else ""


class TestStructure(unittest.TestCase):

    def test_required_files_exist(self):
        missing = [name for name in REQUIRED_FILES if not (SKILL_ROOT / name).is_file()]

        self.assertEqual(missing, [], f"faltan ficheros: {missing}")

    def test_required_files_not_empty(self):
        empty = [name for name in REQUIRED_FILES if not read_file(name).strip()]

        self.assertEqual(empty, [], f"ficheros vacíos: {empty}")

    def test_frontmatter_names_match_folders(self):
        for name in ("skill-evals",) + SUB_SKILLS:
            text = read_file("SKILL.md" if name == "skill-evals" else f"{name}/SKILL.md")
            found = re.search(r"^name:\s*(.+?)\s*$", frontmatter(text), re.M)

            with self.subTest(skill=name):
                self.assertIsNotNone(found, f"{name} sin name")
                self.assertEqual(found.group(1), name)

    def test_frontmatter_declares_license_and_metadata(self):
        version = json.loads(read_file("skills.json"))["version"]

        for name in ("skill-evals",) + SUB_SKILLS:
            text = read_file("SKILL.md" if name == "skill-evals" else f"{name}/SKILL.md")
            block = frontmatter(text)

            with self.subTest(skill=name):
                self.assertIn("license: MIT", block)
                self.assertIn("metadata:", block)
                self.assertIn("  package: skill-evals", block)
                self.assertRegex(block, r'  version: "' + re.escape(version) + r'"')

    def test_descriptions_within_standard_limits(self):
        for name in ("skill-evals",) + SUB_SKILLS:
            text = read_file("SKILL.md" if name == "skill-evals" else f"{name}/SKILL.md")
            block = frontmatter(text)
            description = block.split("description:", 1)[1].split("\nlicense:", 1)[0]

            with self.subTest(skill=name):
                self.assertGreaterEqual(len(description), 20)
                self.assertLessEqual(len(description), 1024)

    def test_master_indexes_every_subskill(self):
        master = read_file("SKILL.md")

        for name in SUB_SKILLS:
            with self.subTest(sub=name):
                self.assertIn(name, master, f"el maestro no menciona {name}")

    def test_subskills_declare_gate_and_handoff(self):
        for name in SUB_SKILLS:
            text = read_file(f"{name}/SKILL.md")
            headings = re.findall(r"^##\s+(.+)$", text, re.M)

            with self.subTest(skill=name):
                self.assertIn("Gate de salida", headings)
                self.assertIn("Handoff", headings)

    def test_master_stays_compact(self):
        text = read_file("SKILL.md")

        self.assertLessEqual(len(text.splitlines()), MASTER_MAX_LINES)
        commands = re.findall(r"^py skill-evals/scripts/\S+", text, re.M)
        self.assertLessEqual(len(commands), MASTER_MAX_COMMANDS,
                             f"el maestro lista {len(commands)} comandos")

    def test_manifest_matches_files(self):
        manifest = json.loads(read_file("skills.json"))
        names = [entry["name"] for entry in manifest["skills"]]
        folders = {path.parent.name for path in SKILL_ROOT.glob("*/SKILL.md")}

        self.assertEqual(len(names), len(folders) + 1)
        self.assertEqual(sorted(names), sorted(folders | {"skill-evals"}))

        for entry in manifest["skills"]:
            with self.subTest(skill=entry["name"]):
                self.assertTrue((SKILL_ROOT / entry["path"]).is_file())

    def test_root_index_lists_package(self):
        index = json.loads((SKILL_ROOT.parent / "skills.json").read_text(encoding="utf-8"))
        entry = next((item for item in index["packages"] if item["name"] == "skill-evals"), None)

        self.assertIsNotNone(entry, "skills.json raíz no declara skill-evals")
        self.assertEqual(entry["manifest"], "skill-evals/skills.json")
        self.assertEqual(entry["skill_count"], 4)
        self.assertEqual(index["skills_total"], sum(pkg["skill_count"] for pkg in index["packages"]))


if __name__ == "__main__":
    unittest.main()
