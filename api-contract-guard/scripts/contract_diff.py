"""Compara dos contratos OpenAPI y calcula el impacto SemVer, sin red.

Uso:
    py api-contract-guard/scripts/contract_diff.py --old old.json --new new.json
        [--json] [--fail-on major]

Niveles: `major` para lo que rompe consumidores, `minor` para lo aditivo,
`patch` para cambios de documentación y `none` cuando no hay ningún cambio
(dos contratos idénticos salen 0 aunque se pase `--fail-on patch`).

Código de salida: 0 por debajo del umbral · 1 umbral alcanzado · 2 contrato
ilegible.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LEVELS = {"patch": 1, "minor": 2, "major": 3}
METHODS = {"get", "put", "post", "delete", "patch", "head", "options"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def response_type(operation: dict) -> str:
    responses = operation.get("responses", {})
    for code in ("200", "201", 200, 201):
        if code in responses:
            content = responses[code].get("content", {})
            for media in content.values():
                return str(media.get("schema", {}).get("type", ""))
    return ""


def diff(old: dict, new: dict) -> list[dict]:
    changes: list[dict] = []
    old_paths = old.get("paths", {})
    new_paths = new.get("paths", {})

    for path in sorted(set(old_paths) - set(new_paths)):
        changes.append({"level": "major", "path": path, "detail": "endpoint eliminado"})
    for path in sorted(set(new_paths) - set(old_paths)):
        changes.append({"level": "minor", "path": path, "detail": "endpoint nuevo"})

    for path in sorted(set(old_paths) & set(new_paths)):
        old_methods = {name: value for name, value in old_paths[path].items() if name.lower() in METHODS}
        new_methods = {name: value for name, value in new_paths[path].items() if name.lower() in METHODS}
        for method in sorted(set(old_methods) - set(new_methods)):
            changes.append({"level": "major", "path": f"{method.upper()} {path}", "detail": "método eliminado"})
        for method in sorted(set(new_methods) - set(old_methods)):
            changes.append({"level": "minor", "path": f"{method.upper()} {path}", "detail": "método nuevo"})
        for method in sorted(set(old_methods) & set(new_methods)):
            before = response_type(old_methods[method])
            after = response_type(new_methods[method])
            if before != after:
                changes.append({"level": "major", "path": f"{method.upper()} {path}",
                                "detail": f"tipo de respuesta {before or 'sin tipo'} → {after or 'sin tipo'}"})
            if old_methods[method].get("description") != new_methods[method].get("description"):
                changes.append({"level": "patch", "path": f"{method.upper()} {path}",
                                "detail": "cambio de descripción"})
    return changes


def verdict(changes: list[dict]) -> str:
    """Nivel de impacto. Sin cambios no hay impacto: no es un `patch`.

    Devolver `patch` para una lista vacía hacía que dos contratos idénticos
    dieran exit 1 con `--fail-on patch`.
    """
    if not changes:
        return "none"
    level = "patch"
    for change in changes:
        if LEVELS[change["level"]] > LEVELS[level]:
            level = change["level"]
    return level


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diff SemVer de dos contratos OpenAPI.")
    parser.add_argument("--old", required=True)
    parser.add_argument("--new", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="major", choices=["patch", "minor", "major", "none"])
    args = parser.parse_args(argv)

    try:
        old = load(Path(args.old))
        new = load(Path(args.new))
    except (OSError, json.JSONDecodeError) as error:
        print(f"contrato ilegible: {error}")
        return 2

    changes = diff(old, new)
    level = verdict(changes)
    if args.json:
        print(json.dumps({"version": level, "changes": changes}, indent=2, ensure_ascii=False))
    else:
        for change in changes:
            print(f"[{change['level']}] {change['path']}: {change['detail']}")
        print(f"impacto: {level.upper()} · cambios: {len(changes)}")

    if args.fail_on == "none" or level == "none":
        return 0
    return 1 if LEVELS[level] >= LEVELS[args.fail_on] else 0


if __name__ == "__main__":
    sys.exit(main())
