"""Compara el coste mensual de dos inventarios y aplica guardrails de CI.

Uso:
    py finops-auditor/scripts/cost_diff.py --before antes.json --after despues.json
        [--max-increase 100] [--max-percent 10] [--budget 5000] [--json]
        [--fail-on guardrail]

Compara por `id` de recurso: altas, bajas y cambios de precio. Sobre el total
aplica tres guardrails independientes y devuelve qué límite se rompió y con qué
cifra. Sin red: solo lee los dos JSON.

Código de salida: 0 sin guardrails superados · 1 algún guardrail superado ·
2 fichero ilegible.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path) -> dict[str, float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    costs: dict[str, float] = {}
    for resource in data.get("resources", []):
        identifier = str(resource.get("id") or resource.get("name") or f"recurso_{len(costs)}")
        costs[identifier] = float(resource.get("monthly_cost", 0.0) or 0.0)
    return costs


def compare(before: dict[str, float], after: dict[str, float]) -> dict:
    added = {key: after[key] for key in sorted(set(after) - set(before))}
    removed = {key: before[key] for key in sorted(set(before) - set(after))}
    changed = {
        key: {"before": before[key], "after": after[key], "delta": round(after[key] - before[key], 2)}
        for key in sorted(set(before) & set(after))
        if round(after[key] - before[key], 2) != 0
    }
    before_total = round(sum(before.values()), 2)
    after_total = round(sum(after.values()), 2)
    delta = round(after_total - before_total, 2)
    percent = round(delta / before_total * 100, 2) if before_total else None
    return {
        "before_total": before_total,
        "after_total": after_total,
        "delta": delta,
        "delta_percent": percent,
        "resources": {
            "added": [{"id": key, "cost": round(value, 2)} for key, value in added.items()],
            "removed": [{"id": key, "cost": round(value, 2)} for key, value in removed.items()],
            "changed": [{"id": key, **value} for key, value in changed.items()],
        },
    }


def guardrails(report: dict, max_increase: float | None,
               max_percent: float | None, budget: float | None) -> list[dict]:
    breaches = []
    if max_increase is not None and report["delta"] > max_increase:
        breaches.append({
            "guardrail": "max-increase",
            "limit": max_increase,
            "actual": report["delta"],
            "message": f"el coste sube {report['delta']}, por encima del máximo permitido {max_increase}",
        })
    if max_percent is not None and report["delta_percent"] is not None \
            and report["delta_percent"] > max_percent:
        breaches.append({
            "guardrail": "max-percent",
            "limit": max_percent,
            "actual": report["delta_percent"],
            "message": f"el coste sube {report['delta_percent']} %, por encima del {max_percent} % permitido",
        })
    if budget is not None and report["after_total"] > budget:
        breaches.append({
            "guardrail": "budget",
            "limit": budget,
            "actual": report["after_total"],
            "message": f"el total nuevo {report['after_total']} supera el presupuesto {budget}",
        })
    return breaches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diferencia de coste con guardrails.")
    parser.add_argument("--before", required=True, help="inventario anterior")
    parser.add_argument("--after", required=True, help="inventario nuevo")
    parser.add_argument("--max-increase", type=float, help="aumento absoluto permitido")
    parser.add_argument("--max-percent", type=float, help="aumento porcentual permitido")
    parser.add_argument("--budget", type=float, help="techo del coste total nuevo")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="guardrail", choices=["guardrail", "none"])
    args = parser.parse_args(argv)

    before_path, after_path = Path(args.before), Path(args.after)
    if not before_path.exists() or not after_path.exists():
        print("inventario inexistente")
        return 2
    try:
        before, after = load(before_path), load(after_path)
    except (OSError, ValueError) as error:
        print(f"inventario ilegible: {error}")
        return 2

    report = compare(before, after)
    breaches = guardrails(report, args.max_increase, args.max_percent, args.budget)
    report["breaches"] = breaches

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        percent = "n/a" if report["delta_percent"] is None else f"{report['delta_percent']} %"
        print(f"antes: {report['before_total']} · después: {report['after_total']} "
              f"· delta: {report['delta']} ({percent})")
        for item in report["resources"]["added"]:
            print(f"  + {item['id']}: {item['cost']}")
        for item in report["resources"]["removed"]:
            print(f"  - {item['id']}: {item['cost']}")
        for item in report["resources"]["changed"]:
            print(f"  ~ {item['id']}: {item['before']} -> {item['after']} ({item['delta']:+})")
        for breach in breaches:
            print(f"[GUARDRAIL] {breach['guardrail']}: {breach['message']}")
        print(f"guardrails superados: {len(breaches)}")

    if args.fail_on == "none":
        return 0
    return 1 if breaches else 0


if __name__ == "__main__":
    sys.exit(main())
