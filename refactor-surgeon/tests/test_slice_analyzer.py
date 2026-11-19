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

# Dos llamadores que comparten un helper (`a → h ← b`): en el grafo no
# dirigido forman una sola componente aunque no haya arista entre a y b.
COMPARTEN_HELPER = '''
def alpha():
    return helper(1)

def beta():
    return helper(2)

def helper(n):
    return n + 1
'''

# Dos clústeres sin ninguna llamada entre sí: deben seguir separados.
CLUSTERES_SEPARADOS = '''
def izquierda():
    return detalle_izq()

def detalle_izq():
    return 1

def derecha():
    return detalle_der()

def detalle_der():
    return 2
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
            # Componentes conexas sobre el grafo NO dirigido: `main` une las
            # dos ramas, así que el fichero entero es una sola componente
            # (el DFS sobre aristas dirigidas lo partía en tres grupos).
            self.assertEqual(report["groups"], [["cargar", "enviar", "formatear", "main", "parsear"]])
            self.assertEqual(report["entry_points"], ["main"])

    def test_comparten_un_helper_quedan_en_la_misma_componente(self):
        """`alpha → helper ← beta`: deben ir juntas, no en dos grupos."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, COMPARTEN_HELPER, "comparten.py")
            code, output = run(["--path", str(path), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["groups"], [["alpha", "beta", "helper"]])
            self.assertEqual(report["entry_points"], ["alpha", "beta"])

    def test_clusters_sin_llamadas_siguen_separados(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, CLUSTERES_SEPARADOS, "clusters.py")
            code, output = run(["--path", str(path), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(
                report["groups"],
                [["derecha", "detalle_der"], ["detalle_izq", "izquierda"]],
            )
            self.assertEqual(report["entry_points"], ["derecha", "izquierda"])

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
