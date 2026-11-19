"""Comprueba que las rutas citadas en la documentación existen en el repositorio.

Uso:
    py docs-sync-engine/scripts/docs_drift.py --docs docs/ --root . [--json] [--fail-on broken]

Extrae de cada Markdown las rutas entre backticks (`pkg/scripts/x.py`) y los
enlaces relativos, y verifica que existan. No ejecuta comandos ni sigue enlaces
externos: solo comprueba que el fichero citado siga en el árbol.

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
CODE_PATH = re.compile(r"""`([A-Za-z0-9_.\-/]+\.(?:py|md|json|yml|yaml|toml))`""")
LINK = re.compile(r"""\]\(([^)]+)\)""")
SKIP_PARTS = {"__pycache__", ".venv", ".git", "node_modules"}


def references(markdown: Path) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    for number, line in enumerate(markdown.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        for match in CODE_PATH.findall(line):
            found.append((match, number))
        for match in LINK.findall(line):
            if match.startswith(("http://", "https://", "mailto:")) or match.startswith("/"):
                continue
            # Ancla y query no forman parte de la ruta: `guia.md#paso` y
            # `guia.md?x=1` apuntan a `guia.md`.
            clean = match.split("#", 1)[0].split("?", 1)[0].strip()
            if clean:
                found.append((clean, number))
    return found


def check(docs: Path, root: Path) -> list[dict]:
    findings = []
    for markdown in sorted(docs.rglob("*.md")):
        for reference, line in references(markdown):
            candidates = [root / reference, docs / reference, markdown.parent / reference]
            if any(candidate.exists() for candidate in candidates):
                continue
            try:
                shown = markdown.relative_to(root).as_posix()
            except ValueError:
                # `--docs` fuera de `--root`: antes reventaba con ValueError.
                shown = markdown.as_posix()
            findings.append({
                "file": shown,
                "line": line,
                "rule": "referencia-rota",
                "severity": "high",
                "message": f"la doc cita {reference}, que no existe",
            })
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Referencias de la documentación frente al árbol.")
    parser.add_argument("--docs", required=True, help="carpeta o fichero Markdown")
    parser.add_argument("--root", default=".", help="raíz contra la que resolver las rutas")
    parser.add_argument("--json", action="store_true")
    # Una referencia rota es siempre `high`: `low` y `medium` no existían.
    parser.add_argument("--fail-on", default="high", choices=["high", "none"])
    parser.add_argument("--exclude", action="append", default=[], help="subcadena de fichero a ignorar")
    args = parser.parse_args(argv)

    docs, root = Path(args.docs), Path(args.root)
    if not docs.exists():
        print(f"ruta inexistente: {docs}")
        return 2

    findings = [item for item in check(docs, root)
                if not any(pattern in item["file"] for pattern in args.exclude)]
    by_severity = {name: sum(1 for item in findings if item["severity"] == name) for name in SEVERITIES}

    if args.json:
        print(json.dumps({"findings": findings, "by_severity": by_severity}, indent=2, ensure_ascii=False))
    else:
        for item in findings:
            print(f"[{item['severity']}] {item['file']}:{item['line']} {item['message']}")
        print(f"referencias rotas: {len(findings)}")

    if args.fail_on == "none":
        return 0
    threshold = SEVERITIES[args.fail_on]
    return 1 if any(SEVERITIES[item["severity"]] >= threshold for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
