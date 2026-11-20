"""Puerta de basenames: dos módulos fuera de los tests no pueden llamarse igual.

Python resuelve un `import x` por nombre, no por ruta: con dos `x.py` en el
`sys.path` de un mismo proceso, gana el primero que se importó y el otro queda
inalcanzable. Eso mismo rompió CI: `contracts/findings/validate_findings.py`
compartía nombre con `appsec-audit/scripts/validate_findings.py`, y al ejecutar
todas las suites juntas (`pytest` desde la raíz) los tests de appsec importaban
el módulo del contrato, que no tiene `fingerprint`.

Las suites por paquete no lo ven porque cada una corre en su proceso con su
`tests/` en el `sys.path`; por eso la comprobación se hace aquí, en una puerta
que corre con todo el repo a la vista.

Excepciones: dos paquetes autocontenidos pueden repetir el nombre de un script
(`report.py`, `export_sarif.py`…) porque un paquete nunca importa de otro y sus
pruebas no comparten proceso. Se listan una a una en `INTENDED`, con el motivo:
un basename nuevo, o el mismo basename en un paquete nuevo, falla hasta que
alguien lo añada a mano.

Uso:
    py tests/lint_module_names.py [--root RUTA]

Código de salida: 0 sin colisiones · 1 colisión · 2 uso.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# La consola de Windows (cp1252) no sabe escribir «colisión» ni «módulos»: sin
# esto la puerta muere con UnicodeEncodeError antes de explicar el problema.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

# Carpetas que no son código del repo: entorno, dependencias y artefactos.
SKIP_DIRS = {".git", ".venv", "node_modules", "dist", "build", "__pycache__", ".ruff_cache"}

# Ficheros de pruebas: el repo ya los resuelve con `--import-mode=importlib`
# (`tests/` por suite y `conftest.py`), así que quedan fuera de esta puerta.
TEST_FILE = "test_"

# Colisiones intencionadas: basename → rutas exactas que se permiten. Cada
# paquete se empaqueta y se prueba por separado, sin importar de otro. Añadir
# aquí una entrada es una decisión; que la puerta la pida es la señal de que
# alguien está repitiendo un nombre sin querer.
INTENDED = {
    "export_sarif.py": (
        "appsec-audit/scripts/export_sarif.py",
        "agent-red-team/scripts/export_sarif.py",
    ),
    "report.py": (
        "skill-evals/scripts/report.py",
        "seo-auditor/scripts/report.py",
    ),
    "schema_audit.py": (
        "seo-auditor/scripts/schema_audit.py",
        "db-architect/scripts/schema_audit.py",
    ),
}


def is_test(path: Path) -> bool:
    """¿Es un fichero de pruebas o un helper de una suite?"""
    return "tests" in path.parts[:-1] or path.name.startswith(TEST_FILE)


def skipped(path: Path) -> bool:
    """¿Queda fuera del recuento por ser entorno, dependencia o artefacto?"""
    return any(part in SKIP_DIRS for part in path.parts)


def modules(root: Path) -> list[str]:
    """Rutas relativas de los módulos que cuentan para la puerta."""
    found = []
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if skipped(relative) or is_test(relative):
            continue
        found.append(relative.as_posix())
    return found


def by_basename(paths: list[str]) -> dict[str, list[str]]:
    """Agrupa las rutas por nombre de fichero, solo donde hay repetición."""
    groups: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        groups[Path(path).name].append(path)
    return {name: sorted(paths) for name, paths in groups.items() if len(paths) > 1}


def intended(name: str, paths: list[str]) -> bool:
    """¿La repetición está en la lista de excepciones, con estas rutas exactas?"""
    allowed = INTENDED.get(name)
    return allowed is not None and set(paths) == set(allowed)


def report(name: str, paths: list[str]) -> None:
    """Explica una colisión y qué se espera de ella."""
    print("colisión de basename fuera de tests: %s" % name, file=sys.stderr)
    for path in paths:
        print("   %s" % path, file=sys.stderr)
    print(
        "   Python elige el módulo por nombre: con los dos en un sys.path, "
        "`import %s` carga el primero y el otro queda inalcanzable." % name.removesuffix(".py"),
        file=sys.stderr,
    )
    print(
        "   Renombra uno de los dos, o añádelo a INTENDED en tests/lint_module_names.py "
        "si de verdad son paquetes autocontenidos que nunca comparten proceso.",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    """Comprueba el repo y devuelve el código de salida."""
    parser = argparse.ArgumentParser(description="Falla si dos módulos fuera de tests comparten basename.")
    parser.add_argument("--root", default=str(ROOT), help="raíz del repositorio (por defecto, la de este script)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print("no existe la raíz: %s" % root, file=sys.stderr)
        return 2

    paths = modules(root)
    collisions = by_basename(paths)
    failures = [(name, group) for name, group in collisions.items() if not intended(name, group)]

    for name, group in failures:
        report(name, group)
    if failures:
        print(
            "\n%d basename(s) repetido(s) fuera de tests, %d intencionado(s)."
            % (len(failures), len(collisions) - len(failures))
        )
        return 1

    print(
        "OK: %d módulos, %d basename(s) repetido(s), todos en paquetes autocontenidos."
        % (len(paths), len(collisions))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
