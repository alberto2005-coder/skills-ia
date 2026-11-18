"""Cruza las variables de entorno del código con `.env.example` y la documentación.

Uso:
    py docs-sync-engine/scripts/env_check.py --path src/ --env-example .env.example
        --docs README.md [--json] [--fail-on low|medium|high|none]

Reconoce `os.environ[...]`, `os.getenv("X")`, `process.env.X` e
`import.meta.env.X`. Compara tres conjuntos: las usadas en código, las declaradas
en `.env.example` y las mencionadas en los documentos indicados.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado ·
2 ruta o fichero ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITIES = {"low": 1, "medium": 2, "high": 3}
SKIP_PARTS = {"__pycache__", ".venv", ".git", "node_modules", "dist", "build"}
PATTERNS = (
    re.compile(r"os\.environ\.get\(\s*[\"']([A-Z][A-Z0-9_]*)"),
    re.compile(r"os\.environ\[\s*[\"']([A-Z][A-Z0-9_]*)"),
    re.compile(r"os\.getenv\(\s*[\"']([A-Z][A-Z0-9_]*)"),
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]*)"),
    re.compile(r"import\.meta\.env\.([A-Z][A-Z0-9_]*)"),
)
CODE_SUFFIXES = {".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"}
DOC_SUFFIXES = {".md", ".mdx", ".txt", ".rst"}


def code_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(item for item in root.rglob("*")
                  if item.is_file() and item.suffix in CODE_SUFFIXES and not SKIP_PARTS & set(item.parts))


def used_variables(root: Path) -> dict[str, list[str]]:
    used: dict[str, list[str]] = {}
    for path in code_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in PATTERNS:
            for name in pattern.findall(text):
                used.setdefault(name, [])
                if path.as_posix() not in used[name]:
                    used[name].append(path.as_posix())
    return used


def example_variables(path: Path) -> set[str]:
    names = set()
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = re.sub(r"^export\s+", "", raw.strip())
        if not line or line.startswith("#") or "=" not in line:
            continue
        names.add(line.split("=", 1)[0].strip())
    return names


def documented_variables(paths: list[Path]) -> set[str]:
    names = set()
    for path in paths:
        if path.is_dir():
            files = [item for item in path.rglob("*") if item.is_file() and item.suffix in DOC_SUFFIXES]
        elif path.is_file():
            files = [path]
        else:
            continue
        for item in files:
            names.update(re.findall(r"\b([A-Z][A-Z0-9_]{2,})\b",
                                    item.read_text(encoding="utf-8", errors="replace")))
    return names


def analyze(root: Path, example: Path | None, docs: list[Path]) -> dict:
    used = used_variables(root)
    declared = example_variables(example) if example else None
    documented = documented_variables(docs)
    findings = []

    def add(rule: str, severity: str, name: str, message: str, sources: list[str] | None = None) -> None:
        findings.append({
            "rule": rule,
            "severity": severity,
            "name": name,
            "message": message,
            "sources": sources or [],
        })

    for name in sorted(used):
        if declared is not None and name not in declared:
            add("env-sin-ejemplo", "medium", name,
                f"{name} se usa en el código y no está en .env.example", used[name])
        if docs and name not in documented:
            add("env-sin-documentar", "medium", name,
                f"{name} se usa en el código y no aparece en la documentación", used[name])
    if declared is not None:
        for name in sorted(declared - set(used)):
            add("ejemplo-sin-uso", "low", name,
                f"{name} está en .env.example y ningún fichero la lee")

    findings.sort(key=lambda item: (item["name"], item["rule"]))
    return {
        "used": len(used),
        "declared": len(declared) if declared is not None else None,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Variables de entorno frente a .env.example y docs.")
    parser.add_argument("--path", required=True, help="código donde buscar variables")
    parser.add_argument("--env-example", help="fichero .env.example")
    parser.add_argument("--docs", action="append", default=[], help="documento o carpeta")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="medium", choices=["low", "medium", "high", "none"])
    args = parser.parse_args(argv)

    root = Path(args.path)
    if not root.exists():
        print(f"ruta inexistente: {root}")
        return 2
    example = Path(args.env_example) if args.env_example else None
    if example is not None and not example.exists():
        print(f"ruta inexistente: {example}")
        return 2

    report = analyze(root, example, [Path(item) for item in args.docs])
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for item in report["findings"]:
            print(f"[{item['severity']}] {item['rule']} {item['name']}: {item['message']}")
        print(f"variables usadas: {report['used']} · hallazgos: {len(report['findings'])}")
    if args.fail_on == "none":
        return 0
    floor = SEVERITIES[args.fail_on]
    return 1 if any(SEVERITIES[item["severity"]] >= floor for item in report["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
