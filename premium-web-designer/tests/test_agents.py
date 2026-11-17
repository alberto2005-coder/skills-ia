import unittest

from config import SPECIALISTS, read_file


class TestAgents(unittest.TestCase):

    def test_all_specialists_exist(self):
        for specialist in SPECIALISTS:
            path = f"agents/{specialist}.md"

            with self.subTest(specialist=specialist):
                self.assertTrue(
                    read_file(path).strip(),
                    f"Missing specialist: {path}"
                )

    def test_specialists_have_role_definitions(self):
        for specialist in SPECIALISTS:
            content = read_file(
                f"agents/{specialist}.md"
            )

            with self.subTest(specialist=specialist):
                self.assertIn("# ", content)
                self.assertIn("MISSION", content.upper())
                self.assertIn(
                    "RESPONSIBILITIES",
                    content.upper()
                )

    def test_orchestrator_defines_ownership(self):
        content = read_file(
            "agents/orchestrator.md"
        ).upper()

        self.assertIn("FILE OWNERSHIP", content)
        self.assertIn("DELEGATION", content)
        self.assertIn("FINAL APPROVAL", content)

    def test_qa_is_independent(self):
        content = read_file(
            "agents/qa-visual-auditor.md"
        ).upper()

        self.assertIn("INDEPENDENT", content)
        self.assertIn("AUDIT", content)
        self.assertIn("SEVERITY", content)


if __name__ == "__main__":
    unittest.main()