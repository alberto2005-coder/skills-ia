"""Genera un borrador de documento de arquitectura a partir del código.

Uso:
    py docs-sync-engine/scripts/arch_gen.py --root pkg --out docs/arquitectura.md

Lee el árbol de Python (sin ejecutarlo), docstrings de módulo y funciones de
entrada, y produce un Markdown con estructura, responsabilidades y comandos.
El resultado es un borrador reproducible: se puede regenerar y comparar.

Código de salida: 0 generado · 2 ruta ilegible.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

SKIP_PARTS = {"__pycache__", ".venv", ".git", "node_modules", "tests"}


def summary(path: Path) -> str:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return "(sin docstring: no se pudo parsear)"
    doc = ast.get_docstring(tree) or ""
    return doc.strip().splitlines()[0] if doc.strip() else "(sin docstring de módulo)"


def entry_points(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    return [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def build(root: Path, title: str) -> str:
    files = sorted(item for item in root.rglob("*.py")
                   if item.is_file() and not SKIP_PARTS & set(item.relative_to(root).parts))
    lines = [f"# {title}", "", f"Generado desde `{root.as_posix()}` con `arch_gen.py`.", "",
             "## Módulos", "", "| Módulo | Responsabilidad | Entradas |", "|---|---|---|"]
    for path in files:
        names = entry_points(path)
        listed = ", ".join(f"`{name}`" for name in names[:4]) or "—"
        lines.append(f"| `{path.relative_to(root).as_posix()}` | {summary(path)} | {listed} |")
    lines += ["", "## Cómo regenerar", "", "```bash",
              f"py docs-sync-engine/scripts/arch_gen.py --root {root.as_posix()} --out <ruta>.md", "```", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Borrador del documento de arquitectura.")
    parser.add_argument("--root", required=True, help="carpeta o fichero de código")
    parser.add_argument("--out", help="fichero Markdown de salida (por defecto, stdout)")
    parser.add_argument("--title", default="Arquitectura")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.exists():
        print(f"ruta inexistente: {root}")
        return 2
    document = build(root, args.title)
    if args.out:
        Path(args.out).write_text(document + "\n", encoding="utf-8")
        print(f"escrito {args.out}")
    else:
        print(document)
    return 0


if __name__ == "__main__":
    sys.exit(main())
