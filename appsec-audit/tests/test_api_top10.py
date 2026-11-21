"""Coherencia entre la referencia de API Security Top 10, las fixtures y appsec-code."""

import re
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
REFERENCE = PACKAGE / "references" / "api-security-top10.md"
SKILL = PACKAGE / "appsec-code" / "SKILL.md"
VULNERABLE = PACKAGE / "tests" / "fixtures" / "api_top10" / "vulnerable" / "app.py"
SAFE = PACKAGE / "tests" / "fixtures" / "api_top10" / "safe" / "app.py"

RULES = ("bola-sin-scope", "mass-assignment", "bfla-sin-rol", "ssrf-sin-allowlist")
OWASP = ("API1:2023", "API3:2023", "API5:2023", "API7:2023")
CWE = ("CWE-639", "CWE-915", "CWE-285", "CWE-918")


class ReferenceTests(unittest.TestCase):
    def test_reference_covers_the_four_families(self):
        text = REFERENCE.read_text(encoding="utf-8")
        for item in RULES + OWASP + CWE:
            with self.subTest(item=item):
                self.assertIn(item, text)

    def test_every_rule_has_a_vulnerable_and_a_safe_pattern(self):
        text = REFERENCE.read_text(encoding="utf-8")
        self.assertEqual(text.count("**Patrón vulnerable:**"), 4)
        self.assertEqual(text.count("**Patrón seguro:**"), 4)

    def test_reference_points_at_the_fixtures(self):
        text = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("fixtures/api_top10/vulnerable/", text)
        self.assertIn("fixtures/api_top10/safe/", text)


class FixtureTests(unittest.TestCase):
    def test_every_rule_has_a_marker_in_the_vulnerable_fixture(self):
        text = VULNERABLE.read_text(encoding="utf-8")
        markers = set(re.findall(r"regla: ([a-z-]+)", text))
        self.assertEqual(markers, set(RULES))

    def test_safe_fixture_has_no_rule_markers(self):
        text = SAFE.read_text(encoding="utf-8")
        self.assertNotIn("regla:", text)

    def test_safe_fixture_has_the_four_mitigations(self):
        text = SAFE.read_text(encoding="utf-8")
        for marker in ("X-Tenant", "require_role", "ALLOWED_FIELDS", "SAFE_HOSTS"):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def test_vulnerable_fixture_keeps_the_unsafe_calls(self):
        text = VULNERABLE.read_text(encoding="utf-8")
        for marker in ("PEDIDOS[pedido_id]", "request.json", '"url"'):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)


class SkillTests(unittest.TestCase):
    def test_appsec_code_links_the_reference(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("references/api-security-top10.md", text)

    def test_appsec_code_names_the_four_rules(self):
        text = SKILL.read_text(encoding="utf-8")
        for rule in RULES:
            with self.subTest(rule=rule):
                self.assertIn(rule, text)

    def test_reference_mapping_matches_the_skill_table(self):
        reference = REFERENCE.read_text(encoding="utf-8")
        skill = SKILL.read_text(encoding="utf-8")
        for family in ("BOLA", "Mass assignment", "BFLA", "SSRF"):
            with self.subTest(family=family):
                self.assertIn(family, reference)
                self.assertIn(family, skill)


if __name__ == "__main__":
    unittest.main()
