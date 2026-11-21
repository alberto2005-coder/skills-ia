import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import docs_parity  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "parity"


def run(argv):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = docs_parity.main(argv)
    return code, out.getvalue()


class ParityShapeTests(unittest.TestCase):
    def test_clean_pair_has_no_findings(self):
        code, output = run(["--docs", str(FIXTURES / "bilingue_ok.md"), "--json", "--no-audit"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["findings"], [])

    def test_broken_pair_reports_table_numbers_and_anchor(self):
        code, output = run(["--docs", str(FIXTURES / "bilingue_roto.md"), "--json", "--no-audit"])
        rules = {item["rule"] for item in json.loads(output)["findings"]}
        self.assertEqual(code, 1)
        self.assertIn("forma-tablas", rules)
        self.assertIn("cifras", rules)
        self.assertIn("ancla-rota", rules)

    def test_number_mismatch_is_high(self):
        code, output = run(["--docs", str(FIXTURES / "bilingue_roto.md"), "--json", "--no-audit"])
        findings = json.loads(output)["findings"]
        numbers = [item for item in findings if item["rule"] == "cifras"]
        self.assertTrue(numbers)
        self.assertEqual(numbers[0]["severity"], "high")
        self.assertEqual(code, 1)

    def test_monolingual_document_is_reported(self):
        code, output = run(["--docs", str(FIXTURES / "sin_idiomas.md"), "--json", "--no-audit"])
        findings = json.loads(output)["findings"]
        self.assertEqual(code, 1)
        self.assertEqual([item["rule"] for item in findings], ["secciones-idioma"])

    def test_threshold_none_never_fails(self):
        code, _ = run(["--docs", str(FIXTURES / "bilingue_roto.md"), "--fail-on", "none", "--no-audit"])
        self.assertEqual(code, 0)

    def test_low_threshold_fails_on_low_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "doc.md"
            target.write_text(
                (FIXTURES / "bilingue_ok.md").read_text(encoding="utf-8").replace(
                    "### Usage", "### Usage\n\n```bash\npy x.py\n```"
                ),
                encoding="utf-8",
            )
            code, output = run(["--docs", str(target), "--fail-on", "low", "--json", "--no-audit"])
            self.assertEqual(code, 1)
            self.assertIn("forma-fences", {item["rule"] for item in json.loads(output)["findings"]})

    def test_missing_path_exits_two(self):
        code, _ = run(["--docs", str(FIXTURES / "no-existe.md"), "--no-audit"])
        self.assertEqual(code, 2)

    def test_report_shape_is_stable(self):
        _, output = run(["--docs", str(FIXTURES / "bilingue_roto.md"), "--json", "--no-audit"])
        document = json.loads(output)
        self.assertEqual(document["source"], "docs_parity")
        self.assertEqual(document["files"], 1)
        self.assertEqual(document["summary"]["total"], len(document["findings"]))
        for item in document["findings"]:
            self.assertEqual(sorted(item), ["file", "fix", "line", "message", "rule", "severity"])


class AuditDocsBridgeTests(unittest.TestCase):
    """La coherencia con el código se delega en `tests/audit_docs.py` por subproceso."""

    def _root(self, tmp):
        root = Path(tmp)
        shutil.copy(FIXTURES / "bilingue_ok.md", root / "README.md")
        tests = root / "tests"
        tests.mkdir()
        (tests / "audit_docs.py").write_text(
            "import sys\n"
            "print('== Rutas ==')\n"
            "print('   - docs/demo.md: falta scripts/nope.py')\n"
            "sys.exit(1)\n",
            encoding="utf-8",
        )
        return root

    def test_findings_from_the_root_audit_are_folded_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            code, output = run(["--root", str(root), "--docs", "README.md", "--json"])
            findings = json.loads(output)["findings"]
            self.assertEqual(code, 0)  # medium < high por defecto
            self.assertEqual([item["rule"] for item in findings], ["drift-codigo"])
            self.assertIn("falta scripts/nope.py", findings[0]["message"])

    def test_no_audit_skips_the_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            _, output = run(["--root", str(root), "--docs", "README.md", "--json", "--no-audit"])
            self.assertEqual(json.loads(output)["findings"], [])

    def test_failing_audit_script_is_high(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._root(tmp)
            (root / "tests" / "audit_docs.py").write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
            code, output = run(["--root", str(root), "--docs", "README.md", "--json"])
            findings = json.loads(output)["findings"]
            self.assertEqual(code, 1)
            self.assertEqual(findings[0]["rule"], "drift-codigo")
            self.assertEqual(findings[0]["severity"], "high")


if __name__ == "__main__":
    unittest.main()
