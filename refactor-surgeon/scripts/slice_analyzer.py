"""Sugiere módulos extrayendo grupos de funciones que solo se llaman entre sí.

Uso:
    py refactor-surgeon/scripts/slice_analyzer.py --path modulo.py [--json]

Construye el grafo de llamadas internas del fichero y devuelve sus componentes
conexas: cada componente es un candidato a módulo propio; las funciones que
nadie llama desde dentro quedan como raíces de entrada.

Código de salida: 0 siempre que el fichero se pueda leer · 2 ruta ilegible.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path


def defined_functions(tree: ast.AST) -> list[str]:
    return [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def call_edges(tree: ast.AST, names: set[str]) -> dict[str, set[str]]:
    edges: dict[str, set[str]] = {name: set() for name in names}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for item in ast.walk(node):
            if isinstance(item, ast.Call) and isinstance(item.func, ast.Name) and item.func.id in names:
                if item.func.id != node.name:
                    edges[node.name].add(item.func.id)
    return edges


def components(edges: dict[str, set[str]]) -> list[list[str]]:
    seen: set[str] = set()
    groups: list[list[str]] = []
    for start in sorted(edges):
        if start in seen:
            continue
        stack = [start]
        group: list[str] = []
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            group.append(current)
            stack.extend(sorted(edges[current] - seen))
        groups.append(sorted(group))
    return sorted(groups, key=lambda group: (-len(group), group))


def analyze(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    names = set(defined_functions(tree))
    edges = call_edges(tree, names)
    groups = components(edges)
    return {
        "file": path.as_posix(),
        "functions": len(names),
        "groups": groups,
        "entry_points": sorted(name for name, targets in edges.items()
                               if not any(name in targets_of for targets_of in edges.values())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Componentes conexas del grafo de llamadas.")
    parser.add_argument("--path", required=True, help="fichero Python")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    try:
        report = analyze(target)
    except SyntaxError as error:
        print(f"no se pudo parsear: {error}")
        return 2

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"funciones: {report['functions']} · grupos: {len(report['groups'])}")
        for group in report["groups"]:
            print(f"  - {', '.join(group)}")
        print(f"entradas: {', '.join(report['entry_points']) or 'ninguna'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
