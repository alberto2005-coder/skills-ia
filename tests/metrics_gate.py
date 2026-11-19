"""Gate de métricas del repositorio: los hallazgos `high` y los clones no crecen.

Los umbrales viven en `tests/metrics_baseline.json`; este script solo los aplica.
Se ejecuta en CI y en local con el intérprete del proyecto, sin red ni instalación:

    py tests/metrics_gate.py

Código de salida: 0 dentro del tope · 1 se ha superado · 2 error de lectura.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "tests" / "metrics_baseline.json"


def load_module(name: str, path: Path):
    """Carga un script del paquete sin ejecutar su `main`."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit("no se puede cargar %s" % path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def code_metrics_high(module) -> list[dict]:
    findings: list[dict] = []
    for path in module.iter_files(ROOT):
        findings.extend(module.scan_file(path)[1])
    return [item for item in findings if item["severity"] == "high"]


def clone_detect_findings(module, min_tokens: int, threshold: float) -> list[dict]:
    _, functions = module.collect(ROOT, 8, min_tokens)
    return module.compare(functions, threshold)


def relative(value: str) -> str:
    try:
        return Path(value).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return value


def main() -> int:
    try:
        limits = json.loads(BASELINE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("no se puede leer el baseline: %s" % exc, file=sys.stderr)
        return 2

    metrics = load_module("code_metrics", ROOT / "refactor-surgeon" / "scripts" / "code_metrics.py")
    clones = load_module("clone_detect", ROOT / "refactor-surgeon" / "scripts" / "clone_detect.py")

    high_limit = int(limits["code_metrics"]["high"])
    clone_limit = int(limits["clone_detect"]["clones"])
    min_tokens = int(limits["clone_detect"]["min_tokens"])
    threshold = float(limits["clone_detect"]["threshold"])

    high = code_metrics_high(metrics)
    duplicated = clone_detect_findings(clones, min_tokens, threshold)

    failures = []
    if len(high) > high_limit:
        failures.append(
            "code_metrics: %d hallazgos high, tope %d" % (len(high), high_limit)
        )
        for item in high:
            print("  [high] %s:%s %s · %s" % (
                relative(item["file"]), item["line"], item["function"], item["rule"]))
    else:
        print("code_metrics: %d hallazgos high (tope %d) OK" % (len(high), high_limit))

    if len(duplicated) > clone_limit:
        failures.append(
            "clone_detect: %d clones con --min-tokens %d --threshold %.2f, tope %d"
            % (len(duplicated), min_tokens, threshold, clone_limit)
        )
        for item in duplicated:
            print("  [%s] %s:%s %s ~ %s:%s %s" % (
                item["severity"],
                relative(item["a"]["file"]), item["a"]["line"], item["a"]["name"],
                relative(item["b"]["file"]), item["b"]["line"], item["b"]["name"]))
    else:
        print("clone_detect: %d clones (tope %d, --min-tokens %d --threshold %.2f) OK"
              % (len(duplicated), clone_limit, min_tokens, threshold))

    if failures:
        print()
        for failure in failures:
            print("FALLO: %s" % failure)
        print("Si la deuda nueva es intencionada, súbela en tests/metrics_baseline.json "
              "en el mismo cambio que la introduce.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
