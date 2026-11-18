"""Divide una migración en el plan expand → contract que se puede desplegar sin cortes.

Uso:
    py db-architect/scripts/expand_contract.py --path migrations/004_cambio.sql
        [--json] [--fail-on unsafe|none]

Clasifica cada sentencia en la fase que le toca: `expand` añade sin romper
(columnas nuevas, índices concurrentes, constraints `NOT VALID`) y `contract`
retira o aprieta (drops, renames, `SET NOT NULL`, cambios de tipo) y por tanto
va en un despliegue posterior. Las operaciones que no se pueden partir se
quedan como aviso con su alternativa.

Código de salida: 0 plan sin avisos · 1 avisos con el umbral · 2 ruta ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXPAND_KINDS = (
    ("create-table", re.compile(r"^\s*CREATE\s+TABLE\b", re.I)),
    ("add-column", re.compile(r"^\s*ALTER\s+TABLE\s+\S+\s+ADD\s+(?:COLUMN\s+)?\S+", re.I)),
    ("create-index", re.compile(r"^\s*CREATE\s+(?:UNIQUE\s+)?INDEX\b", re.I)),
    ("add-constraint", re.compile(r"^\s*ALTER\s+TABLE\s+\S+\s+ADD\s+CONSTRAINT\b", re.I)),
    ("validate", re.compile(r"^\s*ALTER\s+TABLE\s+\S+\s+VALIDATE\s+CONSTRAINT\b", re.I)),
)
CONTRACT_KINDS = (
    ("drop-table", re.compile(r"^\s*DROP\s+TABLE\b", re.I)),
    ("drop-column", re.compile(r"^\s*ALTER\s+TABLE\s+\S+\s+DROP\s+(?:COLUMN\s+)?\S+", re.I)),
    ("drop-constraint", re.compile(r"^\s*ALTER\s+TABLE\s+\S+\s+DROP\s+CONSTRAINT\b", re.I)),
    ("rename", re.compile(r"^\s*ALTER\s+TABLE\s+\S+\s+RENAME\b", re.I)),
    ("set-not-null", re.compile(r"\bSET\s+NOT\s+NULL\b", re.I)),
    ("alter-type", re.compile(r"\bALTER\s+COLUMN\s+\S+\s+(?:SET\s+DATA\s+)?TYPE\b", re.I)),
)
WARNINGS = (
    ("columna-obligatoria-en-un-paso",
     re.compile(r"^\s*ALTER\s+TABLE\b.*\bADD\s+(?:COLUMN\s+)?\S+.*\bNOT\s+NULL\b", re.I | re.S),
     "Añade la columna nullable, rellena en lotes y aprieta con SET NOT NULL en el contrato."),
    ("rename-no-divisible",
     re.compile(r"^\s*ALTER\s+TABLE\s+\S+\s+RENAME\b", re.I),
     "Crea la columna nueva, escribe en las dos y retira la vieja en el contrato."),
    ("reescritura-no-divisible",
     re.compile(r"\bALTER\s+COLUMN\s+\S+\s+(?:SET\s+DATA\s+)?TYPE\b", re.I),
     "Columna nueva con el tipo final, copia por lotes y retirada de la antigua."),
)


def statements(sql: str) -> list[str]:
    return [chunk.strip() for chunk in sql.split(";") if chunk.strip()]


def classify(statement: str) -> str:
    for _, pattern in EXPAND_KINDS:
        if pattern.search(statement):
            return "expand"
    for _, pattern in CONTRACT_KINDS:
        if pattern.search(statement):
            return "contract"
    return "expand"


def kind_of(statement: str) -> str:
    for name, pattern in EXPAND_KINDS + CONTRACT_KINDS:
        if pattern.search(statement):
            return name
    return "desconocida"


def plan(sql: str) -> dict:
    phases = {"expand": [], "contract": []}
    warnings = []
    for statement in statements(sql):
        phase = classify(statement)
        phases[phase].append({
            "step": len(phases[phase]) + 1,
            "kind": kind_of(statement),
            "statement": re.sub(r"\s+", " ", statement),
        })
        for rule, pattern, alternative in WARNINGS:
            if pattern.search(statement):
                warnings.append({
                    "rule": rule,
                    "severity": "high",
                    "statement": re.sub(r"\s+", " ", statement),
                    "message": "la sentencia no se puede repartir entre las dos fases como está",
                    "alternative": alternative,
                })
    return {
        "phases": phases,
        "warnings": warnings,
        "deployable_together": not (phases["expand"] and phases["contract"]),
        "statements": len(phases["expand"]) + len(phases["contract"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan expand → contract de una migración.")
    parser.add_argument("--path", required=True, help="fichero .sql de la migración")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="unsafe", choices=["unsafe", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    report = plan(target.read_text(encoding="utf-8", errors="replace"))

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for phase in ("expand", "contract"):
            print(f"{phase}: {len(report['phases'][phase])} sentencia(s)")
            for item in report["phases"][phase]:
                print(f"  {item['step']}. [{item['kind']}] {item['statement']}")
        for warning in report["warnings"]:
            print(f"[AVISO] {warning['rule']}: {warning['alternative']}")
        print("mismo despliegue: " + ("sí" if report["deployable_together"] else "no, dos despliegues"))

    if args.fail_on == "none":
        return 0
    return 1 if report["warnings"] else 0


if __name__ == "__main__":
    sys.exit(main())
