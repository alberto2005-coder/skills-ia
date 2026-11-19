"""Unidades de cobertura (`coverage-ledger.json`): alta, actualización y huecos.

Uso:
    py appsec-audit/scripts/ledger.py add    <ledger.json> --surface S --subsystem X --class C [--owner O] [--now ISO]
    py appsec-audit/scripts/ledger.py update <ledger.json> --id U-001 --status covered --check "..." [--finding F-001]
    py appsec-audit/scripts/ledger.py validate <ledger.json> [--json]
    py appsec-audit/scripts/ledger.py gaps   <ledger.json> [--strict]

`planned` y `hunting` son huecos. `covered` exige al menos una comprobación;
`skipped` exige motivo. Código de salida: 0 correcto · 1 inválido o huecos con
`--strict` · 2 fichero ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from appsec_util import force_utf8_output

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "coverage-ledger.schema.json"

ATTACK_CLASSES = (
    "injection", "deserialization", "auth", "session", "access-control",
    "data-isolation", "crypto", "secrets", "logic", "race-condition",
    "supply-chain", "dependencies", "cicd", "cloud-infra", "ssrf",
    "file-handling", "client-side", "protocol", "llm-agent",
    "logging-monitoring", "privacy", "availability", "memory-safety", "webhook",
)
STATUSES = ("planned", "hunting", "covered", "skipped")
GAPS = ("planned", "hunting")
REQUIRED_UNIT = ("id", "surface", "subsystem", "attack_class", "status", "updated_at")
ID_RE = re.compile(r"^U-[0-9]{3,}$")
FINDING_RE = re.compile(r"^F-[0-9]{3,}$")


def stamp(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_ledger(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("la raíz debe ser un objeto JSON")
    return data


def save_ledger(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def next_id(units: list[dict]) -> str:
    numbers = [
        int(match.group(1))
        for unit in units
        if isinstance(unit.get("id"), str)
        for match in [re.match(r"^U-([0-9]{3,})$", unit["id"])]
        if match
    ]
    return f"U-{(max(numbers) + 1 if numbers else 1):03d}"


def validate_ledger(data: object) -> list[str]:
    schema = load_schema()
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["la raíz debe ser un objeto JSON"]

    allowed_top = set(schema["properties"])
    for key in data:
        if key not in allowed_top:
            errors.append(f"campo no permitido en la raíz: «{key}»")
    for key in schema["required"]:
        if key not in data:
            errors.append(f"falta el campo obligatorio «{key}»")

    units = data.get("units")
    if not isinstance(units, list):
        errors.append("«units» debe ser una lista")
        return errors

    allowed_unit = set(schema["definitions"]["unit"]["properties"])
    seen: set[str] = set()

    for position, unit in enumerate(units, start=1):
        if not isinstance(unit, dict):
            errors.append(f"units[{position}]: no es un objeto")
            continue

        label = unit.get("id") if isinstance(unit.get("id"), str) else f"units[{position}]"

        for key in unit:
            if key not in allowed_unit:
                errors.append(f"{label}: campo no permitido «{key}»")
        for key in REQUIRED_UNIT:
            if key not in unit:
                errors.append(f"{label}: falta el campo «{key}»")

        unit_id = unit.get("id")
        if isinstance(unit_id, str):
            if not ID_RE.match(unit_id):
                errors.append(f"{label}: id inválido, formato U-000")
            if unit_id in seen:
                errors.append(f"{label}: id duplicado")
            seen.add(unit_id)

        for key in ("surface", "subsystem"):
            value = unit.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label}: «{key}» vacío")

        if unit.get("attack_class") not in ATTACK_CLASSES:
            errors.append(f"{label}: attack_class fuera de la lista permitida")
        if unit.get("status") not in STATUSES:
            errors.append(f"{label}: status debe ser {' | '.join(STATUSES)}")

        checks = unit.get("checks", [])
        if not isinstance(checks, list) or not all(isinstance(item, str) and item.strip() for item in checks):
            errors.append(f"{label}: «checks» debe ser una lista de textos")
            checks = []

        findings = unit.get("findings", [])
        if not isinstance(findings, list) or not all(
            isinstance(item, str) and FINDING_RE.match(item) for item in findings
        ):
            errors.append(f"{label}: «findings» debe ser una lista de ids F-000")

        if unit.get("status") == "covered" and not checks:
            errors.append(f"{label}: covered exige al menos una comprobación en «checks»")
        if unit.get("status") == "skipped" and not (
            isinstance(unit.get("skip_reason"), str) and unit["skip_reason"].strip()
        ):
            errors.append(f"{label}: skipped exige «skip_reason»")

    return errors


def find_unit(data: dict, unit_id: str) -> dict:
    for unit in data.get("units", []):
        if isinstance(unit, dict) and unit.get("id") == unit_id:
            return unit
    raise KeyError(unit_id)


def gaps(data: dict) -> list[dict]:
    # Unidad no-dict (o sin campos) no debe reventar el CLI con KeyError:
    # `unit.get` sobre una cadena daba AttributeError y `unit['id']` KeyError.
    units = data.get("units", []) if isinstance(data, dict) else []
    return [
        unit for unit in units
        if isinstance(unit, dict) and unit.get("status") in GAPS
    ]


def _load_or_exit(path: Path) -> dict:
    if not path.is_file():
        print(f"No existe: {path}", file=sys.stderr)
        raise SystemExit(2)
    try:
        return load_ledger(path)
    except (json.JSONDecodeError, OSError, ValueError, TypeError, AttributeError) as error:
        print(f"No se pudo leer el ledger: {error}", file=sys.stderr)
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> int:
    force_utf8_output()
    parser = argparse.ArgumentParser(description="Gestiona el coverage ledger de una auditoría.")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Añade una unidad planned")
    add.add_argument("ledger")
    add.add_argument("--surface", required=True)
    add.add_argument("--subsystem", required=True)
    add.add_argument("--class", dest="attack_class", required=True, choices=ATTACK_CLASSES)
    add.add_argument("--owner", default="")
    add.add_argument("--now")

    update = sub.add_parser("update", help="Actualiza el estado de una unidad")
    update.add_argument("ledger")
    update.add_argument("--id", required=True)
    update.add_argument("--status", required=True, choices=STATUSES)
    update.add_argument("--check", action="append", default=[])
    update.add_argument("--finding", action="append", default=[])
    update.add_argument("--skip-reason")
    update.add_argument("--now")

    validate = sub.add_parser("validate", help="Valida la estructura del ledger")
    validate.add_argument("ledger")
    validate.add_argument("--json", action="store_true")

    gaps_cmd = sub.add_parser("gaps", help="Lista las unidades sin cubrir")
    gaps_cmd.add_argument("ledger")
    gaps_cmd.add_argument("--strict", action="store_true", help="Sale 1 si quedan huecos")

    args = parser.parse_args(argv)
    path = Path(args.ledger)
    data = _load_or_exit(path)

    if args.command == "add":
        unit = {
            "id": next_id(data.get("units", [])),
            "surface": args.surface,
            "subsystem": args.subsystem,
            "attack_class": args.attack_class,
            "status": "planned",
            "checks": [],
            "findings": [],
            "updated_at": stamp(args.now),
        }
        if args.owner:
            unit["owner"] = args.owner
        data.setdefault("units", []).append(unit)
        data["updated_at"] = stamp(args.now)
        save_ledger(path, data)
        print(f"{unit['id']} añadida: {unit['surface']} · {unit['attack_class']} (planned)")
        return 0

    if args.command == "update":
        try:
            unit = find_unit(data, args.id)
        except KeyError:
            print(f"No existe la unidad {args.id}", file=sys.stderr)
            return 1
        unit["status"] = args.status
        unit["updated_at"] = stamp(args.now)
        if args.check:
            unit["checks"] = list(dict.fromkeys(unit.get("checks", []) + args.check))
        if args.finding:
            unit["findings"] = list(dict.fromkeys(unit.get("findings", []) + args.finding))
        if args.skip_reason:
            unit["skip_reason"] = args.skip_reason
        data["updated_at"] = stamp(args.now)
        errors = validate_ledger(data)
        if errors:
            print("No se guarda: el ledger quedaría inválido", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return 1
        save_ledger(path, data)
        print(f"{unit['id']} -> {unit['status']}")
        return 0

    if args.command == "validate":
        errors = validate_ledger(data)
        if args.json:
            print(json.dumps({"valid": not errors, "errors": errors}, indent=2, ensure_ascii=False))
        elif errors:
            print(f"INVÁLIDO: {len(errors)} problema(s)")
            for error in errors:
                print(f"  - {error}")
        else:
            units = data.get("units", [])
            print(f"OK: {len(units)} unidad(es) · huecos {len(gaps(data))}")
        return 0 if not errors else 1

    pending = gaps(data)
    for unit in pending:
        print(f"{unit.get('id', '?')}  {str(unit.get('status', '?')):8}  "
              f"{unit.get('surface', '?')} · {unit.get('attack_class', '?')}")
    print(f"\n{len(pending)} hueco(s) de {len(data.get('units', []))} unidad(es).")
    return 1 if args.strict and pending else 0


if __name__ == "__main__":
    sys.exit(main())
