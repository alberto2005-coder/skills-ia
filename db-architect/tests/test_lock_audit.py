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

import lock_audit  # noqa: E402

RISKY = """
-- migración que bloquea
CREATE INDEX idx_users_email ON users (email);

ALTER TABLE users ALTER COLUMN email TYPE varchar(320);

ALTER TABLE users RENAME COLUMN email TO mail;

ALTER TABLE orders ADD COLUMN total numeric NOT NULL DEFAULT 0;

ALTER TABLE users ALTER COLUMN mail SET NOT NULL;

ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users (id);

VACUUM FULL users;
"""

SAFE = """
CREATE INDEX CONCURRENTLY idx_users_email ON users (email);

ALTER TABLE orders ADD COLUMN notes text;

ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users (id) NOT VALID;

ALTER TABLE orders ADD CONSTRAINT chk_total CHECK (total >= 0) NOT VALID;
"""


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = lock_audit.main(argv)
    return code, out.getvalue()


class TestLockAudit(unittest.TestCase):

    def _write(self, tmp, text, name="migracion.sql"):
        path = Path(tmp) / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_risky_migration_reports_every_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, RISKY)
            code, output = run(["--path", str(path), "--json"])
            report = json.loads(output)
            rules = {item["rule"] for item in report["findings"]}
            self.assertEqual(code, 1)
            self.assertEqual(rules, {
                "indice-sin-concurrently", "reescritura-de-tipo", "rename-inseguro",
                "columna-not-null-con-default", "set-not-null", "fk-sin-not-valid", "vacuum-full",
            })
            self.assertGreaterEqual(report["by_severity"]["high"], 4)

    def test_safe_migration_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, SAFE)
            code, output = run(["--path", str(path), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["findings"], [])

    def test_comments_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "-- CREATE INDEX idx ON t (a);\n-- VACUUM FULL t;\n")
            code, _ = run(["--path", str(path)])
            self.assertEqual(code, 0)

    def test_fail_on_none_never_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, RISKY)
            code, _ = run(["--path", str(path), "--fail-on", "none"])
            self.assertEqual(code, 0)

    def test_medium_only_stays_below_high_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "CREATE INDEX idx ON users (email);\n")
            code, _ = run(["--path", str(path), "--fail-on", "high"])
            self.assertEqual(code, 0)
            code, _ = run(["--path", str(path), "--fail-on", "medium"])
            self.assertEqual(code, 1)

    def test_missing_path_exits_two(self):
        code, _ = run(["--path", "no-existe"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
