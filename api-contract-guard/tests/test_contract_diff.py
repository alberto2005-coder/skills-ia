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

import contract_diff  # noqa: E402


def operation(kind="object", description="lista"):
    return {
        "description": description,
        "responses": {"200": {"content": {"application/json": {"schema": {"type": kind}}}}},
    }


OLD = {"paths": {"/users": {"get": operation()}, "/orders": {"get": operation()}}}
NEW_ADDITIVE = {"paths": {"/users": {"get": operation()}, "/orders": {"get": operation()},
                          "/invoices": {"get": operation()}}}
NEW_REMOVED = {"paths": {"/users": {"get": operation(description="otra")}}}
NEW_TYPE = {"paths": {"/users": {"get": operation(kind="array")}, "/orders": {"get": operation()}}}


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = contract_diff.main(argv)
    return code, out.getvalue()


class TestContractDiff(unittest.TestCase):

    def _write(self, folder, name, document):
        path = Path(folder) / name
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def test_removed_endpoint_is_major(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = self._write(tmp, "old.json", OLD)
            new = self._write(tmp, "new.json", NEW_REMOVED)
            code, output = run(["--old", str(old), "--new", str(new), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["version"], "major")
            self.assertIn("/orders", [item["path"] for item in report["changes"]])

    def test_added_endpoint_is_minor(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = self._write(tmp, "old.json", OLD)
            new = self._write(tmp, "new.json", NEW_ADDITIVE)
            code, output = run(["--old", str(old), "--new", str(new), "--json", "--fail-on", "major"])
            report = json.loads(output)
            self.assertEqual(code, 0)
            self.assertEqual(report["version"], "minor")

    def test_response_type_change_is_major(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = self._write(tmp, "old.json", OLD)
            new = self._write(tmp, "new.json", NEW_TYPE)
            code, output = run(["--old", str(old), "--new", str(new), "--json"])
            report = json.loads(output)
            self.assertEqual(code, 1)
            self.assertEqual(report["changes"][0]["level"], "major")

    def test_unreadable_contract_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("no es json", encoding="utf-8")
            code, _ = run(["--old", str(bad), "--new", str(bad)])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
