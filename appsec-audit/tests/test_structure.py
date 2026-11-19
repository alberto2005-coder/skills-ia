import json
import re
import unittest

from appsec_config import MASTER_MAX_LINES, REQUIRED_FILES, SKILL_ROOT, SUB_SKILLS, read_file


class TestStructure(unittest.TestCase):

    def test_required_files_exist(self):
        missing = [name for name in REQUIRED_FILES if not (SKILL_ROOT / name).is_file()]

        self.assertEqual(missing, [], f"faltan ficheros: {missing}")

    def test_required_files_not_empty(self):
        empty = [name for name in REQUIRED_FILES if not read_file(name).strip()]

        self.assertEqual(empty, [], f"ficheros vacíos: {empty}")

    def test_frontmatter_names_match_folders(self):
        for name in SUB_SKILLS + ["appsec-audit"]:
            path = "SKILL.md" if name == "appsec-audit" else f"{name}/SKILL.md"
            text = read_file(path)
            found = re.search(r"^name:\s*(.+?)\s*$", text, re.M)

            with self.subTest(skill=name):
                self.assertIsNotNone(found, f"{path} sin name")
                self.assertEqual(found.group(1), name)

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
        lines = len(read_file("SKILL.md").splitlines())

        self.assertLessEqual(lines, MASTER_MAX_LINES, f"el maestro tiene {lines} líneas")

    def test_master_documents_read_only_policy(self):
        master = read_file("SKILL.md").lower()

        for needle in ["solo lectura", "hostil", "nunca se ejecuta código"]:
            with self.subTest(needle=needle):
                self.assertIn(needle, master)

    def test_manifest_matches_files(self):
        manifest = json.loads(read_file("skills.json"))
        names = [entry["name"] for entry in manifest["skills"]]
        folders = {path.parent.name for path in SKILL_ROOT.glob("*/SKILL.md")}

        self.assertEqual(
            len(names),
            len(folders) + 1,
            "el manifiesto debe declarar el maestro y todas las SKILL.md del paquete",
        )
        self.assertEqual(sorted(names), sorted(folders | {"appsec-audit"}))

        for entry in manifest["skills"]:
            with self.subTest(skill=entry["name"]):
                self.assertTrue((SKILL_ROOT / entry["path"]).is_file())

    def test_no_master_prose_repeated_in_subskills(self):
        master_lines = {
            line.strip()
            for line in read_file("SKILL.md").splitlines()
            if len(line.strip()) >= 70
        }

        for name in SUB_SKILLS:
            text = read_file(f"{name}/SKILL.md")
            repeated = master_lines & {
                line.strip() for line in text.splitlines() if len(line.strip()) >= 70
            }

            with self.subTest(skill=name):
                self.assertFalse(repeated, f"{name} repite {sorted(repeated)[:2]}")


if __name__ == "__main__":
    unittest.main()
