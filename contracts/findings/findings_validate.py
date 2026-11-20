"""Valida cualquier `findings.json` contra el contrato común v1.0.0 y corta por umbral.

Uso:
    py contracts/findings/findings_validate.py <findings.json>
        [--fail-on none|info|low|medium|high|critical] [--json]

El esquema `findings.schema.json` es la definición, pero la comprobación se hace
aquí para no añadir dependencias: los paquetes se instalan solos y sus scripts
solo usan la biblioteca estándar. Además de la forma, se verifica lo que un
validador genérico no puede: que el resumen declare el recuento real, que la
huella sea la calculada y que solo `file` lleve líneas.

Código de salida: 0 válido · 1 inválido · 2 entrada ilegible · 3 supera --fail-on.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import findings_contract as contract

VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
RULE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{32}$")
URL_RE = re.compile(r"^https?://")
TOOL_KEYS = ("package", "skill", "version")
LOCATION_KEYS = {"type", "target", "line", "end_line"}
FINDING_KEYS = {
    "fingerprint", "rule_id", "severity", "confidence", "title", "message",
    "evidence", "remediation", "references", "location",
}


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra página de códigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def load_schema() -> dict:
    return json.loads(contract.SCHEMA_PATH.read_text(encoding="utf-8"))


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _unknown_keys(item: dict, allowed: set, label: str, errors: list) -> None:
    for key in item:
        if key not in allowed:
            errors.append(f"{label}: campo no permitido «{key}»")


def _missing_keys(item: dict, required, label: str, errors: list) -> None:
    for key in required:
        if key not in item:
            errors.append(f"{label}: falta el campo «{key}»")


def _check_tool(tool: object, errors: list) -> None:
    if not isinstance(tool, dict):
        errors.append("«tool» debe ser un objeto")
        return
    _unknown_keys(tool, set(TOOL_KEYS), "tool", errors)
    _missing_keys(tool, TOOL_KEYS, "tool", errors)
    for key in ("package", "skill"):
        if not _non_empty(tool.get(key)):
            errors.append(f"tool.{key} debe ser texto no vacío")
    version = tool.get("version")
    if not isinstance(version, str) or not VERSION_RE.match(version):
        errors.append("tool.version debe ser semver X.Y.Z")


def _check_target(payload: dict, errors: list) -> None:
    target = payload.get("target")
    if target is not None and not _non_empty(target):
        errors.append("«target» debe ser texto no vacío o null")
    generated_at = payload.get("generated_at")
    if generated_at is None:
        return
    if not _non_empty(generated_at):
        errors.append("«generated_at» debe ser texto ISO 8601 o null")
        return
    try:
        datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    except ValueError:
        errors.append("«generated_at» debe ser una fecha ISO 8601")


def _check_lines(location: dict, kind: object, label: str, errors: list) -> tuple:
    values = []
    for key in ("line", "end_line"):
        value = location.get(key)
        if value is None:
            values.append(None)
            continue
        if not _is_int(value) or value < 1:
            errors.append(f"{label}: location.{key} debe ser un entero >= 1 o null")
            values.append(None)
            continue
        if kind in contract.LOCATION_TYPES and kind not in contract.LINED_TYPES:
            errors.append(
                f"{label}: location.{key} solo vale con type «file»; "
                f"en «{kind}» la línea sería inventada"
            )
        values.append(value)
    return tuple(values)


def _check_location(location: object, label: str, errors: list) -> dict | None:
    if not isinstance(location, dict):
        errors.append(f"{label}: «location» debe ser un objeto")
        return None
    _unknown_keys(location, LOCATION_KEYS, label, errors)
    kind = location.get("type")
    if kind not in contract.LOCATION_TYPES:
        errors.append(f"{label}: location.type debe ser {' | '.join(contract.LOCATION_TYPES)}")
    target = location.get("target")
    if not _non_empty(target):
        errors.append(f"{label}: location.target debe ser texto no vacío")
    line, end_line = _check_lines(location, kind, label, errors)
    if line is not None and end_line is not None and end_line < line:
        errors.append(f"{label}: location.end_line no puede ser menor que line")
    if not (_non_empty(target) and kind in contract.LOCATION_TYPES):
        return None
    return {"type": kind, "target": target}


def _check_references(references: object, label: str, errors: list) -> None:
    if references is None:
        return
    if not isinstance(references, list):
        errors.append(f"{label}: «references» debe ser una lista")
        return
    for position, item in enumerate(references, start=1):
        if not isinstance(item, dict):
            errors.append(f"{label}: references[{position}] debe ser un objeto")
            continue
        _unknown_keys(item, {"id", "url"}, f"{label}: references[{position}]", errors)
        _missing_keys(item, ("id",), f"{label}: references[{position}]", errors)
        if not _non_empty(item.get("id")):
            errors.append(f"{label}: references[{position}].id debe ser texto no vacío")
        url = item.get("url")
        if url is not None and (not isinstance(url, str) or not URL_RE.match(url)):
            errors.append(f"{label}: references[{position}].url debe ser http(s)")


def _check_texts(item: dict, label: str, errors: list) -> None:
    title = item.get("title")
    if not isinstance(title, str) or not 3 <= len(title.strip()) <= 160:
        errors.append(f"{label}: «title» debe tener entre 3 y 160 caracteres")
    for key in ("message", "evidence", "remediation"):
        if not _non_empty(item.get(key)):
            errors.append(f"{label}: «{key}» no puede estar vacío")


def _check_enums(item: dict, label: str, errors: list) -> None:
    if item.get("severity") not in contract.SEVERITIES:
        errors.append(f"{label}: severity debe ser {' | '.join(contract.SEVERITIES)}")
    if item.get("confidence") not in contract.CONFIDENCES:
        errors.append(f"{label}: confidence debe ser {' | '.join(contract.CONFIDENCES)}")


def _check_fingerprint(item: dict, location: dict | None, label: str, errors: list) -> None:
    stored = item.get("fingerprint")
    if not isinstance(stored, str) or not FINGERPRINT_RE.match(stored):
        errors.append(f"{label}: fingerprint con formato sha256:<32 hex>")
        return
    rule_id = item.get("rule_id")
    title = item.get("title")
    if location is None or not isinstance(rule_id, str) or not isinstance(title, str):
        return
    expected = contract.fingerprint(rule_id, location, title)
    if stored != expected:
        errors.append(f"{label}: fingerprint no coincide (esperado {expected})")


def _check_finding(item: object, position: int, errors: list) -> dict | None:
    if not isinstance(item, dict):
        errors.append(f"findings[{position}]: no es un objeto")
        return None
    label = f"findings[{position}]"
    _unknown_keys(item, FINDING_KEYS, label, errors)
    _missing_keys(item, FINDING_KEYS - {"references"}, label, errors)
    _check_texts(item, label, errors)
    _check_enums(item, label, errors)
    rule_id = item.get("rule_id")
    if not isinstance(rule_id, str) or not RULE_RE.match(rule_id):
        errors.append(f"{label}: rule_id debe empezar por letra y usar [A-Za-z0-9._-]")
    _check_references(item.get("references"), label, errors)
    location = _check_location(item.get("location"), label, errors)
    _check_fingerprint(item, location, label, errors)
    return item


def _check_summary(summary: object, findings: list, errors: list) -> None:
    if not isinstance(summary, dict):
        errors.append("«summary» debe ser un objeto")
        return
    _unknown_keys(summary, {"total", "by_severity", "score", "note"}, "summary", errors)
    total = summary.get("total")
    if not _is_int(total) or total < 0:
        errors.append("summary.total debe ser un entero >= 0")
    elif total != len(findings):
        errors.append(f"summary.total declara {total} y hay {len(findings)} hallazgos")
    expected = contract.summarize([item for item in findings if isinstance(item, dict)])["by_severity"]
    declared = summary.get("by_severity")
    if not isinstance(declared, dict):
        errors.append("summary.by_severity debe ser un objeto")
    else:
        _unknown_keys(declared, set(contract.SEVERITIES), "summary.by_severity", errors)
        for severity in contract.SEVERITIES:
            count = declared.get(severity)
            if not _is_int(count) or count < 0:
                errors.append(f"summary.by_severity.{severity} debe ser un entero >= 0")
            elif count != expected[severity]:
                errors.append(
                    f"summary.by_severity.{severity} declara {count} y hay {expected[severity]}"
                )
    score = summary.get("score")
    if score is not None and (not isinstance(score, (int, float)) or isinstance(score, bool)
                              or not 0 <= score <= 100):
        errors.append("summary.score debe ser un número entre 0 y 100 o null")
    note = summary.get("note")
    if note is not None and not isinstance(note, str):
        errors.append("summary.note debe ser texto o null")


def validate_payload(payload: object) -> list:
    """Lista de problemas; vacía significa que el informe cumple el contrato."""
    schema = load_schema()
    errors: list = []
    if not isinstance(payload, dict):
        return ["la raíz debe ser un objeto JSON"]
    _unknown_keys(payload, set(schema["properties"]), "raíz", errors)
    _missing_keys(payload, schema["required"], "raíz", errors)
    if payload.get("schema_version") != contract.SCHEMA_VERSION:
        errors.append(f"schema_version debe ser «{contract.SCHEMA_VERSION}»")
    _check_tool(payload.get("tool"), errors)
    _check_target(payload, errors)
    findings = payload.get("findings")
    if not isinstance(findings, list):
        errors.append("«findings» debe ser una lista")
        findings = []
    seen: dict = {}
    for position, item in enumerate(findings, start=1):
        checked = _check_finding(item, position, errors)
        if checked is None or not isinstance(checked.get("fingerprint"), str):
            continue
        previous = seen.get(checked["fingerprint"])
        if previous is not None:
            errors.append(
                f"findings[{position}]: fingerprint duplicado (ya en {previous}); "
                "la huella deduplica, así que es el mismo hallazgo"
            )
        else:
            seen[checked["fingerprint"]] = f"findings[{position}]"
    _check_summary(payload.get("summary"), findings, errors)
    return errors


def main(argv: list | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Valida findings.json contra el contrato común v1.0.0.")
    parser.add_argument("findings", help="Ruta de findings.json")
    parser.add_argument(
        "--fail-on",
        default="none",
        choices=("none",) + contract.SEVERITIES,
        help="Sale 3 si algún hallazgo llega a este umbral (por defecto, none)",
    )
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    args = parser.parse_args(argv)

    path = Path(args.findings)
    if not path.is_file():
        print(f"No existe: {path}", file=sys.stderr)
        return 2
    try:
        payload = contract.load_json(path)
    except (json.JSONDecodeError, OSError) as error:
        print(f"No se pudo leer la entrada: {error}", file=sys.stderr)
        return 2

    errors = validate_payload(payload)
    findings = payload.get("findings") if isinstance(payload, dict) else []
    findings = [item for item in findings or [] if isinstance(item, dict)]
    blocking = [item for item in findings if contract.severity_at_or_above(item, args.fail_on)]
    counts = contract.summarize(findings)

    if args.json:
        print(json.dumps({
            "valid": not errors,
            "errors": errors,
            "counts": counts,
            "fail_on": args.fail_on,
            "blocking": len(blocking),
            "exit": 1 if errors else (3 if blocking else 0),
        }, indent=2, ensure_ascii=False))
    elif errors:
        print(f"INVÁLIDO: {len(errors)} problema(s)")
        for error in errors:
            print(f"  - {error}")
    else:
        by_severity = counts["by_severity"]
        print(
            "OK: {total} hallazgo(s) · critical {critical} · high {high} · medium {medium} "
            "· low {low} · info {info}".format(**by_severity, total=counts["total"])
        )
        if args.fail_on != "none":
            print(f"--fail-on {args.fail_on}: {len(blocking)} hallazgo(s) llegan al umbral")

    if errors:
        return 1
    return 3 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
