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
from db_util import split_top_level

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


_MODEL_OPERATIONS = (
    (CREATE_TABLE, "create"),
    (RENAME_TABLE, "rename_table"),
    (RENAME_COLUMN, "rename_column"),
    (DROP_COLUMN, "drop_column"),
    (ALTER_TYPE, "alter_type"),
    (ADD_COLUMN, "add_column"),
    (DROP_TABLE, "drop_table"),
)


def build_model(text: str, tables: dict | None = None) -> dict:
    """Aplica las sentencias en el ORDEN DEL TEXTO, no por categorías.

    Aplicar primero todos los CREATE y después todos los DROP daba un modelo
    distinto al real cuando una migración crea, altera y vuelve a borrar: el
    resultado dependía del tipo de sentencia y no de su posición.
    """
    tables = {} if tables is None else tables
    operations: list[tuple[int, str, tuple]] = []
    for pattern, kind in _MODEL_OPERATIONS:
        for match in pattern.finditer(text):
            operations.append((match.start(), kind, match.groups()))

    for _, kind, groups in sorted(operations, key=lambda item: item[0]):
        _OPERATION_APPLIERS[kind](tables, groups)
    return tables


def _op_create(tables: dict, groups: tuple) -> None:
    apply_create(tables, groups[0], groups[1])


def _op_rename_table(tables: dict, groups: tuple) -> None:
    old, new = groups
    if old.lower() in tables:
        tables[new.lower()] = tables.pop(old.lower())


def _op_rename_column(tables: dict, groups: tuple) -> None:
    table, old, new = groups
    columns = tables.get(table.lower())
    if columns and old.lower() in columns:
        columns[new.lower()] = columns.pop(old.lower())


def _op_drop_column(tables: dict, groups: tuple) -> None:
    table, column = groups
    tables.get(table.lower(), {}).pop(column.lower(), None)


def _op_alter_type(tables: dict, groups: tuple) -> None:
    table, column, new_type = groups
    columns = tables.get(table.lower())
    if columns and column.lower() in columns:
        columns[column.lower()] = re.sub(r"\s+", "", new_type.lower())


def _op_add_column(tables: dict, groups: tuple) -> None:
    table, column, new_type = groups
    tables.setdefault(table.lower(), {})[column.lower()] = re.sub(r"\s+", "", new_type.lower())


def _op_drop_table(tables: dict, groups: tuple) -> None:
    tables.pop(groups[0].lower(), None)


_OPERATION_APPLIERS = {
    "create": _op_create,
    "rename_table": _op_rename_table,
    "rename_column": _op_rename_column,
    "drop_column": _op_drop_column,
    "alter_type": _op_alter_type,
    "add_column": _op_add_column,
    "drop_table": _op_drop_table,
}


# --- Migraciones Alembic -----------------------------------------------------
# Un `.py` de Alembic no contiene SQL: aceptarlo en `migration_files` sin
# traducir sus `op.*` declaraba como deriva cada tabla del esquema.

ALEMBIC_CREATE = re.compile(r"op\.create_table\(\s*[\"'](\w+)[\"']\s*,(.*?)\)\s*$", re.S | re.M)
ALEMBIC_ADD = re.compile(r"op\.add_column\(\s*[\"'](\w+)[\"']\s*,(.*?)\)\s*$", re.S | re.M)
ALEMBIC_DROP_COLUMN = re.compile(r"op\.drop_column\(\s*[\"'](\w+)[\"']\s*,\s*[\"'](\w+)[\"']")
ALEMBIC_RENAME_TABLE = re.compile(r"op\.rename_table\(\s*[\"'](\w+)[\"']\s*,\s*[\"'](\w+)[\"']")
ALEMBIC_DROP_TABLE = re.compile(r"op\.drop_table\(\s*[\"'](\w+)[\"']")
ALEMBIC_ALTER = re.compile(
    r"op\.alter_column\(\s*[\"'](\w+)[\"']\s*,\s*[\"'](\w+)[\"'][^)]*?type_\s*=\s*([A-Za-z_.]+(?:\([^)]*\))?)",
    re.S,
)
SQLALCHEMY_COLUMN = re.compile(r"sa\.Column\(\s*[\"'](\w+)[\"']\s*(?:,\s*([A-Za-z_.]+(?:\([^)]*\))?))?")
SA_TYPE_NAMES = {
    "integer": "integer", "biginteger": "bigint", "smallinteger": "smallint",
    "string": "varchar", "text": "text", "boolean": "boolean",
    "datetime": "timestamp", "date": "date", "time": "time",
    "numeric": "numeric", "decimal": "numeric", "float": "float", "uuid": "uuid",
}


def sa_type(raw: str | None) -> str:
    """`sa.String(80)` → `varchar(80)`: el nombre que usa el DDL declarado."""
    if not raw:
        return "unknown"
    match = re.match(r"(?:sa\.)?(\w+)(?:\(([^)]*)\))?", raw.strip())
    if not match:
        return "unknown"
    name = SA_TYPE_NAMES.get(match.group(1).lower(), match.group(1).lower())
    args = re.sub(r"\s+", "", match.group(2) or "")
    return f"{name}({args})" if args else name


def replay_alembic(text: str, tables: dict) -> None:
    """Traduce las operaciones Alembic equivalentes a las de `build_model`."""
    operations: list[tuple[int, str, tuple]] = []
    for match in ALEMBIC_CREATE.finditer(text):
        operations.append((match.start(), "create", match.groups()))
    for match in ALEMBIC_ADD.finditer(text):
        operations.append((match.start(), "add", match.groups()))
    for match in ALEMBIC_DROP_COLUMN.finditer(text):
        operations.append((match.start(), "drop_column", match.groups()))
    for match in ALEMBIC_RENAME_TABLE.finditer(text):
        operations.append((match.start(), "rename_table", match.groups()))
    for match in ALEMBIC_DROP_TABLE.finditer(text):
        operations.append((match.start(), "drop_table", match.groups()))
    for match in ALEMBIC_ALTER.finditer(text):
        operations.append((match.start(), "alter", match.groups()))

    for _, kind, groups in sorted(operations, key=lambda item: item[0]):
        if kind == "create":
            table, body = groups
            columns = {}
            for column, raw_type in SQLALCHEMY_COLUMN.findall(body):
                columns[column.lower()] = sa_type(raw_type)
            tables[table.lower()] = columns
        elif kind == "add":
            table, body = groups
            for column, raw_type in SQLALCHEMY_COLUMN.findall(body):
                tables.setdefault(table.lower(), {})[column.lower()] = sa_type(raw_type)
        elif kind == "drop_column":
            table, column = groups
            tables.get(table.lower(), {}).pop(column.lower(), None)
        elif kind == "rename_table":
            old, new = groups
            if old.lower() in tables:
                tables[new.lower()] = tables.pop(old.lower())
        elif kind == "drop_table":
            tables.pop(groups[0].lower(), None)
        elif kind == "alter":
            table, column, raw_type = groups
            columns = tables.get(table.lower())
            if columns and column.lower() in columns:
                columns[column.lower()] = sa_type(raw_type)


def migration_files(folder: Path) -> list[Path]:
    if folder.is_file():
        return [folder]
    return sorted(item for item in folder.rglob("*")
                  if item.is_file() and item.suffix in {".sql", ".py"}
                  and not SKIP_PARTS & set(item.relative_to(folder).parts))


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
        source = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".py":
            replay_alembic(source, replayed)
        else:
            build_model(source, replayed)

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
