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

import llm_cost_scan  # noqa: E402

UNBOUNDED = '''
import anthropic

client = anthropic.Anthropic()

def resumir(prompt):
    while True:
        respuesta = client.messages.create(model="claude-opus-4", messages=[{"role": "user", "content": prompt}])
        if respuesta:
            return respuesta
'''

BOUNDED = '''
import anthropic

client = anthropic.Anthropic()

def resumir(prompt):
    return client.messages.create(
        model="claude-haiku",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
'''


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = llm_cost_scan.main(argv)
    return code, out.getvalue()


class TestLlmCostScan(unittest.TestCase):

    def test_flags_unbounded_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agente.py"
            target.write_text(UNBOUNDED, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            report = json.loads(output)
            rules = {item["rule"] for item in report["findings"]}
            self.assertEqual(code, 1)
            self.assertIn("llm-sin-limite-tokens", rules)
            self.assertIn("modelo-caro", rules)
            self.assertIn("bucle-sin-tope", rules)
            self.assertEqual(report["by_severity"]["high"], 2)
            self.assertEqual(report["by_severity"]["medium"], 1)

    def test_accepts_bounded_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agente.py"
            target.write_text(BOUNDED, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])

    def test_fail_on_threshold_controls_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "clasificador.py"
            target.write_text(
                'def classify(client, texto):\n'
                '    return client.messages.create(model="gpt-4o", max_tokens=8, messages=texto)\n',
                encoding="utf-8",
            )
            medium, _ = run(["--path", str(target), "--fail-on", "medium"])
            high, _ = run(["--path", str(target), "--fail-on", "high"])
            off, _ = run(["--path", str(target), "--fail-on", "none"])
            self.assertEqual((medium, high, off), (1, 1, 0))

    def test_json_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "agente.py"
            target.write_text(UNBOUNDED, encoding="utf-8")
            first = run(["--path", str(target), "--json"])[1]
            second = run(["--path", str(target), "--json"])[1]
            self.assertEqual(first, second)

    def test_missing_path_exits_two(self):
        code, output = run(["--path", "no-existe-esta-ruta"])
        self.assertEqual(code, 2)
        self.assertIn("ruta inexistente", output)


if __name__ == "__main__":
    unittest.main()
