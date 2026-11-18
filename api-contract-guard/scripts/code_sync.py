"""Cruza rutas declaradas en el backend con las llamadas del frontend.

Uso:
    py api-contract-guard/scripts/code_sync.py --backend api.py --frontend app.js
        [--json] [--fail-on dead]

Detecta llamadas del frontend que no existen en el backend (`dead-call`, alta) y
endpoints sin ningún consumidor (`sin-consumidor`, baja). El frontend se analiza
con expresiones regulares: no se parsea JavaScript.

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
BACKEND = re.compile(r"""@(?:app|router)\.(get|post|put|patch|delete)\(\s*["']([^"']+)["']""", re.I)
EXPRESS = re.compile(r"""\b(?:app|router)\.(get|post|put|patch|delete)\(\s*["']([^"']+)["']""", re.I)
FETCH = re.compile(r"""\bfetch\(\s*[`"']([^`"']+)[`"']""", re.I)
AXIOS = re.compile(r"""\baxios\.(get|post|put|patch|delete)\(\s*[`"']([^`"']+)[`"']""", re.I)
CALL = re.compile(r"""\.open\(\s*["'](GET|POST|PUT|PATCH|DELETE)["']\s*,\s*[`"']([^`"']+)""", re.I)


def normalize(path: str) -> str:
    path = path.split("?", 1)[0].strip().rstrip("/")
    return path or "/"


def backend_routes(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    routes: dict[str, str] = {}
    for pattern in (BACKEND, EXPRESS):
        for method, route in pattern.findall(text):
            routes[normalize(route)] = method.upper()
    return routes


def frontend_calls(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    calls: dict[str, str] = {}
    for route in FETCH.findall(text):
        calls[normalize(route)] = "GET"
    for method, route in AXIOS.findall(text):
        calls[normalize(route)] = method.upper()
    for method, route in CALL.findall(text):
        calls[normalize(route)] = method.upper()
    return calls


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cruce de rutas backend/frontend.")
    parser.add_argument("--backend", required=True, help="fichero de rutas del backend")
    parser.add_argument("--frontend", required=True, help="fichero de llamadas del frontend")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="dead", choices=["dead", "none"])
    args = parser.parse_args(argv)

    backend_path, frontend_path = Path(args.backend), Path(args.frontend)
    if not backend_path.exists() or not frontend_path.exists():
        print("ruta inexistente")
        return 2

    routes = backend_routes(backend_path)
    calls = frontend_calls(frontend_path)
    findings = []
    for route, method in sorted(calls.items()):
        if route not in routes:
            findings.append({"route": route, "method": method, "rule": "dead-call", "severity": "high",
                             "message": f"el frontend llama a {method} {route}, que el backend no declara"})
        elif routes[route] != method:
            findings.append({"route": route, "method": method, "rule": "metodo-distinto", "severity": "medium",
                             "message": f"el frontend usa {method} y el backend declara {routes[route]}"})
    for route, method in sorted(routes.items()):
        if route not in calls:
            findings.append({"route": route, "method": method, "rule": "sin-consumidor", "severity": "low",
                             "message": f"{method} {route} no tiene consumidor en el frontend"})
    findings.sort(key=lambda item: (item["route"], item["method"], item["rule"]))
    by_severity = {name: sum(1 for item in findings if item["severity"] == name) for name in SEVERITIES}

    if args.json:
        print(json.dumps({"routes": len(routes), "calls": len(calls),
                          "findings": findings, "by_severity": by_severity},
                         indent=2, ensure_ascii=False))
    else:
        for item in findings:
            print(f"[{item['severity']}] {item['rule']}: {item['message']}")
        print(f"rutas: {len(routes)} · llamadas: {len(calls)} · hallazgos: {len(findings)}")

    if args.fail_on == "none":
        return 0
    return 1 if any(item["rule"] == "dead-call" for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
