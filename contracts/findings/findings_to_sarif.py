"""Exporta `findings.json` v1.0.0 a SARIF 2.1.0, una sola vez para todo el catálogo.

Uso:
    py contracts/findings/findings_to_sarif.py <findings.json> [--output <salida.sarif>]

En vez de repetir la lógica SARIF en cada auditor, todos los informes del
contrato pasan por aquí. Mapeo de severidad: `critical` y `high` → `error`,
`medium` → `warning`, `low` e `info` → `note`.

Ubicación: un `file` va a `physicalLocation` con `region` solo si trae línea; una
`url` va a `artifactLocation.uri`; un `resource` o un `schema` va a
`logicalLocations`, porque inventarles un fichero y una línea sería mentir en el
panel de Code Scanning.

Código de salida: 0 exportado · 1 informe que no cumple el contrato · 2 ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import findings_contract as contract

SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
SARIF_VERSION = "2.1.0"
LEVELS = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "info": "note"}
NAME_SAFE = re.compile(r"[^A-Za-z0-9_]+")


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra página de códigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def uri_for(target: str) -> str:
    """Ruta relativa con barras normales: SARIF exige URI, no ruta de Windows."""
    uri = str(target).replace("\\", "/")
    while uri.startswith("./"):
        uri = uri[2:]
    return uri


def relativize(uri: str, base: object) -> str:
    """Ruta absoluta dentro del objetivo → relativa.

    GitHub Code Scanning no resuelve `C:\\Users\\...`: si el hallazgo cae dentro
    del `target` del informe, se recorta a la ruta relativa del repositorio.
    """
    if not isinstance(base, str) or not base.strip():
        return uri
    root = uri_for(base).rstrip("/")
    if uri.lower().startswith(root.lower() + "/"):
        return uri[len(root) + 1:]
    return uri


def logical_location(kind: str, target: str) -> dict:
    """Sitio del hallazgo cuando no es un fichero: recurso o esquema por nombre."""
    return {"locations": [{"logicalLocations": [{"fullyQualifiedName": target, "kind": kind}]}]}


def location_block(finding: dict, base: object = None) -> dict:
    """`locations` de SARIF para una ubicación híbrida, o vacío si no aplica."""
    location = finding.get("location") or {}
    kind = location.get("type")
    target = str(location.get("target") or "")
    if kind == "url":
        # `GET /users/{id}` no es una URI válida: un endpoint sin esquema va a
        # `logicalLocations` en vez de a `artifactLocation.uri`.
        if target.startswith(("http://", "https://")):
            return {"locations": [{"physicalLocation": {"artifactLocation": {"uri": target}}}]}
        return logical_location(kind, target)
    if kind == "file":
        physical = {"artifactLocation": {"uri": relativize(uri_for(target), base)}}
        line = location.get("line")
        if isinstance(line, int) and line > 0:
            region = {"startLine": line}
            end_line = location.get("end_line")
            if isinstance(end_line, int) and end_line >= line:
                region["endLine"] = end_line
            physical["region"] = region
        return {"locations": [{"physicalLocation": physical}]}
    if kind in ("resource", "schema"):
        return logical_location(kind, target)
    return {}


def help_uri(finding: dict) -> str | None:
    for reference in finding.get("references") or []:
        url = reference.get("url")
        if isinstance(url, str) and url:
            return url
    return None


def build_rule(rule_id: str, finding: dict) -> dict:
    rule = {
        "id": rule_id,
        "name": NAME_SAFE.sub("_", rule_id),
        "shortDescription": {"text": finding.get("title") or rule_id},
        "defaultConfiguration": {"level": LEVELS.get(finding.get("severity"), "note")},
    }
    uri = help_uri(finding)
    if uri:
        rule["helpUri"] = uri
        rule["properties"] = {"tags": [reference.get("id") for reference in finding["references"]
                                      if reference.get("id")]}
    return rule


def build_result(finding: dict, rule_index: int, base: object = None) -> dict:
    rule_id = str(finding.get("rule_id"))
    result = {
        "ruleId": rule_id,
        "ruleIndex": rule_index,
        "level": LEVELS.get(finding.get("severity"), "note"),
        "message": {"text": str(finding.get("message") or finding.get("title") or rule_id)},
        "partialFingerprints": {"skillsIaFingerprint/v1": str(finding.get("fingerprint") or "")},
        "properties": {
            "severity": finding.get("severity"),
            "confidence": finding.get("confidence"),
            "title": finding.get("title"),
            "locationType": (finding.get("location") or {}).get("type"),
            "target": (finding.get("location") or {}).get("target"),
        },
    }
    result.update(location_block(finding, base))
    return result


def build_sarif(payload: dict) -> dict:
    rules: dict = {}
    results = []
    base = payload.get("target")
    for finding in payload.get("findings") or []:
        rule_id = str(finding.get("rule_id"))
        if rule_id not in rules:
            rules[rule_id] = build_rule(rule_id, finding)
        results.append(build_result(finding, list(rules).index(rule_id), base))

    tool = payload.get("tool") or {}
    driver = {
        "name": str(tool.get("package") or "skills-ia"),
        "version": str(tool.get("version") or "0.0.0"),
        "rules": list(rules.values()),
    }
    run_properties = {
        "schemaVersion": payload.get("schema_version"),
        "skill": tool.get("skill"),
        "target": payload.get("target"),
        "generatedAt": payload.get("generated_at"),
        "summary": payload.get("summary"),
    }
    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [{"tool": {"driver": driver}, "results": results, "properties": run_properties}],
    }


def main(argv: list | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Exporta findings.json v1.0.0 a SARIF 2.1.0.")
    parser.add_argument("findings", help="Ruta de findings.json")
    parser.add_argument("--output", help="Fichero .sarif de salida; sin él se imprime en stdout")
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
    if not isinstance(payload, dict) or not isinstance(payload.get("findings"), list):
        print("Informe inválido: la raíz debe ser un objeto con «findings»", file=sys.stderr)
        return 1

    sarif = build_sarif(payload)
    text = json.dumps(sarif, indent=2, ensure_ascii=False) + "\n"
    if not args.output:
        print(text, end="")
        return 0
    try:
        Path(args.output).write_text(text, encoding="utf-8")
    except OSError as error:
        print(f"No se pudo escribir {args.output}: {error}", file=sys.stderr)
        return 2
    print(f"SARIF escrito en {args.output} ({len(sarif['runs'][0]['results'])} resultado(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
