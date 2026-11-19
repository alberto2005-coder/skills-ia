"""Detecta antipatrones de coste en llamadas a APIs de LLM sin red ni modelo.

Uso:
    py finops-auditor/scripts/llm_cost_scan.py --path <ruta> [--json] [--fail-on high]

Recorre ficheros Python con `ast` y marca llamadas a proveedores de IA sin
límite de tokens, modelos caros usados como clasificador, bucles de agente sin
tope y prompts de sistema largos sin caché.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado · 2 ruta
ilegible.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from finops_util import iter_files

SEVERITIES = {"low": 1, "medium": 2, "high": 3}
# Nombres que no son de nadie más: identifican una llamada al modelo por sí
# solos.
LLM_CALLS = {
    "completions",
    "generate_content",
    "invoke_model",
    "responses",
}
# `create`/`complete` son demasiado genéricos: `Model.create()` de un ORM
# disparaba `llm-sin-limite-tokens` con severidad alta y rompía CI. Solo
# cuentan si el receptor es de un cliente de IA (`client.chat.completions`,
# `llm.create`, `anthropic.messages`).
GENERIC_LLM_CALLS = {"create", "complete"}
LLM_RECEIVERS = {"chat", "completions", "completion", "messages", "llm",
                 "openai", "anthropic", "gemini", "bedrock", "ai"}
TOKEN_LIMITS = {"max_tokens", "max_output_tokens", "max_completion_tokens", "maxTokens"}
EXPENSIVE_MODELS = ("opus", "gpt-4", "o1", "o3", "pro")
CLASSIFIERS = {"classify", "classifier", "extract", "tag", "route", "label", "summarize_short"}
SKIP_PARTS = {"tests", "fixtures", "__pycache__", ".venv", ".git", "node_modules"}


def _attr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _receiver_names(node: ast.Call) -> set[str]:
    """Tokens de la cadena a la izquierda de la llamada (`client.chat.create`)."""
    names: set[str] = set()
    current: ast.AST | None = node.func.value if isinstance(node.func, ast.Attribute) else None
    while current is not None:
        if isinstance(current, ast.Attribute):
            names.add(current.attr.lower())
            current = current.value
        elif isinstance(current, ast.Call):
            current = current.func
        elif isinstance(current, ast.Name):
            names.add(current.id.lower())
            current = None
        else:
            current = None
    return names


def _is_llm_call(node: ast.Call) -> bool:
    name = _attr_name(node.func)
    if name in LLM_CALLS:
        return True
    if name in GENERIC_LLM_CALLS:
        return bool(_receiver_names(node) & LLM_RECEIVERS)
    return False


def _string_keyword(node: ast.Call, name: str, min_len: int = 0) -> str:
    for keyword in node.keywords:
        if keyword.arg != name:
            continue
        value = keyword.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str) and len(value.value) >= min_len:
            return value.value
    return ""


class Visitor(ast.NodeVisitor):
    def __init__(self, path: Path, source: str) -> None:
        self.path = path
        self.source = source
        self.findings: list[dict] = []
        self.stack: list[str] = []

    def add(self, node: ast.AST, rule: str, severity: str, message: str) -> None:
        self.findings.append({
            "file": self.path.as_posix(),
            "line": getattr(node, "lineno", 0),
            "rule": rule,
            "severity": severity,
            "message": message,
        })

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_Call(self, node: ast.Call) -> None:
        if _is_llm_call(node):
            self._check_call(node, _attr_name(node.func))
        self.generic_visit(node)

    def _check_call(self, node: ast.Call, name: str) -> None:
        keywords = {keyword.arg for keyword in node.keywords if keyword.arg}
        if not keywords & TOKEN_LIMITS:
            self.add(node, "llm-sin-limite-tokens", "high",
                     f"llamada {name}() sin max_tokens: la respuesta puede crecer sin tope")
        model = _string_keyword(node, "model")
        if model and any(marker in model.lower() for marker in EXPENSIVE_MODELS):
            severity = "high" if self.stack and self.stack[-1] in CLASSIFIERS else "medium"
            self.add(node, "modelo-caro", severity,
                     f"modelo de alto coste «{model}» en {self.stack[-1] if self.stack else 'módulo'}")
        if _string_keyword(node, "system", min_len=1000) and "cache_control" not in self.source:
            self.add(node, "prompt-sin-cache", "medium",
                     "prompt de sistema de más de 1000 caracteres sin cache_control")

    def visit_While(self, node: ast.While) -> None:
        endless = isinstance(node.test, ast.Constant) and node.test.value is True
        has_break = any(isinstance(item, ast.Break) for item in ast.walk(node))
        has_call = any(isinstance(item, ast.Call) and _is_llm_call(item) for item in ast.walk(node))
        if endless and not has_break and has_call:
            self.add(node, "bucle-sin-tope", "high",
                     "bucle while True con llamadas al modelo y sin break")
        self.generic_visit(node)


def scan_file(path: Path) -> list[dict]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except SyntaxError:
        return []
    visitor = Visitor(path, source)
    visitor.visit(tree)
    return visitor.findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Escáner de coste de llamadas a LLM.")
    parser.add_argument("--path", required=True, help="fichero o directorio a revisar")
    parser.add_argument("--json", action="store_true", help="salida JSON")
    parser.add_argument("--fail-on", default="high", choices=["low", "medium", "high", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    files = iter_files(target, {".py"}, frozenset(SKIP_PARTS))
    findings = [item for path in files for item in scan_file(path)]
    findings.sort(key=lambda item: (item["file"], item["line"], item["rule"]))
    by_severity = {name: sum(1 for item in findings if item["severity"] == name) for name in SEVERITIES}

    if args.json:
        print(json.dumps({
            "files": len(files),
            "findings": findings,
            "by_severity": by_severity,
        }, indent=2, ensure_ascii=False))
    else:
        for item in findings:
            print(f"{item['file']}:{item['line']} [{item['severity']}] {item['rule']}: {item['message']}")
        print(f"ficheros: {len(files)} · hallazgos: {len(findings)} · "
              + ", ".join(f"{name}={count}" for name, count in by_severity.items()))

    if args.fail_on == "none":
        return 0
    threshold = SEVERITIES[args.fail_on]
    breached = any(SEVERITIES[item["severity"]] >= threshold for item in findings)
    return 1 if breached else 0


if __name__ == "__main__":
    sys.exit(main())
