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

import sql_lint  # noqa: E402

CLEAN = """CREATE TABLE users (
    id integer PRIMARY KEY,
    email text
);

SELECT id, email FROM users;
"""


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = sql_lint.main(argv)
    return code, out.getvalue()


class TestSqlLint(unittest.TestCase):

    def _write(self, tmp, sql, name="migration.sql"):
        path = Path(tmp) / name
        path.write_text(sql, encoding="utf-8")
        return str(path)

    def _rules(self, tmp, sql, extra=None):
        code, output = run(["--path", self._write(tmp, sql), "--json"] + (extra or []))
        return code, json.loads(output)

    def test_clean_file_has_no_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._rules(tmp, CLEAN)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])
            self.assertEqual(report["files"], 1)

    def test_lowercase_keyword_is_low(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._rules(tmp, "select id from users;\n")
            self.assertEqual(code, 0)
            self.assertEqual([item["rule"] for item in report["findings"]],
                             ["palabra-clave-minuscula"])
            self.assertEqual(report["findings"][0]["line"], 1)

    def test_select_star_is_medium(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._rules(tmp, "SELECT * FROM users;\n")
            self.assertEqual(code, 1)
            self.assertEqual(report["findings"][0]["rule"], "select-asterisco")

    def test_table_without_primary_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._rules(tmp, "CREATE TABLE events (id integer, name text)\n")
            self.assertEqual(code, 1)
            rules = {item["rule"] for item in report["findings"]}
            self.assertIn("tabla-sin-clave", rules)

    def test_camel_case_identifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._rules(tmp, "CREATE TABLE auditLog (id integer PRIMARY KEY);\n")
            self.assertEqual(code, 0)
            self.assertIn("identificador-no-snake", {item["rule"] for item in report["findings"]})
            failing, _ = self._rules(tmp, "CREATE TABLE auditLog (id integer PRIMARY KEY);\n",
                                      ["--fail-on", "low"])
            self.assertEqual(failing, 1)

    def test_not_equal_and_long_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            sql = "SELECT id FROM users WHERE id != 3; -- " + "x" * 120 + "\n"
            code, report = self._rules(tmp, sql)
            rules = {item["rule"] for item in report["findings"]}
            self.assertEqual(code, 0)
            self.assertEqual(rules, {"comparacion-distinta", "linea-larga"})

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = self._rules(tmp, "SELECT * FROM users;\n", ["--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
