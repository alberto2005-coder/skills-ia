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

import code_sync  # noqa: E402

BACKEND = '''
@app.get("/users")
def users():
    return []

@router.post("/orders/")
def create_order():
    return {}
'''

FRONTEND_OK = '''
const users = await fetch("/users");
const order = await axios.post("/orders");
'''

FRONTEND_BROKEN = '''
const users = await fetch("/users");
const invoice = await fetch("/invoices");
'''


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = code_sync.main(argv)
    return code, out.getvalue()


class TestCodeSync(unittest.TestCase):

    def _files(self, tmp, frontend):
        backend = Path(tmp) / "api.py"
        backend.write_text(BACKEND, encoding="utf-8")
        client = Path(tmp) / "app.js"
        client.write_text(frontend, encoding="utf-8")
        return backend, client

    def test_matching_routes_are_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend, client = self._files(tmp, FRONTEND_OK)
            code, output = run(["--backend", str(backend), "--frontend", str(client), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])

    def test_dead_call_fails_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend, client = self._files(tmp, FRONTEND_BROKEN)
            code, output = run(["--backend", str(backend), "--frontend", str(client), "--json"])
            report = json.loads(output)
            rules = {item["rule"] for item in report["findings"]}
            self.assertEqual(code, 1)
            self.assertIn("dead-call", rules)
            self.assertIn("sin-consumidor", rules)

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend, client = self._files(tmp, FRONTEND_BROKEN)
            code, _ = run(["--backend", str(backend), "--frontend", str(client), "--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_missing_file_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend, _ = self._files(tmp, FRONTEND_OK)
            code, _ = run(["--backend", str(backend), "--frontend", "no-existe.js"])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
