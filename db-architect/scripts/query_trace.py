"""Detecta consultas ORM dentro de bucles (patrón N+1) sin ejecutar el código.

Uso:
    py db-architect/scripts/query_trace.py --path <ruta> [--json] [--fail-on medium]

Recorre el AST de Python y marca bucles `for`/`async for` cuyo cuerpo llama al
ORM sin carga anticipada (`selectinload`, `joinedload`, `prefetch_related`).

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado · 2 ruta
ilegible.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

SEVERITIES = {"low": 1, "medium": 2, "high": 3}
ORM_CALLS = {"get", "filter", "filter_by", "execute", "query", "all", "first", "one", "fetchall"}
EAGER = {"selectinload", "joinedload", "subqueryload", "prefetch_related", "includes", "with_entities"}
SKIP_PARTS = {"tests", "fixtures", "__pycache__", ".venv", ".git", "node_modules"}


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return ""


class Visitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[dict] = []

    def visit_For(self, node: ast.For) -> None:
        self._check_loop(node)
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._check_loop(node)
        self.generic_visit(node)

    def _check_loop(self, node: ast.For | ast.AsyncFor) -> None:
        calls = [
            item for item in ast.walk(node)
            if isinstance(item, ast.Call) and _call_name(item) in ORM_CALLS
        ]
        if not calls:
            return
        eager = any(
            isinstance(item, ast.Call) and _call_name(item) in EAGER
            for item in ast.walk(node)
        )
        if eager:
            return
        target = node.target
        source = node.iter
        iterated = source.attr if isinstance(source, ast.Attribute) else getattr(source, "id", "la colección")
        loop_var = target.id if isinstance(target, ast.Name) else "el elemento"
        self.findings.append({
            "file": self.path.as_posix(),
            "line": node.lineno,
            "rule": "consulta-en-bucle",
            "severity": "medium",
            "message": (f"bucle sobre {iterated}: consulta al ORM por cada {loop_var}; "
                        "una consulta por fila (N+1)"),
        })


def iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(
        item for item in path.rglob("*.py")
        if item.is_file() and not SKIP_PARTS & set(item.relative_to(path).parts)
    )


def scan_file(path: Path) -> list[dict]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    visitor = Visitor(path)
    visitor.visit(tree)
    return visitor.findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detector estático de consultas N+1.")
    parser.add_argument("--path", required=True, help="fichero o directorio Python")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="medium", choices=["low", "medium", "high", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    files = iter_files(target)
    findings = [item for path in files for item in scan_file(path)]
    findings.sort(key=lambda item: (item["file"], item["line"], item["rule"]))
    by_severity = {name: sum(1 for item in findings if item["severity"] == name) for name in SEVERITIES}

    if args.json:
        print(json.dumps({"files": len(files), "findings": findings, "by_severity": by_severity},
                         indent=2, ensure_ascii=False))
    else:
        for item in findings:
            print(f"{item['file']}:{item['line']} [{item['severity']}] {item['rule']}: {item['message']}")
        print(f"ficheros: {len(files)} · hallazgos: {len(findings)}")

    if args.fail_on == "none":
        return 0
    threshold = SEVERITIES[args.fail_on]
    return 1 if any(SEVERITIES[item["severity"]] >= threshold for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
