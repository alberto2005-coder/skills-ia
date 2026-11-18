"""Compara el esquema declarado con el que resulta de reproducir las migraciones.

Uso:
    py db-architect/scripts/drift.py --schema schema.sql --migrations migrations/
        [--json] [--fail-on drift]

Modelo textual, sin motor: aplica en orden alfabético las migraciones sobre el
esquema vacío y compara tablas, columnas y tipos con el `.sql` declarado. Lo que
solo está en uno de los dos lados se reporta como deriva, con su nombre.

Código de salida: 0 sin deriva · 1 deriva detectada · 2 ruta ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_PARTS = {"__pycache__", ".venv", ".git"}
CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"'`]?(\w+)[\"'`]?\s*\((.*?)\)\s*(?:;|$)",
    re.S | re.I,
)
ADD_COLUMN = re.compile(
    r"ALTER\s+TABLE\s+[\"'`]?(\w+)[\"'`]?\s+ADD\s+(?:COLUMN\s+)?[\"'`]?(\w+)[\"'`]?\s+([A-Za-z]+(?:\s*\([^)]*\))?)",
    re.I,
)
DROP_COLUMN = re.compile(r"ALTER\s+TABLE\s+[\"'`]?(\w+)[\"'`]?\s+DROP\s+(?:COLUMN\s+)?[\"'`]?(\w+)", re.I)
ALTER_TYPE = re.compile(
    r"ALTER\s+TABLE\s+[\"'`]?(\w+)[\"'`]?\s+ALTER\s+COLUMN\s+[\"'`]?(\w+)[\"'`]?\s+(?:SET\s+DATA\s+)?TYPE\s+([A-Za-z]+(?:\s*\([^)]*\))?)",
    re.I,
)
RENAME_COLUMN = re.compile(
    r"ALTER\s+TABLE\s+[\"'`]?(\w+)[\"'`]?\s+RENAME\s+(?:COLUMN\s+)?[\"'`]?(\w+)[\"'`]?\s+TO\s+[\"'`]?(\w+)",
    re.I,
)
RENAME_TABLE = re.compile(
    r"ALTER\s+TABLE\s+[\"'`]?(\w+)[\"'`]?\s+RENAME\s+TO\s+[\"'`]?(\w+)", re.I)
DROP_TABLE = re.compile(r"DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?[\"'`]?(\w+)", re.I)
CONSTRAINT_WORDS = ("primary key", "foreign key", "unique", "check", "constraint")
TYPE_STOP = {"not", "null", "default", "primary", "references", "unique", "check", "constraint"}


def split_top_level(text: str) -> list[str]:
    """Separa por comas ignorando las que están dentro de paréntesis."""
    parts, depth, current = [], 0, []
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [part.strip() for part in parts if part.strip()]


def column_type(raw_type: str) -> str:
    """Tipo normalizado: se detiene en la primera palabra de restricción."""
    pieces = []
    for word in raw_type.split():
        if word.lower() in TYPE_STOP:
            break
        pieces.append(word)
    if not pieces:
        return "unknown"
    return re.sub(r"\s+", "", " ".join(pieces).lower())


def apply_create(tables: dict, name: str, block: str) -> None:
    columns = {}
    for definition in split_top_level(block):
        lowered = definition.lower()
        if lowered.startswith(CONSTRAINT_WORDS):
            continue
        match = re.match(r"[\"'`]?(\w+)[\"'`]?\s+(.+)", definition, re.S)
        if not match:
            continue
        columns[match.group(1).lower()] = column_type(match.group(2))
    tables[name.lower()] = columns


def build_model(text: str, tables: dict | None = None) -> dict:
    tables = {} if tables is None else tables
    for name, block in CREATE_TABLE.findall(text):
        apply_create(tables, name, block)
    for old, new in RENAME_TABLE.findall(text):
        if old.lower() in tables:
            tables[new.lower()] = tables.pop(old.lower())
    for table, old, new in RENAME_COLUMN.findall(text):
        columns = tables.get(table.lower())
        if columns and old.lower() in columns:
            columns[new.lower()] = columns.pop(old.lower())
    for table, column in DROP_COLUMN.findall(text):
        tables.get(table.lower(), {}).pop(column.lower(), None)
    for table, column, new_type in ALTER_TYPE.findall(text):
        columns = tables.get(table.lower())
        if columns and column.lower() in columns:
            columns[column.lower()] = re.sub(r"\s+", "", new_type.lower())
    for table, column, new_type in ADD_COLUMN.findall(text):
        tables.setdefault(table.lower(), {})[column.lower()] = re.sub(r"\s+", "", new_type.lower())
    for table in DROP_TABLE.findall(text):
        tables.pop(table.lower(), None)
    return tables


def migration_files(folder: Path) -> list[Path]:
    if folder.is_file():
        return [folder]
    return sorted(item for item in folder.rglob("*") if item.is_file()
                  and item.suffix in {".sql", ".py"} and not SKIP_PARTS & set(item.parts))


def diff(declared: dict, replayed: dict) -> list[dict]:
    findings = []

    def add(rule: str, severity: str, target: str, message: str) -> None:
        findings.append({"target": target, "rule": rule, "severity": severity, "message": message})

    for table in sorted(set(declared) - set(replayed)):
        add("tabla-solo-en-esquema", "high", table,
            f"la tabla {table} está declarada pero ninguna migración la crea")
    for table in sorted(set(replayed) - set(declared)):
        add("tabla-solo-en-migraciones", "high", table,
            f"la migración crea {table} y el esquema declarado no la tiene")
    for table in sorted(set(declared) & set(replayed)):
        for column in sorted(set(declared[table]) - set(replayed[table])):
            add("columna-solo-en-esquema", "medium", f"{table}.{column}",
                f"{table}.{column} está en el esquema y no en las migraciones")
        for column in sorted(set(replayed[table]) - set(declared[table])):
            add("columna-solo-en-migraciones", "medium", f"{table}.{column}",
                f"{table}.{column} nace de las migraciones y no está en el esquema")
        for column in sorted(set(declared[table]) & set(replayed[table])):
            if declared[table][column] != replayed[table][column]:
                add("tipo-distinto", "high", f"{table}.{column}",
                    f"{table}.{column}: esquema {declared[table][column]}, "
                    f"migraciones {replayed[table][column]}")
    findings.sort(key=lambda item: (item["target"], item["rule"]))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deriva entre esquema declarado y migraciones.")
    parser.add_argument("--schema", required=True, help="fichero .sql con el esquema declarado")
    parser.add_argument("--migrations", required=True, help="carpeta o fichero de migraciones")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="drift", choices=["drift", "none"])
    args = parser.parse_args(argv)

    schema_path, migrations_path = Path(args.schema), Path(args.migrations)
    if not schema_path.exists() or not migrations_path.exists():
        print("ruta inexistente")
        return 2

    declared = build_model(schema_path.read_text(encoding="utf-8", errors="replace"))
    replayed: dict = {}
    files = migration_files(migrations_path)
    for path in files:
        build_model(path.read_text(encoding="utf-8", errors="replace"), replayed)

    findings = diff(declared, replayed)
    by_severity = {
        "medium": sum(1 for item in findings if item["severity"] == "medium"),
        "high": sum(1 for item in findings if item["severity"] == "high"),
    }

    if args.json:
        print(json.dumps({
            "schema_tables": len(declared),
            "migration_tables": len(replayed),
            "migrations": len(files),
            "findings": findings,
            "by_severity": by_severity,
        }, indent=2, ensure_ascii=False))
    else:
        for item in findings:
            print(f"[{item['severity']}] {item['rule']} {item['target']}: {item['message']}")
        print(f"tablas: esquema {len(declared)} · migraciones {len(replayed)} · deriva: {len(findings)}")

    if args.fail_on == "none":
        return 0
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
