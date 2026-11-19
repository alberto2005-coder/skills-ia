"""Sincroniza `license` y `metadata` (paquete y versión) en el frontmatter.

Uso:
    py tests/sync_skill_metadata.py [--check] [--root RUTA]

Toma el nombre del `skills.json` raíz y la versión del manifiesto de cada
paquete, que es la única fuente de verdad, y los escribe en el frontmatter de
cada `SKILL.md`, sin duplicar campos: si `license` o el bloque `metadata` ya
existen, no se tocan. `--check` no escribe nada y sale con 1 si algún fichero
quedaría modificado.

Código de salida: 0 sin cambios pendientes · 1 con cambios (modo --check)
o error de configuración.
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
LICENSE_FIELD = re.compile(r"^license:\s*\S+", re.M)
METADATA_FIELD = re.compile(r"^metadata:\s*$", re.M)
DEFAULT_LICENSE = "MIT"


def _force_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def load_packages(root: Path) -> dict[str, tuple[str, str]]:
    """{carpeta: (nombre, versión)}; la versión sale del manifiesto del paquete."""
    index = json.loads((root / "skills.json").read_text(encoding="utf-8"))
    packages: dict[str, tuple[str, str]] = {}
    for entry in index.get("packages", []):
        name = entry.get("name")
        path = entry.get("path") or name
        if not name or not path:
            raise SystemExit(f"entrada de paquete incompleta en skills.json: {entry!r}")
        try:
            manifest = json.loads((root / path / "skills.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SystemExit(f"{path}/skills.json ilegible: {error}")
        version = manifest.get("version")
        if not isinstance(version, str) or not version:
            raise SystemExit(f"{path}/skills.json sin «version»")
        packages[path] = (name, version)
    if not packages:
        raise SystemExit("skills.json raíz no declara paquetes")
    return packages


def iter_skill_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.glob("**/SKILL.md")
        if not SKIP_PARTS & set(path.relative_to(root).parts)
    )


def build_block(frontmatter: str, package: str, version: str) -> str:
    """Devuelve el bloque a insertar, omitiendo los campos ya presentes."""
    additions: list[str] = []
    if not LICENSE_FIELD.search(frontmatter):
        additions.append(f"license: {DEFAULT_LICENSE}")
    if not METADATA_FIELD.search(frontmatter):
        additions.append(f'metadata:\n  package: {package}\n  version: "{version}"')
    return "\n".join(additions)


def sync_file(path: Path, package: str, version: str, write: bool) -> bool:
    raw = path.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")

    match = FRONTMATTER.match(text)
    if not match:
        raise SystemExit(f"{path}: sin frontmatter delimitado por ---")

    block = build_block(match.group(1), package, version)
    if not block:
        return False
    if not write:
        return True

    index = match.end(1)
    text = text[:index] + "\n" + block + text[index:]
    if crlf:
        text = text.replace("\n", "\r\n")
    path.write_bytes(text.encode("utf-8"))
    return True


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Añade license y metadata al frontmatter.")
    parser.add_argument("--root", default=str(ROOT), help="Raíz del repositorio")
    parser.add_argument("--check", action="store_true", help="No escribe; falla si hay cambios")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    packages = load_packages(root)

    pending: list[str] = []
    for path in iter_skill_files(root):
        relative = path.relative_to(root)
        package_path = relative.parts[0]
        if package_path not in packages:
            raise SystemExit(f"{relative.as_posix()}: paquete «{package_path}» ausente del índice")
        name, version = packages[package_path]
        if sync_file(path, name, version, write=not args.check):
            pending.append(relative.as_posix())

    if args.check:
        for item in pending:
            print(f"pendiente: {item}")
        print(f"{len(pending)} fichero(s) sin license/metadata.")
        return 0 if not pending else 1

    for item in pending:
        print(f"actualizado: {item}")
    print(f"{len(pending)} fichero(s) actualizados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
