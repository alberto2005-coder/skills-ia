"""Lint de frontmatter y manifiestos de todas las skills del repositorio.

Uso:
    py tests/lint_frontmatter.py [--json]

Comprueba, sin dependencias, que cada `SKILL.md` fuera de `tests/` tenga
frontmatter delimitado, `name` en minúsculas (máx. 64) e igual al nombre de su
carpeta, `description` de 20 a 1024 caracteres, cuerpo por debajo de 500
líneas, y que cada entrada de los `skills.json` de paquete resuelva a un
fichero con el nombre declarado. Es la puerta de CI independiente de `unittest`.

Código de salida: 0 limpio · 1 con problemas.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {"tests", "fixtures", "node_modules", "__pycache__", ".venv", ".git"}
FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME = 64
MIN_DESCRIPTION = 20
MAX_DESCRIPTION = 1024
MAX_BODY_LINES = 500


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def frontmatter_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    lines = block.splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^(name|description):\s*(.*?)\s*$", lines[index])
        if not match:
            index += 1
            continue
        key, value = match.groups()
        if key == "description" and value.startswith((">", "|")):
            parts = []
            index += 1
            while index < len(lines):
                line = lines[index]
                if line.strip() and not line[0].isspace():
                    break
                parts.append(line.strip())
                index += 1
            fields[key] = " ".join(parts).strip()
            continue
        fields[key] = value.strip().strip('"').strip("'")
        index += 1
    return fields


def lint_file(path: Path) -> list[str]:
    problems: list[str] = []
    text = path.read_text(encoding="utf-8")

    match = FRONTMATTER.match(text)
    if not match:
        return ["sin bloque de frontmatter delimitado por ---"]

    fields = frontmatter_fields(match.group(1))
    name = fields.get("name", "")
    if not name:
        problems.append("falta «name»")
    else:
        if not NAME_PATTERN.match(name):
            problems.append(
                f"name «{name}» debe usar minúsculas, dígitos y guiones simples"
            )
        if len(name) > MAX_NAME:
            problems.append(f"name de {len(name)} caracteres; máximo {MAX_NAME}")
        if name != path.parent.name:
            problems.append(f"name «{name}» no coincide con la carpeta «{path.parent.name}»")

    description = fields.get("description", "")
    if not MIN_DESCRIPTION <= len(description) <= MAX_DESCRIPTION:
        problems.append(
            f"description de {len(description)} caracteres; debe estar entre "
            f"{MIN_DESCRIPTION} y {MAX_DESCRIPTION}"
        )

    body_lines = len(text[match.end():].splitlines())
    if body_lines >= MAX_BODY_LINES:
        problems.append(
            f"cuerpo de {body_lines} líneas; debe quedar por debajo de {MAX_BODY_LINES}"
        )

    return problems


def iter_skill_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.glob("**/SKILL.md")
        if not SKIP_PARTS & set(path.relative_to(root).parts)
    )


def lint_manifests(root: Path) -> dict[str, list[str]]:
    problems: dict[str, list[str]] = {}
    for manifest_path in sorted(root.glob("*/skills.json")):
        relative = manifest_path.relative_to(root).as_posix()
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            problems.setdefault(relative, []).append(f"JSON inválido: {error}")
            continue

        entries = data.get("skills")
        if not isinstance(entries, list) or not entries:
            problems.setdefault(relative, []).append("sin lista «skills»")
            continue

        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("path") or not entry.get("name"):
                problems.setdefault(relative, []).append(f"entrada incompleta: {entry!r}")
                continue
            target = manifest_path.parent / entry["path"]
            if not target.is_file():
                problems.setdefault(relative, []).append(
                    f"«{entry['name']}» apunta a un fichero inexistente: {entry['path']}"
                )
            elif entry["path"] != "SKILL.md" and target.parent.name != entry["name"]:
                problems.setdefault(relative, []).append(
                    f"«{entry['name']}» no coincide con la carpeta {target.parent.name}"
                )
    return problems


def lint_repository(root: Path = ROOT) -> dict[str, list[str]]:
    problems: dict[str, list[str]] = {}
    for path in iter_skill_files(root):
        found = lint_file(path)
        if found:
            problems[path.relative_to(root).as_posix()] = found
    for path, found in lint_manifests(root).items():
        problems.setdefault(path, []).extend(found)
    return problems


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Lint de frontmatter y manifiestos.")
    parser.add_argument("--root", default=str(ROOT), help="Raíz del repositorio")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    problems = lint_repository(root)

    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems}, indent=2, ensure_ascii=False))
    elif problems:
        for path, found in sorted(problems.items()):
            print(f"{path}")
            for item in found:
                print(f"  - {item}")
        print(f"\n{len(problems)} fichero(s) con problemas.")
    else:
        total = len(iter_skill_files(root))
        print(f"OK: {total} SKILL.md y sus manifiestos coherentes.")

    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
