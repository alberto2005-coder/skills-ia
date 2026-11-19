"""Índice de candidatos `fuente → sumidero` para revisión manual.

Uso:
    py appsec-audit/scripts/map_flows.py <ruta> [--json]

No decide si hay vulnerabilidad: señala dónde mirar. Un candidato es un sumidero
con una fuente de datos cercana en el mismo fichero; el tribunal de
`appsec-report` confirma o descarta.

Código de salida: 0 siempre, salvo ruta inexistente (2).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from appsec_util import force_utf8_output, relative_parts

EXTENSIONS = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".go": "go", ".php": "php", ".java": "java", ".rb": "ruby",
    ".rs": "rust", ".c": "c", ".cc": "c", ".cpp": "c", ".cs": "csharp", ".sh": "shell",
}

SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "dist", "build", ".next", "vendor",
    "__pycache__", "target", ".terraform",
}

SOURCES = re.compile(
    r"(request\.(?:args|form|json|values|get_json|data|cookies|headers)"
    r"|req\.(?:body|query|params|headers|cookies)"
    r"|params\[|\$_GET|\$_POST|\$_REQUEST"
    r"|HttpServletRequest|sys\.argv|os\.environ|process\.env|input\()"
)

SINKS = {
    "sql": re.compile(r"(?i)\b(execute|executemany|raw|query|queryRawUnsafe|mysqli_query|createQuery)\s*\("),
    "command": re.compile(r"\b(os\.system|subprocess\.(?:run|call|Popen)|child_process\.exec|shell_exec|Runtime\.exec|exec\.Command)\s*\("),
    "code": re.compile(r"\b(eval|exec|pickle\.loads|yaml\.load|unserialize|readObject|Marshal\.load)\s*\("),
    "template": re.compile(r"(render_template_string|innerHTML|dangerouslySetInnerHTML|html_safe|\|\s*safe\b)"),
    "file": re.compile(r"\b(open|readFile|writeFile|os\.Open|file_get_contents|File\.read)\s*\("),
    "network": re.compile(r"\b(requests\.(?:get|post|put)|fetch|http\.Get|curl_exec|curl_init)\s*\("),
}

WINDOW = 25


def scan_file(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    lines = text.splitlines()
    findings = []
    for number, line in enumerate(lines, start=1):
        for kind, pattern in SINKS.items():
            if not pattern.search(line):
                continue
            start = max(0, number - 1 - WINDOW)
            nearby = SOURCES.search("\n".join(lines[start:number]))
            findings.append({
                "file": str(path),
                "line": number,
                "sink": kind,
                "source_nearby": bool(nearby),
                "source": nearby.group(0) if nearby else "",
                "snippet": line.strip()[:160],
            })
    return findings


def scan(root: Path) -> list[dict]:
    if root.is_file():
        return scan_file(root)

    findings = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in EXTENSIONS and not any(
            p in SKIP_DIRS for p in relative_parts(path, root)
        ):
            findings.extend(scan_file(path))
    return findings


def main(argv: list[str] | None = None) -> int:
    force_utf8_output()
    parser = argparse.ArgumentParser(description="Índice de candidatos fuente → sumidero.")
    parser.add_argument("target", help="Fichero o carpeta")
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    args = parser.parse_args(argv)

    root = Path(args.target)
    if not root.exists():
        print(f"No existe: {root}", file=sys.stderr)
        return 2

    findings = scan(root)
    candidates = [item for item in findings if item["source_nearby"]]

    if args.json:
        print(json.dumps({
            "target": str(root),
            "sinks": len(findings),
            "candidates": len(candidates),
            "findings": findings,
        }, indent=2, ensure_ascii=False))
    else:
        for item in candidates:
            print(f"{item['file']}:{item['line']}  {item['sink']}  fuente: {item['source']}")
        print(f"\n{len(candidates)} candidato(s) con fuente cercana de {len(findings)} sumidero(s).")
        print("Revisar a mano: la cercanía no implica alcance real hasta llegar al sumidero.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
