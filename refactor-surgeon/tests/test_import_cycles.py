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

import import_cycles  # noqa: E402

LINEAR = {
    "a.py": "from b import uno\n\n\ndef dos():\n    return uno()\n",
    "b.py": "from c import tres\n\n\ndef uno():\n    return tres()\n",
    "c.py": "def tres():\n    return 3\n",
}

TWO_CYCLE = {
    "a.py": "from b import uno\n\n\ndef dos():\n    return uno()\n",
    "b.py": "from a import dos\n\n\ndef uno():\n    return dos()\n",
}

THREE_CYCLE = {
    "a.py": "import b\n",
    "b.py": "import c\n",
    "c.py": "import a\n",
}

SELF_IMPORT = {
    "a.py": "import a\n\n\ndef f():\n    return 1\n",
}


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = import_cycles.main(argv)
    return code, out.getvalue()


class TestImportCycles(unittest.TestCase):

    def _tree(self, tmp, files):
        for name, content in files.items():
            path = Path(tmp) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return tmp

    def test_linear_imports_have_no_cycles(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, LINEAR)
            code, output = run(["--path", tmp, "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["modules"], 3)
            self.assertEqual(report["edges"], 2)
            self.assertEqual(report["cycles"], [])

    def test_two_module_cycle_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, TWO_CYCLE)
            code, output = run(["--path", tmp, "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["cycles"], [["a", "b"]])
            self.assertEqual(report["findings"][0]["severity"], "high")
            self.assertIn("a.py", report["findings"][0]["files"][0])

    def test_three_module_cycle_is_one_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, THREE_CYCLE)
            code, output = run(["--path", tmp, "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["cycles"], [["a", "b", "c"]])
            self.assertEqual(report["findings"][0]["target"], "a -> b -> c -> a")

    def test_relative_imports_inside_a_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, {
                "pkg/__init__.py": "",
                "pkg/a.py": "from .b import uno\n",
                "pkg/b.py": "from . import a\n",
            })
            code, output = run(["--path", tmp, "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["cycles"], [["pkg.a", "pkg.b"]])

    def test_self_import_is_not_a_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, SELF_IMPORT)
            code, output = run(["--path", tmp, "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["cycles"], [])

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, TWO_CYCLE)
            code, _ = run(["--path", tmp, "--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
