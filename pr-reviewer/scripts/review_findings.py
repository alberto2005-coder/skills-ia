"""Consolidación de hallazgos con estado real por comprobación.

Uso:
    py pr-reviewer/scripts/review_findings.py --input A.json B.json
        [--require CHECK ...] [--json] [--out RUTA] [--fail-on low|medium|high|none]

Une los informes de varias comprobaciones, deduplica por fichero, línea y regla
y conserva el estado de cada check. Un informe sin `status` se trata como
`not_run`: lo que no consta ejecutado nunca se presenta como limpio.

Código de salida: 0 sin hallazgos sobre el umbral y con los checks exigidos
ejecutados · 1 umbral superado o check exigido sin ejecutar · 2 entrada ilegible.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pr_review_util as util  # noqa: E402

STATUSES = ("ran", "not_run", "skipped")
FIX_REQUIRED = "Ejecutar el check exigido antes de dar el PR por revisado."
FIX_STATUS = "Declarar el estado real del check: ran, not_run o skipped."


def normalize(path):
    """(check, status, findings) de un informe, o error legible."""
    data, error = util.load_json(path)
    if error:
        return None, error
    if not isinstance(data, dict):
        return None, "%s debe ser un objeto JSON con «check» y «findings»" % path
    check = str(data.get("check") or Path(path).stem)
    status = str(data.get("status") or "not_run").strip().lower()
    if status not in STATUSES:
        return None, "%s declara un estado desconocido: %r" % (path, status)
    raw = data.get("findings") or []
    if not isinstance(raw, list):
        return None, "%s: «findings» debe ser una lista" % path
    findings = []
    for item in raw:
        if not isinstance(item, dict):
            return None, "%s: hallazgo que no es un objeto" % path
        severity = str(item.get("severity", "low")).lower()
        if severity not in util.SEVERITIES:
            return None, "%s: severidad desconocida %r" % (path, severity)
        findings.append(util.finding(
            str(item.get("file", path)), int(item.get("line", 1)), str(item.get("rule", "sin-regla")),
            severity, str(item.get("message", "")), str(item.get("fix", "")),
        ))
    return (check, status, findings), None


def consolidate(reports, required):
    """Informe final: checks con estado, deduplicados y totales."""
    status_by_check = {}
    order = []
    merged = {}
    for check, status, findings in reports:
        if check not in status_by_check:
            status_by_check[check] = status
            order.append(check)
        elif status_by_check[check] == "ran" and status != "ran":
            # Un check solo es `ran` si todas sus entradas se ejecutaron.
            status_by_check[check] = status
        for item in findings:
            key = (item["file"], item["line"], item["rule"])
            if key not in merged:
                merged[key] = dict(item, checks=[check], duplicates=1)
                continue
            kept = merged[key]
            kept["duplicates"] += 1
            if check not in kept["checks"]:
                kept["checks"].append(check)
            if util.severity_rank(item["severity"]) > util.severity_rank(kept["severity"]):
                kept["severity"] = item["severity"]

    findings = util.sort_findings(list(merged.values()))
    for check in required:
        if check not in status_by_check:
            findings.append(util.finding(
                "checks.json", 1, "check-no-ejecutado", "high",
                "el check exigido «%s» no aparece en ningún informe" % check, FIX_REQUIRED,
            ))
        elif status_by_check[check] != "ran":
            findings.append(util.finding(
                "checks.json", 1, "check-no-ejecutado", "high",
                "el check exigido «%s» está en estado %s" % (check, status_by_check[check]), FIX_REQUIRED,
            ))

    findings = util.sort_findings(findings)
    summary = util.summarize(findings)
    summary["checks_ran"] = sum(1 for status in status_by_check.values() if status == "ran")
    summary["checks_not_run"] = sum(1 for status in status_by_check.values() if status != "ran")
    return {
        "source": "pr-findings",
        "checks": [{"check": name, "status": status_by_check[name]} for name in order],
        "not_run": [name for name in order if status_by_check[name] != "ran"],
        "required": sorted(set(required)),
        "summary": summary,
        "findings": findings,
    }


def main(argv=None):
    util.force_utf8()
    parser = argparse.ArgumentParser(description="Consolida hallazgos con estado por check.")
    parser.add_argument("--input", nargs="+", required=True, help="informes JSON de entrada")
    parser.add_argument("--require", action="append", default=[], help="check que debe estar en estado ran")
    parser.add_argument("--json", action="store_true", help="imprime el informe en JSON")
    parser.add_argument("--out", help="escribe el informe en esta ruta")
    parser.add_argument("--fail-on", choices=("low", "medium", "high", "none"), default="high")
    args = parser.parse_args(argv)

    reports = []
    for path in args.input:
        report, error = normalize(path)
        if error:
            print("review_findings: %s" % error, file=sys.stderr)
            return 2
        reports.append(report)

    payload = consolidate(reports, args.require)
    util.emit(payload, args.out)
    missing = {name for name in payload["required"]} - {item["check"] for item in payload["checks"] if item["status"] == "ran"}
    if missing or util.exceeds(payload["findings"], args.fail_on):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
