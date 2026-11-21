"""Patrones de inestabilidad en los tests, sin ejecutarlos.

Uso:
    py test-architect/scripts/flaky_scan.py [--root RUTA] [--paths RUTA ...]
        [--json] [--out RUTA] [--fail-on low|medium|high|none] [--allow-network]

Busca en los ficheros de test las causas típicas de un fallo intermitente: espera
fija, reloj de pared, azar sin semilla, red real, ruta compartida, estado global,
bucle sin salida y `skip` permanente. La causa se nombra con fichero y línea.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado · 2 ruta
ilegible.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import testarch_util as util  # noqa: E402

PATTERNS = (
    {
        "rule": "espera-fija",
        "severity": "medium",
        "regex": re.compile(r"\btime\.sleep\s*\("),
        "message": "espera fija: el test duerme a la espera de que algo ocurra",
        "fix": "Sondea con plazo máximo o espera el evento, no un tiempo fijo.",
    },
    {
        "rule": "reloj-de-pared",
        "severity": "medium",
        "regex": re.compile(r"\b(time\.(time|monotonic)|datetime\.(now|utcnow)|date\.today)\s*\("),
        "message": "reloj de pared: el resultado depende del instante de ejecución",
        "fix": "Inyecta un reloj o congela el tiempo en el test.",
    },
    {
        "rule": "red-real",
        "severity": "high",
        "regex": re.compile(r"\b(requests\.(get|post|put|patch|delete)|httpx\.|urllib\.request|socket\.socket)\b"),
        "message": "red real: el test depende de un servicio que no controla",
        "fix": "Usa un doble de red o declara la excepción con --allow-network.",
    },
    {
        "rule": "ruta-compartida",
        "severity": "medium",
        "regex": re.compile(r"""["'](/tmp/|/var/tmp/|[A-Za-z]:\\Temp\\)"""),
        "message": "ruta compartida: dos ejecuciones pueden pisarse el fichero",
        "fix": "Usa TemporaryDirectory por test.",
    },
    {
        "rule": "estado-global",
        "severity": "medium",
        "regex": re.compile(r"^\s*global\s+[A-Za-z_]"),
        "message": "estado global: el test muta algo que otros tests leen",
        "fix": "Reinicia el estado en setUp o inyecta el colaborador.",
    },
    {
        "rule": "bucle-sin-salida",
        "severity": "medium",
        "regex": re.compile(r"\bwhile\s+True\s*:"),
        "message": "bucle sin salida: si la condición no llega, el test cuelga",
        "fix": "Añade un plazo máximo y falla con un mensaje explícito.",
    },
    {
        "rule": "skip-permanente",
        "severity": "low",
        "regex": re.compile(r"skip.*(flaky|temporal|intermitente|inestable)", re.IGNORECASE),
        "message": "skip permanente: el test está desactivado por inestable",
        "fix": "Arregla la causa o borra el test; un skip sin fecha es deuda.",
    },
)
RANDOM_USE = re.compile(r"\b(random\.(random|choice|shuffle|randint|uniform|sample)|Faker\()")
RANDOM_SEED = re.compile(r"\b(random\.seed|seed\s*=)")
NO_SEED = {
    "rule": "aleatorio-sin-semilla",
    "severity": "high",
    "message": "azar sin semilla: el caso cambia en cada ejecución",
    "fix": "Fija la semilla en el test o usa un doble determinista.",
}


def scan_text(path: Path, name: str, allow_network: bool) -> list:
    """Hallazgos de un fichero de test."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    found = []
    for pattern in PATTERNS:
        if allow_network and pattern["rule"] == "red-real":
            continue
        for number, line in enumerate(lines, start=1):
            if pattern["regex"].search(line):
                found.append(util.finding(name, number, pattern["rule"], pattern["severity"],
                                          pattern["message"], pattern["fix"]))
    if RANDOM_USE.search(text) and not RANDOM_SEED.search(text):
        number = next(index for index, line in enumerate(lines, start=1) if RANDOM_USE.search(line))
        found.append(util.finding(name, number, NO_SEED["rule"], NO_SEED["severity"],
                                  NO_SEED["message"], NO_SEED["fix"]))
    return found


def collect(root: Path, paths: list) -> list | None:
    """Ficheros a escanear: los pedidos o todos los tests del árbol."""
    if not paths:
        return util.test_files(root)
    selected = []
    for raw in paths:
        target = Path(raw)
        if target.is_dir():
            selected.extend(sorted(path for path in target.rglob("*.py") if util.is_test_file(path)))
        elif target.is_file():
            selected.append(target)
        else:
            return None
    return selected


def main(argv: list | None = None) -> int:
    util.force_utf8()
    parser = argparse.ArgumentParser(description="Patrones de inestabilidad en los tests.")
    parser.add_argument("--root", default=".", help="Raíz del árbol")
    parser.add_argument("--paths", nargs="*", help="Ficheros o carpetas de test concretos")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument("--out", help="Escribe el informe JSON en esta ruta")
    parser.add_argument("--fail-on", choices=["low", "medium", "high", "none"], default="high",
                        help="Umbral que rompe la puerta")
    parser.add_argument("--allow-network", action="store_true", help="No marca la red real")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print("No existe la raíz: %s" % root, file=sys.stderr)
        return 2
    files = collect(root, args.paths or [])
    if files is None:
        print("Ruta ilegible en --paths", file=sys.stderr)
        return 2

    findings = []
    for path in files:
        findings.extend(scan_text(path, util.relative(path, root), args.allow_network))
    findings.sort(key=lambda item: (item["file"], item["line"], item["rule"]))
    data = util.report("flaky_scan", findings, len(files), root=root.as_posix())

    if args.json or args.out:
        util.emit(data, args.out)
    else:
        for item in findings:
            print("%s:%d  %-22s %s" % (item["file"], item["line"], item["rule"], item["severity"]))
        print("inestabilidad: %d ficheros, %d hallazgo(s)" % (len(files), len(findings)))
    return util.gate(findings, args.fail_on)


if __name__ == "__main__":
    sys.exit(main())
