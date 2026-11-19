"""Detecta ciclos de imports entre los módulos de un árbol Python.

Uso:
    py refactor-surgeon/scripts/import_cycles.py --path src/ [--json]
        [--fail-on cycle|none]

Resuelve cada import contra los ficheros del árbol (absolutos, relativos y
`from paquete import submodulo`), construye el grafo de dependencias y devuelve
sus componentes fuertemente conexas con más de un módulo: cada una es un ciclo
que impide extraer los módulos por separado.

Código de salida: 0 sin ciclos · 1 con ciclos · 2 ruta ilegible.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

SKIP_PARTS = {"__pycache__", ".venv", ".git", "node_modules", "build", "dist"}


def python_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    return sorted(item for item in root.rglob("*.py")
                  if item.is_file() and not SKIP_PARTS & set(item.relative_to(root).parts))


def module_name(path: Path, root: Path) -> str:
    parts = list(path.relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        return root.resolve().name
    return ".".join(parts)


def package_parts(path: Path, root: Path) -> tuple[str, ...]:
    """Carpetas del fichero respecto a la raíz: el paquete desde el que importa."""
    return tuple(path.relative_to(root).parent.parts)


def resolve_import(node: ast.AST, current_package: tuple[str, ...],
                   modules: dict[str, Path]) -> set[str]:
    found: set[str] = set()
    if isinstance(node, ast.Import):
        for alias in node.names:
            parts = alias.name.split(".")
            for size in range(len(parts), 0, -1):
                candidate = ".".join(parts[:size])
                if candidate in modules:
                    found.add(candidate)
                    break
        return found

    if not isinstance(node, ast.ImportFrom):
        return found
    base_parts = list(current_package)
    if node.level:
        drop = node.level - 1
        base_parts = base_parts[:len(base_parts) - drop] if drop <= len(base_parts) else []
    if node.module:
        base_parts = base_parts + node.module.split(".")
    base = ".".join(base_parts)
    for alias in node.names:
        if alias.name == "*":
            if base in modules:
                found.add(base)
            continue
        candidate = f"{base}.{alias.name}" if base else alias.name
        if candidate in modules:
            found.add(candidate)
        elif base in modules:
            found.add(base)
    return found


def build_graph(files: list[Path], root: Path) -> tuple[dict[str, set[str]], dict[str, Path]]:
    modules = {module_name(path, root): path for path in files}
    graph: dict[str, set[str]] = {name: set() for name in modules}
    for name, path in modules.items():
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        current_package = package_parts(path, root)
        for node in ast.walk(tree):
            for target in resolve_import(node, current_package, modules):
                if target != name:
                    graph[name].add(target)
    return graph, modules


def strongly_connected(graph: dict[str, set[str]]) -> list[list[str]]:
    """Kosaraju iterativo, en orden determinista."""
    seen: set[str] = set()
    order: list[str] = []

    def visit(start: str) -> None:
        stack = [(start, iter(sorted(graph[start])))]
        seen.add(start)
        while stack:
            node, neighbours = stack[-1]
            advanced = False
            for neighbour in neighbours:
                if neighbour not in seen:
                    seen.add(neighbour)
                    stack.append((neighbour, iter(sorted(graph[neighbour]))))
                    advanced = True
                    break
            if not advanced:
                order.append(node)
                stack.pop()

    for name in sorted(graph):
        if name not in seen:
            visit(name)

    reverse: dict[str, set[str]] = {name: set() for name in graph}
    for name, targets in graph.items():
        for target in targets:
            reverse[target].add(name)

    assigned: set[str] = set()
    groups: list[list[str]] = []
    for name in reversed(order):
        if name in assigned:
            continue
        group, stack = [], [name]
        while stack:
            current = stack.pop()
            if current in assigned:
                continue
            assigned.add(current)
            group.append(current)
            stack.extend(sorted(reverse[current] - assigned))
        groups.append(sorted(group))
    return sorted(groups, key=lambda group: group)


def analyze(root: Path) -> dict:
    files = python_files(root)
    base = root if root.is_dir() else root.parent
    graph, modules = build_graph(files, base)
    cycles = [group for group in strongly_connected(graph) if len(group) > 1]
    findings = [{
        "rule": "ciclo",
        "severity": "high",
        "target": " -> ".join(group + [group[0]]),
        "modules": group,
        "files": [modules[name].as_posix() for name in group],
        "message": f"{len(group)} módulos se importan en círculo",
    } for group in cycles]
    return {
        "modules": len(modules),
        "edges": sum(len(targets) for targets in graph.values()),
        "cycles": [item["modules"] for item in findings],
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ciclos de imports entre módulos.")
    parser.add_argument("--path", required=True, help="fichero o carpeta Python")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="cycle", choices=["cycle", "none"])
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
        for item in report["findings"]:
            print(f"[{item['severity']}] {item['rule']} {item['target']}")
            for path in item["files"]:
                print(f"  - {path}")
        print(f"módulos: {report['modules']} · aristas: {report['edges']} "
              f"· ciclos: {len(report['findings'])}")

    if args.fail_on == "none":
        return 0
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
