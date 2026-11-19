"""Agrupa commits convencionales en un borrador de CHANGELOG.

Uso:
    py docs-sync-engine/scripts/changelog_gen.py --input commits.txt --version 3.2.0
    py docs-sync-engine/scripts/changelog_gen.py --range v3.1.0..HEAD --version 3.2.0

`--input` lee un commit por línea; `--range` pide los commits a `git log` local
(sin red). Cada línea se interpreta como `tipo(ámbito): resumen`; lo que no sigue
la convención cae en `Otros` para no perderlo.

Código de salida: 0 generado · 2 entrada ilegible o git fallido.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SECTIONS = [
    ("feat", "Nuevo"),
    ("fix", "Correcciones"),
    ("perf", "Rendimiento"),
    ("refactor", "Refactor"),
    ("docs", "Documentación"),
    ("test", "Pruebas"),
    ("build", "Construcción"),
    ("ci", "CI"),
    ("chore", "Mantenimiento"),
]
CONVENTIONAL = re.compile(r"""^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?!?:\s*(?P<subject>.+)$""")


def collect(range_spec: str | None, input_file: Path | None) -> list[str]:
    if input_file is not None:
        return [line.strip() for line in input_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    # `text=True` decodifica con la página de códigos de la consola: en Windows
    # (cp1252) un asunto con acentos o emoji rompía la lectura.
    result = subprocess.run(["git", "log", "--no-merges", "--pretty=%s", range_spec or "HEAD"],
                            capture_output=True, text=True, check=False,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git log falló")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def group(commits: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    grouped: dict[str, list[str]] = {kind: [] for kind, _ in SECTIONS}
    others: list[str] = []
    for commit in commits:
        match = CONVENTIONAL.match(commit)
        if not match:
            others.append(commit)
            continue
        kind = match.group("type")
        scope = match.group("scope")
        subject = match.group("subject").strip()
        if kind in grouped:
            grouped[kind].append(f"{scope}: {subject}" if scope else subject)
        else:
            others.append(commit)
    return grouped, others


def render(grouped: dict[str, list[str]], others: list[str], version: str) -> str:
    lines = [f"## [{version}]", ""]
    for kind, title in SECTIONS:
        entries = grouped[kind]
        if not entries:
            continue
        lines.append(f"### {title}")
        lines += [f"- {entry}" for entry in sorted(entries)]
        lines.append("")
    if others:
        lines.append("### Otros")
        lines += [f"- {entry}" for entry in sorted(others)]
        lines.append("")
    if not any(grouped.values()) and not others:
        lines.append("_Sin cambios._")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Borrador de CHANGELOG desde commits convencionales.")
    parser.add_argument("--version", required=True, help="versión de la entrega")
    parser.add_argument("--input", help="fichero con un commit por línea")
    parser.add_argument("--range", help="rango para git log, p. ej. v3.1.0..HEAD")
    parser.add_argument("--out", help="fichero de salida (por defecto, stdout)")
    args = parser.parse_args(argv)

    input_file = Path(args.input) if args.input else None
    if input_file is not None and not input_file.exists():
        print(f"entrada inexistente: {input_file}")
        return 2
    try:
        commits = collect(args.range, input_file)
    except (OSError, RuntimeError) as error:
        print(f"no se pudieron leer los commits: {error}")
        return 2

    grouped, others = group(commits)
    document = render(grouped, others, args.version)
    if args.out:
        Path(args.out).write_text(document, encoding="utf-8")
        print(f"escrito {args.out} con {len(commits)} commits")
    else:
        print(document)
    return 0


if __name__ == "__main__":
    sys.exit(main())
