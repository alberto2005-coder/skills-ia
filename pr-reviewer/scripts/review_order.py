"""Orden de lectura de un diff por dependencias locales (Python).

Uso:
    py pr-reviewer/scripts/review_order.py --diff PARCHE [--root RUTA]
        [--json] [--out RUTA]

Construye el grafo de imports locales entre los ficheros del parche y lo agrupa
en oleadas: primero lo que no depende de nada del diff. Los ciclos se señalan y
se agrupan juntos en la última oleada, sin fingir un orden que no existe.

Código de salida: 0 plan generado · 2 parche o raíz ilegibles.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pr_review_util as util  # noqa: E402

FIX_CYCLE = "Romper el ciclo antes de mergear: mover la parte compartida a un módulo base."
FIX_GRAPH = "Leer el fichero aparte: no hay grafo fiable para él en este diff."
FIX_ORPHAN = "Confirmar que el cambio tiene sentido aislado del resto del PR."


def local_imports(path, text, changed):
    """Ficheros del diff que este módulo importa, por ruta relativa al árbol."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    package_parts = list(Path(path).with_suffix("").parts[:-1])
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            base = list(package_parts)
            if node.level:
                base = base[: len(base) - node.level + 1]
            module = (node.module or "").split(".") if node.module else []
            targets = [".".join(base + module)] if module else []
            for alias in node.names:
                targets.append(".".join(base + module + [alias.name]))
        elif isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        else:
            continue
        for target in targets:
            candidate = "/".join(target.split("."))
            for option in (candidate + ".py", candidate + "/__init__.py"):
                if option in changed and option != path:
                    found.add(option)
    return found


def build_edges(root, files):
    changed = {item["path"]: item for item in files}
    edges = {}
    unsupported = []
    for item in files:
        path = item["path"]
        edges[path] = set()
        if not path.endswith(".py"):
            unsupported.append(path)
            continue
        target = Path(root) / path if root else Path(path)
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            unsupported.append(path)
            continue
        edges[path] = local_imports(path, text, changed)
    return edges, unsupported


def waves(edges):
    """(oleadas, nodos del ciclo) con desempate alfabético."""
    pending = {node: set(deps) for node, deps in edges.items()}
    ordered = []
    while pending:
        ready = sorted(node for node, deps in pending.items() if not deps)
        if not ready:
            break
        ordered.append(ready)
        for node in ready:
            pending.pop(node)
        for deps in pending.values():
            deps.difference_update(ready)
    return ordered, sorted(pending)


def analyze(root, files):
    edges, unsupported = build_edges(root, files)
    grouped, cycle = waves(edges)
    findings = []
    for path in cycle:
        findings.append(
            util.finding(path, 1, "ciclo-dependencias", "high",
                         "participa en un ciclo de imports con " + ", ".join(sorted(edges[path] & set(cycle))),
                         FIX_CYCLE)
        )
    if cycle:
        grouped.append(cycle)
    for path in unsupported:
        findings.append(util.finding(path, 1, "sin-grafo", "low",
                                     "sin grafo de imports fiable en este diff", FIX_GRAPH))
    imported = {dep for deps in edges.values() for dep in deps}
    no_graph = set(unsupported)
    for path in sorted(edges):
        if path in no_graph:
            continue
        if len(edges) > 1 and not edges[path] and path not in imported:
            findings.append(util.finding(path, 1, "huerfano", "low",
                                         "no importa ni es importado por otro fichero del diff", FIX_ORPHAN))
    payload = {
        "source": "pr-order",
        "waves": [{"index": number, "files": files_in} for number, files_in in enumerate(grouped, start=1)],
        "edges": sorted([importer, dep] for importer, deps in edges.items() for dep in deps),
        "summary": util.summarize(findings),
        "findings": util.sort_findings(findings),
    }
    return payload


def main(argv=None):
    util.force_utf8()
    parser = argparse.ArgumentParser(description="Orden de lectura de un diff por dependencias.")
    parser.add_argument("--diff", required=True, help="parche unificado de entrada")
    parser.add_argument("--root", default=".", help="raíz para leer los imports (por defecto, el cwd)")
    parser.add_argument("--json", action="store_true", help="imprime el plan en JSON")
    parser.add_argument("--out", help="escribe el plan en esta ruta")
    args = parser.parse_args(argv)

    text = util.read_diff(args.diff)
    if text is None:
        print("review_order: no se pudo leer %s" % args.diff, file=sys.stderr)
        return 2
    files = util.parse_diff(text)
    if not files:
        print("review_order: el parche no contiene ficheros", file=sys.stderr)
        return 2
    root = Path(args.root)
    if not root.is_dir():
        print("review_order: la raíz %s no existe" % args.root, file=sys.stderr)
        return 2

    util.emit(analyze(root, files), args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
