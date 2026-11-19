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
from db_util import iter_files

SEVERITIES = {"low": 1, "medium": 2, "high": 3}
# Llamadas que son consulta por sí mismas.
ORM_CALLS = {"filter", "filter_by", "execute", "query"}
# Métodos que solo son consulta cuando cierran una cadena (`Model.query.all()
# `, `session.query(X).first()`). Sobre un receptor simple, `d.get(k)` o
# `items.all()` son un dict/lista y no una consulta al ORM.
CHAINED_CALLS = {"get", "all", "first", "one", "fetchall"}
EAGER = {"selectinload", "joinedload", "subqueryload", "prefetch_related", "includes", "with_entities"}
SKIP_PARTS = {"tests", "fixtures", "__pycache__", ".venv", ".git", "node_modules"}


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return ""


def _is_orm_call(node: ast.Call) -> bool:
    name = _call_name(node)
    if name in ORM_CALLS:
        return True
    if name in CHAINED_CALLS and isinstance(node.func, ast.Attribute):
        # `Model.query.all()` (Attribute) o `session.query(X).all()` (Call).
        return isinstance(node.func.value, (ast.Call, ast.Attribute))
    return False


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
        # Solo el CUERPO del bucle: `ast.walk(node)` incluía `node.iter`, así
        # que `for row in Model.query.all()` —una única consulta— se marcaba
        # como N+1.
        body = list(node.body)
        calls = [
            item for statement in body for item in ast.walk(statement)
            if isinstance(item, ast.Call) and _is_orm_call(item)
        ]
        if not calls:
            return
        eager = any(
            isinstance(item, ast.Call) and _call_name(item) in EAGER
            for statement in body for item in ast.walk(statement)
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
    # Solo se emite `medium`: `low` y `high` nunca podían disparar el gate.
    parser.add_argument("--fail-on", default="medium", choices=["medium", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    files = iter_files(target, {".py"}, frozenset(SKIP_PARTS))
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
