import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import review_risk  # noqa: E402


def run(*args):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = review_risk.main(list(args))
    return code, buffer.getvalue()


def temp_patch(text):
    handle = tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False, encoding="utf-8")
    handle.write(text)
    handle.close()
    return handle.name


class RiskTests(unittest.TestCase):
    def setUp(self):
        self.patch = FIXTURES / "riesgo.patch"

    def test_parse_diff_lists_every_file(self):
        from pr_review_util import parse_diff

        files = parse_diff(self.patch.read_text(encoding="utf-8"))
        self.assertEqual(
            [item["path"] for item in files],
            [
                "src/auth/session.py",
                "requirements.txt",
                "src/utilidades.py",
                "src/tests/test_utilidades.py",
                "README.md",
            ],
        )

    def test_sensitive_path_is_high(self):
        code, output = run("--diff", str(self.patch), "--json")
        self.assertEqual(code, 1)
        self.assertIn('"rule": "ruta-sensible"', output)
        self.assertIn('"severity": "high"', output)

    def test_secret_line_is_high(self):
        patch = temp_patch(
            "diff --git a/src/app.py b/src/app.py\n"
            "--- a/src/app.py\n+++ b/src/app.py\n@@ -1,1 +1,2 @@\n"
            "+API_KEY = \"clave-de-ejemplo-no-real-123456\"\n x = 1\n"
        )
        code, output = run("--diff", patch, "--json")
        self.assertEqual(code, 1)
        self.assertIn("secreto-expuesto", output)

    def test_dependency_manifest_is_high(self):
        code, output = run("--diff", str(self.patch), "--json")
        self.assertEqual(code, 1)
        self.assertIn("dependencia-tocada", output)

    def test_disabled_check_is_medium(self):
        code, output = run("--diff", str(self.patch), "--json", "--fail-on", "none")
        self.assertEqual(code, 0)
        self.assertIn("check-desactivado", output)

    def test_clean_file_produces_no_finding(self):
        from pr_review_util import parse_diff

        payload = run("--diff", str(self.patch), "--json")[1]
        files = [item["path"] for item in parse_diff(self.patch.read_text(encoding="utf-8"))]
        self.assertIn("README.md", files)
        self.assertNotIn('"file": "README.md"', payload)

    def test_fail_on_none_never_fails(self):
        code, _ = run("--diff", str(self.patch), "--fail-on", "none")
        self.assertEqual(code, 0)

    def test_unreadable_diff_exits_two(self):
        code, _ = run("--diff", "no-existe.patch")
        self.assertEqual(code, 2)

    def test_small_file_budget_flags_the_pull_request(self):
        code, output = run("--diff", str(self.patch), "--max-files", "2", "--json")
        self.assertEqual(code, 1)
        self.assertIn("presupuesto 2", output)

    def test_report_is_deterministic(self):
        first = run("--diff", str(self.patch), "--json")[1]
        second = run("--diff", str(self.patch), "--json")[1]
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
