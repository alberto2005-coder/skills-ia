"""Utilidades compartidas de pr-reviewer: parche, hallazgos y salida.

Solo stdlib y sin estado global: cada script importa este módulo por ruta y
mantiene su propio contrato de línea de comandos.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SEVERITIES = ("low", "medium", "high")
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}
FAIL_ON_CHOICES = ("low", "medium", "high", "none")

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def finding(file, line, rule, severity, message, fix):
    """Hallazgo con la forma que comparte todo el repositorio."""
    return {
        "file": file,
        "line": line,
        "rule": rule,
        "severity": severity,
        "message": message,
        "fix": fix,
    }


def severity_rank(severity):
    return SEVERITY_RANK.get(severity, 0)


def summarize(findings):
    """Totales por severidad y por regla, siempre con las tres claves."""
    by_severity = {level: 0 for level in SEVERITIES}
    by_rule = {}
    for item in findings:
        by_severity[item["severity"]] = by_severity.get(item["severity"], 0) + 1
        by_rule[item["rule"]] = by_rule.get(item["rule"], 0) + 1
    return {
        "total": len(findings),
        "by_severity": by_severity,
        "by_rule": dict(sorted(by_rule.items())),
    }


def exceeds(findings, fail_on):
    """¿Algún hallazgo alcanza el umbral pedido?"""
    if fail_on == "none":
        return False
    limit = severity_rank(fail_on)
    return any(severity_rank(item["severity"]) >= limit for item in findings)


def sort_findings(findings):
    order = {level: -rank for level, rank in SEVERITY_RANK.items()}
    return sorted(findings, key=lambda item: (order.get(item["severity"], 0), item["file"], item["line"], item["rule"]))


def parse_diff(text):
    """Ficheros de un parche unificado, con líneas añadidas y número de destino."""
    files = []
    current = None
    new_line = 0
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            parts = raw.split()
            path = parts[3][2:] if len(parts) > 3 and parts[3].startswith("b/") else ""
            current = {"path": path, "added": [], "removed": 0, "hunks": 0}
            files.append(current)
            continue
        if current is None:
            continue
        if raw.startswith("+++ "):
            candidate = raw[4:].strip()
            if candidate and candidate != "/dev/null":
                current["path"] = candidate[2:] if candidate.startswith("b/") else candidate
            continue
        if raw.startswith("--- "):
            continue
        match = HUNK.match(raw)
        if match:
            new_line = int(match.group(1))
            current["hunks"] += 1
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            current["added"].append((new_line, raw[1:]))
            new_line += 1
            continue
        if raw.startswith("-") and not raw.startswith("---"):
            current["removed"] += 1
            continue
        if raw.startswith(" "):
            new_line += 1
    return [item for item in files if item["path"]]


def read_diff(path):
    """Parche como texto, o None si no se puede leer."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def load_json(path):
    """(datos, error): el error es texto legible y nunca una excepción."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        return None, "no se pudo leer %s: %s" % (path, error)
    try:
        return json.loads(text), None
    except json.JSONDecodeError as error:
        return None, "JSON inválido en %s: %s" % (path, error)


def emit(payload, out=None):
    """Imprime el JSON o lo escribe en `out`."""
    text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    if out:
        Path(out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def force_utf8():
    """Consola de Windows: evita mojibake al imprimir acentos."""
    import sys

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
