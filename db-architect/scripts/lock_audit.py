"""Detecta operaciones de migración que bloquean la tabla o reescriben datos.

Uso:
    py db-architect/scripts/lock_audit.py --path migrations/ [--json] [--fail-on high]

Complementa a `migration_guard.py`, que mira destrucción de datos: aquí el foco
es el bloqueo. Un `ALTER COLUMN ... TYPE` o un `ADD COLUMN NOT NULL DEFAULT`
reescribe la tabla y deja las escrituras esperando; un `CREATE INDEX` sin
`CONCURRENTLY` bloquea mientras construye; un `RENAME` rompe a los clientes que
aún no se han desplegado.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado · 2 ruta
ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITIES = {"low": 1, "medium": 2, "high": 3}
SKIP_PARTS = {"__pycache__", ".venv", ".git"}

RULES = (
    (re.compile(r"ALTER\s+TABLE\s+\S+\s+ALTER\s+COLUMN\s+\S+\s+(?:SET\s+DATA\s+)?TYPE\b", re.I),
     "high", "reescritura-de-tipo",
     "cambiar el tipo reescribe la tabla y bloquea escrituras mientras dura"),
    (re.compile(r"ALTER\s+TABLE\s+\S+\s+ADD\s+(?:COLUMN\s+)?\S+(?=[^;]*\bDEFAULT\b)(?=[^;]*\bNOT\s+NULL\b)", re.I),
     "high", "columna-not-null-con-default",
     "ADD COLUMN NOT NULL con DEFAULT reescribe la tabla en vez de añadir la columna"),
    (re.compile(r"ALTER\s+TABLE\s+\S+\s+ALTER\s+COLUMN\s+\S+\s+SET\s+NOT\s+NULL\b", re.I),
     "high", "set-not-null",
     "SET NOT NULL recorre la tabla entera con bloqueo de escrituras"),
    (re.compile(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?!CONCURRENTLY)", re.I),
     "medium", "indice-sin-concurrently",
     "crear el índice sin CONCURRENTLY bloquea la tabla mientras se construye"),
    (re.compile(r"ALTER\s+TABLE\s+\S+\s+RENAME\s+(?:COLUMN\s+\S+\s+TO\s+\S+|TO\s+\S+)", re.I),
     "medium", "rename-inseguro",
     "renombrar en un paso rompe a los clientes que aún usan el nombre anterior"),
    (re.compile(r"ADD\s+CONSTRAINT\s+\S+\s+FOREIGN\s+KEY\b(?!\s*[^;]*\bNOT\s+VALID\b)", re.I),
     "medium", "fk-sin-not-valid",
     "la clave foránea valida toda la tabla al crearse; usa NOT VALID y valida después"),
    (re.compile(r"ADD\s+CONSTRAINT\s+\S+\s+CHECK\b(?!\s*[^;]*\bNOT\s+VALID\b)", re.I),
     "medium", "check-sin-not-valid",
     "el CHECK recorre toda la tabla al crearse; usa NOT VALID y valida después"),
    (re.compile(r"\bVACUUM\s+FULL\b", re.I),
     "high", "vacuum-full",
     "VACUUM FULL toma un bloqueo exclusivo y reescribe la tabla completa"),
    (re.compile(r"\bDELETE\s+FROM\s+\S+\s*$", re.I | re.M),
     "low", "delete-sin-where",
     "un DELETE sin WHERE deja filas muertas que luego exigen VACUUM"),
)


def statements(path: Path) -> list[tuple[int, str]]:
    """Devuelve (línea inicial, sentencia) ignorando comentarios de línea."""
    text = path.read_text(encoding="utf-8", errors="replace")
    cleaned_lines = []
    for line in text.splitlines():
        if line.lstrip().startswith(("--", "#")):
            cleaned_lines.append("")
        else:
            cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)
    chunks: list[tuple[int, str]] = []
    start = 0
    for match in re.finditer(r";", cleaned):
        chunk = cleaned[start:match.start()]
        if chunk.strip():
            line = cleaned.count("\n", 0, start) + 1
            chunks.append((line, chunk))
        start = match.end()
    tail = cleaned[start:]
    if tail.strip():
        chunks.append((cleaned.count("\n", 0, start) + 1, tail))
    return chunks


def scan_file(path: Path) -> list[dict]:
    findings = []
    for line, statement in statements(path):
        for pattern, severity, rule, message in RULES:
            if not pattern.search(statement):
                continue
            table = ""
            match = re.search(r"(?:ALTER|CREATE\s+INDEX\s+\S+\s+ON|DELETE\s+FROM)\s+([\"'`]?\w+[\"'`]?)",
                              statement, re.I)
            if match:
                table = match.group(1).strip("\"'`")
            findings.append({
                "file": path.as_posix(),
                "line": line,
                "table": table,
                "rule": rule,
                "severity": severity,
                "message": message,
            })
    findings.sort(key=lambda item: (item["file"], item["line"], item["rule"]))
    return findings


def iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(
        item for item in path.rglob("*")
        if item.is_file() and item.suffix in {".sql", ".py"}
        and not SKIP_PARTS & set(item.parts)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bloqueos y reescrituras en migraciones.")
    parser.add_argument("--path", required=True, help="fichero o carpeta de migraciones")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="high", choices=["low", "medium", "high", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    files = iter_files(target)
    findings = [item for path in files for item in scan_file(path)]
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
