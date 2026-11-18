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

import seed_gen  # noqa: E402

SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    total NUMERIC NOT NULL
);
"""

CYCLE = """
CREATE TABLE a (
    id INTEGER PRIMARY KEY,
    b_id INTEGER REFERENCES b(id)
);

CREATE TABLE b (
    id INTEGER PRIMARY KEY,
    a_id INTEGER REFERENCES a(id)
);
"""


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = seed_gen.main(argv)
    return code, out.getvalue()


class TestSeedGen(unittest.TestCase):

    def test_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema = Path(tmp) / "schema.sql"
            schema.write_text(SCHEMA, encoding="utf-8")
            first = run(["--schema", str(schema), "--rows", "4", "--seed", "7"])
            second = run(["--schema", str(schema), "--rows", "4", "--seed", "7"])
            self.assertEqual(first, second)
            self.assertEqual(first[0], 0)

    def test_parents_are_inserted_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema = Path(tmp) / "schema.sql"
            schema.write_text(SCHEMA, encoding="utf-8")
            code, output = run(["--schema", str(schema), "--rows", "2"])
            self.assertEqual(code, 0)
            self.assertLess(output.index("INSERT INTO users"), output.index("INSERT INTO orders"))
            self.assertEqual(output.count("INSERT INTO orders"), 2)

    def test_json_format_has_requested_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema = Path(tmp) / "schema.sql"
            schema.write_text(SCHEMA, encoding="utf-8")
            code, output = run(["--schema", str(schema), "--rows", "3", "--format", "json"])
            data = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(len(data["users"]), 3)
            self.assertEqual(sorted(data["users"][0]), ["email", "id"])

    def test_cycle_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema = Path(tmp) / "cycle.sql"
            schema.write_text(CYCLE, encoding="utf-8")
            code, output = run(["--schema", str(schema)])
            self.assertEqual(code, 2)
            self.assertIn("ciclo", output)

    def test_schema_without_tables_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema = Path(tmp) / "empty.sql"
            schema.write_text("-- nada\n", encoding="utf-8")
            code, _ = run(["--schema", str(schema)])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
