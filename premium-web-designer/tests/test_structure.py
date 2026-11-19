import unittest

from pwd_config import REQUIRED_FILES, SKILL_ROOT, read_file


class TestStructure(unittest.TestCase):

    def test_required_files_exist(self):
        missing = [
            file for file in REQUIRED_FILES
            if not (SKILL_ROOT / file).is_file()
        ]

        self.assertEqual(
            missing,
            [],
            f"Missing required files: {missing}"
        )

    def test_required_files_not_empty(self):
        empty = [
            file for file in REQUIRED_FILES
            if not read_file(file).strip()
        ]

        self.assertEqual(
            empty,
            [],
            f"Empty files detected: {empty}"
        )

    def test_required_directories_exist(self):
        directories = [
            "agents",
            "workflows",
            "references",
            "templates",
            "tests",
        ]

        for directory in directories:
            with self.subTest(directory=directory):
                self.assertTrue(
                    (SKILL_ROOT / directory).is_dir()
                )

    def test_skill_has_reasonable_size(self):
        content = read_file("SKILL.md")

        self.assertGreater(
            len(content),
            1000,
            "SKILL.md seems unusually short."
        )


if __name__ == "__main__":
    unittest.main()