"""Objetivos de mutación desde el AST, sin ejecutar un solo mutante.

Uso:
    py test-architect/scripts/mutation_targets.py [--root RUTA] [--json]
        [--out RUTA] [--limit N] [--min-mutants N]

Cuenta por función los puntos donde una mutación mínima cambiaría la conducta
(comparaciones, booleanos, límites y retornos), los cruza con la cobertura por
nombre de test y devuelve un presupuesto ordenado. Quien ejecuta los mutantes es
el proyecto, con su runner.

Código de salida: 0 informe generado · 2 raíz ilegible.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import testarch_util as util  # noqa: E402

OPERATORS = ("condicional-negada", "booleano", "limite", "retorno")
FIX = "Añade un caso que contradiga la condición: sin él, el mutante sobrevive."


def is_boundary(value) -> bool:
    """Constante que suele marcar un límite: 0, 1, cadena vacía."""
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float, str)) and value in (0, 1, "")


def count_operators(function: ast.AST) -> dict:
    """Mutantes posibles por operador dentro de una función."""
    counts = {name: 0 for name in OPERATORS}
    for child in ast.walk(function):
        if isinstance(child, ast.Compare):
            counts["condicional-negada"] += 1
        elif isinstance(child, ast.BoolOp):
            counts["booleano"] += 1
        elif isinstance(child, ast.Constant) and is_boundary(child.value):
            counts["limite"] += 1
        elif isinstance(child, ast.Return):
            counts["retorno"] += 1
    return counts


def tokens_of(name: str) -> set:
    """Palabras del nombre, separadas por `_` y `-`, en minúsculas."""
    clean = name.lower().replace("-", "_").replace(".py", "")
    return {piece for piece in clean.split("_") if piece}


def covered_stems(root: Path) -> set:
    """Palabras que aparecen en el nombre de algún fichero de test."""
    stems = set()
    for path in util.test_files(root):
        stems |= tokens_of(path.name)
    return stems


def targets_of(path: Path, root: Path, stems: set) -> list:
    """Funciones de módulo con sus operadores y cobertura."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    name = util.relative(path, root)
    covered = bool(tokens_of(path.name) & stems)
    found = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        counts = count_operators(node)
        mutants = sum(counts.values())
        found.append({
            "function": node.name,
            "file": name,
            "line": node.lineno,
            "mutants": mutants,
            "operators": {key: value for key, value in counts.items() if value},
            "covered": covered,
        })
    return found


def build_report(root: Path, limit: int, min_mutants: int) -> dict:
    """Objetivos ordenados por mutantes y presupuesto."""
    stems = covered_stems(root)
    modules = util.python_files(root)
    targets = [item for path in modules for item in targets_of(path, root, stems)]
    ranked = sorted(
        (item for item in targets if item["mutants"] >= min_mutants),
        key=lambda item: (-item["mutants"], item["file"], item["line"]),
    )
    selected = ranked[:limit]
    findings = [
        util.finding(item["file"], item["line"], "objetivo-sin-test", "medium",
                     "%s concentra %d mutantes y no tiene test reconocible" % (item["function"], item["mutants"]),
                     FIX)
        for item in selected
        if not item["covered"]
    ]
    return util.report(
        "mutation_targets",
        findings,
        len(modules),
        targets=selected,
        discarded=[item for item in ranked if item not in selected],
        budget={"limit": limit, "min_mutants": min_mutants,
                "planned_mutants": sum(item["mutants"] for item in selected)},
    )


def main(argv: list | None = None) -> int:
    util.force_utf8()
    parser = argparse.ArgumentParser(description="Objetivos de mutación desde el AST.")
    parser.add_argument("--root", default=".", help="Raíz del árbol")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument("--out", help="Escribe el informe JSON en esta ruta")
    parser.add_argument("--limit", type=int, default=10, help="Funciones objetivo")
    parser.add_argument("--min-mutants", type=int, default=3, help="Mutantes mínimos por función")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print("No existe la raíz: %s" % root, file=sys.stderr)
        return 2

    data = build_report(root, max(args.limit, 0), max(args.min_mutants, 1))
    if args.json or args.out:
        return util.emit(data, args.out)
    print("mutación: %d módulos, %d objetivos, %d mutantes en el presupuesto"
          % (data["files"], len(data["targets"]), data["budget"]["planned_mutants"]))
    for item in data["targets"]:
        print("  %3d  %-28s %s:%d" % (item["mutants"], item["function"], item["file"], item["line"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
