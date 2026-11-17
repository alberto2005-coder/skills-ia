"""Validador determinista de `findings.json`. Solo lectura, sin red.

Uso:
    py appsec-audit/scripts/validate_findings.py <findings.json>
        [--ledger <coverage-ledger.json>] [--json]

Comprueba estructura, campos permitidos contra el esquema, coherencia entre
veredicto y severidad, y que el fingerprint sea el calculado a partir de la
causa raíz. Con `--ledger` verifica además que cada `source_unit` exista.

Código de salida: 0 válido · 1 inválido · 2 fichero ilegible o JSON roto.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "findings.schema.json"
CONFIRMED_MIN_CONFIDENCE = 7

REQUIRED_FINDING = (
    "id", "title", "verdict", "confidence", "cwe", "location", "evidence", "fingerprint",
)
VERDICTS = ("confirmed", "needs_validation", "rejected")
SEVERITIES = ("critica", "alta", "media", "baja")
ID_RE = re.compile(r"^F-[0-9]{3,}$")
CWE_RE = re.compile(r"^CWE-[0-9]+$")
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{32}$")


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def fingerprint(cwe: str, file: str, root_cause: str) -> str:
    """Huella estable del hallazgo: no depende del número de línea."""
    normalized = " ".join(str(root_cause).split()).lower()
    digest = hashlib.sha256(f"{cwe}|{file}|{normalized}".encode("utf-8")).hexdigest()
    return "sha256:" + digest[:32]


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _check_finding(item: object, allowed: set[str], position: int,
                   ledger_units: set[str] | None, errors: list[str]) -> str | None:
    if not isinstance(item, dict):
        errors.append(f"findings[{position}]: no es un objeto")
        return None

    label = item.get("id") if isinstance(item.get("id"), str) else f"findings[{position}]"

    for key in item:
        if key not in allowed:
            errors.append(f"{label}: campo no permitido «{key}»")
    for key in REQUIRED_FINDING:
        if key not in item:
            errors.append(f"{label}: falta el campo «{key}»")

    finding_id = item.get("id")
    if isinstance(finding_id, str) and not ID_RE.match(finding_id):
        errors.append(f"{label}: id inválido, formato F-000")

    if not _non_empty(item.get("title")):
        errors.append(f"{label}: «title» vacío")

    verdict = item.get("verdict")
    if verdict not in VERDICTS:
        errors.append(f"{label}: verdict debe ser {' | '.join(VERDICTS)}")

    confidence = item.get("confidence")
    if not _is_int(confidence) or not 1 <= confidence <= 10:
        errors.append(f"{label}: confidence debe ser un entero entre 1 y 10")

    cwe = item.get("cwe")
    if not isinstance(cwe, str) or not CWE_RE.match(cwe):
        errors.append(f"{label}: cwe debe tener formato CWE-000")

    file = ""
    location = item.get("location")
    if not isinstance(location, dict):
        errors.append(f"{label}: «location» debe ser un objeto")
    else:
        for key in location:
            if key not in ("file", "line"):
                errors.append(f"{label}: location con campo no permitido «{key}»")
        file = location.get("file") if isinstance(location.get("file"), str) else ""
        if not file.strip():
            errors.append(f"{label}: location.file vacío")
        line = location.get("line")
        if not _is_int(line) or line < 1:
            errors.append(f"{label}: location.line debe ser un entero >= 1")

    if not _non_empty(item.get("evidence")):
        errors.append(f"{label}: «evidence» vacío")

    severity = item.get("severity")
    if severity is not None and severity not in SEVERITIES:
        errors.append(f"{label}: severity debe ser crítica, alta, media o baja")

    if verdict == "confirmed":
        if severity is None:
            errors.append(f"{label}: un hallazgo confirmed exige «severity»")
        if _is_int(confidence) and confidence < CONFIRMED_MIN_CONFIDENCE:
            errors.append(
                f"{label}: confirmed exige confidence >= {CONFIRMED_MIN_CONFIDENCE} "
                f"(tiene {confidence}); por debajo pasa a needs_validation"
            )
        steps = item.get("exploit")
        if not isinstance(steps, list) or len(steps) < 2 or not all(_non_empty(s) for s in steps):
            errors.append(f"{label}: confirmed exige «exploit» con al menos 2 pasos")
        if not _non_empty(item.get("patch")):
            errors.append(f"{label}: confirmed exige «patch»")

    if verdict == "needs_validation":
        if severity is not None:
            errors.append(f"{label}: needs_validation no lleva «severity»")
        if not _non_empty(item.get("unresolved")):
            errors.append(f"{label}: needs_validation exige «unresolved» con el dato que falta")

    if verdict == "rejected":
        if severity is not None:
            errors.append(f"{label}: rejected no lleva «severity»")
        if not _non_empty(item.get("reason")):
            errors.append(f"{label}: rejected exige «reason»")

    unit = item.get("source_unit")
    if unit is not None:
        if ledger_units is not None and unit not in ledger_units:
            errors.append(f"{label}: source_unit «{unit}» no existe en el ledger")
        elif not isinstance(unit, str) or not re.match(r"^U-[0-9]{3,}$", unit):
            errors.append(f"{label}: source_unit con formato U-000")

    stored = item.get("fingerprint")
    if not isinstance(stored, str) or not FINGERPRINT_RE.match(stored):
        errors.append(f"{label}: fingerprint con formato sha256:<32 hex>")
    elif _non_empty(cwe) and file:
        cause = item.get("root_cause") if _non_empty(item.get("root_cause")) else item.get("title")
        expected = fingerprint(cwe, file, cause)
        if stored != expected:
            errors.append(f"{label}: fingerprint no coincide (esperado {expected})")

    return finding_id if isinstance(finding_id, str) else None


def validate_payload(payload: object, ledger_units: set[str] | None = None) -> list[str]:
    """Devuelve la lista de errores; vacía significa válido."""
    schema = load_schema()
    errors: list[str] = []

    if not isinstance(payload, dict):
        return ["la raíz debe ser un objeto JSON"]

    allowed_top = set(schema["properties"])
    for key in payload:
        if key not in allowed_top:
            errors.append(f"campo no permitido en la raíz: «{key}»")
    for key in schema["required"]:
        if key not in payload:
            errors.append(f"falta el campo obligatorio «{key}»")

    for key in ("audit_id", "target"):
        if key in payload and not _non_empty(payload.get(key)):
            errors.append(f"«{key}» no puede estar vacío")

    profile = payload.get("profile")
    if profile is not None and profile not in ("quick", "standard", "deep"):
        errors.append("profile debe ser quick, standard o deep")

    findings = payload.get("findings")
    if not isinstance(findings, list):
        errors.append("«findings» debe ser una lista")
        return errors

    allowed_finding = set(schema["definitions"]["finding"]["properties"])
    seen: set[str] = set()
    seen_fingerprints: dict[str, str] = {}
    for position, item in enumerate(findings, start=1):
        found_id = _check_finding(item, allowed_finding, position, ledger_units, errors)

        label = found_id or f"findings[{position}]"
        stored = item.get("fingerprint") if isinstance(item, dict) else None
        if isinstance(stored, str) and FINGERPRINT_RE.match(stored):
            previous = seen_fingerprints.get(stored)
            if previous is not None:
                errors.append(
                    f"{label}: fingerprint duplicado (ya usado por {previous}); "
                    "la huella deduplica entre pasadas, así que es el mismo hallazgo"
                )
            else:
                seen_fingerprints[stored] = label

        if found_id is None:
            continue
        if found_id in seen:
            errors.append(f"{found_id}: id duplicado")
        seen.add(found_id)

    return errors


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_units(path: Path) -> set[str]:
    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("units"), list):
        raise ValueError("el ledger no tiene una lista «units»")
    return {
        unit.get("id")
        for unit in data["units"]
        if isinstance(unit, dict) and isinstance(unit.get("id"), str)
    }


def summarize(payload: object) -> dict:
    counts = {verdict: 0 for verdict in VERDICTS}
    severities = {severity: 0 for severity in SEVERITIES}
    if isinstance(payload, dict) and isinstance(payload.get("findings"), list):
        for item in payload["findings"]:
            if not isinstance(item, dict):
                continue
            verdict = item.get("verdict")
            if verdict in counts:
                counts[verdict] += 1
            severity = item.get("severity")
            if severity in severities and verdict == "confirmed":
                severities[severity] += 1
    return {"verdicts": counts, "severities": severities}


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Valida findings.json contra su esquema.")
    parser.add_argument("findings", help="Ruta de findings.json")
    parser.add_argument("--ledger", help="coverage-ledger.json para comprobar source_unit")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    args = parser.parse_args(argv)

    path = Path(args.findings)
    if not path.is_file():
        print(f"No existe: {path}", file=sys.stderr)
        return 2

    try:
        payload = load_json(path)
        units = load_units(Path(args.ledger)) if args.ledger else None
    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(f"No se pudo leer la entrada: {error}", file=sys.stderr)
        return 2

    errors = validate_payload(payload, units)
    summary = summarize(payload)

    if args.json:
        print(json.dumps({
            "valid": not errors,
            "errors": errors,
            "counts": summary,
            "ledger": args.ledger,
        }, indent=2, ensure_ascii=False))
    else:
        counts = summary["verdicts"]
        if errors:
            print(f"INVÁLIDO: {len(errors)} problema(s)")
            for error in errors:
                print(f"  - {error}")
        else:
            print(
                f"OK: {sum(counts.values())} hallazgo(s) "
                f"· confirmed {counts['confirmed']} · "
                f"needs_validation {counts['needs_validation']} · "
                f"rejected {counts['rejected']}"
            )

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
