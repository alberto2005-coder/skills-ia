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

import migration_guard  # noqa: E402

DESTRUCTIVE = """
-- migración 0042
ALTER TABLE orders DROP COLUMN legacy_total;
"""

SAFE = """
-- migración 0043
ALTER TABLE orders ADD COLUMN note TEXT;

-- DOWN
ALTER TABLE orders DROP COLUMN note;
"""

SLOW = """
-- migración 0044
CREATE INDEX idx_orders_created ON orders(created_at);

-- DOWN
DROP INDEX idx_orders_created;

-- DROP TABLE viejo no es código: está en un comentario
"""


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = migration_guard.main(argv)
    return code, out.getvalue()


class TestMigrationGuard(unittest.TestCase):

    def test_destructive_migration_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "0042_drop.sql"
            target.write_text(DESTRUCTIVE, encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            report = json.loads(output)
            rules = {item["rule"] for item in report["findings"]}
            self.assertEqual(code, 1)
            self.assertIn("drop-column", rules)
            self.assertIn("sin-reversion", rules)
            self.assertEqual(report["by_severity"]["critical"], 1)

    def test_safe_migration_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "0043_add.sql"
            target.write_text(SAFE, encoding="utf-8")
            code, output = run(["--path", str(target), "--json", "--fail-on", "warning"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])

    def test_slow_index_is_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "0044_index.sql"
            target.write_text(SLOW, encoding="utf-8")
            strict, output = run(["--path", str(target), "--json", "--fail-on", "warning"])
            lenient, _ = run(["--path", str(target), "--json"])
            report = json.loads(output)
            self.assertEqual(strict, 1)
            self.assertEqual(lenient, 0)
            self.assertEqual([item["rule"] for item in report["findings"]], ["indice-sin-concurrently"])

    def test_comments_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "0045.sql"
            target.write_text("-- TRUNCATE users\nSELECT 1;\n-- DOWN\nSELECT 2;\n", encoding="utf-8")
            code, output = run(["--path", str(target), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["findings"], [])


if __name__ == "__main__":
    unittest.main()
