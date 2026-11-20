"""Sube la versión de un paquete en todos los sitios que la declaran.

Uso:
    py scripts/bump_version.py <paquete> <version> [--root RUTA] [--no-bundle] [--dry-run]

La versión del paquete vive en su manifiesto, pero aparece replicada en el
índice raíz, en el `metadata.version` de cada `SKILL.md` y en el marketplace.
`tests/lint_frontmatter.py` falla si divergen, así que este script mueve las
cuatro copias de una vez:

1. `<paquete>/skills.json` → `version`.
2. El `metadata.version` de cada `SKILL.md` de ese paquete.
3. La entrada del paquete en el índice raíz, más la `version` del índice
   (la del bundle) con un salto de parche, salvo `--no-bundle`.
4. El plugin del paquete en `.claude-plugin/marketplace.json` y la `version`
   del marketplace, sincronizadas con lo anterior.

No toca git ni crea commits: deja el árbol listo para revisar el diff y subirlo.

Código de salida: 0 correcto · 1 datos inválidos · 2 uso.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_PATH = Path(".claude-plugin") / "marketplace.json"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
PACKAGE_LINE = re.compile(r"^\s+package:\s*[\"']?([^\"'\s]+)", re.M)
VERSION_LINE = re.compile(r"^(\s+version:\s*)(\"[^\"]*\"|'[^']*'|[^\s#]+)", re.M)
SKILL_SKIP_PARTS = {"tests", "fixtures", "__pycache__", ".git", "output", "reports"}


class BumpError(RuntimeError):
    """Los datos de entrada no permiten subir la versión sin romper el lint."""


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def version_key(version: str) -> tuple[int, int, int] | None:
    """Tupla comparable de una versión X.Y.Z, o None si no lo es."""
    match = SEMVER.match(version or "")
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())


def next_patch(version: str) -> str:
    """X.Y.Z → X.Y.(Z+1), para el bundle."""
    major, minor, patch = version.split(".")
    return "%s.%s.%d" % (major, minor, int(patch) + 1)


def read_json(path: Path) -> dict:
    """Objeto JSON del fichero, con un error legible si no se puede leer."""
    try:
        data = json.loads(path.read_bytes().decode("utf-8"))
    except OSError as error:
        raise BumpError("no se pudo leer %s: %s" % (path, error))
    except json.JSONDecodeError as error:
        raise BumpError("%s tiene JSON inválido: %s" % (path, error))
    if not isinstance(data, dict):
        raise BumpError("%s no contiene un objeto JSON" % path)
    return data


def dump_json(path: Path, data: dict) -> bytes:
    """JSON con el mismo estilo del fichero: dos espacios y sus saltos de línea."""
    raw = path.read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    return text.replace("\n", newline).encode("utf-8")


def _bump_manifest(root: Path, name: str, version: str) -> tuple[dict, Path, str]:
    """Manifiesto del paquete ya actualizado, su ruta y la versión anterior."""
    path = root / name / "skills.json"
    if not path.is_file():
        raise BumpError("no existe el paquete «%s» (%s)" % (name, path))
    manifest = read_json(path)
    old = str(manifest.get("version") or "")
    new_key, old_key = version_key(version), version_key(old)
    if new_key is None:
        raise BumpError("«%s» no es una versión X.Y.Z" % version)
    if old_key is None:
        raise BumpError("%s declara version %r, que no es X.Y.Z" % (path, old))
    if new_key <= old_key:
        raise BumpError("la versión nueva %s debe ser mayor que %s" % (version, old))
    manifest["version"] = version
    return manifest, path, old


def _skill_files(root: Path, name: str) -> list[Path]:
    """SKILL.md del paquete, fuera de sus tests y de otras carpetas de descarte."""
    package_dir = root / name
    found: list[Path] = []
    for path in sorted(package_dir.glob("**/SKILL.md")):
        relative = path.relative_to(root)
        if SKILL_SKIP_PARTS & set(relative.parts):
            continue
        found.append(path)
    return found


def _bump_skill(path: Path, name: str, version: str) -> bytes:
    """SKILL.md con el `metadata.version` del paquete cambiado."""
    text = path.read_bytes().decode("utf-8")
    match = FRONTMATTER.match(text)
    if match is None:
        raise BumpError("%s no tiene frontmatter" % path)
    block = match.group(1)
    owner = PACKAGE_LINE.search(block)
    if owner is None or owner.group(1) != name:
        raise BumpError("%s no declara «package: %s»" % (path, name))
    line = VERSION_LINE.search(block)
    if line is None:
        raise BumpError("%s no declara metadata.version" % path)

    def replace(found: re.Match) -> str:
        value = found.group(2)
        quote = value[0] if value[0] in "\"'" else ""
        return found.group(1) + quote + version + quote

    updated = VERSION_LINE.sub(replace, block, count=1)
    return text.replace(block, updated, 1).encode("utf-8")


def _bump_index(root: Path, name: str, version: str, bundle: bool) -> tuple[bytes, Path, str]:
    """Índice raíz: entrada del paquete, versión de bundle y fecha."""
    path = root / "skills.json"
    index = read_json(path)
    entry = next(
        (item for item in index.get("packages") or [] if item.get("name") == name),
        None,
    )
    if entry is None:
        raise BumpError("el índice raíz no declara el paquete «%s»" % name)
    current = str(index.get("version") or "")
    bundle_version = next_patch(current) if bundle and version_key(current) else current
    entry["version"] = version
    index["version"] = bundle_version
    index["updated"] = datetime.date.today().isoformat()
    return dump_json(path, index), path, bundle_version


def _bump_marketplace(root: Path, name: str, version: str, bundle_version: str) -> tuple[bytes, Path]:
    """Marketplace: plugin del paquete y versión del catálogo."""
    path = root / MARKETPLACE_PATH
    if not path.is_file():
        raise BumpError("no existe %s" % MARKETPLACE_PATH.as_posix())
    data = read_json(path)
    plugin = next(
        (item for item in data.get("plugins") or [] if item.get("name") == name),
        None,
    )
    if plugin is None:
        raise BumpError("el marketplace no declara el plugin «%s»" % name)
    plugin["version"] = version
    data["version"] = bundle_version
    return dump_json(path, data), path


def plan(root: Path, name: str, version: str, bundle: bool = True) -> tuple[dict[Path, bytes], str]:
    """Bytes nuevos por fichero, sin escribir nada todavía."""
    _, manifest_path, _ = _bump_manifest(root, name, version)
    manifest = read_json(manifest_path)
    manifest["version"] = version
    edits: dict[Path, bytes] = {manifest_path: dump_json(manifest_path, manifest)}

    skills = _skill_files(root, name)
    if not skills:
        raise BumpError("el paquete «%s» no tiene ningún SKILL.md" % name)
    for skill in skills:
        edits[skill] = _bump_skill(skill, name, version)

    index_payload, index_path, bundle_version = _bump_index(root, name, version, bundle)
    edits[index_path] = index_payload

    market_payload, market_path = _bump_marketplace(root, name, version, bundle_version)
    edits[market_path] = market_payload
    return edits, bundle_version


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Sube la versión de un paquete en todos sus sitios.")
    parser.add_argument("package", help="carpeta del paquete, por ejemplo db-architect")
    parser.add_argument("version", help="versión nueva en formato X.Y.Z")
    parser.add_argument("--root", default=str(ROOT), help="raíz del repositorio")
    parser.add_argument(
        "--no-bundle",
        action="store_true",
        help="no sube la versión del índice raíz (no habrá release de bundle)",
    )
    parser.add_argument("--dry-run", action="store_true", help="enseña los cambios sin escribir")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        edits, bundle_version = plan(root, args.package, args.version, not args.no_bundle)
    except BumpError as error:
        print("bump_version: %s" % error, file=sys.stderr)
        return 1

    for path, payload in sorted(edits.items()):
        relative = path.relative_to(root).as_posix()
        if args.dry_run:
            print("cambiaría %s" % relative)
            continue
        path.write_bytes(payload)
        print("actualizado %s" % relative)

    if not args.no_bundle:
        print("bundle %s (%s %s)" % (bundle_version, args.package, args.version))
    return 0


if __name__ == "__main__":
    sys.exit(main())
