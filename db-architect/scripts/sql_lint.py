"""Lint de estilo sobre ficheros SQL, con un subconjunto acotado de reglas.

Uso:
    py db-architect/scripts/sql_lint.py --path migrations/ [--json]
        [--fail-on low|medium|none]

Reglas: palabras clave en minúscula, `SELECT *`, tablas sin clave primaria,
identificadores que no son snake_case, líneas de más de 120 caracteres,
tabuladores y `!=` en lugar de `<>`. Sin motor y sin dialectos: lee texto.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado ·
2 ruta ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITIES = {"low": 1, "medium": 2}
SKIP_PARTS = {"__pycache__", ".venv", ".git"}
LOWERCASE_KEYWORD = re.compile(r"^\s*(select|insert|update|delete|create|alter|drop|with)\b", re.M)
STAR = re.compile(r"\bSELECT\s+\*\s+FROM\b", re.I)
CREATE_TABLE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*?)\)\s*(?:;|$)", re.I | re.S)
COMMENT = re.compile(r"--[^\n]*")
CAMEL = re.compile(r"\b[a-z]+[A-Z]\w*\b")
MAX_LINE = 120


def sql_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix == ".sql" else []
    return sorted(item for item in root.rglob("*.sql")
                  if item.is_file() and not SKIP_PARTS & set(item.parts))


def lint_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    findings = []

    def add(rule: str, severity: str, line: int, message: str) -> None:
        findings.append({
            "file": path.as_posix(),
            "line": line,
            "rule": rule,
            "severity": severity,
            "message": message,
        })

    for match in LOWERCASE_KEYWORD.finditer(text):
        add("palabra-clave-minuscula", "low", text[:match.start()].count("\n") + 1,
            "la palabra clave va en minúsculas; usa mayúsculas para distinguirla del identificador")
    for match in STAR.finditer(text):
        add("select-asterisco", "medium", text[:match.start()].count("\n") + 1,
            "SELECT * acopla la consulta al orden de columnas; nómbralas")
    for number, line in enumerate(text.splitlines(), 1):
        if len(line) > MAX_LINE:
            add("linea-larga", "low", number, f"línea de {len(line)} caracteres (máximo {MAX_LINE})")
        code = COMMENT.sub("", line)
        for name in sorted(set(CAMEL.findall(code))):
            add("identificador-no-snake", "low", number, f"{name} no está en snake_case")
        if "\t" in code:
            add("tabulador", "low", number, "usa espacios en lugar de tabuladores")
        if "!=" in code:
            add("comparacion-distinta", "low", number, "usa <> en lugar de != para SQL portátil")
    for match in CREATE_TABLE.finditer(text):
        table, block = match.group(1), match.group(2)
        if not re.search(r"\bPRIMARY\s+KEY\b", block, re.I):
            add("tabla-sin-clave", "medium", text[:match.start()].count("\n") + 1,
                f"la tabla {table} no declara clave primaria")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint de estilo SQL acotado.")
    parser.add_argument("--path", required=True, help="fichero o carpeta con .sql")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on", default="medium", choices=["low", "medium", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    files = sql_files(target)
    findings = []
    for path in files:
        findings.extend(lint_file(path))
    findings.sort(key=lambda item: (item["file"], item["line"], item["rule"]))

    if args.json:
        print(json.dumps({
            "files": len(files),
            "findings": findings,
            "by_rule": {rule: sum(1 for item in findings if item["rule"] == rule)
                        for rule in sorted({item["rule"] for item in findings})},
        }, indent=2, ensure_ascii=False))
    else:
        for item in findings:
            print(f"[{item['severity']}] {item['file']}:{item['line']} {item['rule']}: {item['message']}")
        print(f"ficheros: {len(files)} · hallazgos: {len(findings)}")

    if args.fail_on == "none":
        return 0
    floor = SEVERITIES[args.fail_on]
    return 1 if any(SEVERITIES[item["severity"]] >= floor for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
