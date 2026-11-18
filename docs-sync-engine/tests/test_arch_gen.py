import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import arch_gen  # noqa: E402


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = arch_gen.main(argv)
    return code, out.getvalue()


class TestArchGen(unittest.TestCase):

    def _tree(self, tmp):
        root = Path(tmp) / "pkg"
        root.mkdir()
        (root / "api.py").write_text('"""Capa HTTP."""\n\ndef handler():\n    return 1\n', encoding="utf-8")
        (root / "sin_doc.py").write_text("def util():\n    return 2\n", encoding="utf-8")
        (root / "tests").mkdir()
        (root / "tests" / "test_api.py").write_text('"""No debe aparecer."""\n', encoding="utf-8")
        return root

    def test_lists_modules_with_their_docstring(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp)
            code, output = run(["--root", str(root), "--title", "Mi paquete"])
            self.assertEqual(code, 0)
            self.assertIn("# Mi paquete", output)
            self.assertIn("| `api.py` | Capa HTTP. | `handler` |", output)
            self.assertIn("(sin docstring de módulo)", output)
            self.assertNotIn("test_api.py", output)

    def test_writes_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp)
            out = Path(tmp) / "arq.md"
            code, _ = run(["--root", str(root), "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertIn("## Cómo regenerar", out.read_text(encoding="utf-8"))

    def test_missing_root_exits_two(self):
        code, _ = run(["--root", "no-existe"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
