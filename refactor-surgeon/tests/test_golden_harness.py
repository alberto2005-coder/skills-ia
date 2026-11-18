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

import golden_harness  # noqa: E402

MODULE = '''
def sumar(a, b):
    return a + b

def fallar():
    raise ValueError("boom")
'''


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = golden_harness.main(argv)
    return code, out.getvalue()


class TestGoldenHarness(unittest.TestCase):

    def _setup(self, tmp, text=MODULE):
        module = Path(tmp) / "app.py"
        module.write_text(text, encoding="utf-8")
        cases = Path(tmp) / "cases.json"
        cases.write_text(json.dumps({"module": str(module), "cases": [
            {"function": "sumar", "args": [1, 2]},
            {"function": "fallar"},
        ]}), encoding="utf-8")
        return cases, Path(tmp) / "golden.json", module

    def test_record_then_verify_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases, snapshot, _ = self._setup(tmp)
            code, _ = run(["--cases", str(cases), "--snapshot", str(snapshot), "--record", "--allow-exec"])
            self.assertEqual(code, 0)
            saved = json.loads(snapshot.read_text(encoding="utf-8"))
            self.assertEqual(saved["results"][0]["result"], 3)
            code, output = run(["--cases", str(cases), "--snapshot", str(snapshot), "--verify", "--allow-exec"])
            self.assertEqual(code, 0)
            self.assertIn("discrepancias: 0", output)

    def test_changed_behaviour_is_a_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases, snapshot, module = self._setup(tmp)
            run(["--cases", str(cases), "--snapshot", str(snapshot), "--record", "--allow-exec"])
            module.write_text(MODULE.replace("a + b", "a - b"), encoding="utf-8")
            code, output = run(["--cases", str(cases), "--snapshot", str(snapshot), "--verify", "--allow-exec"])
            self.assertEqual(code, 1)
            self.assertIn("[MISMATCH] sumar", output)

    def test_without_allow_exec_nothing_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases, snapshot, _ = self._setup(tmp)
            code, output = run(["--cases", str(cases), "--snapshot", str(snapshot), "--record"])
            self.assertEqual(code, 0)
            self.assertFalse(snapshot.exists())
            self.assertIn("sin ejecutar", output)

    def test_missing_snapshot_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases, snapshot, _ = self._setup(tmp)
            code, _ = run(["--cases", str(cases), "--snapshot", str(snapshot), "--verify", "--allow-exec"])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
