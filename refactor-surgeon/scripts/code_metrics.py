"""Mide complejidad ciclomática y mantenibilidad de un módulo Python, sin ejecutarlo.

Uso:
    py refactor-surgeon/scripts/code_metrics.py --path <ruta> [--json] [--fail-on high]

Complejidad de McCabe: `V(G) = 1 + puntos de decisión` (`if`, bucles, `except`,
`with`, `assert`, comprensiones y `and`/`or`). Añade anidamiento máximo, líneas y
parámetros por función, y una nota de mantenibilidad 0–100.

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
DECISIONS = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.With,
             ast.AsyncWith, ast.Assert, ast.comprehension, ast.BoolOp)
LIMITS = {"complexity": 10, "nesting": 4, "parameters": 6, "lines": 60}
SKIP_PARTS = {"tests", "fixtures", "__pycache__", ".venv", ".git", "node_modules"}


def locate(node: ast.AST, depth: int = 0) -> int:
    """Anidamiento máximo de bloques dentro de un nodo."""
    nested = [child for child in ast.iter_child_nodes(node)
              if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith))]
    if not nested:
        return depth
    return max(locate(child, depth + 1) for child in nested)


def measure(function: ast.AST) -> dict:
    decisions = sum(1 for item in ast.walk(function) if isinstance(item, DECISIONS))
    body_lines = (getattr(function, "end_lineno", function.lineno) or function.lineno) - function.lineno + 1
    parameters = len(getattr(function.args, "args", [])) + len(getattr(function.args, "kwonlyargs", []))
    return {
        "name": function.name,
        "line": function.lineno,
        "complexity": 1 + decisions,
        "nesting": locate(function),
        "lines": body_lines,
        "parameters": parameters,
    }


def findings_for(module: Path, rows: list[dict]) -> list[dict]:
    findings = []
    for row in rows:
        for metric, limit in LIMITS.items():
            if row[metric] > limit:
                findings.append({
                    "file": module.as_posix(),
                    "line": row["line"],
                    "function": row["name"],
                    "rule": f"{metric}-alta",
                    "severity": "high" if row[metric] > limit * 2 else "medium",
                    "message": f"{row['name']}: {metric}={row[metric]} supera el límite {limit}",
                })
    return findings


def maintainability(rows: list[dict]) -> int:
    if not rows:
        return 100
    penalty = sum(max(0, row["complexity"] - 4) * 2 + max(0, row["nesting"] - 2) * 3 for row in rows)
    return max(0, 100 - penalty)


def iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(item for item in path.rglob("*.py") if item.is_file()
                  and not SKIP_PARTS & set(item.relative_to(path).parts))


def scan_file(path: Path) -> tuple[list[dict], list[dict]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return [], []
    rows = [measure(node) for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    rows.sort(key=lambda row: (row["line"], row["name"]))
    return rows, findings_for(path, rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Métricas de complejidad y mantenibilidad.")
    parser.add_argument("--path", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="high", choices=["low", "medium", "high", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    files = iter_files(target)
    rows, findings = [], []
    for path in files:
        file_rows, file_findings = scan_file(path)
        rows.extend(file_rows)
        findings.extend(file_findings)
    score = maintainability(rows)

    if args.json:
        print(json.dumps({"files": len(files), "functions": rows, "findings": findings,
                          "maintainability": score}, indent=2, ensure_ascii=False))
    else:
        for row in rows:
            print(f"{row['line']:>4} {row['name']}: V(G)={row['complexity']} "
                  f"anidamiento={row['nesting']} líneas={row['lines']} params={row['parameters']}")
        print(f"mantenibilidad: {score}/100 · hallazgos: {len(findings)}")

    if args.fail_on == "none":
        return 0
    threshold = SEVERITIES[args.fail_on]
    return 1 if any(SEVERITIES[item["severity"]] >= threshold for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
