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

MIN_CONFIDENCE = 7
PENALTY = {"critica": 25, "alta": 10, "media": 3, "baja": 1}
ALIASES = {
    "critica": "critica", "crítica": "critica", "critical": "critica", "critico": "critica", "crítico": "critica",
    "alta": "alta", "high": "alta", "alto": "alta",
    "media": "media", "medium": "media", "medio": "media",
    "baja": "baja", "low": "baja", "bajo": "baja",
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
        return list(data.get("findings", []))
    return list(data)


def grade_findings(findings: list[dict]) -> dict:
    accepted = []
    discarded = []

    for item in findings:
        confidence = int(item.get("confidence", 10))
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


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
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
    except (json.JSONDecodeError, OSError) as error:
        print(f"JSON inválido: {error}", file=sys.stderr)
        return 2

    result = grade_findings(findings)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        counts = result["counts"]
        print(f"Nota: {result['letter']} ({result['score']}/100)")
        print(f"Críticos: {counts['critica']} · Altos: {counts['alta']} · "
              f"Medios: {counts['media']} · Bajos: {counts['baja']}")
        print(f"Aceptados: {result['accepted']} · Descartados: {len(result['discarded'])}")
        for item in result["discarded"]:
            print(f"  descartado {item['id']}: {item['reason']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
