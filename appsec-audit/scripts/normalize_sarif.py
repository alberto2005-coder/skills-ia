"""Normaliza SARIF externo a `findings.json` y comprueba que sea subible a GitHub.

Uso:
    py appsec-audit/scripts/normalize_sarif.py <sarif> [--output findings.json]
        [--target T] [--audit-id ID] [--fail-on none|low|medium|high|critical] [--json]
    py appsec-audit/scripts/normalize_sarif.py <sarif> --check

Todo lo importado entra como `needs_validation` con confianza 5: un SARIF de
terceros es una pista, no un hallazgo verificado. La severidad original se
conserva solo para la puerta `--fail-on`; el veredicto lo pone el tribunal.

Código de salida: 0 correcto · 1 `--check` falla o `--fail-on` se dispara · 2 ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_findings as findings_lib  # noqa: E402

DEFAULT_CWE = "CWE-710"
CWE_RE = re.compile(r"CWE-[0-9]+")
LEVEL_SEVERITY = {"error": "high", "warning": "medium", "note": "low", "none": "low"}
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}
CONFIDENCE = 5


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def uri_path(uri: object) -> str:
    text = str(uri or "")
    text = re.sub(r"^file:///?", "", text)
    while text.startswith("./"):
        text = text[2:]
    return text.replace("\\", "/")


def rule_index(run: dict) -> dict[str, dict]:
    rules = ((run.get("tool") or {}).get("driver") or {}).get("rules") or []
    return {
        str(rule.get("id")): rule
        for rule in rules
        if isinstance(rule, dict) and rule.get("id") is not None
    }


def severity_of(result: dict, rule: dict) -> str:
    properties = rule.get("properties") if isinstance(rule.get("properties"), dict) else {}
    score = properties.get("security-severity")
    try:
        value = float(score)
    except (TypeError, ValueError):
        value = None
    if value is not None:
        if value >= 9:
            return "critical"
        if value >= 7:
            return "high"
        if value >= 4:
            return "medium"
        return "low"
    level = str(result.get("level") or (rule.get("defaultConfiguration") or {}).get("level") or "warning")
    return LEVEL_SEVERITY.get(level, "medium")


def cwe_of(rule: dict) -> str:
    properties = rule.get("properties") if isinstance(rule.get("properties"), dict) else {}
    tags = properties.get("tags") or []
    for tag in tags:
        match = CWE_RE.search(str(tag))
        if match:
            return match.group(0)
    match = CWE_RE.search(str(rule.get("id") or ""))
    return match.group(0) if match else DEFAULT_CWE


def location_of(result: dict) -> tuple[str, int] | None:
    locations = result.get("locations") or []
    for location in locations:
        if not isinstance(location, dict):
            continue
        physical = location.get("physicalLocation") or {}
        artifact = (physical.get("artifactLocation") or {}).get("uri")
        path = uri_path(artifact)
        if not path:
            continue
        region = physical.get("region") or {}
        line = region.get("startLine")
        return path, line if isinstance(line, int) and line > 0 else 1
    return None


def sanitize_windows_drive(path: str) -> str:
    return re.sub(r"^[A-Za-z]:", "", path).lstrip("/")


def normalize(sarif: dict, target: str, audit_id: str) -> dict:
    findings = []
    skipped = 0
    tool_names = []

    for run in sarif.get("runs") or []:
        if not isinstance(run, dict):
            continue
        tool = ((run.get("tool") or {}).get("driver") or {}).get("name") or "sarif"
        tool_names.append(str(tool))
        rules = rule_index(run)
        for result in run.get("results") or []:
            if not isinstance(result, dict):
                continue
            location = location_of(result)
            if location is None:
                skipped += 1
                continue
            path, line = location
            rule_id = str(result.get("ruleId") or result.get("rule", {}).get("id") or "desconocida")
            rule = rules.get(rule_id, {})
            message = str((result.get("message") or {}).get("text") or rule_id).strip()
            cwe = cwe_of(rule)
            root_cause = f"{tool}:{rule_id}"
            findings.append({
                "id": f"F-{len(findings) + 1:03d}",
                "title": (message.splitlines()[0] if message else rule_id)[:160],
                "verdict": "needs_validation",
                "confidence": CONFIDENCE,
                "cwe": cwe,
                "location": {"file": sanitize_windows_drive(path), "line": line},
                "root_cause": root_cause,
                "evidence": f"{tool}: {rule_id} ({result.get('level') or 'warning'})",
                "unresolved": "confirmar ruta explotable y mitigación del framework antes de puntuar",
                "fingerprint": findings_lib.fingerprint(cwe, sanitize_windows_drive(path), root_cause),
            })

    return {
        "audit_id": audit_id,
        "target": target,
        "findings": findings,
        "skipped_without_location": skipped,
        "tools": sorted(set(tool_names)),
    }


def check_upload_sarif(sarif: dict) -> list[str]:
    errors: list[str] = []
    if sarif.get("version") != "2.1.0":
        errors.append("version debe ser 2.1.0 para upload-sarif")
    runs = sarif.get("runs")
    if not isinstance(runs, list) or not runs:
        return errors + ["«runs» debe ser una lista no vacía"]
    for index, run in enumerate(runs, start=1):
        driver = ((run or {}).get("tool") or {}).get("driver") or {}
        if not driver.get("name"):
            errors.append(f"runs[{index}]: driver sin nombre")
        for position, result in enumerate((run or {}).get("results") or [], start=1):
            if not isinstance(result, dict):
                errors.append(f"runs[{index}].results[{position}]: no es un objeto")
                continue
            if not result.get("ruleId"):
                errors.append(f"runs[{index}].results[{position}]: sin ruleId")
            if not (result.get("message") or {}).get("text"):
                errors.append(f"runs[{index}].results[{position}]: sin message.text")
            if location_of(result) is None:
                errors.append(f"runs[{index}].results[{position}]: sin ubicación física")
    return errors


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Normaliza SARIF externo a findings.json.")
    parser.add_argument("sarif")
    parser.add_argument("--output")
    parser.add_argument("--target", default="sarif importado")
    parser.add_argument("--audit-id", default="audit-sarif")
    parser.add_argument("--fail-on", choices=("none", "low", "medium", "high", "critical"), default="none")
    parser.add_argument("--check", action="store_true", help="Solo comprueba compatibilidad con upload-sarif")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.sarif)
    if not path.is_file():
        print(f"No existe: {path}", file=sys.stderr)
        return 2
    try:
        sarif = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        print(f"SARIF ilegible: {error}", file=sys.stderr)
        return 2

    if args.check:
        errors = check_upload_sarif(sarif)
        if args.json:
            print(json.dumps({"compatible": not errors, "errors": errors}, indent=2, ensure_ascii=False))
        elif errors:
            print(f"NO COMPATIBLE: {len(errors)} problema(s)")
            for error in errors:
                print(f"  - {error}")
        else:
            print("OK: apto para upload-sarif")
        return 0 if not errors else 1

    report = normalize(sarif, args.target, args.audit_id)
    findings = report["findings"]
    skipped = report["skipped_without_location"]
    tools = report["tools"]
    payload = {
        "audit_id": report["audit_id"],
        "target": report["target"],
        "findings": findings,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")

    threshold = SEVERITY_RANK.get(args.fail_on, 0)
    worst = 0
    for run in sarif.get("runs") or []:
        rules = rule_index(run if isinstance(run, dict) else {})
        for result in (run or {}).get("results") or []:
            if not isinstance(result, dict):
                continue
            rule = rules.get(str(result.get("ruleId")), {})
            worst = max(worst, SEVERITY_RANK.get(severity_of(result, rule), 0))
    triggered = threshold > 0 and worst >= threshold

    if args.json:
        print(text, end="")
    else:
        print(f"{len(findings)} hallazgo(s) importado(s) · {skipped} sin ubicación · "
              f"herramientas: {', '.join(tools) or 'ninguna'}")
        if args.output:
            print(f"findings.json escrito en {args.output}")
        if threshold:
            print(f"severidad máxima observada: {worst} (umbral {threshold})")

    return 1 if triggered else 0


if __name__ == "__main__":
    sys.exit(main())
