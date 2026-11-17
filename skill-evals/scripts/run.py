"""Ejecuta los casos contra el router y aplica las puertas de calidad.

Uso:
    py skill-evals/scripts/run.py --cases casos.json [--out run.json]
        [--baseline anterior.json] [--fail-under precision=0.95]
        [--fail-on-regression] [--json]

Reutiliza `tests/trigger_router.py`: mide precisión y recall de activación,
colisiones entre descripciones, presupuesto de tokens del catálogo y
regresiones contra una corrida anterior. Todo offline y determinista.

Código de salida: 0 correcto · 1 puerta o regresión · 2 entrada ilegible.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import evalkit  # noqa: E402


def _read(path: Path) -> dict:
    try:
        return evalkit.read_json(path)
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"no se pudo leer {path}: {error}") from error


def _write(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _gate_report(run: dict, gates: dict[str, float]) -> list[dict]:
    checks = []
    for metric, target in sorted(gates.items()):
        value = float(run["metrics"].get(metric, 0.0))
        checks.append({
            "metric": metric,
            "target": target,
            "value": value,
            "passed": value >= target,
        })
    return checks


def _print_summary(run: dict, diff: dict | None, checks: list[dict]) -> None:
    metrics = run["metrics"]
    print(f"casos: {metrics['cases']} · pass: {metrics['passed']} · "
          f"precision: {metrics['precision']:.3f} · recall: {metrics['recall']:.3f} · "
          f"mrr: {metrics['mrr']:.3f}")
    print(f"colisiones: {metrics['collisions']} · falsos negativos: "
          f"{metrics['false_negatives']} · falsos positivos: {metrics['false_positives']}")
    budget = run["budget"]
    print(f"catálogo: {budget['catalog_tokens']} tokens (límite {budget['catalog_limit']}) · "
          f"fuera de presupuesto: {len(budget['over_budget'])}")
    if diff is not None:
        print(f"regresiones: {len(diff['regressions'])} · arreglos: {len(diff['fixes'])} · "
              f"nuevos: {len(diff['new'])} · retirados: {len(diff['removed'])}")
    for check in checks:
        state = "OK" if check["passed"] else "FALLA"
        print(f"puerta {check['metric']}: {check['value']:.3f} >= {check['target']:.3f} {state}")


def main(argv: list[str] | None = None) -> int:
    evalkit.force_utf8_output()
    parser = argparse.ArgumentParser(description="Ejecuta casos de evaluación de skills.")
    parser.add_argument("--cases", required=True, help="fichero de casos")
    parser.add_argument("--out", help="escribe el informe máquina de la corrida")
    parser.add_argument("--baseline", help="corrida anterior para comparar")
    parser.add_argument("--fail-under", action="append", default=[], metavar="METRICA=VALOR")
    parser.add_argument("--fail-on-regression", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    _, router = evalkit.load_router()
    document = _read(Path(args.cases))
    problems = evalkit.validate_cases(document, router.names)
    if problems:
        for problem in problems:
            print(f"  - {problem}")
        return 2

    run = evalkit.evaluate(router, document)
    diff = None
    if args.baseline:
        diff = evalkit.diff_runs(run, _read(Path(args.baseline)))

    try:
        gates = evalkit.parse_gates(args.fail_under)
    except ValueError as error:
        print(f"gate inválido: {error}")
        return 2

    checks = _gate_report(run, gates)
    gate_failed = any(not check["passed"] for check in checks)
    regression_failed = bool(diff and diff["regressions"]) and args.fail_on_regression
    verdict = "fail" if gate_failed or regression_failed else "pass"
    run["gate"] = {
        "checks": checks,
        "regressions": diff["regressions"] if diff else [],
        "verdict": verdict,
    }

    if args.out:
        _write(Path(args.out), run)

    if args.json:
        print(json.dumps({
            "verdict": verdict,
            "metrics": run["metrics"],
            "gate": run["gate"],
            "diff": diff,
        }, indent=2, ensure_ascii=False))
    else:
        _print_summary(run, diff, checks)
        if diff and diff["regressions"]:
            print("regresiones: " + ", ".join(diff["regressions"]))
        print(f"veredicto: {verdict.upper()}")

    return 0 if verdict == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
