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

import dead_code  # noqa: E402

CLEAN = """
import os


def ruta_actual():
    return os.getcwd()


def main():
    print(ruta_actual())
"""

UNUSED_IMPORT = """
import os
import json


def saluda(nombre):
    return f"hola {nombre}"
"""

NOQA_IMPORT = """
import os  # noqa: F401


def nada():
    return 1
"""

UNUSED_PRIVATE = """
def _ayuda():
    return 1


def publica():
    return 2
"""

PUBLIC_UNUSED = """
def publica():
    return 2
"""

CROSS_FILE_CALLER = """
from modulo import _ayuda


def usa():
    return _ayuda()
"""

IMPORTED_MODULE = """
def _ayuda():
    return 1
"""


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = dead_code.main(argv)
    return code, out.getvalue()


class TestDeadCode(unittest.TestCase):

    def _tree(self, tmp, name, content):
        path = Path(tmp) / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_clean_module_has_no_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, "modulo.py", CLEAN)
            code, output = run(["--path", tmp, "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])
            self.assertEqual(report["files"], 1)

    def test_unused_import_is_reported_low(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, "modulo.py", UNUSED_IMPORT)
            code, output = run(["--path", tmp, "--json", "--fail-on", "low"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual([item["rule"] for item in report["findings"]],
                             ["import-sin-uso", "import-sin-uso"])
            self.assertEqual([item["name"] for item in report["findings"]], ["os", "json"])
            self.assertEqual([item["line"] for item in report["findings"]], [2, 3])
            self.assertEqual(report["by_rule"]["import-sin-uso"], 2)

    def test_noqa_line_suppresses_the_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, "modulo.py", NOQA_IMPORT)
            code, output = run(["--path", tmp, "--json", "--fail-on", "low"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])

    def test_unused_private_function_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, "modulo.py", UNUSED_PRIVATE)
            code, output = run(["--path", tmp, "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual([item["name"] for item in report["findings"]], ["_ayuda"])
            self.assertEqual(report["findings"][0]["severity"], "medium")

    def test_function_used_from_another_file_is_alive(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, "modulo.py", IMPORTED_MODULE)
            self._tree(tmp, "llamador.py", CROSS_FILE_CALLER)
            code, output = run(["--path", tmp, "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertNotIn("_ayuda", [item["name"] for item in report["findings"]])

    def test_public_definition_needs_the_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, "modulo.py", PUBLIC_UNUSED)
            hidden_code, hidden_output = run(["--path", tmp, "--json"])
            shown_code, output = run(["--path", tmp, "--json", "--include-public"])
            self.assertEqual(hidden_code, 0)
            self.assertEqual(shown_code, 1)
            self.assertEqual(json.loads(hidden_output)["findings"], [])
            self.assertIn("publica", [item["name"] for item in json.loads(output)["findings"]])

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, "modulo.py", UNUSED_IMPORT)
            code, _ = run(["--path", tmp, "--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
