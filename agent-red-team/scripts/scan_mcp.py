"""Escanea configuración y servidores MCP en busca de riesgos de superficie.

Uso:
    py agent-red-team/scripts/scan_mcp.py --target <ruta> [--json]

Lee sin ejecutar nada: un `mcp.json`/`mcpServers` y el código del servidor que
lo acompaña. Comprueba secretos en claro, transporte sin TLS, comandos sin
versión fijada, autoaprobación de herramientas peligrosas, descripciones que
secuestran instrucciones y permisos de escritura o red.

No es una auditoría de prompt injection: la taxonomía de inyección y el OWASP
LLM Top 10 viven en `appsec-audit/appsec-llm`. Aquí solo se juzga la superficie
MCP (transporte, tools/resources/prompts, scopes y tokens).

Código de salida: 0 sin riesgos altos · 2 con algún `high`/`reject` · 1 ruta
ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITIES = {"low": 1, "medium": 2, "high": 3, "reject": 4}
RULES_PATH = Path(__file__).resolve().parent / "mcp_rules.json"
SCAN_SUFFIXES = {".json", ".py", ".js", ".ts", ".mjs", ".cjs", ".yaml", ".yml"}
SKIP_DIRS = {"__pycache__", ".venv", ".git", "node_modules", ".ruff_cache"}
STRING_FIELD = re.compile(r'"([A-Za-z0-9_.-]+)"\s*:\s*"([^"]*)"')
COMMAND_FIELD = re.compile(r'"command"\s*:\s*"([^"]*)"')
LIST_FIELD = re.compile(r'"(?P<key>[A-Za-z]+)"\s*:\s*\[(?P<body>[^\]]*)\]')


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def load_rules(path: Path = RULES_PATH) -> dict:
    """Reglas del escáner, con las expresiones compiladas y validadas."""
    data = json.loads(path.read_text(encoding="utf-8"))
    for entry in data.get("hijack_patterns", []):
        if not (isinstance(entry, list) and len(entry) >= 3):
            raise ValueError("entrada malformada en hijack_patterns: %r" % (entry,))
        re.compile(entry[0])
        if entry[1] not in SEVERITIES:
            raise ValueError("severidad desconocida: %r" % (entry[1],))
    return data


def line_of(text: str, index: int) -> int:
    """Número de línea (1-based) de un desplazamiento en el texto."""
    return text.count("\n", 0, index) + 1


def is_placeholder(value: str, markers: list[str]) -> bool:
    """¿El valor es una referencia a entorno en vez de un secreto literal?"""
    lowered = value.lower()
    return not value.strip() or any(marker.lower() in lowered for marker in markers)


def finding(path: str, number: int, rule: str, severity: str, message: str, fix: str) -> dict:
    """Hallazgo con la forma nativa que consume `contracts/findings/emit.py`."""
    return {
        "file": path, "line": number, "rule": rule, "severity": severity,
        "message": message, "fix": fix,
    }


def secret_findings(text: str, path: str, rules: dict) -> list[dict]:
    """Secretos literales en claves de configuración (`MCP_TOKEN`, `apiKey`…)."""
    keys = [key.lower() for key in rules.get("secret_keys", [])]
    markers = rules.get("placeholder_markers", [])
    found = []
    for match in STRING_FIELD.finditer(text):
        key, value = match.group(1).lower(), match.group(2)
        if not any(needle in key for needle in keys) or is_placeholder(value, markers):
            continue
        found.append(finding(
            path, line_of(text, match.start()), "token-en-claro", "high",
            "«%s» lleva un secreto literal en el fichero" % match.group(1),
            "Referencia la variable de entorno (`${MCP_TOKEN}`) y rota el valor expuesto.",
        ))
    return found


def transport_findings(text: str, path: str) -> list[dict]:
    """Endpoints remotos servidos sin TLS."""
    found = []
    for match in re.finditer(r"http://(?!localhost|127\.0\.0\.1)[^\s\"']+", text):
        found.append(finding(
            path, line_of(text, match.start()), "transporte-sin-tls", "high",
            "endpoint MCP sin TLS: %s" % match.group(0)[:80],
            "Usa https:// o un túnel local; el transporte lleva tokens y resultados de tools.",
        ))
    return found


def command_findings(text: str, path: str) -> list[dict]:
    """Comandos de arranque que ejecutan shell o paquetes sin versión fijada."""
    found = []
    for match in COMMAND_FIELD.finditer(text):
        command = match.group(1)
        number = line_of(text, match.start())
        if re.search(r"\b(?:sh|bash|cmd|powershell)\s+[-/]c\b", command):
            found.append(finding(
                path, number, "stdio-shell", "high",
                "el servidor arranca con un shell intermedio: %s" % command[:80],
                "Invoca el binario directamente; un `-c` convierte args en ejecución.",
            ))
        if re.search(r"\b(?:npx|uvx|pipx\s+run)\b", command) and not re.search(r"@\d|==\d", command):
            found.append(finding(
                path, number, "comando-sin-version", "medium",
                "el comando descarga un paquete sin versión fijada: %s" % command[:80],
                "Fija la versión (`paquete@1.4.2`); una actualización cambia el servidor sin revisión.",
            ))
    return found


def approval_findings(text: str, path: str, rules: dict) -> list[dict]:
    """Autoaprobación de todas las tools o de las peligrosas."""
    approval_keys = {key.lower() for key in rules.get("approval_keys", [])}
    dangerous = {tool.lower() for tool in rules.get("dangerous_tools", [])}
    found = []
    for match in LIST_FIELD.finditer(text):
        key = match.group("key")
        if key.lower() not in approval_keys:
            continue
        entries = [item.strip().strip('"').lower() for item in match.group("body").split(",") if item.strip()]
        risky = [entry for entry in entries if entry == "*" or entry in dangerous]
        if not risky:
            continue
        found.append(finding(
            path, line_of(text, match.start()), "autoaprobacion-amplia", "high",
            "«%s» aprueba sin confirmación: %s" % (key, ", ".join(sorted(risky))[:80]),
            "Deja la lista vacía o limita la aprobación a tools de solo lectura.",
        ))
    return found


def hijack_findings(text: str, path: str, rules: dict) -> list[dict]:
    """Descripciones de tools que intentan secuestrar instrucciones del agente."""
    found = []
    for pattern, severity, message in rules.get("hijack_patterns", []):
        for match in re.finditer(pattern, text, re.IGNORECASE):
            found.append(finding(
                path, line_of(text, match.start()), "tool-envenenada", severity,
                "%s: «%s»" % (message, match.group(0)[:60]),
                "Trata la descripción como dato no confiable y no la instales sin revisión manual.",
            ))
    return found


def permission_findings(text: str, path: str, rules: dict) -> list[dict]:
    """Permisos de escritura, borrado o red declarados por el servidor."""
    permission_keys = {key.lower() for key in rules.get("permission_keys", [])}
    risky_values = {value.lower() for value in rules.get("permission_values", [])}
    found = []
    for match in STRING_FIELD.finditer(text):
        key, value = match.group(1).lower(), match.group(2).lower()
        if key in permission_keys and value in risky_values:
            found.append(finding(
                path, line_of(text, match.start()), "permiso-excesivo", "medium",
                "el servidor declara permiso «%s: %s»" % (key, value),
                "Reduce el permiso a lectura o justifícalo en el propósito del servidor.",
            ))
    return found


def scan_file(path: Path, root: Path, rules: dict) -> list[dict]:
    """Hallazgos de un fichero; vacío si no es texto legible."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    relative = path.relative_to(root).as_posix() if path != root else path.name
    findings = []
    findings.extend(secret_findings(text, relative, rules))
    findings.extend(transport_findings(text, relative))
    findings.extend(command_findings(text, relative))
    findings.extend(approval_findings(text, relative, rules))
    findings.extend(hijack_findings(text, relative, rules))
    findings.extend(permission_findings(text, relative, rules))
    return findings


def scan_target(target: Path, rules: dict) -> dict:
    """Informe completo del objetivo."""
    files = []
    if target.is_file():
        files = [target]
    else:
        for path in sorted(target.rglob("*")):
            if path.is_file() and path.suffix.lower() in SCAN_SUFFIXES:
                if not SKIP_DIRS & set(path.relative_to(target).parts):
                    files.append(path)

    findings = []
    for path in files:
        findings.extend(scan_file(path, target if target.is_dir() else target.parent, rules))

    counts = {severity: sum(1 for item in findings if item["severity"] == severity) for severity in SEVERITIES}
    return {
        "target": str(target),
        "files": len(files),
        "findings": findings,
        "summary": {"total": len(findings), **counts},
        "verdict": "REVISAR" if counts["high"] or counts["reject"] else "SIN RIESGOS ALTOS",
    }


def print_text(document: dict) -> None:
    """Informe legible para el chat."""
    print("MCP · %s (%d ficheros)" % (document["target"], document["files"]))
    print("VEREDICTO: %s · %d hallazgo(s)" % (document["verdict"], document["summary"]["total"]))
    for item in document["findings"]:
        print("- [%s] %s %s:%s — %s" % (item["severity"], item["rule"], item["file"], item["line"], item["message"]))


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Riesgos de superficie en configuración y servidores MCP.")
    parser.add_argument("--target", required=True, help="configuración, carpeta o servidor MCP")
    parser.add_argument("--json", action="store_true", help="salida JSON")
    args = parser.parse_args(argv)

    target = Path(args.target).resolve()
    if not target.exists():
        print("no existe la ruta: %s" % target, file=sys.stderr)
        return 1
    try:
        rules = load_rules()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("no se pudieron cargar las reglas: %s" % error, file=sys.stderr)
        return 1

    document = scan_target(target, rules)
    if args.json:
        print(json.dumps(document, indent=2, ensure_ascii=False))
    else:
        print_text(document)
    return 2 if document["verdict"] == "REVISAR" else 0


if __name__ == "__main__":
    sys.exit(main())
