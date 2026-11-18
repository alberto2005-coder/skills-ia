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

import drift  # noqa: E402

SCHEMA = """
CREATE TABLE users (
    id integer PRIMARY KEY,
    email varchar(320) NOT NULL,
    org_id integer REFERENCES orgs (id)
);

CREATE TABLE orgs (
    id integer PRIMARY KEY,
    name text
);
"""

MIGRATION_OK = """
CREATE TABLE orgs (id integer PRIMARY KEY, name text);

CREATE TABLE users (
    id integer PRIMARY KEY,
    email varchar(320) NOT NULL,
    org_id integer
);
"""

MIGRATION_DRIFT = """
CREATE TABLE orgs (id integer PRIMARY KEY, name varchar(80));

CREATE TABLE users (
    id integer PRIMARY KEY,
    email text
);

CREATE TABLE invoices (id integer PRIMARY KEY);
"""


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = drift.main(argv)
    return code, out.getvalue()


class TestDrift(unittest.TestCase):

    def _setup(self, tmp, migration):
        root = Path(tmp)
        schema = root / "schema.sql"
        schema.write_text(SCHEMA, encoding="utf-8")
        migrations = root / "migrations"
        migrations.mkdir()
        (migrations / "001_init.sql").write_text(migration, encoding="utf-8")
        return schema, migrations

    def test_matching_schema_has_no_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema, migrations = self._setup(tmp, MIGRATION_OK)
            code, output = run(["--schema", str(schema), "--migrations", str(migrations), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])
            self.assertEqual(report["schema_tables"], 2)

    def test_column_and_table_drift_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema, migrations = self._setup(tmp, MIGRATION_DRIFT)
            code, output = run(["--schema", str(schema), "--migrations", str(migrations), "--json"])
            report = json.loads(output)
            rules = {(item["rule"], item["target"]) for item in report["findings"]}
            self.assertEqual(code, 1)
            self.assertIn(("columna-solo-en-esquema", "users.org_id"), rules)
            self.assertIn(("tabla-solo-en-migraciones", "invoices"), rules)
            self.assertIn(("tipo-distinto", "orgs.name"), rules)
            self.assertIn(("tipo-distinto", "users.email"), rules)

    def test_migration_dropping_a_declared_table_is_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema, migrations = self._setup(tmp, MIGRATION_OK + "\nDROP TABLE users;\n")
            code, output = run(["--schema", str(schema), "--migrations", str(migrations), "--json"])
            report = json.loads(output)
            rules = {(item["rule"], item["target"]) for item in report["findings"]}
            self.assertEqual(code, 1)
            self.assertEqual(rules, {("tabla-solo-en-esquema", "users")})
            self.assertEqual(report["schema_tables"], 2)
            self.assertEqual(report["migration_tables"], 1)

    def test_rename_and_add_are_applied_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema, migrations = self._setup(tmp, MIGRATION_OK)
            (migrations / "002_rename.sql").write_text(
                "ALTER TABLE users RENAME COLUMN email TO mail;\n", encoding="utf-8")
            code, output = run(["--schema", str(schema), "--migrations", str(migrations), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            targets = {item["target"] for item in report["findings"]}
            self.assertIn("users.mail", targets)
            self.assertIn("users.email", targets)

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema, migrations = self._setup(tmp, MIGRATION_DRIFT)
            code, _ = run(["--schema", str(schema), "--migrations", str(migrations), "--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_missing_path_exits_two(self):
        code, _ = run(["--schema", "no-existe.sql", "--migrations", "no-existe"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
