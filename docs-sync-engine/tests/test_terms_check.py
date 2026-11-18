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

import terms_check  # noqa: E402


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = terms_check.main(argv)
    return code, out.getvalue()


class TestTermsCheck(unittest.TestCase):

    def _setup(self, tmp, markdown, accept="OpenAPI", reject="endpoint => ruta"):
        root = Path(tmp)
        doc = root / "guia.md"
        doc.write_text(markdown, encoding="utf-8")
        accept_path = root / "accept.txt"
        accept_path.write_text(accept, encoding="utf-8")
        reject_path = root / "reject.txt"
        reject_path.write_text(reject, encoding="utf-8")
        return str(doc), str(accept_path), str(reject_path)

    def _run(self, tmp, markdown, extra=None):
        doc, accept, reject = self._setup(tmp, markdown)
        code, output = run(["--path", doc, "--accept", accept, "--reject", reject, "--json"] + (extra or []))
        return code, json.loads(output)

    def test_clean_document_has_no_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._run(tmp, "La API sigue la especificación OpenAPI y usa PostgreSQL.\n")
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])

    def test_rejected_term_suggests_the_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._run(tmp, "Este endpoint devuelve los pedidos.\n")
            self.assertEqual(code, 1)
            finding = report["findings"][0]
            self.assertEqual(finding["rule"], "termino-rechazado")
            self.assertEqual(finding["line"], 1)
            self.assertIn("usa ruta", finding["message"])
            self.assertEqual(report["by_rule"]["termino-rechazado"], 1)

    def test_canonical_spelling_is_low(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._run(tmp, "El proyecto usa openapi en los contratos.\n")
            self.assertEqual(code, 0)
            finding = report["findings"][0]
            self.assertEqual(finding["rule"], "grafia-no-canonica")
            self.assertEqual(finding["found"], "openapi")
            self.assertIn("«openapi»", finding["message"])
            self.assertIn("«OpenAPI»", finding["message"])
            self.assertNotIn("«OpenAPI» aparece", finding["message"])
            failing, _ = self._run(tmp, "El proyecto usa openapi en los contratos.\n", ["--fail-on", "low"])
            self.assertEqual(failing, 1)

    def test_code_fences_are_ignored_without_shifting_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            markdown = "```json\n{\"endpoint\": \"/x\"}\n```\nEste endpoint devuelve los pedidos.\n"
            code, report = self._run(tmp, markdown)
            self.assertEqual(code, 1)
            self.assertEqual(len(report["findings"]), 1)
            self.assertEqual(report["findings"][0]["line"], 4)

    def test_inline_code_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._run(tmp, "La clave `endpoint` del contrato es opcional.\n")
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = self._run(tmp, "Este endpoint devuelve los pedidos.\n", ["--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_missing_document_exits_two(self):
        code, _ = run(["--path", "no-existe.md"])
        self.assertEqual(code, 2)

    def test_missing_glossary_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc, _, _ = self._setup(tmp, "texto\n")
            code, _ = run(["--path", doc, "--reject", str(Path(tmp) / "no.txt")])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
