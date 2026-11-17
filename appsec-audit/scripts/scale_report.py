"""Informe de sistema: varios repos, topología de terceros, perfil y coste por fase.

Uso:
    py appsec-audit/scripts/scale_report.py --repos a,b [--vendor vendors.json]
        [--profile standard] [--cost costes.json] [--output informe.json] [--json]

Lee los artefactos de cada repo (`.appsec-audit/findings.json` y
`coverage-ledger.json`), dibuja la topología repo → tercero y estima horas y
coste por fase según el perfil. No ejecuta nada del proyecto auditado.

Código de salida: 0 correcto · 2 entrada ilegible o repos inexistentes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROFILES = {"quick": 1.0, "standard": 2.0, "deep": 4.0}
BASE_HOURS = {
    "recon": 1.0,
    "code": 2.0,
    "infra": 1.0,
    "threat": 0.5,
    "deps": 0.5,
    "ci": 0.5,
    "report": 1.0,
}
DEFAULT_HOURLY = 80.0
DEFAULT_CURRENCY = "EUR"


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_summary(name: str, path: Path) -> dict:
    audit = path / ".appsec-audit"
    findings_path = audit / "findings.json"
    ledger_path = audit / "coverage-ledger.json"
    summary: dict = {
        "name": name,
        "path": str(path),
        "artifacts": {"findings": findings_path.is_file(), "ledger": ledger_path.is_file()},
        "findings": {"confirmed": 0, "needs_validation": 0, "rejected": 0, "by_severity": {}},
        "ledger": {"units": 0, "gaps": 0},
        "notes": [],
    }

    if findings_path.is_file():
        payload = load_json(findings_path)
        for item in payload.get("findings") or []:
            if not isinstance(item, dict):
                continue
            verdict = item.get("verdict")
            if verdict in summary["findings"]:
                summary["findings"][verdict] += 1
            if verdict == "confirmed":
                severity = item.get("severity") or "sin severidad"
                summary["findings"]["by_severity"][severity] = (
                    summary["findings"]["by_severity"].get(severity, 0) + 1
                )
    else:
        summary["notes"].append("sin findings.json: repo contado como superficie, no como hallazgos")

    if ledger_path.is_file():
        ledger = load_json(ledger_path)
        units = [unit for unit in ledger.get("units") or [] if isinstance(unit, dict)]
        summary["ledger"]["units"] = len(units)
        summary["ledger"]["gaps"] = sum(
            1 for unit in units if unit.get("status") in ("planned", "hunting")
        )

    return summary


def load_vendors(path: Path | None) -> list[dict]:
    if path is None:
        return []
    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("vendors"), list):
        raise ValueError("el fichero de terceros no tiene una lista «vendors»")
    vendors = []
    for item in data["vendors"]:
        if not isinstance(item, dict) or not item.get("name"):
            raise ValueError(f"tercero inválido: {item!r}")
        vendors.append({
            "name": str(item["name"]),
            "service": item.get("service"),
            "data": item.get("data"),
            "repos": [str(repo) for repo in item.get("repos") or []],
        })
    return vendors


def load_costs(path: Path | None) -> tuple[float, str]:
    if path is None:
        return DEFAULT_HOURLY, DEFAULT_CURRENCY
    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError("el fichero de costes debe ser un objeto")
    hourly = data.get("hourly", DEFAULT_HOURLY)
    if not isinstance(hourly, (int, float)) or hourly <= 0:
        raise ValueError("«hourly» debe ser un número positivo")
    return float(hourly), str(data.get("currency", DEFAULT_CURRENCY))


def topology(repos: list[dict], vendors: list[dict]) -> dict:
    names = {repo["name"] for repo in repos}
    edges = []
    for vendor in vendors:
        linked = [repo for repo in vendor["repos"] if repo in names]
        for repo in linked:
            edges.append({"from": f"repo:{repo}", "to": f"vendor:{vendor['name']}",
                          "data": vendor["data"]})
        if not linked:
            edges.append({"from": "system", "to": f"vendor:{vendor['name']}",
                          "data": vendor["data"]})
    return {
        "nodes": [f"repo:{repo['name']}" for repo in repos] + [f"vendor:{vendor['name']}" for vendor in vendors],
        "edges": edges,
        "vendors_without_repo": [vendor["name"] for vendor in vendors
                                 if not set(vendor["repos"]) & names],
    }


def cost_breakdown(profile: str, repos: int, vendors: int, hourly: float, currency: str) -> dict:
    multiplier = PROFILES[profile]
    phases = []
    for phase, hours in BASE_HOURS.items():
        scaled = round(hours * multiplier * max(repos, 1), 2)
        if vendors and phase in ("threat", "deps"):
            scaled = round(scaled + 0.5 * vendors * multiplier, 2)
        phases.append({"phase": phase, "hours": scaled, "cost": round(scaled * hourly, 2)})
    total_hours = round(sum(item["hours"] for item in phases), 2)
    return {
        "currency": currency,
        "hourly": hourly,
        "profile": profile,
        "repos": max(repos, 1),
        "vendors": vendors,
        "phases": phases,
        "total_hours": total_hours,
        "total_cost": round(total_hours * hourly, 2),
    }


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Informe de sistema multi-repo con coste.")
    parser.add_argument("--repos", required=True, help="Repos separados por coma (nombre=ruta o ruta)")
    parser.add_argument("--vendor", help="JSON con la lista de terceros")
    parser.add_argument("--profile", choices=tuple(PROFILES), default="standard")
    parser.add_argument("--cost", help="JSON con hourly y currency")
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    entries = [item.strip() for item in args.repos.split(",") if item.strip()]
    if not entries:
        print("--repos no puede estar vacío", file=sys.stderr)
        return 2

    repos = []
    for entry in entries:
        name, _, path_text = entry.partition("=")
        if not path_text:
            path_text = name
        path = Path(path_text)
        if not path.is_dir():
            print(f"No existe el repo: {path}", file=sys.stderr)
            return 2
        try:
            repos.append(repo_summary(name, path))
        except (json.JSONDecodeError, OSError) as error:
            print(f"Artefactos ilegibles en {path}: {error}", file=sys.stderr)
            return 2

    try:
        vendors = load_vendors(Path(args.vendor) if args.vendor else None)
        hourly, currency = load_costs(Path(args.cost) if args.cost else None)
    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(f"Entrada ilegible: {error}", file=sys.stderr)
        return 2

    report = {
        "system": {"repos": len(repos), "vendors": len(vendors), "profile": args.profile},
        "repos": repos,
        "topology": topology(repos, vendors),
        "cost": cost_breakdown(args.profile, len(repos), len(vendors), hourly, currency),
        "limits": [
            "El coste es una estimación por fase, no un presupuesto cerrado.",
            "Un repo sin artefactos cuenta como superficie pendiente, no como auditoría hecha.",
        ],
    }

    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")

    if args.json:
        print(text, end="")
    else:
        confirmed = sum(repo["findings"]["confirmed"] for repo in repos)
        gaps = sum(repo["ledger"]["gaps"] for repo in repos)
        print(f"{len(repos)} repo(s) · {len(vendors)} tercero(s) · perfil {args.profile}")
        print(f"  confirmados {confirmed} · huecos de ledger {gaps}")
        cost = report["cost"]
        for phase in cost["phases"]:
            print(f"  {phase['phase']:<7} {phase['hours']:>5} h  {phase['cost']:>9.2f} {cost['currency']}")
        print(f"  total   {cost['total_hours']:>5} h  {cost['total_cost']:>9.2f} {cost['currency']}")
        if report["topology"]["vendors_without_repo"]:
            print("  terceros sin repo asociado: " + ", ".join(report["topology"]["vendors_without_repo"]))
        if args.output:
            print(f"Informe escrito en {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
