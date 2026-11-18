import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import changelog_gen  # noqa: E402


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = changelog_gen.main(argv)
    return code, out.getvalue()


class TestChangelogGen(unittest.TestCase):

    def _input(self, tmp, lines):
        path = Path(tmp) / "commits.txt"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def test_groups_by_conventional_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._input(tmp, [
                "feat(api): añade el endpoint de facturas",
                "fix: corrige el 404 del mock",
                "docs: actualiza la guía",
            ])
            code, output = run(["--input", str(path), "--version", "3.2.0"])
            self.assertEqual(code, 0)
            self.assertIn("## [3.2.0]", output)
            self.assertIn("### Nuevo", output)
            self.assertIn("- api: añade el endpoint de facturas", output)
            self.assertIn("### Correcciones", output)

    def test_unconventional_commits_go_to_otros(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._input(tmp, ["arreglos varios", "wip"])
            _, output = run(["--input", str(path), "--version", "1.0.0"])
            self.assertIn("### Otros", output)
            self.assertIn("- arreglos varios", output)

    def test_empty_input_says_sin_cambios(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "vacio.txt"
            path.write_text("", encoding="utf-8")
            _, output = run(["--input", str(path), "--version", "1.0.0"])
            self.assertIn("_Sin cambios._", output)

    def test_missing_input_exits_two(self):
        code, _ = run(["--input", "no-existe.txt", "--version", "1.0.0"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
