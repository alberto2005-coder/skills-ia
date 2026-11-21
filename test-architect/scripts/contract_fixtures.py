"""Deriva entre el contrato del proveedor y el payload del consumidor.

Uso:
    py test-architect/scripts/contract_fixtures.py --provider RUTA --consumer RUTA
        [--json] [--out RUTA] [--fail-on low|medium|high|none]

El fixture del proveedor declara campo y especificación (`string`, `number?`,
`array<string>`…); el consumidor es un payload JSON. Se comparan forma, tipo y
nulabilidad, sin arrancar el proveedor ni ejecutar código de ninguna parte. Las
rutas y el SemVer de una API son de `api-contract-guard`, no de aquí.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado · 2
fichero ilegible.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import testarch_util as util  # noqa: E402

SCALARS = {
    "string": lambda value: isinstance(value, str),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "object": lambda value: isinstance(value, dict),
}
FIX_MISSING = "Añade el campo al payload o declara el contrato como opcional con su motivo."
FIX_TYPE = "Corrige el dato en el origen o actualiza la especificación del fixture."
FIX_NULL = "Prohíbe el nulo en el proveedor o marca el campo como opcional."
FIX_EXTRA = "Declara el campo en el contrato o deja de enviarlo."


def parse_spec(spec: str) -> tuple:
    """Tipo base, si es array y si el campo es opcional."""
    text = str(spec).strip()
    optional = text.endswith("?")
    base = text[:-1] if optional else text
    if base.startswith("array<") and base.endswith(">"):
        return base[6:-1], True, optional
    return base, False, optional


def type_problem(value, base: str) -> bool:
    """¿El valor incumple el tipo declarado?"""
    check = SCALARS.get(base)
    return True if check is None else not check(value)


def item_findings(name: str, field: str, base: str, values: list) -> list:
    """Tipo divergente dentro de un array."""
    return [
        util.finding(name, 0, "tipo-divergente", "high",
                     "«%s» declara array<%s> y trae un valor %s" % (field, base, type(values[index]).__name__),
                     FIX_TYPE)
        for index in range(len(values))
        if type_problem(values[index], base)
    ]


def field_findings(name: str, field: str, spec: str, consumer: dict) -> list:
    """Hallazgos de un campo declarado por el proveedor."""
    base, is_array, optional = parse_spec(spec)
    if field not in consumer:
        if optional:
            return []
        return [util.finding(name, 0, "campo-faltante", "high",
                             "el consumidor no envía «%s», obligatorio (%s)" % (field, spec), FIX_MISSING)]
    value = consumer[field]
    if value is None:
        if optional:
            return []
        return [util.finding(name, 0, "nulo-no-permitido", "high",
                             "«%s» es obligatorio y llega como null" % field, FIX_NULL)]
    if is_array:
        if not isinstance(value, list):
            return [util.finding(name, 0, "tipo-divergente", "high",
                                 "«%s» declara %s y trae %s" % (field, spec, type(value).__name__), FIX_TYPE)]
        return item_findings(name, field, base, value)
    if type_problem(value, base):
        return [util.finding(name, 0, "tipo-divergente", "high",
                             "«%s» declara %s y trae %s" % (field, base, type(value).__name__), FIX_TYPE)]
    return []


def compare(provider: dict, consumer: dict, name: str) -> list:
    """Todos los hallazgos del contrato frente al payload."""
    findings = []
    for field, spec in provider.items():
        findings.extend(field_findings(name, field, spec, consumer))
    for field in sorted(set(consumer) - set(provider)):
        findings.append(util.finding(name, 0, "campo-extra", "low",
                                     "el consumidor envía «%s», que el proveedor no declara" % field, FIX_EXTRA))
    return findings


def main(argv: list | None = None) -> int:
    util.force_utf8()
    parser = argparse.ArgumentParser(description="Contrato proveedor/consumidor sobre fixtures.")
    parser.add_argument("--provider", required=True, help="Fixture con el contrato del proveedor")
    parser.add_argument("--consumer", required=True, help="Payload del consumidor")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument("--out", help="Escribe el informe JSON en esta ruta")
    parser.add_argument("--fail-on", choices=["low", "medium", "high", "none"], default="high",
                        help="Umbral que rompe la puerta")
    args = parser.parse_args(argv)

    try:
        provider = util.load_json(args.provider)
        consumer = util.load_json(args.consumer)
    except (OSError, ValueError) as error:
        print("No se pudo leer la entrada: %s" % error, file=sys.stderr)
        return 2
    if not isinstance(provider, dict) or not isinstance(consumer, dict):
        print("El contrato y el payload deben ser objetos JSON", file=sys.stderr)
        return 2

    findings = compare(provider, consumer, Path(args.consumer).name)
    data = util.report("contract_fixtures", findings, 2,
                       provider=Path(args.provider).as_posix(), consumer=Path(args.consumer).as_posix())

    if args.json or args.out:
        util.emit(data, args.out)
    else:
        for item in findings:
            print("%-24s %-8s %s" % (item["rule"], item["severity"], item["message"]))
        print("contrato: %d campo(s) declarados, %d hallazgo(s)" % (len(provider), len(findings)))
    return util.gate(findings, args.fail_on)


if __name__ == "__main__":
    sys.exit(main())
