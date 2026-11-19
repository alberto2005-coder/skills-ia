import re
import unittest

from pwd_config import read_file


class TestFrontmatter(unittest.TestCase):

    def setUp(self):
        self.content = read_file("SKILL.md")

    def test_frontmatter_exists(self):
        self.assertTrue(
            self.content.startswith("---"),
            "Missing YAML frontmatter."
        )

        self.assertGreaterEqual(
            self.content.count("---"),
            2
        )

    def test_frontmatter_has_name(self):
        match = re.search(
            r"^name:\s*(.+)$",
            self.content,
            re.MULTILINE
        )

        self.assertIsNotNone(match)

        if match:
            self.assertEqual(
                match.group(1).strip(),
                "premium-web-designer"
            )

    def test_frontmatter_has_description(self):
        self.assertRegex(
            self.content,
            r"(?m)^description:"
        )

    def test_frontmatter_has_closing_delimiter(self):
        lines = self.content.splitlines()

        self.assertGreaterEqual(len(lines), 3)

        self.assertEqual(lines[0], "---")

        self.assertIn(
            "---",
            lines[1:],
            "Missing closing YAML delimiter."
        )


if __name__ == "__main__":
    unittest.main()