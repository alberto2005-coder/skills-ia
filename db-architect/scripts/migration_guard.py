"""Clasifica el riesgo de una migración antes de aplicarla, sin red.

Uso:
    py db-architect/scripts/migration_guard.py --path <ruta> [--json] [--fail-on critical]

Niveles: `critical` para lo que bloquea tablas o destruye datos, `medium` para
lo que puede tardar o dejar la migración sin vuelta atrás.

Código de salida: 0 sin hallazgos en el umbral · 1 umbral superado · 2 ruta
ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from db_util import iter_files

SEVERITIES = {"info": 1, "medium": 2, "warning": 2, "critical": 3}
RULES = (
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "critical", "drop-table",
     "DROP TABLE destruye datos y no tiene vuelta atrás"),
    (re.compile(r"\bDROP\s+COLUMN\b", re.I), "critical", "drop-column",
     "DROP COLUMN rompe lectores antiguos durante el despliegue"),
    (re.compile(r"\bTRUNCATE\b", re.I), "critical", "truncate",
     "TRUNCATE vacía la tabla sin posibilidad de recuperación"),
    (re.compile(r"ALTER\s+COLUMN\s+\w+\s+(?:SET\s+DATA\s+)?TYPE\b", re.I), "critical", "cambio-de-tipo",
     "cambiar el tipo reescribe la tabla y bloquea escrituras"),
    (re.compile(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?!CONCURRENTLY)", re.I), "medium", "indice-sin-concurrently",
     "crear el índice sin CONCURRENTLY bloquea la tabla"),
    (re.compile(r"ADD\s+COLUMN\s+\w+[^;]*DEFAULT\s+\S+[^;]*NOT\s+NULL", re.I), "medium",
     "columna-not-null-con-default",
     "ADD COLUMN NOT NULL con DEFAULT reescribe la tabla en motores antiguos"),
)
ROLLBACK_MARKERS = ("downgrade(", "downgrade (", "def downgrade")
ROLLBACK_LINE = re.compile(r"^\s*(?:--\s*)?DOWN\b", re.I | re.M)


def rollback_index(text: str) -> int:
    """Posición donde empieza la sección de reversión, o -1 si no existe."""
    match = ROLLBACK_LINE.search(text)
    if match:
        return match.start()
    lowered = text.lower()
    positions = [lowered.find(marker) for marker in ROLLBACK_MARKERS if marker in lowered]
    return min(positions) if positions else -1


def scan_file(path: Path) -> list[dict]:
    # Un .sql en latin-1 reventaba con UnicodeDecodeError en vez de analizarse.
    text = path.read_text(encoding="utf-8", errors="replace")
    split = rollback_index(text)
    forward = text if split < 0 else text[:split]
    findings = []
    for pattern, severity, rule, message in RULES:
        for match in pattern.finditer(forward):
            line = text.count("\n", 0, match.start()) + 1
            line_text = text.splitlines()[line - 1].strip()
            if line_text.startswith(("--", "#")):
                continue
            findings.append({
                "file": path.as_posix(),
                "line": line,
                "rule": rule,
                "severity": severity,
                "message": message,
            })
    if split < 0:
        findings.append({
            "file": path.as_posix(),
            "line": 1,
            "rule": "sin-reversion",
            "severity": "medium",
            "message": "la migración no declara DOWN/downgrade(): no se puede revertir",
        })
    findings.sort(key=lambda item: (item["line"], item["rule"]))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Guardián de riesgo de migraciones.")
    parser.add_argument("--path", required=True, help="fichero o directorio de migraciones")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="critical",
                        choices=["info", "medium", "warning", "critical", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    files = [target] if target.is_file() else (
        iter_files(target, {".py"}) + iter_files(target, {".sql"})
    )
    findings = [item for path in files for item in scan_file(path)]
    findings.sort(key=lambda item: (item["file"], item["line"], item["rule"]))
    by_severity = {name: sum(1 for item in findings if item["severity"] == name) for name in SEVERITIES}

    if args.json:
        print(json.dumps({"files": len(files), "findings": findings, "by_severity": by_severity},
                         indent=2, ensure_ascii=False))
    else:
        for item in findings:
            print(f"{item['file']}:{item['line']} [{item['severity']}] {item['rule']}: {item['message']}")
        print(f"ficheros: {len(files)} · hallazgos: {len(findings)}")

    if args.fail_on == "none":
        return 0
    threshold = SEVERITIES[args.fail_on]
    return 1 if any(SEVERITIES[item["severity"]] >= threshold for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
