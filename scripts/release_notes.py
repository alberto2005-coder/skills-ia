"""Compone la descripción bilingüe de una release.

Uso:
    py scripts/release_notes.py --version 2.1.1 --package db-architect --input commits.txt
    py scripts/release_notes.py --version 5.1.2 --bundle --input commits.txt

Reutiliza el agrupado de `docs-sync-engine/scripts/changelog_gen.py` (una línea
por commit, convencional) y lo pinta con una cabecera y unos títulos en español
e inglés. La lista de cambios es única: los asuntos ya van en inglés por la
convención de commits del repo, así que duplicarlos solo alargaría la release.

Código de salida: 0 generado · 2 entrada ilegible.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = "alberto2005-coder/skills-ia"
TITLES_EN = {
    "feat": "New",
    "fix": "Fixes",
    "perf": "Performance",
    "refactor": "Refactor",
    "docs": "Docs",
    "test": "Tests",
    "build": "Build",
    "ci": "CI",
    "chore": "Chores",
}


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def load_generator(root: Path):
    """Módulo de agrupado del paquete `docs-sync-engine`."""
    sys.path.insert(0, str(root / "docs-sync-engine" / "scripts"))
    import changelog_gen  # noqa: PLC0415  (depende del sys.path de arriba)

    return changelog_gen


def package_header(package: str, version: str) -> list[str]:
    """Cabecera de una release de paquete."""
    return [
        "## %s v%s" % (package, version),
        "",
        "**Instalación / Installation:** `/plugin install %s@skills-ia`" % package,
        "",
        "Paquete `%s` en la versión **%s** — cambios incluidos en este release."
        % (package, version),
        "Package `%s` at version **%s** — changes shipped in this release." % (package, version),
        "",
        "**Verifica el archivo / Verify the archive:** `sha256sum -c SHA256SUMS`",
        "",
    ]


def bundle_header(root: Path, version: str) -> list[str]:
    """Cabecera del release que agrupa todos los paquetes."""
    index = json.loads((root / "skills.json").read_text(encoding="utf-8"))
    packages = index.get("packages") or []
    skills = index.get("skills_total")
    return [
        "## Catálogo completo v%s / Full catalog v%s" % (version, version),
        "",
        "**Instalación / Installation:** `/plugin marketplace add %s`" % MARKETPLACE,
        "",
        "Los %d paquetes del catálogo (%s skills) con sus zips y `SHA256SUMS`."
        % (len(packages), skills),
        "All %d catalog packages (%s skills) with their zips and `SHA256SUMS`."
        % (len(packages), skills),
        "",
    ]


def sections(grouped: dict[str, list[str]], others: list[str], titles: list[tuple[str, str]]) -> list[str]:
    """Cambios agrupados, con el título en los dos idiomas."""
    lines: list[str] = []
    for kind, title_es in titles:
        entries = grouped.get(kind) or []
        if not entries:
            continue
        title_en = TITLES_EN.get(kind, kind)
        heading = title_es if title_es == title_en else "%s / %s" % (title_es, title_en)
        lines.append("### %s" % heading)
        lines.append("")
        lines += ["- %s" % entry for entry in sorted(entries)]
        lines.append("")
    if others:
        lines.append("### Otros / Other")
        lines.append("")
        lines += ["- %s" % entry for entry in sorted(others)]
        lines.append("")
    if not any(grouped.values()) and not others:
        lines += ["_Sin cambios / No changes._", ""]
    return lines


def render(root: Path, version: str, commits: list[str], package: str | None) -> str:
    """Documento completo: cabecera bilingüe más los cambios agrupados."""
    generator = load_generator(root)
    grouped, others = generator.group(commits)
    header = package_header(package, version) if package else bundle_header(root, version)
    return "\n".join(header + sections(grouped, others, generator.SECTIONS))


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Descripción bilingüe de una release.")
    parser.add_argument("--version", required=True, help="versión de la entrega")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--package", help="paquete del release")
    target.add_argument("--bundle", action="store_true", help="release del catálogo completo")
    parser.add_argument("--input", required=True, help="fichero con un commit por línea")
    parser.add_argument("--out", help="fichero de salida (por defecto, stdout)")
    parser.add_argument("--root", default=str(ROOT), help="raíz del repositorio")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        raw = Path(args.input).read_text(encoding="utf-8")
    except OSError as error:
        print("no se pudo leer %s: %s" % (args.input, error), file=sys.stderr)
        return 2
    commits = [line.strip() for line in raw.splitlines() if line.strip()]

    package = args.package or None
    document = render(root, args.version, commits, package)
    if args.out:
        Path(args.out).write_text(document, encoding="utf-8")
        print("escrito %s con %d commits" % (args.out, len(commits)))
    else:
        print(document)
    return 0


if __name__ == "__main__":
    sys.exit(main())
