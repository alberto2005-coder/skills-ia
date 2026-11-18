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

import auth_coverage  # noqa: E402

BEARER = [{"bearerAuth": []}]

SPEC = {
    "openapi": "3.0.0",
    "paths": {
        "/users": {"get": {"security": BEARER, "responses": {}}},
        "/orders": {"post": {"security": BEARER, "responses": {}}},
    },
}

SPEC_UNPROTECTED = {
    "openapi": "3.0.0",
    "paths": {"/users": {"get": {"responses": {}}}},
}

SPEC_GLOBAL = {
    "openapi": "3.0.0",
    "security": BEARER,
    "paths": {
        "/users": {"get": {"responses": {}}},
        "/orders": {"post": {"responses": {}}},
    },
}

GUARDED_CODE = """
from fastapi import FastAPI

app = FastAPI()


@app.get("/users")
@login_required
def list_users():
    return []


@app.post("/orders")
@jwt_required()
def create_order():
    return {}
"""

PLAIN_CODE = """
from fastapi import FastAPI

app = FastAPI()


@app.get("/users")
def list_users():
    return []
"""


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = auth_coverage.main(argv)
    return code, out.getvalue()


class TestAuthCoverage(unittest.TestCase):

    def _setup(self, tmp, spec, code):
        root = Path(tmp)
        spec_path = root / "openapi.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        code_path = root / "app.py"
        code_path.write_text(code, encoding="utf-8")
        return str(spec_path), str(code_path)

    def _run(self, spec, code, extra=None):
        with tempfile.TemporaryDirectory() as tmp:
            spec_path, code_path = self._setup(tmp, spec, code)
            run_code, output = run(["--spec", spec_path, "--code", code_path, "--json"] + (extra or []))
            return run_code, json.loads(output)

    def test_guarded_routes_match_the_contract(self):
        code, report = self._run(SPEC, GUARDED_CODE)
        self.assertEqual(code, 0)
        self.assertEqual(report["findings"], [])

    def test_spec_security_without_guard_is_high(self):
        code, report = self._run(SPEC, PLAIN_CODE)
        self.assertEqual(code, 1)
        rules = {item["rule"] for item in report["findings"]}
        self.assertIn("ruta-sin-guarda", rules)
        finding = next(item for item in report["findings"] if item["rule"] == "ruta-sin-guarda")
        self.assertEqual(finding["target"], "GET /users")
        self.assertEqual(finding["severity"], "high")

    def test_guard_without_spec_security(self):
        code, report = self._run(SPEC_UNPROTECTED, GUARDED_CODE)
        self.assertEqual(code, 1)
        self.assertIn("spec-sin-security", {item["rule"] for item in report["findings"]})

    def test_route_missing_from_the_contract(self):
        code, report = self._run(SPEC, PLAIN_CODE + '\n\n@app.get("/health")\ndef health():\n    return "ok"\n')
        self.assertIn("ruta-sin-spec", {item["rule"] for item in report["findings"]})

    def test_contract_operation_without_code(self):
        code, report = self._run(SPEC, PLAIN_CODE)
        self.assertEqual(code, 1)
        targets = {(item["rule"], item["target"]) for item in report["findings"]}
        self.assertIn(("spec-sin-codigo", "POST /orders"), targets)

    def test_global_security_is_inherited(self):
        code, report = self._run(SPEC_GLOBAL, GUARDED_CODE)
        self.assertEqual(code, 0)
        self.assertEqual(report["findings"], [])

    def test_flask_route_methods_are_normalised(self):
        spec = {"openapi": "3.0.0", "paths": {
            "/items/{item_id}": {"get": {"security": BEARER}, "post": {"security": BEARER}}}}
        code_text = """
from flask import Flask

app = Flask(__name__)


@app.route("/items/<int:item_id>", methods=["GET", "POST"])
@requires_auth
def item(item_id):
    return {}
"""
        run_code, report = self._run(spec, code_text)
        self.assertEqual(run_code, 0)
        self.assertEqual(report["findings"], [])

    def test_missing_spec_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_path = Path(tmp) / "app.py"
            code_path.write_text(PLAIN_CODE, encoding="utf-8")
            run_code, _ = run(["--spec", "no-existe.json", "--code", str(code_path)])
            self.assertEqual(run_code, 2)

    def test_fail_on_none_never_fails(self):
        code, _ = self._run(SPEC, PLAIN_CODE, ["--fail-on", "none"])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
