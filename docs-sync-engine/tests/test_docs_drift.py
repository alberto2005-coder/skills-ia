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

import docs_drift  # noqa: E402


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = docs_drift.main(argv)
    return code, out.getvalue()


class TestDocsDrift(unittest.TestCase):

    def _tree(self, tmp, markdown):
        root = Path(tmp)
        (root / "pkg").mkdir()
        (root / "pkg" / "existe.py").write_text("x = 1", encoding="utf-8")
        docs = root / "docs"
        docs.mkdir()
        (docs / "guia.md").write_text(markdown, encoding="utf-8")
        return root, docs

    def test_existing_reference_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, docs = self._tree(tmp, "Ejecuta `pkg/existe.py` y lee [la guía](guia.md).")
            code, output = run(["--docs", str(docs), "--root", str(root), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["findings"], [])

    def test_missing_reference_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, docs = self._tree(tmp, "Ejecuta `pkg/falta.py` para empezar.")
            code, output = run(["--docs", str(docs), "--root", str(root), "--json"])
            findings = json.loads(output)["findings"]
            self.assertEqual(code, 1)
            self.assertEqual(findings[0]["rule"], "referencia-rota")
            self.assertEqual(findings[0]["line"], 1)

    def test_external_links_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, docs = self._tree(tmp, "Ver [docs](https://example.com/guia.md).")
            code, _ = run(["--docs", str(docs), "--root", str(root), "--fail-on", "high"])
            self.assertEqual(code, 0)

    def test_missing_docs_path_exits_two(self):
        code, _ = run(["--docs", "no-existe"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
