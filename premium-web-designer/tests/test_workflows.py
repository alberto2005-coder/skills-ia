import unittest

from pwd_config import WORKFLOWS, read_file


class TestWorkflows(unittest.TestCase):

    def test_all_workflows_exist(self):
        for workflow in WORKFLOWS:
            path = f"workflows/{workflow}.md"

            with self.subTest(workflow=workflow):
                self.assertTrue(
                    read_file(path).strip(),
                    f"Missing workflow: {path}"
                )

    def test_workflows_have_objectives(self):
        for workflow in WORKFLOWS:
            content = read_file(
                f"workflows/{workflow}.md"
            ).upper()

            with self.subTest(workflow=workflow):
                self.assertIn(
                    "OBJECTIVE",
                    content
                )

    def test_hybrid_execution_modes(self):
        content = read_file(
            "workflows/hybrid-orchestration.md"
        ).upper()

        for mode in [
            "NATIVE SUBAGENTS",
            "SEQUENTIAL SIMULATION",
            "PARTIAL DELEGATION",
        ]:
            with self.subTest(mode=mode):
                self.assertIn(mode, content)

    def test_delivery_includes_verification(self):
        content = read_file(
            "workflows/delivery.md"
        ).upper()

        self.assertIn("FINAL CHECKLIST", content)
        self.assertIn("FINAL REPORT", content)


if __name__ == "__main__":
    unittest.main()