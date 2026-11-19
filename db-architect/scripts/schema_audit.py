"""Audita esquemas SQL con SQLite en memoria, sin tocar bases reales.

Uso:
    py db-architect/scripts/schema_audit.py --path <ruta> [--json] [--fail-on high]

Valida la sintaxis con `sqlite3` sobre `:memory:` y detecta tablas sin clave
primaria y claves foráneas sin índice, que son las dos causas de consultas
lentas y migraciones caras.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado · 2 ruta
ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from db_util import iter_files

SEVERITIES = {"low": 1, "medium": 2, "high": 3}
TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"'`]?(\w+)[\"'`]?\s*\((.*?)\)\s*;",
    re.S | re.I,
)
INDEX = re.compile(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+\w+\s+ON\s+[\"'`]?(\w+)[\"'`]?\s*\(([^)]*)\)",
    re.I,
)
FOREIGN_KEY = re.compile(r"FOREIGN\s+KEY\s*\(([^)]*)\)", re.I)
REFERENCES = re.compile(r"^\s*[\"'`]?(\w+)[\"'`]?\s+[^,]*REFERENCES\s+", re.I | re.M)


def _line_of(text: str, token: str) -> int:
    position = text.lower().find(token.lower())
    if position < 0:
        return 1
    return text.count("\n", 0, position) + 1


def _columns(raw: str) -> list[str]:
    return [item.strip().strip("\"'`") for item in raw.split(",") if item.strip()]


def index_sql(table: str, column: str) -> str:
    """El `CREATE INDEX` que el gate de salida promete para cada FK."""
    return f"CREATE INDEX idx_{table}_{column} ON {table} ({column});"


def scan_sql(path: Path, text: str) -> list[dict]:
    findings: list[dict] = []

    def add(rule: str, severity: str, message: str, table: str, fix: str = "") -> None:
        findings.append({
            "file": path.as_posix(),
            "line": _line_of(text, f"create table {table}"),
            "table": table,
            "rule": rule,
            "severity": severity,
            "message": message,
            "fix": fix,
        })

    try:
        connection = sqlite3.connect(":memory:")
        connection.executescript(text)
        connection.close()
    except sqlite3.Error as error:
        findings.append({
            "file": path.as_posix(),
            "line": 1,
            "table": "",
            "rule": "sql-invalido",
            "severity": "high",
            "message": f"SQLite no puede ejecutar el esquema: {error}",
        })
        return findings

    indexed: dict[str, set[str]] = {}
    for table, columns in INDEX.findall(text):
        indexed.setdefault(table, set()).update(_columns(columns))

    for table, block in TABLE.findall(text):
        if "primary key" not in block.lower():
            add("tabla-sin-primary-key", "medium",
                f"la tabla {table} no declara PRIMARY KEY", table)
        for raw in FOREIGN_KEY.findall(block):
            for column in _columns(raw):
                if column not in indexed.get(table, set()):
                    add("fk-sin-indice", "medium",
                        f"la clave foránea {table}.{column} no tiene índice; "
                        f"propuesto: {index_sql(table, column)}", table,
                        fix=index_sql(table, column))
        for column in REFERENCES.findall(block):
            if column not in indexed.get(table, set()):
                add("fk-sin-indice", "medium",
                    f"la clave foránea {table}.{column} no tiene índice; "
                    f"propuesto: {index_sql(table, column)}", table,
                    fix=index_sql(table, column))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Auditoría de esquemas SQL en memoria.")
    parser.add_argument("--path", required=True, help="fichero .sql o directorio")
    parser.add_argument("--json", action="store_true")
    # Las reglas emiten `medium` y `high`: `low` era una opción inalcanzable.
    parser.add_argument("--fail-on", default="high", choices=["medium", "high", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    files = iter_files(target, {".sql"})
    findings = [item for path in files
                for item in scan_sql(path, path.read_text(encoding="utf-8", errors="replace"))]
    findings.sort(key=lambda item: (item["file"], item["line"], item["rule"], item["table"]))
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
