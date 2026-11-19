import unittest

from pwd_config import read_file


class TestPortability(unittest.TestCase):

    def test_provider_independent_architecture(self):
        content = read_file("SKILL.md").upper()

        self.assertIn(
            "UNIVERSAL HYBRID MULTI-AGENT",
            content
        )

    def test_sequential_fallback_exists(self):
        content = read_file(
            "workflows/hybrid-orchestration.md"
        ).upper()

        self.assertIn("SEQUENTIAL SIMULATION", content)
        self.assertIn("NATIVE SUBAGENTS", content)

    def test_multilingual_support(self):
        content = read_file("SKILL.md").upper()

        self.assertIn("LANGUAGE POLICY", content)
        self.assertIn("ANY LANGUAGE", content)

    def test_technology_is_not_mandatory(self):
        content = read_file(
            "references/tech-stack.md"
        ).lower()

        self.assertIn("do not force a universal stack", content)
        self.assertIn("inspect the existing repository", content)

    def test_platform_specific_installation_is_not_required(self):
        # La comprobación vive dentro de la skill: leer `docs/` del repositorio
        # hacía que el test dependiera de un fichero fuera de su carpeta.
        content = read_file("references/tech-stack.md").lower()

        self.assertIn("host platform", content)
        self.assertIn("native", content)


if __name__ == "__main__":
    unittest.main()