"""Nota de seguridad A-F a partir de hallazgos validados.

Uso:
    py appsec-audit/scripts/grade.py hallazgos.json [--json]

Entrada: `{"findings": [...]}` o una lista. Cada hallazgo admite `severity`
(crítica/alta/media/baja o critical/high/medium/low) y `confidence` (1-10).

Los hallazgos con confianza menor que 7 se descartan y no puntúan: son los que
el tribunal rechaza. Sin `confidence` se asume 10 para no perder un hallazgo ya
validado por error de formato.

Código de salida: 0 con informe, 2 si el fichero no existe o no es JSON válido.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from appsec_util import force_utf8_output

MIN_CONFIDENCE = 7
PENALTY = {"critical": 25, "high": 10, "medium": 3, "low": 1}
ALIASES = {
    # Escala canónica: critical | high | medium | low (las variantes en
    # español y los adjetivos siguen aceptándose como alias de entrada).
    "critical": "critical", "critica": "critical", "crítica": "critical",
    "critico": "critical", "crítico": "critical",
    "high": "high", "alta": "high", "alto": "high",
    "medium": "medium", "media": "medium", "medio": "medium",
    "low": "low", "baja": "low", "bajo": "low",
}
THRESHOLDS = ((90, "A"), (80, "B"), (70, "C"), (60, "D"), (50, "E"))


def normalize(severity: str) -> str | None:
    return ALIASES.get(str(severity).strip().lower())


def letter_for(score: float) -> str:
    for limit, letter in THRESHOLDS:
        if score >= limit:
            return letter
    return "F"


def load(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        items = data.get("findings", [])
    elif isinstance(data, list):
        items = data
    else:
        # Una cadena o un número convertido con list() daba una lista de
        # caracteres/números y un traceback más adelante.
        raise ValueError(f"findings.json debe ser un objeto o una lista, no {type(data).__name__}")
    if not isinstance(items, list):
        raise ValueError("el campo «findings» debe ser una lista")
    return [item for item in items if isinstance(item, dict)]


def grade_findings(findings: list[dict]) -> dict:
    accepted = []
    discarded = []

    for item in findings:
        # `confidence: null` llegaba a int(None) → TypeError en vez de exit 2.
        raw_confidence = item.get("confidence", 10)
        try:
            confidence = int(raw_confidence)
        except (TypeError, ValueError):
            discarded.append({"id": item.get("id", "?"),
                              "reason": f"confianza no numérica: {raw_confidence!r}"})
            continue
        severity = normalize(item.get("severity", ""))
        if severity is None:
            discarded.append({"id": item.get("id", "?"), "reason": "severidad desconocida"})
            continue
        if confidence < MIN_CONFIDENCE:
            discarded.append({"id": item.get("id", "?"), "reason": f"confianza {confidence} < {MIN_CONFIDENCE}"})
            continue
        accepted.append({"id": item.get("id", "?"), "severity": severity, "confidence": confidence})

    counts = {key: sum(1 for item in accepted if item["severity"] == key) for key in PENALTY}
    penalty = sum(counts[key] * PENALTY[key] for key in PENALTY)
    score = max(0, 100 - penalty)

    return {
        "score": score,
        "letter": letter_for(score),
        "counts": counts,
        "accepted": len(accepted),
        "discarded": discarded,
    }


def main(argv: list[str] | None = None) -> int:
    force_utf8_output()
    parser = argparse.ArgumentParser(description="Nota A-F desde hallazgos validados.")
    parser.add_argument("findings", help="JSON con hallazgos")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    args = parser.parse_args(argv)

    path = Path(args.findings)
    if not path.is_file():
        print(f"No existe: {path}", file=sys.stderr)
        return 2
    try:
        findings = load(path)
    except (json.JSONDecodeError, OSError, ValueError, TypeError, AttributeError) as error:
        print(f"JSON inválido: {error}", file=sys.stderr)
        return 2

    result = grade_findings(findings)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        counts = result["counts"]
        print(f"Nota: {result['letter']} ({result['score']}/100)")
        print(f"Críticos: {counts['critical']} · Altos: {counts['high']} · "
              f"Medios: {counts['medium']} · Bajos: {counts['low']}")
        print(f"Aceptados: {result['accepted']} · Descartados: {len(result['discarded'])}")
        for item in result["discarded"]:
            print(f"  descartado {item['id']}: {item['reason']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
