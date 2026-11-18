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

import clone_detect  # noqa: E402

ORIGINAL = '''
def total_facturas(facturas, iva):
    total = 0
    for factura in facturas:
        base = factura["base"]
        if factura["pagada"]:
            total += base * (1 + iva)
        else:
            total += base
    return round(total, 2)
'''

RENAMED = '''
def suma_albaranes(albaranes, impuesto):
    acumulado = 0
    for albaran in albaranes:
        base = albaran["importe"]
        if albaran["cobrado"]:
            acumulado += base * (1 + impuesto)
        else:
            acumulado += base
    return round(acumulado, 2)
'''

DISTINCT = '''
def correo_valido(direccion):
    if "@" not in direccion:
        return False
    usuario, dominio = direccion.split("@", 1)
    if not usuario or "." not in dominio:
        return False
    return len(direccion) <= 254
'''

TINY = '''
def doble(x):
    return x * 2

def triple(x):
    return x * 3
'''


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = clone_detect.main(argv)
    return code, out.getvalue()


class TestCloneDetect(unittest.TestCase):

    def _write(self, tmp, name, text):
        path = Path(tmp) / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_renamed_clone_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = self._write(tmp, "original.py", ORIGINAL)
            renamed = self._write(tmp, "renamed.py", RENAMED)
            code, output = run(["--path", str(Path(tmp)), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(len(report["findings"]), 1)
            item = report["findings"][0]
            self.assertIn(item["rule"], {"clon-exacto", "clon-cercano"})
            self.assertGreaterEqual(item["similarity"], 0.8)
            self.assertEqual({Path(item["a"]["file"]).name, Path(item["b"]["file"]).name},
                             {"original.py", "renamed.py"})
            self.assertTrue(original.exists() and renamed.exists())

    def test_distinct_functions_are_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "original.py", ORIGINAL)
            self._write(tmp, "distinct.py", DISTINCT)
            code, output = run(["--path", str(Path(tmp)), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])
            self.assertEqual(report["functions"], 2)

    def test_small_functions_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "tiny.py", TINY)
            code, output = run(["--path", str(Path(tmp)), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["functions"], 0)
            self.assertEqual(report["findings"], [])

    def test_normalisation_turns_a_rename_into_an_exact_clone(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "original.py", ORIGINAL)
            self._write(tmp, "renamed.py", RENAMED)
            _, output = run(["--path", str(Path(tmp)), "--threshold", "1.0", "--json"])
            report = json.loads(output)
            self.assertEqual(report["findings"][0]["rule"], "clon-exacto")
            self.assertEqual(report["findings"][0]["similarity"], 1.0)

    def test_threshold_above_the_similarity_filters_the_pair(self):
        variant = ORIGINAL.replace('if factura["pagada"]:', 'if not factura["pagada"]:')
        variant = variant.replace("total += base * (1 + iva)", "total += base * 2")
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "original.py", ORIGINAL)
            self._write(tmp, "similar.py", variant)
            _, output = run(["--path", str(Path(tmp)), "--threshold", "0.0", "--json"])
            similarity = json.loads(output)["findings"][0]["similarity"]
            self.assertGreater(similarity, 0.0)
            self.assertLess(similarity, 0.95)
            code, output = run(["--path", str(Path(tmp)), "--threshold", "0.95", "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["findings"], [])

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "original.py", ORIGINAL)
            self._write(tmp, "renamed.py", RENAMED)
            code, _ = run(["--path", str(Path(tmp)), "--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
