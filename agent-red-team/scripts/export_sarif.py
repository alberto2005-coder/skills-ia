"""Exporta un informe de `agent-red-team` a SARIF 2.1.0 (opcional).

Uso:
    py agent-red-team/scripts/export_sarif.py <informe.json> [--output salida.sarif]
        [--include-pending]

Solo se exportan los hallazgos `confirmed`; con `--include-pending` se añaden los
`needs_validation` como `note`. Los `rejected` nunca salen: están refutados y
viven en el anexo del informe markdown.

Código de salida: 0 exportado · 1 informe inválido · 2 fichero ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
SARIF_VERSION = "2.1.0"
LEVELS = {"reject": "error", "critical": "error", "high": "error", "medium": "warning", "low": "note"}


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def slug(text: object) -> str:
    decomposed = unicodedata.normalize("NFKD", str(text).lower())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9]+", "-", plain).strip("-")
    return value or "otros"


def uri_for(path: object) -> str:
    uri = str(path).replace("\\", "/")
    while uri.startswith("./"):
        uri = uri[2:]
    return uri


def level_for(finding: dict) -> str:
    if finding.get("verificacion") == "needs_validation":
        return "note"
    if finding.get("nivel") == "REJECT":
        return "error"
    return LEVELS.get(finding.get("severidad"), "note")


def selected_findings(report: dict, include_pending: bool) -> list[dict]:
    chosen = []
    for finding in report.get("findings") or []:
        if not isinstance(finding, dict):
            continue
        verification = finding.get("verificacion")
        if verification == "confirmed":
            chosen.append(finding)
        elif verification == "needs_validation" and include_pending:
            chosen.append(finding)
    return chosen


def build_sarif(report: dict, include_pending: bool = False) -> dict:
    rules: dict[str, dict] = {}
    rule_index: dict[str, int] = {}
    results = []

    for finding in selected_findings(report, include_pending):
        categoria = finding.get("categoria") or "otros"
        rule_id = f"agent-red-team/{slug(categoria)}"
        level = level_for(finding)

        if rule_id not in rules:
            rule_index[rule_id] = len(rules)
            rules[rule_id] = {
                "id": rule_id,
                "name": slug(categoria),
                "shortDescription": {"text": str(categoria)},
                "defaultConfiguration": {"level": level},
            }

        result = {
            "ruleId": rule_id,
            "ruleIndex": rule_index[rule_id],
            "level": level,
            "message": {
                "text": f"{finding.get('titulo', 'Hallazgo')}. {finding.get('recomendacion', '')}".strip(),
            },
            "partialFingerprints": {
                "agentRedTeamId/v1": str(finding.get("id", "")),
            },
            "properties": {
                "verification": finding.get("verificacion"),
                "severity": finding.get("severidad"),
                "category": str(categoria),
                "reject": finding.get("nivel") == "REJECT",
            },
        }

        file = finding.get("fichero")
        if isinstance(file, str) and file.strip():
            physical = {"artifactLocation": {"uri": uri_for(file)}}
            line = finding.get("linea")
            if isinstance(line, int) and line > 0:
                physical["region"] = {"startLine": line}
            result["locations"] = [{"physicalLocation": physical}]

        results.append(result)

    driver = {
        "name": "agent-red-team",
        "version": str(report.get("version") or "2.0.0"),
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
                    "target": report.get("target"),
                    "modo": report.get("modo"),
                    "veredicto": report.get("veredicto"),
                    "puntuacion_riesgo": report.get("puntuacion_riesgo"),
                    "rechazo": bool(report.get("rechazo")),
                    "fecha": report.get("fecha"),
                },
            }
        ],
    }


def load_report(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("la raíz debe ser un objeto JSON")
    if not isinstance(data.get("findings"), list):
        raise ValueError("el informe no tiene una lista «findings»")
    return data


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Exporta un informe a SARIF 2.1.0.")
    parser.add_argument("report", help="Informe JSON del esquema report-schema.json")
    parser.add_argument("--output", help="Fichero .sarif de salida; sin él, se imprime en stdout")
    parser.add_argument(
        "--include-pending",
        action="store_true",
        help="Incluye needs_validation como note (los rejected nunca se exportan)",
    )
    args = parser.parse_args(argv)

    path = Path(args.report)
    if not path.is_file():
        print(f"No existe: {path}", file=sys.stderr)
        return 2
    try:
        report = load_report(path)
    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(f"Informe inválido: {error}", file=sys.stderr)
        return 1

    sarif = build_sarif(report, include_pending=args.include_pending)
    payload = json.dumps(sarif, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        out = Path(args.output)
        try:
            out.write_text(payload, encoding="utf-8")
        except OSError as error:
            # Sin esto el directorio inexistente daba traceback en vez del
            # código de salida 2 documentado en la docstring.
            print(f"No se pudo escribir {out}: {error}", file=sys.stderr)
            return 2
        count = len(sarif["runs"][0]["results"])
        print(f"SARIF escrito en {out} ({count} resultado(s))")
    else:
        print(payload, end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
