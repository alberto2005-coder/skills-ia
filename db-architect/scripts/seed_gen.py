"""Genera datos de siembra deterministas a partir de un esquema SQL.

Uso:
    py db-architect/scripts/seed_gen.py --schema schema.sql [--rows 3] [--seed 42]
        [--format sql|json]

Ordena las tablas respetando las claves foráneas y emite valores reproducibles:
la misma semilla y el mismo esquema producen byte a byte el mismo resultado.

Código de salida: 0 correcto · 1 esquema sin tablas · 2 esquema ilegible o ciclo
de referencias.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"'`]?(\w+)[\"'`]?\s*\((.*?)\)\s*;",
    re.S | re.I,
)
CONSTRAINTS = ("primary", "foreign", "unique", "check", "constraint")
REFERENCES = re.compile(r"REFERENCES\s+[\"'`]?(\w+)", re.I)
NUMERIC = re.compile(r"int|serial|numeric|decimal|real|float|double", re.I)
BOOLEAN = re.compile(r"bool", re.I)
TEMPORAL = re.compile(r"date|time", re.I)


def parse_schema(text: str) -> dict[str, list[dict]]:
    tables: dict[str, list[dict]] = {}
    for name, block in TABLE.findall(text):
        columns = []
        for raw in block.split(","):
            line = raw.strip()
            if not line or line.lower().startswith(CONSTRAINTS):
                continue
            parts = line.split()
            column = parts[0].strip("\"'`")
            kind = " ".join(parts[1:])
            references = REFERENCES.search(kind)
            columns.append({
                "name": column,
                "kind": kind,
                "primary": "primary key" in kind.lower(),
                "references": references.group(1) if references else "",
            })
        tables[name] = columns
    return tables


def order_tables(tables: dict[str, list[dict]]) -> list[str]:
    pending = {name: {col["references"] for col in columns if col["references"] in tables}
               for name, columns in tables.items()}
    ordered: list[str] = []
    while pending:
        ready = sorted(name for name, deps in pending.items() if not deps - set(ordered))
        if not ready:
            raise ValueError("ciclo de referencias entre tablas")
        for name in ready:
            ordered.append(name)
            del pending[name]
    return ordered


def value_for(column: dict, index: int, rows: int, rng: random.Random) -> object:
    if column["primary"] or column["name"].lower() == "id":
        return index + 1
    if column["references"]:
        return rng.randint(1, max(1, rows))
    if NUMERIC.search(column["kind"]):
        return rng.randint(1, 100)
    if BOOLEAN.search(column["kind"]):
        return rng.choice([0, 1])
    if TEMPORAL.search(column["kind"]):
        return f"2024-01-0{index % 9 + 1}"
    return f"{column['name']}_{index + 1}"


def build_rows(tables: dict[str, list[dict]], order: list[str], rows: int, seed: int) -> dict[str, list[dict]]:
    rng = random.Random(seed)
    data: dict[str, list[dict]] = {}
    for table in order:
        data[table] = [
            {column["name"]: value_for(column, index, rows, rng) for column in tables[table]}
            for index in range(rows)
        ]
    return data


def render_sql(data: dict[str, list[dict]]) -> str:
    lines = []
    for table, rows in data.items():
        for row in rows:
            columns = ", ".join(row)
            values = ", ".join(repr(value) for value in row.values())
            lines.append(f"INSERT INTO {table} ({columns}) VALUES ({values});")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generador determinista de datos de siembra.")
    parser.add_argument("--schema", required=True, help="fichero .sql con el esquema")
    parser.add_argument("--rows", type=int, default=3, help="filas por tabla")
    parser.add_argument("--seed", type=int, default=42, help="semilla del generador")
    parser.add_argument("--format", default="sql", choices=["sql", "json"])
    args = parser.parse_args(argv)

    path = Path(args.schema)
    if not path.exists():
        print(f"ruta inexistente: {path}")
        return 2
    try:
        tables = parse_schema(path.read_text(encoding="utf-8"))
        if not tables:
            print("el esquema no declara tablas CREATE TABLE")
            return 1
        order = order_tables(tables)
    except (OSError, ValueError) as error:
        print(f"esquema ilegible: {error}")
        return 2

    data = build_rows(tables, order, max(1, args.rows), args.seed)
    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        sys.stdout.write(render_sql(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
