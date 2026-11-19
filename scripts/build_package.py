"""Empaqueta un paquete de skills en un .zip determinista y lo valida.

Uso:
    py scripts/build_package.py <paquete> [--root RUTA] [--out dist]
    py scripts/build_package.py --all [--out dist]

El zip contiene el paquete completo bajo `<paquete>/` y un `manifest.json` en
la raíz con la versión, el commit y las skills incluidas. Las entradas van
ordenadas y con fecha fija, así que dos builds del mismo árbol dan el mismo
SHA256.

Antes de dar el artefacto por bueno se descomprime en un directorio temporal y
se le pasa `tests/lint_frontmatter.py`; si falla cualquier comprobación, el zip
se borra y el script sale con error.

Código de salida: 0 correcto · 1 paquete o validación inválidos · 2 uso.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_PARTS = {
    "tests", "__pycache__", ".ruff_cache", ".pytest_cache", ".venv", ".git", "output", "reports",
}
EXCLUDED_SUFFIXES = {
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".log", ".zip", ".tar", ".gz",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".woff", ".woff2", ".ttf",
}
MANIFEST_NAME = "manifest.json"
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
CHUNK = 1 << 16


class BuildError(RuntimeError):
    """El paquete no se puede empaquetar o el artefacto no pasa la validación."""


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def load_package(root: Path, name: str) -> tuple[Path, dict]:
    """Carpeta y manifiesto del paquete, con `version` obligatoria."""
    package_dir = root / name
    manifest_path = package_dir / "skills.json"
    if not manifest_path.is_file():
        raise BuildError("no existe el manifiesto %s" % manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise BuildError("%s tiene JSON inválido: %s" % (manifest_path, error))
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise BuildError("%s no declara «version»" % manifest_path)
    return package_dir, manifest


def ensure_text(relative: str, data: bytes) -> None:
    """Rechaza binarios: NUL o bytes que no sean UTF-8."""
    if b"\x00" in data:
        raise BuildError("%s no es un fichero de texto (contiene NUL)" % relative)
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        raise BuildError("%s no es un fichero de texto (UTF-8 inválido)" % relative)


def collect_entries(package_dir: Path) -> list[tuple[str, bytes]]:
    """[(ruta dentro del zip, contenido)] ordenado y sin caches, tests ni binarios."""
    entries: list[tuple[str, bytes]] = []
    for path in package_dir.rglob("*"):
        if path.is_dir():
            continue
        relative = path.relative_to(package_dir)
        if EXCLUDED_PARTS & set(relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        data = path.read_bytes()
        name = "%s/%s" % (package_dir.name, relative.as_posix())
        ensure_text(name, data)
        entries.append((name, data))
    if not entries:
        raise BuildError("el paquete %s no tiene ficheros empaquetables" % package_dir.name)
    return sorted(entries, key=lambda entry: entry[0])


def archive_manifest(manifest: dict, commit: str, file_count: int) -> bytes:
    """`manifest.json` del zip: versión, commit y skills incluidas."""
    skills = [entry.get("name") for entry in manifest.get("skills") or [] if entry.get("name")]
    payload = {
        "format": "skills-ia-package-archive",
        "format_version": "1.0",
        "package": manifest.get("name"),
        "version": manifest.get("version"),
        "commit": commit,
        "file_count": file_count,
        "skills": skills,
    }
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _zip_info(name: str) -> zipfile.ZipInfo:
    """Entrada con fecha fija, permisos fijos y sistema Unix, para que sea reproducible."""
    info = zipfile.ZipInfo(name, date_time=ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    info.create_system = 3
    return info


def write_archive(zip_path: Path, entries: list[tuple[str, bytes]]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in entries:
            archive.writestr(_zip_info(name), data)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_archive(zip_path: Path, linter_path: Path) -> None:
    """Descomprime el zip y le pasa el lint de frontmatter sobre el árbol extraído."""
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(target)
        result = subprocess.run(
            [sys.executable, str(linter_path), "--root", str(target)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    if result.returncode == 0:
        return
    lines = [line.strip() for line in (result.stdout or result.stderr).splitlines() if line.strip()]
    raise BuildError("el zip no pasa lint_frontmatter: %s" % " | ".join(lines[:6]))


def resolve_commit(root: Path) -> str:
    """`GITHUB_SHA` si existe; si no, HEAD; si no hay git, «unknown»."""
    from_env = os.environ.get("GITHUB_SHA", "").strip()
    if from_env:
        return from_env
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(root), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except OSError:
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def write_checksum(checksum_path: Path, digest: str, zip_name: str) -> None:
    """Fichero estilo `sha256sum`: `<hash>  <nombre>`."""
    with open(str(checksum_path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("%s  %s\n" % (digest, zip_name))


def build_package(
    root: Path, name: str, out_dir: Path, commit: str, linter_path: Path | None = None
) -> tuple[Path, str]:
    """Construye y valida el zip; ante cualquier fallo no deja artefactos."""
    linter = linter_path or ROOT / "tests" / "lint_frontmatter.py"
    package_dir, manifest = load_package(root, name)
    entries = collect_entries(package_dir)
    entries.append((MANIFEST_NAME, archive_manifest(manifest, commit, len(entries))))
    entries.sort(key=lambda entry: entry[0])

    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / ("%s-%s.zip" % (name, manifest["version"]))
    checksum_path = out_dir / ("%s-%s.zip.sha256" % (name, manifest["version"]))
    try:
        write_archive(zip_path, entries)
        digest = sha256_of(zip_path)
        write_checksum(checksum_path, digest, zip_path.name)
        validate_archive(zip_path, linter)
    except Exception:
        zip_path.unlink(missing_ok=True)
        checksum_path.unlink(missing_ok=True)
        raise
    return zip_path, digest


def package_names(root: Path) -> list[str]:
    """Paquetes declarados en el índice raíz."""
    index_path = root / "skills.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BuildError("no se pudo leer %s: %s" % (index_path, error))
    names = [entry.get("path") or entry.get("name") for entry in index.get("packages") or []]
    return [name for name in names if name]


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Empaqueta y valida un paquete de skills.")
    parser.add_argument("package", nargs="?", help="nombre del paquete")
    parser.add_argument("--all", action="store_true", help="empaqueta todos los del índice")
    parser.add_argument("--root", default=str(ROOT), help="raíz del repositorio")
    parser.add_argument("--out", default="dist", help="directorio de salida")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    out_dir = Path(args.out) if Path(args.out).is_absolute() else root / args.out
    if not args.all and not args.package:
        parser.error("indica un paquete o usa --all")

    try:
        names = package_names(root) if args.all else [args.package]
    except BuildError as error:
        print("build_package: %s" % error, file=sys.stderr)
        return 2

    commit = resolve_commit(root)
    failures = 0
    for name in names:
        try:
            zip_path, digest = build_package(root, name, out_dir, commit)
        except BuildError as error:
            failures += 1
            print("ERROR %s: %s" % (name, error), file=sys.stderr)
            continue
        print("%s  %s  (%d bytes, commit %s)" % (digest, zip_path.name, zip_path.stat().st_size, commit[:12]))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
