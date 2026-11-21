"""Utilidades compartidas por los scripts de `test-architect`.

Solo stdlib y sin importar módulos de la raíz: el paquete se instala y se ejecuta
suelto, así que todo lo que necesita vive aquí o en la biblioteca estándar.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SEVERITY_WEIGHT = {"low": 1, "medium": 2, "high": 3}
SKIP_DIRS = {
    "__pycache__",
    ".venv",
    ".git",
    "node_modules",
    "dist",
    "build",
    ".ruff_cache",
    ".pytest_cache",
    "fixtures",
}
TEST_PREFIX = "test_"


def force_utf8() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra página de códigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def is_test_file(path: Path) -> bool:
    """Nombre que un runner reconoce como fichero de test."""
    name = Path(path).name
    return name.startswith(TEST_PREFIX) or name.endswith("_test.py")


def python_files(root: Path, include_tests: bool = False) -> list:
    """`.py` del árbol, sin entorno ni artefactos; los tests solo si se piden."""
    root = Path(root)
    found = []
    for path in sorted(root.rglob("*.py")):
        parts = set(path.relative_to(root).parts)
        if parts & SKIP_DIRS:
            continue
        if not include_tests and (is_test_file(path) or "tests" in parts):
            continue
        found.append(path)
    return found


def test_files(root: Path) -> list:
    """Ficheros de test del árbol, con la misma poda que el resto."""
    return [path for path in python_files(Path(root), include_tests=True) if is_test_file(path)]


def relative(path: Path, root: Path) -> str:
    """Ruta POSIX relativa a la raíz, o absoluta si cae fuera."""
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def finding(file: str, line: int, rule: str, severity: str, message: str, fix: str = "") -> dict:
    """Hallazgo con la forma que consume el contrato `findings.json`."""
    item = {
        "file": file,
        "line": int(line),
        "rule": rule,
        "severity": severity,
        "message": " ".join(message.split()),
    }
    if fix:
        item["fix"] = " ".join(fix.split())
    return item


def summary(findings: list) -> dict:
    """Recuento por severidad, siempre con las tres claves."""
    counts = {"low": 0, "medium": 0, "high": 0}
    for item in findings:
        counts[item["severity"]] = counts.get(item["severity"], 0) + 1
    return {"total": len(findings), "by_severity": counts}


def report(source: str, findings: list, files: int, **extra) -> dict:
    """Informe completo: fuente, recuento, resumen y hallazgos."""
    data = {"source": source, "files": int(files), "summary": summary(findings), "findings": findings}
    data.update(extra)
    return data


def emit(data: dict, out: str = "") -> int:
    """Imprime el informe o lo escribe en `out`."""
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if out:
        Path(out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def exceeds(findings: list, fail_on: str) -> bool:
    """¿Algún hallazgo alcanza el umbral? `none` nunca bloquea."""
    if fail_on == "none":
        return False
    limit = SEVERITY_WEIGHT[fail_on]
    return any(SEVERITY_WEIGHT.get(item["severity"], 0) >= limit for item in findings)


def gate(findings: list, fail_on: str) -> int:
    """Código de salida de la puerta: 1 si se supera el umbral."""
    return 1 if exceeds(findings, fail_on) else 0


def load_json(path: str):
    """JSON de un fichero, con el error del sistema si no se puede leer."""
    return json.loads(Path(path).read_text(encoding="utf-8"))
