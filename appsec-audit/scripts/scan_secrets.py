"""Barrido de secretos en un árbol de trabajo. Solo lectura, sin red.

Uso:
    py appsec-audit/scripts/scan_secrets.py <ruta> [--json] [--strict]

Encuentra claves y credenciales por patrón conocido y por entropía en
asignaciones genéricas. Los valores se redactan siempre: el informe nunca
contiene el secreto completo.

Código de salida: 0 siempre, salvo `--strict` con hallazgos (1) o ruta
inexistente (2).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from appsec_util import force_utf8_output, relative_parts

SKIP_DIRS = {
    ".git", ".hg", "node_modules", "venv", ".venv", "env", "dist", "build",
    ".next", "vendor", "__pycache__", "target", ".terraform", "coverage",
}
MAX_BYTES = 1_000_000

PATTERNS = [
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("stripe_key", re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
]

GENERIC = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password|passwd|pwd)\b\s*[:=]\s*['\"]([^'\"\s]{12,})['\"]"
)
ENTROPY_MIN = 3.5


def entropy(value: str) -> float:
    """Entropía de Shannon en bits por carácter."""
    if not value:
        return 0.0
    counts = {char: value.count(char) for char in set(value)}
    total = len(value)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def redact(value: str) -> str:
    """Deja pistas para localizar el secreto sin publicarlo.

    Como máximo revela 4+4 caracteres y nunca más de una octava parte del
    valor: `4…4` sobre un secreto de 12-16 caracteres dejaba al descubierto
    la mitad de la contraseña.
    """
    if len(value) <= 8:
        return "…"
    keep = max(1, min(4, len(value) // 8))
    return f"{value[:keep]}…{value[-keep:]}"


def scan_file(path: Path) -> list[dict]:
    try:
        if path.stat().st_size > MAX_BYTES:
            return []
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in PATTERNS:
            for match in pattern.finditer(line):
                findings.append({
                    "file": str(path),
                    "line": number,
                    "kind": kind,
                    "preview": redact(match.group(0)),
                })

        for match in GENERIC.finditer(line):
            value = match.group(2)
            if entropy(value) >= ENTROPY_MIN:
                findings.append({
                    "file": str(path),
                    "line": number,
                    "kind": f"generic_{match.group(1).lower()}",
                    "preview": redact(value),
                })
    return findings


def scan(root: Path) -> tuple[list[dict], int]:
    """(hallazgos, ficheros omitidos por tamaño).

    Los mayores que `MAX_BYTES` se saltaban en silencio: el informe prometía
    cobertura total sin declarar el hueco.
    """
    if root.is_file():
        return scan_file(root), 0

    findings = []
    skipped_large = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in relative_parts(path, root)):
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                skipped_large += 1
                continue
        except OSError:
            continue
        findings.extend(scan_file(path))
    return findings, skipped_large


def main(argv: list[str] | None = None) -> int:
    force_utf8_output()
    parser = argparse.ArgumentParser(description="Barrido de secretos en solo lectura.")
    parser.add_argument("target", help="Fichero o carpeta a revisar")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument("--strict", action="store_true", help="Sale 1 si hay hallazgos")
    args = parser.parse_args(argv)

    root = Path(args.target)
    if not root.exists():
        print(f"No existe: {root}", file=sys.stderr)
        return 2

    findings, skipped_large = scan(root)

    if args.json:
        print(json.dumps({"target": str(root), "count": len(findings),
                          "skipped_large": skipped_large, "findings": findings},
                         indent=2, ensure_ascii=False))
    else:
        if not findings:
            print(f"Sin secretos evidentes en {root}")
        for item in findings:
            print(f"{item['file']}:{item['line']}  {item['kind']}  {item['preview']}")
        print(f"\nTotal: {len(findings)} hallazgo(s). Valores redactados; no se copia ningún secreto.")
        if skipped_large:
            print(f"Aviso: {skipped_large} fichero(s) mayores de {MAX_BYTES} bytes "
                  f"no se han escaneado.")

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    sys.exit(main())
