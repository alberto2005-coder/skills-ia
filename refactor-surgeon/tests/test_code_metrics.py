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

import code_metrics  # noqa: E402

SIMPLE = '''
def sumar(a, b):
    return a + b
'''

COMPLEX = '''
def enredado(items, flag):
    total = 0
    for item in items:
        if flag:
            for sub in item:
                if sub:
                    try:
                        total += sub
                    except TypeError:
                        total += 0
        elif item:
            total += 1
        if total > 10 and flag:
            if item:
                total -= 1
        while total < 0:
            total += 1
    return total
'''

WIDE = """
def ancha(a, b, c, d, e, f, g):
    return a or b or c or d or e or f or g
"""


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = code_metrics.main(argv)
    return code, out.getvalue()


class TestCodeMetrics(unittest.TestCase):

    def _write(self, tmp, text, name="mod.py"):
        path = Path(tmp) / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_simple_function_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, SIMPLE)
            code, output = run(["--path", str(path), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["functions"][0]["complexity"], 1)
            self.assertEqual(report["maintainability"], 100)

    def test_nested_function_exceeds_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, COMPLEX)
            code, output = run(["--path", str(path), "--json", "--fail-on", "medium"])
            report = json.loads(output)
            rules = {item["rule"] for item in report["findings"]}
            self.assertEqual(code, 1)
            self.assertIn("complexity-alta", rules)
            self.assertIn("nesting-alta", rules)

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, COMPLEX)
            code, _ = run(["--path", str(path), "--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_wide_signature_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, WIDE)
            _, output = run(["--path", str(path), "--json"])
            report = json.loads(output)
            self.assertEqual(report["functions"][0]["parameters"], 7)

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
