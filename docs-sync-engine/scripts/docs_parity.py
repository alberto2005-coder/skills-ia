"""Comprueba la paridad estructural y de cifras entre las mitades ES y EN de un Markdown.

Uso:
    py docs-sync-engine/scripts/docs_parity.py [--docs RUTA ...] [--root RUTA]
        [--json] [--fail-on high|medium|low|none] [--no-audit]

Cada documento bilingüe del repositorio lleva dos mitades (`## 🇪🇸 Español` y
`## 🇬🇧 English`). Este script compara su **forma**, no su prosa: número de
encabezados por nivel, filas de cada tabla, fences de código, anclas internas y
las cifras que ambas mitades afirman (skills, tests, paquetes…). Una sección que
existe en un idioma y falta en el otro, o un recuento que dice 79 en español y
81 en inglés, es documentación rota.

La coherencia con el código no se reimplementa aquí: si existe
`tests/audit_docs.py` en la raíz, se invoca como subproceso (`--no-audit` lo
desactiva). El paquete sigue siendo autónomo: se ejecuta el script de la raíz,
no se importa.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado · 2 ruta
ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SEVERITIES = {"low": 1, "medium": 2, "high": 3}
ES_MARKERS = ("## 🇪🇸 Español", "## Español")
EN_MARKERS = ("## 🇬🇧 English", "## English")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
ANCHOR_LINK = re.compile(r"\]\(#([^)\s]+)\)")
NUMBER_CLAIM = re.compile(
    r"(\d+)\s+(skills?|paquetes?|packages?|tests?|pruebas?|sub-skills?|subskills?|scripts?)",
    re.IGNORECASE,
)
SLUG_STRIP = re.compile(r"[^\w\s-]")
SKIP_PARTS = {"__pycache__", ".venv", ".git", "node_modules"}


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def language_blocks(text: str) -> dict[str, list[tuple[int, str]]]:
    """Líneas (número, texto) de cada mitad, o vacío si el documento no es bilingüe."""
    lines = text.splitlines()
    blocks: dict[str, list[tuple[int, str]]] = {"es": [], "en": []}
    current = None
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped in ES_MARKERS:
            current = "es"
            continue
        if stripped in EN_MARKERS:
            current = "en"
            continue
        if stripped.startswith("# ") and current is not None:
            # Un H1 nuevo cierra la mitad aunque no haya marcador de idioma.
            current = None
        if current is not None:
            blocks[current].append((number, line))
    return blocks


def heading_shape(block: list[tuple[int, str]]) -> Counter:
    """Recuento de encabezados por nivel, sin el marcador de idioma."""
    levels = Counter()
    for _, line in block:
        match = HEADING.match(line)
        if match:
            levels[len(match.group(1))] += 1
    return levels


def table_shapes(block: list[tuple[int, str]]) -> list[int]:
    """Filas de datos de cada tabla, en orden de aparición."""
    shapes: list[int] = []
    rows = 0
    for _, line in block:
        if line.lstrip().startswith("|"):
            rows += 1
        elif rows:
            shapes.append(max(rows - 2, 0))
            rows = 0
    if rows:
        shapes.append(max(rows - 2, 0))
    return shapes


def fence_languages(block: list[tuple[int, str]]) -> Counter:
    """Lenguajes de los bloques de código abiertos."""
    languages = Counter()
    inside = False
    for _, line in block:
        match = re.match(r"^\s*(`{3,}|~{3,})\s*([^\s`~]*)", line)
        if not match:
            continue
        if inside:
            inside = False
            continue
        inside = True
        languages[match.group(2).strip().lower() or "none"] += 1
    return languages


def number_claims(block: list[tuple[int, str]]) -> Counter:
    """Cifras con unidad («79 skills», «27 tests») que ambas mitades deben repetir."""
    return Counter(
        f"{match.group(1)} {match.group(2).lower()}"
        for _, line in block
        for match in NUMBER_CLAIM.finditer(line)
    )


def slug(text: str) -> str:
    """Ancla que GitHub genera para un encabezado."""
    text = re.sub(r"`|\*|_", "", text.strip().lower())
    return re.sub(r"\s+", "-", SLUG_STRIP.sub("", text))


def anchors(block: list[tuple[int, str]]) -> set[str]:
    """Anclas disponibles en la mitad, con el sufijo -1, -2 de los repetidos."""
    seen: dict[str, int] = {}
    found: set[str] = set()
    for _, line in block:
        match = HEADING.match(line)
        if not match:
            continue
        base = slug(match.group(2))
        count = seen.get(base, 0)
        seen[base] = count + 1
        found.add(base if count == 0 else "%s-%d" % (base, count))
    return found


def _first_line(block: list[tuple[int, str]]) -> int:
    return block[0][0] if block else 0


def compare_shape(path: Path, name: str) -> list[dict]:
    """Hallazgos de forma entre las dos mitades de un documento."""
    text = path.read_text(encoding="utf-8", errors="replace")
    blocks = language_blocks(text)
    if not blocks["es"] or not blocks["en"]:
        return [{
            "file": name, "line": 1, "rule": "secciones-idioma", "severity": "high",
            "message": "faltan las mitades «## 🇪🇸 Español» y «## 🇬🇧 English»",
            "fix": "Añade ambas secciones: el resto de comprobaciones necesita las dos.",
        }]

    findings: list[dict] = []
    pairs = (
        ("forma-encabezados", "medium", heading_shape),
        ("forma-fences", "low", fence_languages),
        ("cifras", "high", number_claims),
    )
    for rule, severity, extract in pairs:
        es_value, en_value = extract(blocks["es"]), extract(blocks["en"])
        if es_value != en_value:
            findings.append({
                "file": name, "line": _first_line(blocks["en"]), "rule": rule, "severity": severity,
                "message": "ES declara %s y EN %s" % (_render(es_value), _render(en_value)),
                "fix": "Iguala las dos mitades: lo que falta en una es un desfase, no una traducción.",
            })

    es_tables, en_tables = table_shapes(blocks["es"]), table_shapes(blocks["en"])
    if es_tables != en_tables:
        findings.append({
            "file": name, "line": _first_line(blocks["en"]), "rule": "forma-tablas", "severity": "medium",
            "message": "tablas ES %s y EN %s (filas de datos)" % (es_tables, en_tables),
            "fix": "Añade o retira la fila que sobra; las tablas se leen en paralelo.",
        })

    for label, block in (("ES", blocks["es"]), ("EN", blocks["en"])):
        available = anchors(block)
        for number, line in block:
            for target in ANCHOR_LINK.findall(line):
                if target not in available:
                    findings.append({
                        "file": name, "line": number, "rule": "ancla-rota", "severity": "medium",
                        "message": "%s: #%s no apunta a ningún encabezado" % (label, target),
                        "fix": "Apunta al encabezado real o elimina el enlace.",
                    })
    return findings


def _render(value) -> str:
    """Representación estable de un Counter o una lista para el mensaje."""
    if isinstance(value, Counter):
        return json.dumps(dict(sorted(value.items())), ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)


def audit_findings(root: Path) -> list[dict]:
    """Hallazgos de `tests/audit_docs.py` de la raíz, si existe, como subproceso."""
    script = root / "tests" / "audit_docs.py"
    if not script.is_file():
        return []
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--root", str(root)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(root),
        )
    except OSError as error:
        return [{
            "file": "tests/audit_docs.py", "line": 0, "rule": "drift-codigo", "severity": "high",
            "message": "no se pudo ejecutar audit_docs.py: %s" % error,
            "fix": "Comprueba que el intérprete y la ruta del script funcionan.",
        }]
    if result.returncode not in (0, 1):
        return [{
            "file": "tests/audit_docs.py", "line": 0, "rule": "drift-codigo", "severity": "high",
            "message": "audit_docs.py salió con %d: %s" % (result.returncode, result.stderr.strip()[:200]),
            "fix": "Revisa la invocación: la raíz pasada debe ser la del repositorio.",
        }]
    return [
        {
            "file": "docs/", "line": 0, "rule": "drift-codigo", "severity": "medium",
            "message": line.strip()[2:].strip(),
            "fix": "Corrige el desfase que señala la auditoría de documentación.",
        }
        for line in result.stdout.splitlines()
        if line.strip().startswith("- ")
    ]


def targets(root: Path, docs: list[str] | None) -> list[Path]:
    """Documentos a comparar: los pedidos o README más docs/*.md."""
    if docs:
        found = []
        for item in docs:
            path = Path(item)
            path = path if path.is_absolute() else root / path
            if path.is_dir():
                found.extend(sorted(path.glob("*.md")))
            elif path.is_file():
                found.append(path)
            else:
                raise FileNotFoundError(str(path))
        return found
    candidates = [root / "README.md"] + sorted((root / "docs").glob("*.md"))
    return [path for path in candidates if path.is_file()]


def findings_for(root: Path, paths: list[Path], with_audit: bool) -> list[dict]:
    """Todos los hallazgos de forma más los de la auditoría de la raíz."""
    findings: list[dict] = []
    for path in paths:
        findings.extend(compare_shape(path, _relative(path, root)))
    if with_audit:
        findings.extend(audit_findings(root))
    return findings


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _summary(findings: list[dict]) -> dict:
    counts = Counter(item["severity"] for item in findings)
    return {
        "total": len(findings),
        "high": counts.get("high", 0),
        "medium": counts.get("medium", 0),
        "low": counts.get("low", 0),
    }


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Paridad ES/EN entre las dos mitades de la documentación.")
    parser.add_argument("--docs", nargs="+", help="Markdown o carpetas; por defecto README y docs/*.md")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent.parent.parent),
                        help="Raíz del repositorio")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument("--fail-on", default="high", choices=["high", "medium", "low", "none"])
    parser.add_argument("--no-audit", action="store_true", help="No invoca tests/audit_docs.py")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        paths = targets(root, args.docs)
    except FileNotFoundError as error:
        print("no existe la ruta: %s" % error, file=sys.stderr)
        return 2

    findings = findings_for(root, paths, not args.no_audit)
    document = {
        "source": "docs_parity",
        "root": str(root),
        "files": len(paths),
        "summary": _summary(findings),
        "findings": findings,
    }

    if args.json:
        print(json.dumps(document, indent=2, ensure_ascii=False))
    else:
        for item in findings:
            print("%s:%s [%s] %s: %s" % (item["file"], item["line"], item["severity"], item["rule"], item["message"]))
        print("paridad: %d ficheros, %d hallazgo(s)" % (len(paths), len(findings)))

    if args.fail_on == "none" or not findings:
        return 0
    threshold = SEVERITIES[args.fail_on]
    return 1 if any(SEVERITIES[item["severity"]] >= threshold for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
