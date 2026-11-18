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

import slice_analyzer  # noqa: E402

MODULE = '''
def cargar(ruta):
    return parsear(ruta)

def parsear(texto):
    return texto.split()

def enviar(payload):
    return formatear(payload)

def formatear(payload):
    return str(payload)

def main():
    cargar("a")
    enviar({})
'''


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = slice_analyzer.main(argv)
    return code, out.getvalue()


class TestSliceAnalyzer(unittest.TestCase):

    def _write(self, tmp, text, name="mod.py"):
        path = Path(tmp) / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_groups_follow_call_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, MODULE)
            code, output = run(["--path", str(path), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["groups"], [["cargar", "parsear"], ["enviar", "formatear"], ["main"]])
            self.assertEqual(report["entry_points"], ["main"])

    def test_unreadable_file_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = self._write(tmp, "def (:", "bad.py")
            code, _ = run(["--path", str(bad)])
            self.assertEqual(code, 2)

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe.py"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
