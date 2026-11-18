"""Detecta funciones duplicadas comparando shingles normalizados de su AST.

Uso:
    py refactor-surgeon/scripts/clone_detect.py --path src/ [--json]
        [--shingle 8] [--min-tokens 20] [--threshold 0.8] [--fail-on clone]

Cada función se convierte en una secuencia de tokens del AST donde los nombres
de variables, parámetros y atributos se normalizan: dos funciones que solo
cambian los identificadores producen la misma secuencia. Esa secuencia se parte
en ventanas de `--shingle` tokens y dos funciones son candidatas a clon cuando el
Jaccard de sus ventanas llega a `--threshold`.

No ejecuta código, no sigue imports y no usa red: es lectura estática.

Código de salida: 0 sin clones o por debajo del umbral · 1 clones encontrados ·
2 ruta ilegible.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

SKIP_PARTS = {"__pycache__", ".venv", ".git", "node_modules"}
DECLARATIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


def normalize(node: ast.AST) -> str:
    """Token estable: el tipo de nodo, sin nombres ni valores concretos."""
    if isinstance(node, ast.Name):
        return "Name"
    if isinstance(node, ast.arg):
        return "arg"
    if isinstance(node, ast.Attribute):
        return "Attribute"
    if isinstance(node, ast.Constant):
        return f"Constant:{type(node.value).__name__}"
    return type(node).__name__


def tokenize(function: ast.AST) -> list[str]:
    """Secuencia de tokens de una función en el orden del árbol, sin decoradores."""
    tokens: list[str] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            return  # docstring: no aporta estructura
        tokens.append(normalize(node))
        for child in ast.iter_child_nodes(node):
            visit(child)

    body = getattr(function, "body", [])
    for statement in body:
        visit(statement)
    return tokens


def shingles(tokens: list[str], size: int) -> set[tuple[str, ...]]:
    if size <= 0 or len(tokens) < size:
        return set()
    return {tuple(tokens[index:index + size]) for index in range(len(tokens) - size + 1)}


def collect(path: Path, size: int, min_tokens: int) -> tuple[int, list[dict]]:
    files = [path] if path.is_file() else sorted(
        item for item in path.rglob("*.py")
        if item.is_file() and not SKIP_PARTS & set(item.parts)
    )
    functions: list[dict] = []
    for file in files:
        try:
            tree = ast.parse(file.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, DECLARATIONS):
                continue
            tokens = tokenize(node)
            if len(tokens) < min_tokens:
                continue
            functions.append({
                "file": file.as_posix(),
                "line": node.lineno,
                "name": node.name,
                "tokens": len(tokens),
                "shingles": shingles(tokens, size),
            })
    return len(files), functions


def compare(functions: list[dict], threshold: float) -> list[dict]:
    findings: list[dict] = []
    for index, first in enumerate(functions):
        for second in functions[index + 1:]:
            union = first["shingles"] | second["shingles"]
            if not union:
                continue
            shared = len(first["shingles"] & second["shingles"])
            similarity = shared / len(union)
            if similarity < threshold:
                continue
            findings.append({
                "rule": "clon-exacto" if similarity == 1.0 else "clon-cercano",
                "severity": "high" if similarity >= 0.9 else "medium",
                "similarity": round(similarity, 3),
                "shared_shingles": shared,
                "a": {"file": first["file"], "line": first["line"], "name": first["name"]},
                "b": {"file": second["file"], "line": second["line"], "name": second["name"]},
            })
    findings.sort(key=lambda item: (-item["similarity"], item["a"]["file"], item["a"]["line"]))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clones por shingles normalizados del AST.")
    parser.add_argument("--path", required=True, help="fichero o carpeta Python")
    parser.add_argument("--shingle", type=int, default=8, help="tokens por ventana")
    parser.add_argument("--min-tokens", type=int, default=20, help="tamaño mínimo de función")
    parser.add_argument("--threshold", type=float, default=0.8, help="Jaccard mínimo")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="clone", choices=["clone", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    files, functions = collect(target, args.shingle, args.min_tokens)
    findings = compare(functions, args.threshold)
    by_severity = {
        "medium": sum(1 for item in findings if item["severity"] == "medium"),
        "high": sum(1 for item in findings if item["severity"] == "high"),
    }

    if args.json:
        print(json.dumps({"files": files, "functions": len(functions),
                          "findings": findings, "by_severity": by_severity},
                         indent=2, ensure_ascii=False))
    else:
        for item in findings:
            print(f"[{item['severity']}] {item['rule']} {item['similarity']:.2f}: "
                  f"{item['a']['file']}:{item['a']['line']} {item['a']['name']} ~ "
                  f"{item['b']['file']}:{item['b']['line']} {item['b']['name']}")
        print(f"ficheros: {files} · funciones: {len(functions)} · clones: {len(findings)}")

    if args.fail_on == "none":
        return 0
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
