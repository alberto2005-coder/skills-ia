"""Detecta imports y definiciones que nadie usa en un árbol de ficheros Python.

Uso:
    py refactor-surgeon/scripts/dead_code.py --path src/ [--include-public]
        [--json] [--fail-on low|medium|high|none]

Cuenta usos por identificador en todo el árbol: `ast.Name`, atributos, decoradores
y argumentos de `getattr`/`hasattr`. Un import cuyo nombre no se usa en su fichero
es `import-sin-uso`; una función o clase privada (con guion bajo) que nadie
referencia es `definicion-sin-uso`. Lo público solo se reporta con
`--include-public`, porque puede formar parte de la API del paquete.

Código de salida: 0 sin hallazgos sobre el umbral · 1 alguno · 2 ruta ilegible.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

SKIP_PARTS = {"__pycache__", ".venv", ".git", "node_modules", "build", "dist"}
SEVERITY = {"low": 1, "medium": 2, "high": 3}
ENTRY_NAMES = {"main", "__main__"}
STRING_LOOKUPS = {"getattr", "hasattr", "setattr"}


def python_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    return sorted(item for item in root.rglob("*.py")
                  if item.is_file() and not SKIP_PARTS & set(item.parts))


def exported_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        target = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            target = node.target
        if isinstance(target, ast.Name) and target.id == "__all__":
            value = getattr(node, "value", None)
            if isinstance(value, (ast.List, ast.Tuple)):
                for item in value.elts:
                    if isinstance(item, ast.Constant) and isinstance(item.value, str):
                        names.add(item.value)
    return names


def referenced_names(tree: ast.AST) -> set[str]:
    """Nombres que el fichero usa: cargas, atributos y búsquedas por cadena."""
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            used.add(node.attr)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in STRING_LOOKUPS:
            for argument in node.args:
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    used.add(argument.value)
    return used


def imported_bindings(tree: ast.AST) -> list[tuple[str, int]]:
    """(nombre, línea) por cada import del fichero."""
    bindings: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bindings.append((alias.asname or alias.name.split(".")[0], node.lineno))
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    bindings.append((alias.asname or alias.name, node.lineno))
    return bindings


def noqa_lines(source: str) -> set[int]:
    lines = set()
    for number, text in enumerate(source.splitlines(), 1):
        if "noqa" in text.lower():
            lines.add(number)
    return lines


def definitions(tree: ast.AST) -> list[tuple[str, str, int]]:
    """(nombre, tipo, línea) de funciones y clases de nivel de módulo."""
    found = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append((node.name, "función", node.lineno))
        elif isinstance(node, ast.ClassDef):
            found.append((node.name, "clase", node.lineno))
    return found


def analyze(root: Path, include_public: bool = False) -> dict:
    files = python_files(root)
    sources: dict[Path, str] = {}
    trees: dict[Path, ast.AST] = {}
    uses: dict[str, int] = {}
    exports: set[str] = set()

    for path in files:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
        sources[path] = source
        trees[path] = tree
        exports |= exported_names(tree)
        for name in referenced_names(tree):
            uses[name] = uses.get(name, 0) + 1

    findings = []
    for path in files:
        tree = trees[path]
        ignored_lines = noqa_lines(sources[path])
        for name, line in imported_bindings(tree):
            if line in ignored_lines:
                continue
            if uses.get(name, 0) == 0:
                findings.append({
                    "rule": "import-sin-uso",
                    "severity": "low",
                    "file": path.as_posix(),
                    "line": line,
                    "name": name,
                    "message": f"el import {name} no se usa en {path.name}",
                })
        for name, kind, line in definitions(tree):
            if name.startswith("__") or name in ENTRY_NAMES or name.startswith("test_"):
                continue
            if name in exports:
                continue
            private = name.startswith("_")
            if not private and not include_public:
                continue
            if uses.get(name, 0) > 0:
                continue
            findings.append({
                "rule": "definicion-sin-uso",
                "severity": "medium",
                "file": path.as_posix(),
                "line": line,
                "name": name,
                "message": f"la {kind} {name} no se referencia en el árbol analizado",
            })

    findings.sort(key=lambda item: (item["file"], item["line"], item["rule"]))
    return {
        "files": len(files),
        "findings": findings,
        "by_rule": {
            rule: sum(1 for item in findings if item["rule"] == rule)
            for rule in ("import-sin-uso", "definicion-sin-uso")
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Código muerto: imports y definiciones sin uso.")
    parser.add_argument("--path", required=True, help="fichero o carpeta Python")
    parser.add_argument("--include-public", action="store_true",
                        help="reporta también funciones y clases públicas sin uso")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="medium", choices=["low", "medium", "high", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    try:
        report = analyze(target, args.include_public)
    except SyntaxError as error:
        print(f"no se pudo parsear: {error}")
        return 2

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for item in report["findings"]:
            print(f"[{item['severity']}] {item['rule']} {item['file']}:{item['line']} "
                  f"{item['name']}: {item['message']}")
        print(f"ficheros: {report['files']} · hallazgos: {len(report['findings'])}")

    if args.fail_on == "none":
        return 0
    floor = SEVERITY[args.fail_on]
    return 1 if any(SEVERITY[item["severity"]] >= floor for item in report["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
