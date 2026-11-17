"""Modo diff/PR: limita la auditoría a las líneas que cambian.

Uso:
    py appsec-audit/scripts/diff_scope.py --diff cambios.patch [--findings findings.json]
        [--output scope.json] [--json]
    py appsec-audit/scripts/diff_scope.py --repo . --base origin/main [--findings ...]

Produce `{"files": {ruta: [[inicio, fin], ...]}}` a partir de un parche unificado
o de `git diff` contra una base, y con `--findings` separa los hallazgos que caen
dentro del cambio de los que quedan fuera. No ejecuta nada del proyecto auditado:
`git diff` es lectura del historial local.

Código de salida: 0 correcto · 1 findings ilegible · 2 diff o git no disponible.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def normalize_path(target: str) -> str:
    path = target.strip().split("\t")[0]
    for prefix in ("b/", "a/"):
        if path.startswith(prefix):
            return path[len(prefix):]
    return path


def merge_ranges(ranges: list[list[int]]) -> list[list[int]]:
    merged: list[list[int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def parse_patch(text: str) -> dict[str, list[list[int]]]:
    """Devuelve, por fichero, las líneas añadidas según un parche unificado."""
    files: dict[str, list[list[int]]] = {}
    current: str | None = None

    for line in text.splitlines():
        if line.startswith("+++ "):
            target = line[4:].strip()
            current = None if target == "/dev/null" else normalize_path(target)
            if current is not None:
                files.setdefault(current, [])
            continue
        if current is None or not line.startswith("@@"):
            continue
        match = HUNK_RE.match(line)
        if not match:
            continue
        start = int(match.group(1))
        count = int(match.group(2)) if match.group(2) is not None else 1
        if count > 0:
            files[current].append([start, start + count - 1])

    return {path: merge_ranges(ranges) for path, ranges in files.items() if ranges}


def git_diff(repo: Path, base: str) -> str:
    if shutil.which("git") is None:
        raise RuntimeError("git no está disponible en el PATH")
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--unified=0", "--no-color", "--no-ext-diff", base],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git diff {base} falló")
    return result.stdout


def in_scope(finding: object, files: dict[str, list[list[int]]]) -> bool:
    if not isinstance(finding, dict):
        return False
    location = finding.get("location")
    if not isinstance(location, dict):
        return False
    path = location.get("file")
    line = location.get("line")
    if not isinstance(path, str) or not isinstance(line, int):
        return False
    for start, end in files.get(normalize_path(path), []):
        if start <= line <= end:
            return True
    return False


def build_scope(files: dict[str, list[list[int]]], findings: object | None,
                source: str) -> dict:
    scope = {
        "mode": "diff",
        "source": source,
        "files": files,
        "summary": {
            "files": len(files),
            "changed_lines": sum(end - start + 1 for ranges in files.values() for start, end in ranges),
        },
    }

    if findings is not None:
        if not isinstance(findings, dict) or not isinstance(findings.get("findings"), list):
            raise ValueError("el fichero de hallazgos no tiene una lista «findings»")
        items = findings["findings"]
        inside = [
            item.get("id") for item in items
            if isinstance(item, dict) and in_scope(item, files)
        ]
        outside = [
            item.get("id") for item in items
            if isinstance(item, dict) and not in_scope(item, files)
        ]
        scope["findings"] = {
            "total": len([item for item in items if isinstance(item, dict)]),
            "in_scope": inside,
            "out_of_scope": outside,
        }

    return scope


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Alcance de auditoría limitado a un diff.")
    origin = parser.add_mutually_exclusive_group(required=True)
    origin.add_argument("--diff", help="Parche unificado (salida de git diff o de un PR)")
    origin.add_argument("--base", help="Referencia base; usa git diff contra ella")
    parser.add_argument("--repo", default=".", help="Repositorio local para --base")
    parser.add_argument("--findings", help="findings.json para separar lo que cae en el diff")
    parser.add_argument("--output", help="Fichero JSON de salida")
    parser.add_argument("--json", action="store_true", help="Imprime el alcance en stdout")
    args = parser.parse_args(argv)

    try:
        if args.diff:
            patch_path = Path(args.diff)
            if not patch_path.is_file():
                raise OSError(f"no existe el parche: {patch_path}")
            text = patch_path.read_text(encoding="utf-8", errors="replace")
            source = str(patch_path)
        else:
            repo = Path(args.repo)
            if not repo.is_dir():
                raise OSError(f"no existe el repositorio: {repo}")
            text = git_diff(repo, args.base)
            source = f"git:{args.base}"
        files = parse_patch(text)
    except (OSError, RuntimeError) as error:
        print(f"No se pudo calcular el diff: {error}", file=sys.stderr)
        return 2

    findings = None
    if args.findings:
        try:
            findings_path = Path(args.findings)
            findings = json.loads(findings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            print(f"Hallazgos ilegibles: {error}", file=sys.stderr)
            return 1

    try:
        scope = build_scope(files, findings, source)
    except ValueError as error:
        print(f"Hallazgos inválidos: {error}", file=sys.stderr)
        return 1

    text = json.dumps(scope, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Alcance escrito en {args.output} "
              f"({scope['summary']['files']} fichero(s), "
              f"{scope['summary']['changed_lines']} línea(s) cambiada(s))")
    elif args.json:
        print(text, end="")
    else:
        print(f"{scope['summary']['files']} fichero(s) · "
              f"{scope['summary']['changed_lines']} línea(s) cambiada(s) · {source}")
        for path, ranges in files.items():
            rendered = ", ".join(f"{start}-{end}" for start, end in ranges)
            print(f"  {path}: {rendered}")
        if "findings" in scope:
            print(f"  en el diff: {', '.join(scope['findings']['in_scope']) or 'ninguno'}")
            print(f"  fuera: {', '.join(scope['findings']['out_of_scope']) or 'ninguno'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
