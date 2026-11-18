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

import expand_contract  # noqa: E402

ADDITIVE = """
CREATE TABLE audit (id integer PRIMARY KEY, user_id integer);

ALTER TABLE users ADD COLUMN last_seen timestamp;

CREATE INDEX CONCURRENTLY idx_users_seen ON users (last_seen);

ALTER TABLE users ADD CONSTRAINT fk_org FOREIGN KEY (org_id) REFERENCES orgs (id) NOT VALID;
"""

DESTRUCTIVE = """
ALTER TABLE users DROP COLUMN legacy;

ALTER TABLE users DROP CONSTRAINT fk_org;

DROP TABLE invoices;
"""


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = expand_contract.main(argv)
    return code, out.getvalue()


class TestExpandContract(unittest.TestCase):

    def _write(self, tmp, sql):
        path = Path(tmp) / "migration.sql"
        path.write_text(sql, encoding="utf-8")
        return str(path)

    def test_additive_migration_stays_in_expand(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, output = run(["--path", self._write(tmp, ADDITIVE), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(len(report["phases"]["expand"]), 4)
            self.assertEqual(report["phases"]["contract"], [])
            self.assertTrue(report["deployable_together"])

    def test_destructive_migration_goes_to_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, output = run(["--path", self._write(tmp, DESTRUCTIVE), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["phases"]["expand"], [])
            self.assertEqual([item["kind"] for item in report["phases"]["contract"]],
                             ["drop-column", "drop-constraint", "drop-table"])

    def test_mixed_migration_needs_two_deploys(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, output = run(["--path", self._write(tmp, ADDITIVE + DESTRUCTIVE), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertFalse(report["deployable_together"])
            self.assertEqual(report["statements"], 7)

    def test_not_null_column_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            sql = "ALTER TABLE users ADD COLUMN email text NOT NULL;\n"
            code, output = run(["--path", self._write(tmp, sql), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual([item["rule"] for item in report["warnings"]],
                             ["columna-obligatoria-en-un-paso"])
            self.assertEqual(len(report["phases"]["expand"]), 1)

    def test_type_change_warns_and_lands_in_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            sql = "ALTER TABLE users ALTER COLUMN id TYPE bigint;\n"
            code, output = run(["--path", self._write(tmp, sql), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["phases"]["contract"][0]["kind"], "alter-type")
            self.assertEqual(report["warnings"][0]["rule"], "reescritura-no-divisible")

    def test_rename_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            sql = "ALTER TABLE users RENAME COLUMN email TO mail;\n"
            code, output = run(["--path", self._write(tmp, sql), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["phases"]["contract"][0]["kind"], "rename")
            self.assertEqual(report["warnings"][0]["rule"], "rename-no-divisible")

    def test_function_body_semicolons_are_not_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            sql = "CREATE FUNCTION f() RETURNS int AS $$ SELECT 1; $$ LANGUAGE sql;\n"
            code, output = run(["--path", self._write(tmp, sql), "--json"])
            report = json.loads(output)
            self.assertEqual(report["statements"], 1)
            self.assertEqual(len(report["phases"]["unknown"]), 1)
            self.assertEqual(code, 1)

    def test_unrecognised_statement_is_not_expand(self):
        with tempfile.TemporaryDirectory() as tmp:
            sql = "DROP INDEX idx_users_seen;\n\nINSERT INTO audit VALUES (1);\n"
            code, output = run(["--path", self._write(tmp, sql), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["phases"]["expand"], [])
            self.assertEqual(report["phases"]["contract"], [])
            self.assertEqual(len(report["phases"]["unknown"]), 2)
            self.assertEqual([item["kind"] for item in report["phases"]["unknown"]],
                             ["desconocida", "desconocida"])
            self.assertEqual([item["rule"] for item in report["warnings"]],
                             ["sentencia-desconocida", "sentencia-desconocida"])
            self.assertFalse(report["deployable_together"])
            self.assertEqual(report["statements"], 2)

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            sql = "ALTER TABLE users ADD COLUMN email text NOT NULL;\n"
            code, _ = run(["--path", self._write(tmp, sql), "--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe.sql"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
