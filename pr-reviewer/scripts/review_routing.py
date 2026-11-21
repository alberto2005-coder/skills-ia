"""Reparto de la revisión por rutas, con carga y respaldo.

Uso:
    py pr-reviewer/scripts/review_routing.py --diff PARCHE --owners REGLAS
        [--json] [--out RUTA] [--fail-on low|medium|high|none]

Aplica reglas de rutas al estilo CODEOWNERS (gana la última coincidencia), suma
la carga por revisor y señala ficheros sin dueño, revisores por encima de su
capacidad y rutas sensibles con un único revisor.

Código de salida: 0 limpio o bajo el umbral · 1 umbral superado · 2 entrada
ilegible.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pr_review_util as util  # noqa: E402

SENSITIVE = ("auth", "login", "session", "permission", "payment", "billing", "migration", "terraform", "deploy")


def compile_pattern(pattern):
    """Glob con `**` que cruza carpetas y `*` que no."""
    out = "^"
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "*":
            if pattern[index:index + 2] == "**":
                out += ".*"
                index += 2
                continue
            out += "[^/]*"
        elif char == "?":
            out += "[^/]"
        else:
            out += re.escape(char)
        index += 1
    return re.compile(out + "$")


def load_rules(path):
    data, error = util.load_json(path)
    if error:
        return None, error
    if not isinstance(data, dict) or not isinstance(data.get("routes"), list):
        return None, "%s no declara una lista «routes»" % path
    routes = []
    for entry in data["routes"]:
        if not isinstance(entry, dict) or not entry.get("pattern") or not entry.get("reviewers"):
            return None, "regla incompleta en %s: %r" % (path, entry)
        routes.append((compile_pattern(str(entry["pattern"])), [str(name) for name in entry["reviewers"]]))
    reviewers = data.get("reviewers") or {}
    capacities = {
        str(name): int(config.get("capacity", 0))
        for name, config in reviewers.items()
        if isinstance(config, dict) and config.get("capacity")
    }
    return (routes, capacities), None


def assign(path, routes):
    owners = []
    for pattern, names in routes:
        if pattern.match(path):
            owners = names
    return owners


def analyze(files, routes, capacities):
    assignments = []
    load = {}
    findings = []
    for item in files:
        path = item["path"]
        owners = assign(path, routes)
        assignments.append({"path": path, "reviewers": owners})
        if not owners:
            findings.append(util.finding(
                path, 1, "ruta-sin-dueno", "high",
                "ninguna regla de propiedad cubre el fichero",
                "Añadir una regla en owners.json o asignar el fichero a mano.",
            ))
            continue
        for name in owners:
            load[name] = load.get(name, 0) + 1
        if any(needle in path.lower() for needle in SENSITIVE) and len(owners) == 1:
            findings.append(util.finding(
                path, 1, "sin-respaldo", "low",
                "ruta sensible con un único revisor: %s" % owners[0],
                "Añadir un segundo revisor a la regla de esa ruta.",
            ))
    for name in sorted(load):
        capacity = capacities.get(name)
        if capacity and load[name] > capacity:
            findings.append(util.finding(
                "owners.json", 1, "revisor-sobrecargado", "medium",
                "%s acumula %d ficheros; capacidad %d" % (name, load[name], capacity),
                "Repartir ficheros entre revisores o subir la capacidad con motivo.",
            ))
    return {
        "source": "pr-routing",
        "assignments": assignments,
        "load": dict(sorted(load.items())),
        "summary": util.summarize(findings),
        "findings": util.sort_findings(findings),
    }


def main(argv=None):
    util.force_utf8()
    parser = argparse.ArgumentParser(description="Reparto de la revisión de un diff por rutas.")
    parser.add_argument("--diff", required=True, help="parche unificado de entrada")
    parser.add_argument("--owners", required=True, help="reglas de propiedad en JSON")
    parser.add_argument("--json", action="store_true", help="imprime el reparto en JSON")
    parser.add_argument("--out", help="escribe el reparto en esta ruta")
    parser.add_argument("--fail-on", choices=("low", "medium", "high", "none"), default="high")
    args = parser.parse_args(argv)

    text = util.read_diff(args.diff)
    if text is None:
        print("review_routing: no se pudo leer %s" % args.diff, file=sys.stderr)
        return 2
    files = util.parse_diff(text)
    if not files:
        print("review_routing: el parche no contiene ficheros", file=sys.stderr)
        return 2
    rules, error = load_rules(args.owners)
    if error:
        print("review_routing: %s" % error, file=sys.stderr)
        return 2

    payload = analyze(files, rules[0], rules[1])
    util.emit(payload, args.out)
    return 1 if util.exceeds(payload["findings"], args.fail_on) else 0


if __name__ == "__main__":
    sys.exit(main())
