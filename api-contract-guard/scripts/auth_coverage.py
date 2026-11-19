"""Cruza la seguridad declarada en OpenAPI con las guardas reales de las rutas.

Uso:
    py api-contract-guard/scripts/auth_coverage.py --spec openapi.json --code src/
        [--json] [--fail-on medium|none]

Lee `security` global y por operación del contrato y busca las rutas del código
en decoradores (`@app.get("/x")`, `@router.post(...)`, `@app.route(..., methods=...)`).
Una ruta se considera protegida si su función lleva un decorador de guarda
(`login_required`, `jwt_required`, `requires_auth`, …) o un `Depends` con nombre
de seguridad. Compara las dos listas y reporta los huecos.

Código de salida: 0 sin hallazgos sobre el umbral · 1 alguno · 2 fichero ilegible.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

METHODS = {"get", "put", "post", "delete", "patch", "head", "options"}
SEVERITIES = {"low": 1, "medium": 2, "high": 3}
# Se comparan como palabras del identificador, no como subcadena: `author_only`
# contiene "auth" y contaba como guarda de autenticación.
GUARD_WORDS = {"auth", "login", "jwt", "permission", "token", "guard", "security", "require"}
TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*")
SKIP_PARTS = {"__pycache__", ".venv", ".git", "node_modules"}
ROUTE_DECORATORS = {"get", "post", "put", "delete", "patch", "head", "options", "route"}
PARAM = re.compile(r"<(?:\w+:)?(\w+)>")


def normalize(path: str) -> str:
    return PARAM.sub(r"{\1}", path).rstrip("/") or "/"


def spec_operations(spec: dict) -> dict[tuple[str, str], bool]:
    """(método, ruta) → protegida, con la seguridad global como herencia."""
    global_protected = bool(spec.get("security"))
    operations: dict[tuple[str, str], bool] = {}
    for path, item in sorted(spec.get("paths", {}).items()):
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if method.lower() not in METHODS or not isinstance(operation, dict):
                continue
            if "security" in operation:
                protected = bool(operation["security"])
            else:
                protected = global_protected
            operations[(method.upper(), normalize(path))] = protected
    return operations


def python_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    # Partes RELATIVAS: mirar el path absoluto descartaba todo si la raíz del
    # proyecto se llamaba `dist`, `build` o `vendor`.
    return sorted(item for item in root.rglob("*.py")
                  if item.is_file() and not SKIP_PARTS & set(item.relative_to(root).parts))


def is_guard(node: ast.expr) -> bool:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr.lower() in ROUTE_DECORATORS:
        return False
    tokens = {token.lower() for token in TOKEN.findall(ast.unparse(node))}
    return bool(tokens & GUARD_WORDS)


def code_routes(root: Path) -> dict[tuple[str, str], dict]:
    routes: dict[tuple[str, str], dict] = {}
    for path in python_files(root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as error:
            # Un fichero a medio escribir reventaba el CLI con traceback.
            print(f"no se pudo parsear {path}: {error}", file=sys.stderr)
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            guarded = any(is_guard(decorator) for decorator in node.decorator_list)
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                name = decorator.func.attr.lower()
                if name not in ROUTE_DECORATORS:
                    continue
                literal = next((arg.value for arg in decorator.args
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str)), None)
                if literal is None:
                    continue
                if name == "route":
                    methods = ["GET"]
                    for keyword in decorator.keywords:
                        if keyword.arg == "methods" and isinstance(keyword.value, (ast.List, ast.Tuple)):
                            methods = [item.value.upper() for item in keyword.value.elts
                                       if isinstance(item, ast.Constant) and isinstance(item.value, str)]
                else:
                    methods = [name.upper()]
                for method in methods:
                    routes[(method, normalize(literal))] = {
                        "file": path.as_posix(),
                        "line": node.lineno,
                        "function": node.name,
                        "guarded": guarded,
                    }
    return routes


def coverage(spec: dict, root: Path) -> list[dict]:
    declared = spec_operations(spec)
    implemented = code_routes(root)
    findings = []

    def add(rule: str, severity: str, target: str, message: str, extra: dict | None = None) -> None:
        finding = {"rule": rule, "severity": severity, "target": target, "message": message}
        finding.update(extra or {})
        findings.append(finding)

    for key in sorted(implemented):
        method, path = key
        target = f"{method} {path}"
        route = implemented[key]
        if key not in declared:
            add("ruta-sin-spec", "medium", target,
                f"la ruta existe en el código ({route['file']}:{route['line']}) y no en el contrato",
                {"file": route["file"], "line": route["line"]})
        elif declared[key] and not route["guarded"]:
            add("ruta-sin-guarda", "high", target,
                f"el contrato exige seguridad y {route['function']} no lleva guarda",
                {"file": route["file"], "line": route["line"]})
        elif not declared[key] and route["guarded"]:
            add("spec-sin-security", "medium", target,
                "el código protege la ruta y el contrato no declara `security`",
                {"file": route["file"], "line": route["line"]})

    for key in sorted(declared):
        if key in implemented:
            continue
        method, path = key
        add("spec-sin-codigo", "low", f"{method} {path}",
            "el contrato declara la operación y no hay ruta que la implemente")

    findings.sort(key=lambda item: (item["target"], item["rule"]))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cobertura de autenticación entre contrato y rutas.")
    parser.add_argument("--spec", required=True, help="contrato OpenAPI en JSON")
    parser.add_argument("--code", required=True, help="fichero o carpeta con las rutas")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="medium", choices=["low", "medium", "high", "none"])
    args = parser.parse_args(argv)

    spec_path, code_path = Path(args.spec), Path(args.code)
    if not spec_path.exists() or not code_path.exists():
        print("ruta inexistente")
        return 2
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"contrato ilegible: {error}")
        return 2

    findings = coverage(spec, code_path)
    by_severity = {name: sum(1 for item in findings if item["severity"] == name) for name in SEVERITIES}
    if args.json:
        print(json.dumps({"findings": findings, "by_severity": by_severity}, indent=2, ensure_ascii=False))
    else:
        for item in findings:
            location = f" ({item['file']}:{item['line']})" if item.get("file") else ""
            print(f"[{item['severity']}] {item['rule']} {item['target']}{location}: {item['message']}")
        print(f"hallazgos: {len(findings)}")
    if args.fail_on == "none":
        return 0
    floor = SEVERITIES[args.fail_on]
    return 1 if any(SEVERITIES[item["severity"]] >= floor for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
