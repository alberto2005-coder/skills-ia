"""Auditoría de la documentación contra el repositorio.

Comprueba lo que el markdown no puede comprobar por sí solo:

1. Rutas del repo citadas entre acentos graves que no existen.
2. Flags `--x` documentadas que ningún script del paquete declara.
3. Tablas de paquetes (`README` e índice) contra `skills.json`.
4. Cabeceras «maestro + N» contra el recuento real de skills.
5. Recuentos «N skills» de cada guía contra su manifiesto.
6. Recuentos «N tests» de cada guía contra lo que colecciona pytest.
7. Enlaces internos `#ancla` contra los encabezados del documento.

Uso:
    py tests/audit_docs.py [--root RUTA]

Código de salida: 0 sin desfases · 1 con desfases · 2 uso.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPAN = re.compile(r"`([^`\n]+)`")
FLAG = re.compile(r"(?<![\w-])(--[a-z][a-z0-9-]+)")
ARGUMENT = re.compile(r"""add_argument\(\s*["'](--[a-z0-9-]+)["']""")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)
ANCHOR_LINK = re.compile(r"\]\(#([^)\s]+)\)")
SKILLS_CLAIM = re.compile(r"(\d+)\s+(?:sub-)?skills\b")
TESTS_CLAIM = re.compile(r"(\d+)\s+tests\b")
MASTER_HEADING = re.compile(r"^#### `([a-z0-9-]+)` [—-] maestro \+ (\d+)", re.M)
README_ROW = re.compile(r"\*\*\[`([a-z0-9-]+)`\]\([^)]*\)\*\*[^|]*\|[^|]*\|\s*(\d+)\s*\|")
INDEX_ROW = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|\s*(\d+)\s*\|(.+)$")
SLUG_STRIP = re.compile(r"[^\w\s-]")


def documents(root: Path) -> list[Path]:
    """README, índice y las guías de cada paquete."""
    return [root / "README.md"] + sorted((root / "docs").glob("*.md"))


def load_index(root: Path) -> dict:
    """Índice raíz como dict, o error legible."""
    path = root / "skills.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit("no se pudo leer %s: %s" % (path, error))
    return data


def top_level(root: Path) -> set[str]:
    """Carpetas que pueden abrir una ruta citada: docs, tests, scripts, paquetes."""
    names = {"docs", "tests", "scripts", ".github"}
    names |= {path.name for path in root.iterdir() if (path / "skills.json").is_file()}
    return names


def _path_exists(root: Path, doc: Path, span: str) -> bool:
    span = span.rstrip("/")
    candidates = [root / span, doc.parent / span]
    if doc.parent.name == "docs":
        candidates.append(root / doc.stem / span)
    return any(candidate.exists() for candidate in candidates)


def missing_paths(root: Path) -> list[str]:
    """Rutas del repo citadas en la documentación que no existen."""
    allowed = top_level(root)
    problems = []
    for doc in documents(root):
        for span in SPAN.findall(doc.read_text(encoding="utf-8")):
            span = span.strip()
            if not span or " " in span or "*" in span or "<" in span or span.startswith("-"):
                continue
            if span.split("/")[0] not in allowed:
                continue
            if not _path_exists(root, doc, span):
                problems.append("%s: falta %s" % (doc.relative_to(root).as_posix(), span))
    return sorted(set(problems))


def package_flags(root: Path, package: str) -> set[str]:
    """Flags que declara el argparse de los scripts del paquete."""
    flags: set[str] = set()
    for script in (root / package).glob("**/*.py"):
        if "tests" in script.relative_to(root).parts:
            continue
        flags |= set(ARGUMENT.findall(script.read_text(encoding="utf-8", errors="replace")))
    return flags


def flag_drift(root: Path, index: dict) -> list[str]:
    """Flags documentadas que el paquete no reconoce."""
    problems = []
    for entry in index["packages"]:
        doc = root / "docs" / ("%s.md" % entry["name"])
        if not doc.is_file():
            continue
        known = package_flags(root, entry["name"])
        for flag in sorted(set(FLAG.findall(doc.read_text(encoding="utf-8"))) - known):
            problems.append("%s: %s no existe en los scripts del paquete" % (doc.name, flag))
    return problems


def _row_counts(doc: Path, pattern: re.Pattern) -> dict[str, int]:
    text = doc.read_text(encoding="utf-8")
    return {match.group(1): int(match.group(2)) for match in pattern.finditer(text)}


def table_drift(root: Path, index: dict) -> list[str]:
    """Recuentos de la tabla de paquetes del README y del índice."""
    problems = []
    tables = {
        "README.md": _row_counts(root / "README.md", README_ROW),
        "docs/index.md": _row_counts(root / "docs" / "index.md", INDEX_ROW),
    }
    for name, counts in tables.items():
        for entry in index["packages"]:
            claimed = counts.get(entry["name"])
            if claimed is not None and claimed != entry["skill_count"]:
                problems.append(
                    "%s: «%s» dice %d skills y el índice %d"
                    % (name, entry["name"], claimed, entry["skill_count"])
                )
    return problems


def heading_drift(root: Path, index: dict) -> list[str]:
    """Cabeceras «maestro + N» del README contra el manifiesto."""
    text = (root / "README.md").read_text(encoding="utf-8")
    counts = {entry["name"]: entry["skill_count"] for entry in index["packages"]}
    problems = []
    for name, subs in MASTER_HEADING.findall(text):
        if counts.get(name) != int(subs) + 1:
            problems.append(
                "README.md: «%s» anuncia maestro + %s y son %s skills"
                % (name, subs, counts.get(name))
            )
    return problems


def skill_count_drift(root: Path, index: dict) -> list[str]:
    """Recuentos «N skills» que declara cada guía de paquete."""
    problems = []
    for entry in index["packages"]:
        doc = root / "docs" / ("%s.md" % entry["name"])
        if not doc.is_file():
            problems.append("falta la guía docs/%s.md" % entry["name"])
            continue
        claimed = {int(value) for value in SKILLS_CLAIM.findall(doc.read_text(encoding="utf-8"))}
        if claimed and entry["skill_count"] not in claimed:
            problems.append(
                "%s: declara %s skills y el manifiesto %d"
                % (doc.name, sorted(claimed), entry["skill_count"])
            )
    return problems


def test_count_drift(root: Path) -> list[str]:
    """Recuentos «N tests» que declara cada guía, contra pytest."""
    problems = []
    for doc in sorted((root / "docs").glob("*.md")):
        claimed = {int(value) for value in TESTS_CLAIM.findall(doc.read_text(encoding="utf-8"))}
        claimed = {value for value in claimed if value > 5}
        suite = root / doc.stem / "tests"
        if not claimed or not suite.is_dir():
            continue
        actual = _collected(root, suite)
        if actual is not None and actual not in claimed:
            problems.append("%s: declara %s tests y pytest colecciona %d" % (doc.name, sorted(claimed), actual))
    return problems


def _collected(root: Path, suite: Path) -> int | None:
    """Número de tests que pytest colecciona en una suite."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(suite), "-q", "--collect-only"],
        capture_output=True, text=True, cwd=str(root), encoding="utf-8", errors="replace",
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    return int(match.group(1)) if match else None


def slug(text: str) -> str:
    """Ancla que GitHub genera para un encabezado."""
    text = re.sub(r"`|\*|_", "", text.strip().lower())
    return re.sub(r"\s+", "-", SLUG_STRIP.sub("", text))


def anchors_of(text: str) -> set[str]:
    """Anclas del documento, con el sufijo -1, -2 que GitHub pone a los repetidos."""
    seen: dict[str, int] = {}
    anchors: set[str] = set()
    for _, heading in HEADING.findall(text):
        base = slug(heading)
        count = seen.get(base, 0)
        seen[base] = count + 1
        anchors.add(base if count == 0 else "%s-%d" % (base, count))
    return anchors


def anchor_drift(root: Path) -> list[str]:
    """Enlaces internos que no apuntan a ningún encabezado."""
    problems = []
    for doc in documents(root):
        text = doc.read_text(encoding="utf-8")
        anchors = anchors_of(text)
        for link in sorted({link for link in ANCHOR_LINK.findall(text)} - anchors):
            problems.append("%s: #%s no apunta a ningún encabezado" % (doc.name, link))
    return problems


def audit(root: Path) -> dict[str, list[str]]:
    """Todos los grupos de desfases encontrados."""
    index = load_index(root)
    return {
        "Rutas citadas que no existen": missing_paths(root),
        "Flags documentadas que no existen": flag_drift(root, index),
        "Tablas de paquetes": table_drift(root, index),
        "Cabeceras «maestro + N»": heading_drift(root, index),
        "Recuentos de skills por guía": skill_count_drift(root, index),
        "Recuentos de tests por guía": test_count_drift(root),
        "Enlaces internos": anchor_drift(root),
    }


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Auditoría de la documentación contra el repo.")
    parser.add_argument("--root", default=str(ROOT), help="raíz del repositorio")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not (root / "skills.json").is_file():
        print("audit_docs: %s no parece la raíz del repo" % root, file=sys.stderr)
        return 2

    total = 0
    for title, problems in audit(root).items():
        if not problems:
            continue
        print("== %s ==" % title)
        for problem in problems:
            print("   - %s" % problem)
        total += len(problems)

    if total:
        print("\naudit_docs: %d desfase(s) entre la documentación y el repo" % total)
        return 1
    print("OK: la documentación cuadra con el repositorio.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
