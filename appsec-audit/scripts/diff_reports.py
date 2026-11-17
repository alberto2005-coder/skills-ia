"""Baseline: compara dos `findings.json` por fingerprint.

Uso:
    py appsec-audit/scripts/diff_reports.py <baseline.json> <current.json>
        [--json] [--fail-on new]

Clasifica por huella: `new` (solo en el actual), `fixed` (solo en el baseline),
`changed` (misma huella, veredicto distinto) y `persisting` (igual que antes).
El fingerprint no incluye la línea, así que un refactor no convierte un hallazgo
conocido en nuevo.

Con `--fail-on new` sale 1 si el informe actual introduce hallazgos `confirmed`
que no estaban en el baseline: es la puerta de un PR.

Código de salida: 0 sin bloqueo · 1 bloqueado por `--fail-on` o fichero ilegible · 2 fichero ilegible.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def index_by_fingerprint(payload: object) -> dict[str, dict]:
    if not isinstance(payload, dict) or not isinstance(payload.get("findings"), list):
        raise ValueError("el informe no tiene una lista «findings»")
    indexed: dict[str, dict] = {}
    for item in payload["findings"]:
        if not isinstance(item, dict):
            continue
        key = item.get("fingerprint") or item.get("id")
        if isinstance(key, str) and key not in indexed:
            indexed[key] = item
    return indexed


def brief(finding: dict) -> dict:
    location = finding.get("location") if isinstance(finding.get("location"), dict) else {}
    return {
        "id": finding.get("id"),
        "fingerprint": finding.get("fingerprint"),
        "title": finding.get("title"),
        "verdict": finding.get("verdict"),
        "severity": finding.get("severity"),
        "cwe": finding.get("cwe"),
        "file": location.get("file"),
        "line": location.get("line"),
    }


def compare(baseline: dict[str, dict], current: dict[str, dict]) -> dict:
    new = [brief(current[key]) for key in current if key not in baseline]
    fixed = [brief(baseline[key]) for key in baseline if key not in current]
    changed = []
    persisting = []

    for key in current:
        if key not in baseline:
            continue
        before, after = baseline[key], current[key]
        if before.get("verdict") != after.get("verdict"):
            changed.append({
                "id": after.get("id"),
                "fingerprint": after.get("fingerprint"),
                "from": before.get("verdict"),
                "to": after.get("verdict"),
            })
        else:
            persisting.append(brief(after))

    new_confirmed = [item for item in new if item["verdict"] == "confirmed"]

    return {
        "new": new,
        "fixed": fixed,
        "changed": changed,
        "persisting": persisting,
        "counts": {
            "new": len(new),
            "fixed": len(fixed),
            "changed": len(changed),
            "persisting": len(persisting),
            "new_confirmed": len(new_confirmed),
        },
        "new_confirmed": [item["id"] for item in new_confirmed],
    }


def load(path: Path) -> dict[str, dict]:
    return index_by_fingerprint(json.loads(path.read_text(encoding="utf-8")))


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Diff de dos informes por fingerprint.")
    parser.add_argument("baseline", help="Informe de referencia")
    parser.add_argument("current", help="Informe de la pasada actual")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument(
        "--fail-on",
        choices=("new", "none"),
        default="none",
        help="«new» bloquea el PR si aparecen hallazgos confirmed nuevos",
    )
    args = parser.parse_args(argv)

    paths = {"baseline": Path(args.baseline), "current": Path(args.current)}
    indexed = {}
    for name, path in paths.items():
        if not path.is_file():
            print(f"No existe el informe {name}: {path}", file=sys.stderr)
            return 2
        try:
            indexed[name] = load(path)
        except (json.JSONDecodeError, OSError, ValueError) as error:
            print(f"Informe {name} ilegible: {error}", file=sys.stderr)
            return 2

    result = compare(indexed["baseline"], indexed["current"])
    counts = result["counts"]
    blocked = args.fail_on == "new" and counts["new_confirmed"] > 0

    if args.json:
        print(json.dumps({
            **result,
            "baseline": args.baseline,
            "current": args.current,
            "gate": {"fail_on": args.fail_on, "blocked": blocked},
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Nuevos {counts['new']} · Corregidos {counts['fixed']} · "
              f"Cambiados {counts['changed']} · Persistentes {counts['persisting']}")
        for item in result["new"]:
            print(f"  + {item['id']} ({item['verdict']}, {item['severity'] or 'sin severidad'}) "
                  f"{item['title']} — {item['file']}:{item['line']}")
        for item in result["fixed"]:
            print(f"  - {item['id']} {item['title']} — {item['file']}:{item['line']}")
        for item in result["changed"]:
            print(f"  ~ {item['id']}: {item['from']} → {item['to']}")
        if blocked:
            print(f"BLOQUEADO: {counts['new_confirmed']} hallazgo(s) confirmed nuevos "
                  "que no estaban en el baseline")

    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
