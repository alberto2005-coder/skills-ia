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

import schema_audit  # noqa: E402

HEALTHY = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id)
);

CREATE INDEX idx_orders_user ON orders(user_id);
"""

WITHOUT_INDEX = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id)
);

CREATE TABLE notes (
    body TEXT
);
"""

BROKEN = "CREATE TABLE users (id INTEGER, ;"


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = schema_audit.main(argv)
    return code, out.getvalue()


class TestSchemaAudit(unittest.TestCase):

    def test_healthy_schema_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "schema.sql"
            target.write_text(HEALTHY, encoding="utf-8")
            code, output = run(["--path", str(target), "--json", "--fail-on", "medium"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])

    def test_missing_primary_key_and_index_are_medium(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "schema.sql"
            target.write_text(WITHOUT_INDEX, encoding="utf-8")
            code, output = run(["--path", str(target), "--json", "--fail-on", "medium"])
            report = json.loads(output)
            rules = {item["rule"] for item in report["findings"]}
            self.assertEqual(code, 1)
            self.assertIn("tabla-sin-primary-key", rules)
            self.assertIn("fk-sin-indice", rules)
            self.assertEqual(report["by_severity"]["medium"], 2)

    def test_invalid_sql_is_high(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "schema.sql"
            target.write_text(BROKEN, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["findings"][0]["rule"], "sql-invalido")

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe-esta-ruta"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
