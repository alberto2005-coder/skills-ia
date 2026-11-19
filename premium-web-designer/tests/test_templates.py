import unittest

from pwd_config import read_file


class TestTemplates(unittest.TestCase):

    def test_project_brief_template(self):
        content = read_file(
            "templates/project-brief.md"
        ).upper()

        required = [
            "PROJECT INFORMATION",
            "BUSINESS",
            "BRAND",
            "WEBSITE STRUCTURE",
            "FUNCTIONALITY",
            "TECHNICAL REQUIREMENTS",
            "SUCCESS CRITERIA",
        ]

        for item in required:
            with self.subTest(item=item):
                self.assertIn(item, content)

    def test_design_system_template(self):
        content = read_file(
            "templates/design-system.md"
        ).upper()

        required = [
            "COLOR SYSTEM",
            "TYPOGRAPHY",
            "LAYOUT",
            "COMPONENTS",
            "IMAGERY",
            "MOTION",
        ]

        for item in required:
            with self.subTest(item=item):
                self.assertIn(item, content)

    def test_handoff_template(self):
        content = read_file(
            "templates/task-handoff.md"
        ).upper()

        for item in [
            "OBJECTIVE",
            "DEPENDENCIES",
            "EXPECTED DELIVERABLE",
            "ACCEPTANCE CRITERIA",
        ]:
            self.assertIn(item, content)

    def test_qa_template(self):
        content = read_file(
            "templates/qa-report.md"
        ).upper()

        for item in [
            "VISUAL FINDINGS",
            "FUNCTIONAL FINDINGS",
            "RESPONSIVE FINDINGS",
            "ACCESSIBILITY FINDINGS",
            "TESTS PERFORMED",
            "FINAL ASSESSMENT",
        ]:
            self.assertIn(item, content)


if __name__ == "__main__":
    unittest.main()