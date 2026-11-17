import re
import unittest

from config import all_markdown_files, read_file


SECRET_PATTERNS = [
    re.compile(
        r"""(?i)\b(?:api_key|secret_key|access_token)\s*=\s*['"][^'"]{12,}['"]"""
    ),
    re.compile(
        r"""(?i)\bpassword\s*=\s*['"][^'"]{8,}['"]"""
    ),
    re.compile(
        r"\bsk-[A-Za-z0-9]{20,}\b"
    ),
]


class TestSecurity(unittest.TestCase):

    def test_no_hardcoded_credentials(self):
        findings = []

        for document in all_markdown_files():
            content = document.read_text(
                encoding="utf-8"
            )

            for pattern in SECRET_PATTERNS:
                for match in pattern.finditer(content):
                    findings.append(
                        f"{document.name}: {match.group(0)[:25]}"
                    )

        self.assertEqual(
            findings,
            [],
            "Possible hardcoded secrets found."
        )

    def test_skill_requires_secret_protection(self):
        content = read_file("SKILL.md").upper()

        self.assertIn("NEVER EXPOSE API KEYS", content)
        self.assertIn("ENVIRONMENT VARIABLES", content)

    def test_backend_security_rules(self):
        content = read_file(
            "agents/backend-specialist.md"
        ).upper()

        required = [
            "VALIDATE",
            "AUTHORIZATION",
            "SENSITIVE INFORMATION",
            "ENVIRONMENT VARIABLES",
        ]

        for item in required:
            with self.subTest(item=item):
                self.assertIn(item, content)

    def test_ecommerce_payment_safety(self):
        content = read_file(
            "references/ecommerce.md"
        ).upper()

        self.assertIn("SERVER-SIDE", content)
        self.assertIn("RAW CARD DETAILS", content)
        self.assertIn("PAYMENT PROVIDER", content)


if __name__ == "__main__":
    unittest.main()