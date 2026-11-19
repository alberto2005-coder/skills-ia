import unittest

from pwd_config import read_file


class TestContentQuality(unittest.TestCase):

    def test_anti_generic_design_rules(self):
        content = read_file(
            "references/visual-quality.md"
        ).upper()

        required = [
            "GENERIC AI",
            "TYPOGRAPHY",
            "COMPOSITION",
            "VISUAL HIERARCHY",
            "IMAGERY",
            "VISUAL AUDIT",
        ]

        for item in required:
            with self.subTest(item=item):
                self.assertIn(item, content)

    def test_design_principles(self):
        content = read_file(
            "references/design-principles.md"
        ).upper()

        required = [
            "ORIGINAL ART DIRECTION",
            "TYPOGRAPHY",
            "COLOR",
            "COMPOSITION",
            "IMAGERY",
            "ANIMATION",
        ]

        for item in required:
            with self.subTest(item=item):
                self.assertIn(item, content)

    def test_responsive_requirements(self):
        content = read_file(
            "references/responsive-design.md"
        )

        for viewport in [
            "360px",
            "390px",
            "768px",
            "1024px",
            "1440px",
        ]:
            with self.subTest(viewport=viewport):
                self.assertIn(viewport, content)

    def test_supported_project_types(self):
        content = read_file(
            "references/project-types.md"
        ).lower()

        project_types = [
            "corporate",
            "landing pages",
            "ecommerce",
            "creative websites",
            "saas",
            "portfolios",
        ]

        for project_type in project_types:
            with self.subTest(project_type=project_type):
                self.assertIn(project_type, content)

    def test_accessibility_standards(self):
        content = read_file(
            "references/accessibility.md"
        ).upper()

        self.assertIn("WCAG 2.2 AA", content)
        self.assertIn("KEYBOARD", content)
        self.assertIn("FOCUS", content)

    def test_performance_and_seo(self):
        content = read_file(
            "references/performance-seo.md"
        ).upper()

        self.assertIn("PERFORMANCE", content)
        self.assertIn("SEO", content)
        self.assertIn("MEASURE", content)


if __name__ == "__main__":
    unittest.main()