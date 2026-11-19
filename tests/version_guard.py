"""Guardia de versiones: tocar un paquete obliga a subir su versión.

Uso:
    py tests/version_guard.py [--base REV] [--root RUTA] [--bumped]

Compara el manifiesto `skills.json` de cada paquete entre `REV` (por defecto
`HEAD~1`) y el árbol actual. Si hay ficheros cambiados dentro de un paquete y
la versión del manifiesto no ha subido, sale con error: el manifiesto del
paquete es la única fuente de verdad de la versión.

`--bumped` imprime las subidas detectadas (`<paquete> <versión>`) y `--plan`
devuelve el plan de publicación en JSON (paquetes con tag y bundle si cambia la
versión del índice raíz), que es lo que consumen los workflows de tags.

Código de salida: 0 sin problemas · 1 paquetes sin subir · 2 entorno inválido.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
EMPTY_REF = "0" * 40


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def version_key(version: str) -> tuple[int, int, int] | None:
    """`(mayor, menor, parche)` o None si no es X.Y.Z."""
    match = SEMVER.match(version or "")
    return tuple(int(part) for part in match.groups()) if match else None


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git %s falló" % " ".join(args))
    return result.stdout


def resolve_base(root: Path, base: str | None) -> str | None:
    """Revisión utilizable como base, o None si no hay historial para comparar."""
    candidates = ["HEAD~1"] if base in (None, "", EMPTY_REF) else [base]
    for candidate in candidates:
        try:
            found = _git(root, "rev-parse", "--verify", "--quiet", candidate + "^{commit}")
        except RuntimeError:
            continue
        if found.strip():
            return found.strip()
    return None


def changed_files(root: Path, base: str) -> list[str]:
    """Rutas cambiadas entre `base` y HEAD, relativas a la raíz."""
    output = _git(root, "diff", "--name-only", base, "HEAD")
    return [line.strip() for line in output.splitlines() if line.strip()]


def manifest_version(root: Path, package: str, rev: str | None = None) -> str | None:
    """`version` del manifiesto del paquete en el árbol actual o en `rev`."""
    relative = "%s/skills.json" % package
    try:
        if rev is None:
            text = (root / relative).read_text(encoding="utf-8")
        else:
            text = _git(root, "show", "%s:%s" % (rev, relative))
    except (OSError, RuntimeError):
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    version = data.get("version")
    return version if isinstance(version, str) else None


def package_changes(root: Path, base: str) -> dict[str, list[str]]:
    """{paquete: rutas cambiadas} tomando como paquete el primer nivel de ruta."""
    changes: dict[str, list[str]] = {}
    for path in changed_files(root, base):
        parts = path.split("/")
        if len(parts) > 1:
            changes.setdefault(parts[0], []).append(path)
    return changes


def bumped_packages(root: Path, base: str) -> dict[str, tuple[str, str]]:
    """{paquete: (versión anterior, nueva)} solo con subidas estrictas."""
    bumps: dict[str, tuple[str, str]] = {}
    for package in sorted(package_changes(root, base)):
        old = manifest_version(root, package, base)
        new = manifest_version(root, package)
        old_key = version_key(old or "")
        new_key = version_key(new or "")
        if old_key is not None and new_key is not None and new_key > old_key:
            bumps[package] = (old, new)
    return bumps


def index_version(root: Path, rev: str | None = None) -> str | None:
    """`version` del índice raíz en el árbol actual o en `rev`."""
    if rev is None:
        try:
            text = (root / "skills.json").read_text(encoding="utf-8")
        except OSError:
            return None
    else:
        try:
            text = _git(root, "show", "%s:skills.json" % rev)
        except RuntimeError:
            return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    version = data.get("version")
    return version if isinstance(version, str) else None


def bundle_bump(root: Path, base: str) -> tuple[str, str] | None:
    """(antigua, nueva) si la versión del índice raíz cambió entre `base` y HEAD."""
    old = index_version(root, base)
    new = index_version(root)
    if old and new and old != new:
        return old, new
    return None


def release_plan(root: Path, base: str) -> dict:
    """Plan de publicación: paquetes con tag y bundle cuando cambia el índice."""
    packages = [
        {"package": name, "version": new, "tag": "%s-v%s" % (name, new)}
        for name, (_, new) in sorted(bumped_packages(root, base).items())
    ]
    bundle = None
    bump = bundle_bump(root, base)
    if bump is not None:
        bundle = {"version": bump[1], "tag": "bundle-v%s" % bump[1]}
    return {"packages": packages, "bundle": bundle}


def lint_changes(root: Path, base: str) -> list[str]:
    """Problemas de la guardia: paquetes modificados sin subir la versión."""
    problems: list[str] = []
    for package, files in sorted(package_changes(root, base).items()):
        old = manifest_version(root, package, base)
        new = manifest_version(root, package)
        if old is None or new is None:
            continue  # paquete nuevo (sin base) o borrado (sin manifiesto actual)
        old_key, new_key = version_key(old), version_key(new)
        if old_key is None or new_key is None:
            problems.append("%s: version no es X.Y.Z (%s -> %s)" % (package, old, new))
        elif new_key <= old_key:
            problems.append(
                "%s: %d fichero(s) cambiados y el manifiesto sigue en %s"
                % (package, len(files), new)
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Guardia de versiones de los paquetes.")
    parser.add_argument("--base", default=None, help="revisión base (por defecto HEAD~1)")
    parser.add_argument("--root", default=str(ROOT), help="raíz del repositorio")
    parser.add_argument("--bumped", action="store_true", help="imprime las subidas detectadas")
    parser.add_argument("--plan", action="store_true", help="imprime el plan de publicación en JSON")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        base = resolve_base(root, args.base)
    except RuntimeError as error:
        print("version_guard: %s" % error, file=sys.stderr)
        return 2
    if base is None:
        print("version_guard: sin historial suficiente para comparar; no se valida", file=sys.stderr)
        return 0

    if args.plan:
        print(json.dumps(release_plan(root, base), indent=2, sort_keys=True))
        return 0

    if args.bumped:
        for package, (_, new) in sorted(bumped_packages(root, base).items()):
            print("%s %s" % (package, new))
        return 0

    problems = lint_changes(root, base)
    if not problems:
        print("OK: las versiones suben con los cambios desde %s" % base[:12])
        return 0
    print("%d paquete(s) con cambios y sin subir de versión:" % len(problems))
    for problem in problems:
        print("  - %s" % problem)
    print("Sube «version» en el skills.json del paquete y en el índice raíz.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
