"""Exporta `findings.json` a SARIF 2.1.0 para GitHub Code Scanning.

Uso:
    py appsec-audit/scripts/export_sarif.py <findings.json> [--output appsec.sarif]
        [--include-pending]

Solo salen los `confirmed`; con `--include-pending` se añaden los
`needs_validation` como `note`. Los `rejected` nunca se exportan: están
refutados y su sitio es el anexo del informe.

Código de salida: 0 exportado · 1 informe inválido · 2 fichero ilegible.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from appsec_util import FORMAT_VERSION, TOOL_VERSION, force_utf8_output

SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
SARIF_VERSION = "2.1.0"
LEVELS = {"critical": "error", "high": "error", "medium": "warning", "low": "note"}


def uri_for(path: object) -> str:
    uri = str(path).replace("\\", "/")
    while uri.startswith("./"):
        uri = uri[2:]
    return uri


def level_for(finding: dict) -> str:
    if finding.get("verdict") == "needs_validation":
        return "note"
    return LEVELS.get(finding.get("severity"), "note")


def selected_findings(payload: dict, include_pending: bool) -> list[dict]:
    chosen = []
    for finding in payload.get("findings") or []:
        if not isinstance(finding, dict):
            continue
        verdict = finding.get("verdict")
        if verdict == "confirmed":
            chosen.append(finding)
        elif verdict == "needs_validation" and include_pending:
            chosen.append(finding)
    return chosen


def build_sarif(payload: dict, include_pending: bool = False) -> dict:
    rules: dict[str, dict] = {}
    rule_index: dict[str, int] = {}
    results = []

    for finding in selected_findings(payload, include_pending):
        rule_id = str(finding.get("cwe") or "CWE-0")
        level = level_for(finding)

        if rule_id not in rules:
            rule_index[rule_id] = len(rules)
            rules[rule_id] = {
                "id": rule_id,
                "name": rule_id.replace("-", "_").lower(),
                "shortDescription": {"text": rule_id},
                "defaultConfiguration": {"level": level},
            }

        properties = {
            "verdict": finding.get("verdict"),
            "confidence": finding.get("confidence"),
            "severity": finding.get("severity"),
            "cwe": rule_id,
            "fingerprint": finding.get("fingerprint"),
        }
        for key in ("source_unit", "unresolved"):
            if finding.get(key):
                properties[key] = finding[key]

        result = {
            "ruleId": rule_id,
            "ruleIndex": rule_index[rule_id],
            "level": level,
            "message": {"text": str(finding.get("title") or rule_id)},
            "partialFingerprints": {
                "appsecAuditFingerprint/v1": str(finding.get("fingerprint") or ""),
            },
            "properties": properties,
        }

        location = finding.get("location")
        if isinstance(location, dict) and isinstance(location.get("file"), str) and location["file"].strip():
            physical = {"artifactLocation": {"uri": uri_for(location["file"])}}
            line = location.get("line")
            if isinstance(line, int) and line > 0:
                physical["region"] = {"startLine": line}
            result["locations"] = [{"physicalLocation": physical}]

        results.append(result)

    driver = {
        "name": "appsec-audit",
        "version": TOOL_VERSION,
        "rules": list(rules.values()),
    }

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {"driver": driver},
                "results": results,
                "properties": {
                    "audit_id": payload.get("audit_id"),
                    "format_version": payload.get("format_version") or FORMAT_VERSION,
                    "target": payload.get("target"),
                    "profile": payload.get("profile"),
                    "generated_at": payload.get("generated_at"),
                },
            }
        ],
    }


def load_payload(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("la raíz debe ser un objeto JSON")
    if not isinstance(data.get("findings"), list):
        raise ValueError("el informe no tiene una lista «findings»")
    return data


def main(argv: list[str] | None = None) -> int:
    force_utf8_output()
    parser = argparse.ArgumentParser(description="Exporta findings.json a SARIF 2.1.0.")
    parser.add_argument("findings", help="Ruta de findings.json")
    parser.add_argument("--output", help="Fichero .sarif de salida; sin él se imprime en stdout")
    parser.add_argument(
        "--include-pending",
        action="store_true",
        help="Incluye needs_validation como note (los rejected nunca se exportan)",
    )
    args = parser.parse_args(argv)

    path = Path(args.findings)
    if not path.is_file():
        print(f"No existe: {path}", file=sys.stderr)
        return 2
    try:
        payload = load_payload(path)
    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(f"Informe inválido: {error}", file=sys.stderr)
        return 1

    sarif = build_sarif(payload, include_pending=args.include_pending)
    text = json.dumps(sarif, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        out = Path(args.output)
        try:
            out.write_text(text, encoding="utf-8")
        except OSError as error:
            # Directorio inexistente o sin permisos: exit 2 documentado,
            # no un traceback.
            print(f"No se pudo escribir {out}: {error}", file=sys.stderr)
            return 2
        print(f"SARIF escrito en {out} ({len(sarif['runs'][0]['results'])} resultado(s))")
    else:
        print(text, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
