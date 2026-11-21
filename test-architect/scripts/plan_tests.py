"""Plan de pruebas por riesgo a partir del árbol; no ejecuta la suite.

Uso:
    py test-architect/scripts/plan_tests.py [--root RUTA] [--json] [--out RUTA]
        [--limit N] [--min-score N]

Cruza cada módulo con los ficheros de test cuyo nombre lo menciona y puntúa el
riesgo por dominio (sesión, cobro, permisos), superficie pública y tamaño. La
salida es un plan ordenado más un ledger con lo que queda fuera y por qué.

Código de salida: 0 plan generado · 2 raíz ilegible.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import testarch_util as util  # noqa: E402

RISK_TOKENS = (
    "auth",
    "login",
    "session",
    "token",
    "password",
    "pay",
    "payments",
    "checkout",
    "billing",
    "invoice",
    "charge",
    "admin",
    "permission",
    "role",
    "secret",
    "crypto",
)
FIX_UNCOVERED = "Añade un test que ejercite la entrada pública y su caso de error, o anota la exclusión."
FIX_RISK = "Prueba el camino feliz y el de error de este dominio antes que el resto del módulo."
FIX_WIDE = "Parte el módulo o empieza por sus funciones de entrada, no por los ayudantes privados."


def tokens_of(name: str) -> set:
    """Palabras del nombre, separadas por `_` y `-`, en minúsculas."""
    clean = name.lower().replace("-", "_").replace(".py", "")
    return {piece for piece in clean.split("_") if piece}


def public_functions(tree: ast.AST) -> list:
    """Funciones y métodos de módulo cuyo nombre no empieza por `_`."""
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
    ]


def covered_stems(root: Path) -> set:
    """Palabras que aparecen en el nombre de algún fichero de test."""
    stems = set()
    for path in util.test_files(root):
        stems |= tokens_of(path.name)
    return stems


def parse_module(path: Path):
    """AST del módulo, o `None` si no parsea."""
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return None


def score_module(path: Path, root: Path, stems: set) -> dict:
    """Puntuación, cobertura y motivos de un módulo."""
    tree = parse_module(path)
    functions = public_functions(tree) if tree is not None else []
    name_tokens = tokens_of(path.name)
    risk = sorted(name_tokens & set(RISK_TOKENS))
    lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    covered = bool(name_tokens & stems)
    score = 0
    if not covered:
        score += 6
    score += 6 * len(risk)
    score += min(len(functions), 8)
    score += min(lines // 40, 5) * 2
    return {
        "module": path.stem,
        "file": util.relative(path, root),
        "score": score,
        "risk": risk,
        "functions": len(functions),
        "lines": lines,
        "covered": covered,
    }


def findings_for(entry: dict) -> list:
    """Hallazgos de un módulo del plan."""
    found = []
    if not entry["covered"]:
        severity = "high" if entry["risk"] else "medium"
        found.append(util.finding(entry["file"], 1, "modulo-sin-tests", severity,
                                  "%s no tiene un test reconocible por nombre" % entry["module"],
                                  FIX_UNCOVERED))
    if entry["risk"]:
        found.append(util.finding(entry["file"], 1, "dominio-riesgoso", "medium",
                                  "%s toca un dominio sensible: %s" % (entry["module"], ", ".join(entry["risk"])),
                                  FIX_RISK))
    if entry["functions"] >= 8:
        found.append(util.finding(entry["file"], 1, "superficie-grande", "low",
                                  "%s expone %d funciones públicas" % (entry["module"], entry["functions"]),
                                  FIX_WIDE))
    return found


def build_plan(root: Path, limit: int, min_score: int) -> dict:
    """Plan ordenado y ledger de exclusiones."""
    stems = covered_stems(root)
    entries = [score_module(path, root, stems) for path in util.python_files(root)]
    entries.sort(key=lambda item: (-item["score"], item["file"]))
    selected = [item for item in entries if item["score"] >= min_score][:limit]
    excluded = [
        {"file": item["file"], "score": item["score"], "reason": "fuera del presupuesto"}
        for item in entries
        if item not in selected
    ]
    findings = [item for entry in selected for item in findings_for(entry)]
    return util.report(
        "plan_tests",
        findings,
        len(entries),
        plan=selected,
        ledger=excluded,
        budget={"limit": limit, "min_score": min_score, "planned": len(selected)},
    )


def print_plan(data: dict) -> None:
    """Resumen legible del plan en vez del JSON."""
    print("plan: %d módulos analizados, %d en el plan" % (data["files"], len(data["plan"])))
    for item in data["plan"]:
        flag = "test" if item["covered"] else "sin test"
        print("  %3d  %-32s %-9s %s" % (item["score"], item["file"], flag, ",".join(item["risk"]) or "-"))


def main(argv: list | None = None) -> int:
    util.force_utf8()
    parser = argparse.ArgumentParser(description="Plan de pruebas por riesgo desde el árbol.")
    parser.add_argument("--root", default=".", help="Raíz del árbol a analizar")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument("--out", help="Escribe el informe JSON en esta ruta")
    parser.add_argument("--limit", type=int, default=12, help="Módulos del plan")
    parser.add_argument("--min-score", type=int, default=0, help="Puntuación mínima para entrar")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print("No existe la raíz: %s" % root, file=sys.stderr)
        return 2

    data = build_plan(root, max(args.limit, 0), args.min_score)
    if args.json or args.out:
        return util.emit(data, args.out)
    print_plan(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
