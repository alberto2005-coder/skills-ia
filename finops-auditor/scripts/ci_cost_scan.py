"""Detecta coste evitable en workflows de GitHub Actions, sin red.

Uso:
    py finops-auditor/scripts/ci_cost_scan.py --path .github/workflows [--json] [--fail-on high]

Reglas: workflow sin caché de dependencias y workflow disparado por `push` y
`pull_request` a la vez sin `concurrency: cancel-in-progress`, que paga dos veces
la misma suite.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado · 2 ruta
ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITIES = {"low": 1, "medium": 2, "high": 3}
CACHE = re.compile(r"actions/cache|enable-cache:\s*true|cache:\s*[\"']?true|setup-uv@|cache-dependency-path")
TRIGGERS = {
    "push": re.compile(r"^\s{2}push:\s*$", re.M),
    "pull_request": re.compile(r"^\s{2}pull_request:\s*$", re.M),
}
CONCURRENCY = re.compile(r"^\s*concurrency:", re.M)


def iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(
        item for item in path.rglob("*")
        if item.is_file() and item.suffix in {".yml", ".yaml"}
    )


def scan_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    findings = []
    active = [name for name, pattern in TRIGGERS.items() if pattern.search(text)]
    has_cancel = CONCURRENCY.search(text) and "cancel-in-progress" in text
    if "push" in active and "pull_request" in active and not has_cancel:
        findings.append({
            "file": path.as_posix(),
            "line": 1,
            "rule": "ci-doble-ejecucion",
            "severity": "high",
            "message": "push y pull_request sin concurrency/cancel-in-progress: la misma suite se paga dos veces",
        })
    if not CACHE.search(text):
        findings.append({
            "file": path.as_posix(),
            "line": 1,
            "rule": "ci-sin-cache",
            "severity": "medium",
            "message": "workflow sin caché de dependencias: cada ejecución reinstala todo",
        })
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Escáner de coste de workflows de CI.")
    parser.add_argument("--path", required=True, help="fichero o directorio a revisar")
    parser.add_argument("--json", action="store_true", help="salida JSON")
    parser.add_argument("--fail-on", default="high", choices=["low", "medium", "high", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    files = iter_files(target)
    findings = [item for path in files for item in scan_file(path)]
    findings.sort(key=lambda item: (item["file"], item["line"], item["rule"]))
    by_severity = {name: sum(1 for item in findings if item["severity"] == name) for name in SEVERITIES}

    if args.json:
        print(json.dumps({
            "files": len(files),
            "findings": findings,
            "by_severity": by_severity,
        }, indent=2, ensure_ascii=False))
    else:
        for item in findings:
            print(f"{item['file']}:{item['line']} [{item['severity']}] {item['rule']}: {item['message']}")
        print(f"ficheros: {len(files)} · hallazgos: {len(findings)} · "
              + ", ".join(f"{name}={count}" for name, count in by_severity.items()))

    if args.fail_on == "none":
        return 0
    threshold = SEVERITIES[args.fail_on]
    return 1 if any(SEVERITIES[item["severity"]] >= threshold for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
