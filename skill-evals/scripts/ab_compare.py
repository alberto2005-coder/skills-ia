"""Comparativa A/B de dos corridas de evaluación ya grabadas.

Uso:
    py skill-evals/scripts/ab_compare.py --a A.json --b B.json [--json]
        [--out RUTA] [--max-cost-increase PCT] [--max-latency-increase PCT]
        [--max-variability-increase ABS] [--min-effectiveness-delta PP]

No ejecuta agentes ni modelos: lee dos corridas en JSON, calcula eficacia,
cumplimiento, coste, latencia y variabilidad, y compara B contra A. Una corrida
admite `cases[].samples` o una lista plana de muestras con el mismo `id`.

Código de salida: 0 sin puerta superada · 1 alguna puerta superada · 2 corrida
ilegible.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

KINDS_OBLIGATORIOS = ("negative", "required")


def force_utf8():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), None
    except OSError as error:
        return None, "no se pudo leer %s: %s" % (path, error)
    except json.JSONDecodeError as error:
        return None, "JSON inválido en %s: %s" % (path, error)


def normalize(document, path):
    """{label, cases: {id: {kind, samples}}} o error legible."""
    if not isinstance(document, dict) or not isinstance(document.get("cases"), list):
        return None, "%s debe declarar una lista «cases»" % path
    cases = {}
    for entry in document["cases"]:
        if not isinstance(entry, dict) or not entry.get("id"):
            return None, "%s: caso sin «id»" % path
        identifier = str(entry["id"])
        kind = str(entry.get("kind", "positive"))
        if "samples" in entry:
            raw = entry["samples"] or []
        else:
            raw = [entry]
        if not isinstance(raw, list):
            return None, "%s: «samples» de %s no es una lista" % (path, identifier)
        bucket = cases.setdefault(identifier, {"kind": kind, "samples": []})
        for sample in raw:
            if not isinstance(sample, dict):
                return None, "%s: muestra de %s que no es un objeto" % (path, identifier)
            bucket["samples"].append({
                "passed": bool(sample.get("passed")),
                "score": float(sample.get("score", 0.0)),
                "latency_ms": float(sample.get("latency_ms", 0.0)),
                "cost_usd": float(sample.get("cost_usd", 0.0)),
            })
    return {"label": str(document.get("label") or Path(path).stem), "cases": cases}, None


def metrics(run):
    samples = [sample for case in run["cases"].values() for sample in case["samples"]]
    if not samples:
        return {
            "cases": 0, "samples": 0, "effectiveness": None, "compliance": None,
            "cost": None, "latency": None, "variability": None,
        }
    required = [
        sample for case in run["cases"].values() if case["kind"] in KINDS_OBLIGATORIOS
        for sample in case["samples"]
    ]
    deviations = []
    for case in run["cases"].values():
        scores = [sample["score"] for sample in case["samples"]]
        if len(scores) > 1:
            deviations.append(statistics.pstdev(scores))
    return {
        "cases": len(run["cases"]),
        "samples": len(samples),
        "effectiveness": sum(1 for sample in samples if sample["passed"]) / len(samples),
        "compliance": (sum(1 for sample in required if sample["passed"]) / len(required)) if required else None,
        "cost": sum(sample["cost_usd"] for sample in samples) / len(samples),
        "latency": sum(sample["latency_ms"] for sample in samples) / len(samples),
        "variability": (sum(deviations) / len(deviations)) if deviations else None,
    }


def per_case(run):
    summary = {}
    for identifier, case in run["cases"].items():
        samples = case["samples"]
        summary[identifier] = (sum(1 for sample in samples if sample["passed"]) / len(samples)) if samples else None
    return summary


def delta(a, b, absolute=True):
    if a is None or b is None:
        return None
    return round(b - a, 6) if absolute else round(((b - a) / a) * 100, 3) if a else None


def compare(run_a, run_b):
    metrics_a, metrics_b = metrics(run_a), metrics(run_b)
    cases_a, cases_b = per_case(run_a), per_case(run_b)
    shared = sorted(set(cases_a) & set(cases_b))
    cases = [
        {
            "id": identifier,
            "a": cases_a[identifier],
            "b": cases_b[identifier],
            "delta": delta(cases_a[identifier], cases_b[identifier]),
        }
        for identifier in shared
    ]
    return {
        "source": "eval-ab",
        "a": dict(metrics_a, label=run_a["label"]),
        "b": dict(metrics_b, label=run_b["label"]),
        "delta": {
            "effectiveness": delta(metrics_a["effectiveness"], metrics_b["effectiveness"]),
            "compliance": delta(metrics_a["compliance"], metrics_b["compliance"]),
            "cost_pct": delta(metrics_a["cost"], metrics_b["cost"], absolute=False),
            "latency_pct": delta(metrics_a["latency"], metrics_b["latency"], absolute=False),
            "variability": delta(metrics_a["variability"], metrics_b["variability"]),
        },
        "only_in_a": sorted(set(cases_a) - set(cases_b)),
        "only_in_b": sorted(set(cases_b) - set(cases_a)),
        "cases": cases,
    }


def gates(report, args):
    checks = []
    comparisons = (
        ("max-cost-increase", report["delta"]["cost_pct"], args.max_cost_increase, "menor o igual"),
        ("max-latency-increase", report["delta"]["latency_pct"], args.max_latency_increase, "menor o igual"),
        ("max-variability-increase", report["delta"]["variability"], args.max_variability_increase, "menor o igual"),
    )
    for name, value, limit, _ in comparisons:
        if limit is None:
            continue
        checks.append({
            "gate": name,
            "value": value,
            "limit": limit,
            "passed": value is not None and value <= limit,
        })
    if args.min_effectiveness_delta is not None:
        value = report["delta"]["effectiveness"]
        checks.append({
            "gate": "min-effectiveness-delta",
            "value": value,
            "limit": args.min_effectiveness_delta,
            "passed": value is not None and value >= args.min_effectiveness_delta,
        })
    return checks


def main(argv=None):
    force_utf8()
    parser = argparse.ArgumentParser(description="Comparativa A/B de dos corridas grabadas.")
    parser.add_argument("--a", required=True, help="corrida de control")
    parser.add_argument("--b", required=True, help="corrida de la variante")
    parser.add_argument("--json", action="store_true", help="imprime la comparativa en JSON")
    parser.add_argument("--out", help="escribe la comparativa en esta ruta")
    parser.add_argument("--max-cost-increase", type=float, help="porcentaje máximo de subida de coste")
    parser.add_argument("--max-latency-increase", type=float, help="porcentaje máximo de subida de latencia")
    parser.add_argument("--max-variability-increase", type=float, help="subida máxima de variabilidad (absoluta)")
    parser.add_argument("--min-effectiveness-delta", type=float, help="mejora mínima de eficacia (puntos)")
    args = parser.parse_args(argv)

    document_a, error = read(args.a)
    if error:
        print("ab_compare: %s" % error, file=sys.stderr)
        return 2
    document_b, error = read(args.b)
    if error:
        print("ab_compare: %s" % error, file=sys.stderr)
        return 2

    run_a, error = normalize(document_a, args.a)
    if error:
        print("ab_compare: %s" % error, file=sys.stderr)
        return 2
    run_b, error = normalize(document_b, args.b)
    if error:
        print("ab_compare: %s" % error, file=sys.stderr)
        return 2

    report = compare(run_a, run_b)
    report["gates"] = gates(report, args)
    report["verdict"] = "pass" if all(item["passed"] for item in report["gates"]) else "fail"

    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    if not args.json:
        print("veredicto: %s" % report["verdict"], file=sys.stderr)
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
