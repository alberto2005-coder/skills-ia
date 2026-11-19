"""Cruza el churn de `git log` con la complejidad para ordenar dónde refactorizar.

Uso:
    py refactor-surgeon/scripts/hotspots.py --path . --since 2026-01-01
        [--top 10] [--json] [--fail-on hotspot] [--min-score 1000]

Una fecha sin hora se normaliza a `T00:00:00`: git, con solo la fecha, usa la
hora actual del día y perdería los commits de la mañana.

Churn = líneas añadidas + borradas por fichero desde `--since`; complejidad =
suma de `V(G)` de sus funciones. El producto ordena los ficheros que más cambian
y más cuestan. Es el único script del paquete que lee historia: sin `--since`,
sin repositorio git o con un clon shallow no se mide y se declara.

Código de salida: 0 medido · 1 umbral de score superado · 2 no medido.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

# Una sola definición de V(G) en el paquete: la de `code_metrics`.
# Duplicarla aquí (con `Try`/`IfExp` y contando `BoolOp` por valores) daba dos
# números distintos para la misma función según el script que la midiera.
try:
    from .code_metrics import DECISIONS as VG_DECISIONS
except (ImportError, ValueError):
    try:
        from code_metrics import DECISIONS as VG_DECISIONS
    except ImportError:  # pragma: no cover - solo si se copia el script suelto
        VG_DECISIONS = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler,
                        ast.With, ast.AsyncWith, ast.Assert, ast.comprehension, ast.BoolOp)


def normalize_since(value: str) -> str:
    """Una fecha sin hora se fija a medianoche: git la redondearía a la hora actual."""
    clean = value.strip()
    return f"{clean}T00:00:00" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", clean) else clean


def git(path: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", "-C", str(path), *args], capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
    except OSError as error:
        # Sin `git` instalado, `subprocess.run` lanzaba FileNotFoundError.
        return subprocess.CompletedProcess(["git", *args], 127, "", str(error))


def not_measured(reason: str, as_json: bool) -> int:
    if as_json:
        print(json.dumps({"measured": False, "reason": reason, "files": []}, indent=2, ensure_ascii=False))
    else:
        print(f"no medido: {reason}")
    return 2


def complexity(path: Path) -> int:
    if path.suffix != ".py" or not path.exists():
        return 1
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return 1
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decisions = sum(1 for item in ast.walk(node)
                            if isinstance(item, VG_DECISIONS) and item is not node)
            total += 1 + decisions
    return max(1, total)


def churn_per_file(root: Path, since: str) -> tuple[dict[str, int], int]:
    result = git(root, "log", f"--since={since}", "--numstat", "--pretty=format:__C__%H")
    churn: dict[str, int] = {}
    commits = 0
    for line in result.stdout.splitlines():
        if line.startswith("__C__"):
            commits += 1
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, removed, name = parts
        if not added.isdigit() or not removed.isdigit():
            continue
        churn[name] = churn.get(name, 0) + int(added) + int(removed)
    return churn, commits


def measure(root: Path, since: str, top: int) -> dict:
    churn, commits = churn_per_file(root, since)
    # `git log` da rutas relativas a la RAÍZ del repositorio, no a `--path`:
    # con `--path src/`, `root / name` buscaba `src/src/x.py` y descartaba todo.
    top_level = git(root, "rev-parse", "--show-toplevel").stdout.strip()
    repo_root = Path(top_level) if top_level else root
    files, skipped = [], []
    for name, lines in churn.items():
        target = repo_root / name
        if not target.exists():
            skipped.append(name)
            continue
        value = complexity(target)
        try:
            shown = target.relative_to(root).as_posix()
        except ValueError:
            shown = name
        files.append({
            "path": shown,
            "churn": lines,
            "complexity": value,
            "score": lines * value,
        })
    files.sort(key=lambda item: (-item["score"], item["path"]))
    return {
        "measured": True,
        "since": since,
        "commits": commits,
        "files": files[:top],
        "total_files": len(files),
        "skipped": len(skipped),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hotspots: churn × complejidad.")
    parser.add_argument("--path", default=".", help="raíz del repositorio git")
    parser.add_argument("--since", required=False, help="fecha ISO desde la que contar (obligatoria)")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="none", choices=["hotspot", "none"])
    parser.add_argument("--min-score", type=int, default=1000)
    args = parser.parse_args(argv)

    root = Path(args.path)
    if not root.exists():
        return not_measured(f"ruta inexistente: {root}", args.json)
    if not args.since:
        return not_measured("falta --since; sin fecha el churn no es reproducible", args.json)

    inside = git(root, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return not_measured(f"{root} no es un repositorio git", args.json)
    shallow = git(root, "rev-parse", "--is-shallow-repository")
    if shallow.stdout.strip() == "true":
        return not_measured("clon shallow: la historia está truncada y el churn sería falso", args.json)

    report = measure(root, normalize_since(args.since), args.top)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"desde {report['since']} · commits {report['commits']} · ficheros {report['total_files']} "
              f"· omitidos (borrados) {report['skipped']}")
        for item in report["files"]:
            print(f"  {item['score']:>6}  churn {item['churn']:>4} × complejidad {item['complexity']:>3}  {item['path']}")

    if args.fail_on == "none":
        return 0
    return 1 if report["files"] and report["files"][0]["score"] >= args.min_score else 0


if __name__ == "__main__":
    sys.exit(main())
