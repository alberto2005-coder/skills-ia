import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import env_check  # noqa: E402


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = env_check.main(argv)
    return code, out.getvalue()


class TestEnvCheck(unittest.TestCase):

    def _setup(self, tmp, code_text, example="DATABASE_URL=\n", docs="Configura DATABASE_URL.\n"):
        root = Path(tmp)
        (root / "app.py").write_text(code_text, encoding="utf-8")
        (root / ".env.example").write_text(example, encoding="utf-8")
        (root / "README.md").write_text(docs, encoding="utf-8")
        return str(root), str(root / ".env.example"), str(root / "README.md")

    def _run(self, tmp, code_text, extra=None, example="DATABASE_URL=\n",
             docs="Configura DATABASE_URL.\n"):
        root, example_path, docs_path = self._setup(tmp, code_text, example, docs)
        code, output = run(["--path", root, "--env-example", example_path, "--docs", docs_path,
                            "--json"] + (extra or []))
        return code, json.loads(output)

    def test_consistent_variable_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._run(tmp, "import os\n\nURL = os.getenv(\"DATABASE_URL\")\n")
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])
            self.assertEqual(report["used"], 1)
            self.assertEqual(report["declared"], 1)

    def test_used_variable_missing_from_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._run(tmp, "import os\n\nKEY = os.environ[\"STRIPE_KEY\"]\n")
            self.assertEqual(code, 1)
            rules = {(item["rule"], item["name"]) for item in report["findings"]}
            self.assertIn(("env-sin-ejemplo", "STRIPE_KEY"), rules)

    def test_used_variable_missing_from_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._run(tmp, "import os\n\nURL = os.environ[\"DATABASE_URL\"]\n",
                                     docs="Sin variables documentadas aqui.\n")
            self.assertEqual(code, 1)
            self.assertIn(("env-sin-documentar", "DATABASE_URL"),
                          {(item["rule"], item["name"]) for item in report["findings"]})

    def test_example_variable_without_use_is_low(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._run(tmp, "import os\n\nURL = os.getenv(\"DATABASE_URL\")\n",
                                     example="DATABASE_URL=\nexport OLD_TOKEN=\n",
                                     docs="Configura DATABASE_URL y OLD_TOKEN.\n")
            self.assertEqual(code, 0)
            self.assertIn(("ejemplo-sin-uso", "OLD_TOKEN"),
                          {(item["rule"], item["name"]) for item in report["findings"]})

    def test_process_env_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.js").write_text("const url = process.env.API_URL;\n", encoding="utf-8")
            (root / ".env.example").write_text("API_URL=\n", encoding="utf-8")
            (root / "README.md").write_text("Configura API_URL en el entorno.\n", encoding="utf-8")
            code, output = run(["--path", str(root), "--env-example", str(root / ".env.example"),
                                "--docs", str(root / "README.md"), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["findings"], [])

    def test_import_meta_env_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.ts").write_text("const key = import.meta.env.VITE_KEY;\n", encoding="utf-8")
            (root / ".env.example").write_text("VITE_KEY=\n", encoding="utf-8")
            (root / "README.md").write_text("Configura VITE_KEY.\n", encoding="utf-8")
            code, output = run(["--path", str(root), "--env-example", str(root / ".env.example"),
                                "--docs", str(root / "README.md"), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["findings"], [])

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = self._run(tmp, "import os\n\nKEY = os.getenv(\"STRIPE_KEY\")\n",
                                ["--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_missing_code_path_exits_two(self):
        code, _ = run(["--path", "no-existe"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
