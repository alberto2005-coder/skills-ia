#!/usr/bin/env python3
"""
Agent Red Team - Motor de Análisis Estático y AST para Agent Skills.
Detecta esteganografía Unicode, Prompt Injection oculto, payloads Base64/Hex,
alta entropía, primitivas RCE en AST Python y exfiltración de credenciales.

Uso:
  python3 scripts/scan_skill.py --target ./ruta-skill
  python3 scripts/scan_skill.py --target ./ruta-skill --json
"""

import argparse
import ast
import base64
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

# 1. Rangos Unicode peligrosos (ASCII Smuggling, Zero-Width, Bidi Overrides)
INVISIBLE_UNICODE_RANGES = [
    (0x200B, 0x200F, "Zero-Width / Directional Mark"),
    (0x202A, 0x202E, "Bidirectional Text Override (Trojan Source)"),
    (0x2060, 0x2064, "Word Joiner / Invisible Operators"),
    (0x2066, 0x2069, "Bidirectional Isolate"),
    (0xFEFF, 0xFEFF, "Zero-Width No-Break Space (BOM fuera de inicio)"),
    (0xE0000, 0xE007F, "Unicode Tag Characters (ASCII Smuggling Payload)"),
]

# 2. Patrones de Prompt Injection y secuestro de instrucciones
PROMPT_INJECTION_PATTERNS = [
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", "CRÍTICA", "LLM01: Override directo de instrucciones del sistema"),
    (r"disregard\s+(all\s+)?(previous|prior|system)\s+", "CRÍTICA", "LLM01: Anulación de reglas previas"),
    (r"you\s+are\s+now\s+(in\s+)?(developer|jailbreak|dan|unrestricted)\s+mode", "CRÍTICA", "LLM01: Intento de Jailbreak / cambio de rol"),
    (r"(do\s+not|never|don't)\s+(tell|inform|mention|show|alert)\s+(the\s+)?user", "ALTA", "LLM01: Instrucción encubierta para ocultar acciones al usuario"),
    (r"silently\s+(execute|run|send|upload|post|exfiltrate|read)", "CRÍTICA", "LLM01: Ejecución o exfiltración silenciosa"),
    (r"<!--[\s\S]*?(ignore|system|execute|curl|http|password|secret|token|ssh|env)[\s\S]*?-->", "ALTA", "LLM01: Comentario HTML oculto con directivas sospechosas"),
    (r"!\[.*?\]\(https?://[^\)]*(\{|%7B|\$|query=|data=|token=|key=|secret=)", "CRÍTICA", "LLM02: Posible exfiltración Markdown vía parámetros URL"),
    (r"(printenv|env\b|set\b)\s*\|\s*(curl|wget|nc|netcat|bash|sh|python)", "CRÍTICA", "Exfiltración directa de variables de entorno"),
]

# 3. Rutas y archivos sensibles objetivo de exfiltración
SENSITIVE_PATHS = [
    r"~/\.ssh", r"/\.ssh/", r"id_rsa", r"id_ed25519", r"authorized_keys",
    r"~/\.aws", r"/\.aws/credentials",
    r"~/\.gnupg", r"/\.gnupg/",
    r"\.env\b", r"\.env\.local", r"\.env\.production",
    r"\.git-credentials", r"\.npmrc", r"\.pypirc", r"\.netrc",
    r"/etc/shadow", r"/etc/passwd",
    r"Library/Keychains", r"Login Data", r"Cookies",
    r"OPENAI_API_KEY", r"ANTHROPIC_API_KEY", r"AWS_SECRET_ACCESS_KEY", r"GITHUB_TOKEN",
]

# 4. Patrones peligrosos en Bash / Shell / JS
SHELL_DANGER_PATTERNS = [
    (r"(curl|wget)\s+[^\n]*\|\s*(bash|sh|zsh|python|perl|ruby)", "CRÍTICA", "Ejecución remota arbitraria (Pipe to Shell)"),
    (r"/dev/tcp/\d+\.\d+\.\d+\.\d+/\d+", "CRÍTICA", "Reverse Shell vía /dev/tcp"),
    (r"\b(nc|ncat|netcat)\s+.*(-e|-c)\s+", "CRÍTICA", "Reverse Shell con Netcat"),
    (r"base64\s+(-d|--decode)", "ALTA", "Decodificación Base64 en shell (posible drop/payload)"),
    (r"chmod\s+(\+x|777)\s+", "MEDIA", "Asignación de permisos de ejecución/globales"),
    (r"(crontab|systemctl\s+enable|/etc/cron|~/\.bashrc|~/\.zshrc)", "ALTA", "Mecanismo de persistencia en sistema"),
]

# 5. Módulos y llamadas críticas en AST Python
DANGEROUS_IMPORTS = {
    "subprocess": "ALTA",
    "pty": "CRÍTICA",
    "socket": "ALTA",
    "ctypes": "CRÍTICA",
    "pickle": "ALTA",
    "marshal": "ALTA",
    "telnetlib": "ALTA",
    "ftplib": "ALTA",
    "paramiko": "ALTA",
    "webbrowser": "MEDIA",
}

NETWORK_IMPORTS = {"requests", "urllib", "urllib3", "httpx", "aiohttp", "http.client", "websocket"}

DANGEROUS_CALLS = {
    "eval": "CRÍTICA",
    "exec": "CRÍTICA",
    "compile": "ALTA",
    "__import__": "CRÍTICA",
    "os.system": "CRÍTICA",
    "os.popen": "CRÍTICA",
    "os.execve": "CRÍTICA",
    "os.spawnl": "CRÍTICA",
    "subprocess.Popen": "ALTA",
    "subprocess.run": "MEDIA",
    "subprocess.call": "ALTA",
    "subprocess.check_output": "ALTA",
    "pickle.loads": "CRÍTICA",
    "yaml.load": "ALTA",
}

SEVERITY_WEIGHTS = {"CRÍTICA": 45, "ALTA": 25, "MEDIA": 10, "BAJA": 3}


def shannon_entropy(data: str) -> float:
    if not data:
        return 0.0
    freq = {ch: data.count(ch) for ch in set(data)}
    length = len(data)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


def detect_unicode_anomalies(text: str, rel_path: str) -> List[Dict[str, Any]]:
    findings = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        hidden_chars = []
        decoded_tags = []
        for idx, ch in enumerate(line):
            if line_num == 1 and idx == 0 and ord(ch) == 0xFEFF:
                continue
            cp = ord(ch)
            for start, end, label in INVISIBLE_UNICODE_RANGES:
                if start <= cp <= end:
                    hidden_chars.append((cp, label))
                    if 0xE0020 <= cp <= 0xE007E:
                        decoded_tags.append(chr(cp - 0xE0000))
        if hidden_chars:
            detail = f"Detectados {len(hidden_chars)} caracteres Unicode invisibles/control ({hidden_chars[0][1]})."
            if decoded_tags:
                detail += f" Payload ASCII Smuggling decodificado: '{''.join(decoded_tags)}'"
            findings.append({
                "severity": "CRÍTICA",
                "file": rel_path,
                "line": line_num,
                "category": "Unicode Steganography / ASCII Smuggling",
                "evidence": repr(line[:120]),
                "description": detail,
            })
    return findings


def inspect_base64_blobs(text: str, rel_path: str) -> List[Dict[str, Any]]:
    findings = []
    b64_regex = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{28,}={0,2}(?![A-Za-z0-9+/=])")
    suspicious_keywords = ("http://", "https://", "/bin/sh", "/bin/bash", "ignore", "system", "curl", "wget", "eval(", "exec(", "ssh", "password", "token")

    for line_num, line in enumerate(text.splitlines(), start=1):
        for match in b64_regex.finditer(line):
            blob = match.group(0)
            try:
                raw = base64.b64decode(blob, validate=True)
                decoded = raw.decode("utf-8", errors="ignore")
                if len(decoded) >= 8 and sum(c.isprintable() for c in decoded) / len(decoded) > 0.8:
                    lower_dec = decoded.lower()
                    if any(kw in lower_dec for kw in suspicious_keywords):
                        findings.append({
                            "severity": "CRÍTICA",
                            "file": rel_path,
                            "line": line_num,
                            "category": "Obfuscated Payload (Base64)",
                            "evidence": f"{blob[:40]}... -> '{decoded[:80]}'",
                            "description": "Cadena Base64 decodifica a una URL, comando o instrucción sospechosa.",
                        })
                    elif shannon_entropy(blob) > 4.7 and len(blob) > 60:
                        findings.append({
                            "severity": "MEDIA",
                            "file": rel_path,
                            "line": line_num,
                            "category": "High-Entropy Encoded Blob",
                            "evidence": f"{blob[:50]}...",
                            "description": "Bloque Base64 largo embebido en el texto; requiere revisión manual.",
                        })
            except Exception:
                continue
    return findings


def analyze_python_ast(code: str, rel_path: str) -> List[Dict[str, Any]]:
    findings = []
    try:
        tree = ast.parse(code, filename=rel_path)
    except SyntaxError as e:
        findings.append({
            "severity": "MEDIA",
            "file": rel_path,
            "line": e.lineno or 1,
            "category": "Python Syntax Error",
            "evidence": str(e),
            "description": "El archivo Python no pudo parsearse con AST (posible ofuscación o código corrupto).",
        })
        return findings

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                base_mod = mod.split(".")[0]
                if mod in DANGEROUS_IMPORTS or base_mod in DANGEROUS_IMPORTS:
                    sev = DANGEROUS_IMPORTS.get(mod, DANGEROUS_IMPORTS.get(base_mod, "MEDIA"))
                    findings.append({
                        "severity": sev,
                        "file": rel_path,
                        "line": node.lineno,
                        "category": "AST Dangerous Import",
                        "evidence": f"import {mod}",
                        "description": f"Importación de módulo con capacidad de ejecución de comandos, memoria o red baja ({mod}).",
                    })
                elif mod in NETWORK_IMPORTS or base_mod in NETWORK_IMPORTS:
                    findings.append({
                        "severity": "MEDIA",
                        "file": rel_path,
                        "line": node.lineno,
                        "category": "AST Network Capability",
                        "evidence": f"import {mod}",
                        "description": f"El script importa librerías de red ({mod}). Verificar si la Skill realmente requiere salida a Internet.",
                    })

        elif isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module
            base_mod = mod.split(".")[0]
            if mod in DANGEROUS_IMPORTS or base_mod in DANGEROUS_IMPORTS:
                sev = DANGEROUS_IMPORTS.get(mod, DANGEROUS_IMPORTS.get(base_mod, "MEDIA"))
                findings.append({
                    "severity": sev,
                    "file": rel_path,
                    "line": node.lineno,
                    "category": "AST Dangerous ImportFrom",
                    "evidence": f"from {mod} import ...",
                    "description": f"Importación desde módulo crítico ({mod}).",
                })
            elif mod in NETWORK_IMPORTS or base_mod in NETWORK_IMPORTS:
                findings.append({
                    "severity": "MEDIA",
                    "file": rel_path,
                    "line": node.lineno,
                    "category": "AST Network Capability",
                    "evidence": f"from {mod} import ...",
                    "description": f"Capacidad de red detectada vía {mod}.",
                })

        elif isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                call_name = f"{node.func.value.id}.{node.func.attr}"

            if call_name in DANGEROUS_CALLS:
                sev = DANGEROUS_CALLS[call_name]
                extra = ""
                if call_name.startswith("subprocess."):
                    for kw in node.keywords:
                        if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            sev = "CRÍTICA"
                            extra = " con shell=True (riesgo de Command Injection)"
                findings.append({
                    "severity": sev,
                    "file": rel_path,
                    "line": node.lineno,
                    "category": "AST Critical Function Call",
                    "evidence": f"{call_name}(...)",
                    "description": f"Llamada potencialmente peligrosa a '{call_name}'{extra}.",
                })

            if call_name == "getattr" and len(node.args) >= 2:
                if isinstance(node.args[1], ast.Constant) and str(node.args[1].value) in ("system", "popen", "eval", "exec", "__import__"):
                    findings.append({
                        "severity": "CRÍTICA",
                        "file": rel_path,
                        "line": node.lineno,
                        "category": "AST Reflection Obfuscation",
                        "evidence": f"getattr(..., '{node.args[1].value}')",
                        "description": "Uso de getattr() para evadir detección estática de llamadas peligrosas.",
                    })

        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value
            if re.match(r"^https?://", val.strip(), re.IGNORECASE):
                findings.append({
                    "severity": "BAJA",
                    "file": rel_path,
                    "line": node.lineno,
                    "category": "AST Hardcoded URL",
                    "evidence": val[:100],
                    "description": "URL hardcodeada dentro del código Python; confirmar que sea un endpoint legítimo y documentado.",
                })

    return findings


def scan_text_patterns(text: str, rel_path: str, ext: str) -> List[Dict[str, Any]]:
    findings = []
    lines = text.splitlines()

    for pattern, sev, desc in PROMPT_INJECTION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            line_num = text[: match.start()].count("\n") + 1
            findings.append({
                "severity": sev,
                "file": rel_path,
                "line": line_num,
                "category": "Prompt Injection / Instruction Hijack",
                "evidence": match.group(0).strip()[:120],
                "description": desc,
            })

    for line_num, line in enumerate(lines, start=1):
        for path_pat in SENSITIVE_PATHS:
            if re.search(path_pat, line):
                findings.append({
                    "severity": "ALTA",
                    "file": rel_path,
                    "line": line_num,
                    "category": "Sensitive Credential / Path Access",
                    "evidence": line.strip()[:120],
                    "description": f"Referencia a archivo o variable sensible ({path_pat}).",
                })

    if ext in (".sh", ".bash", ".zsh", ".md", ".py", ".js", ".ts"):
        for pattern, sev, desc in SHELL_DANGER_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                line_num = text[: match.start()].count("\n") + 1
                findings.append({
                    "severity": sev,
                    "file": rel_path,
                    "line": line_num,
                    "category": "Dangerous Shell / Execution Pattern",
                    "evidence": match.group(0).strip()[:120],
                    "description": desc,
                })

    return findings


def scan_target(target_path: str) -> Dict[str, Any]:
    target = Path(target_path).resolve()
    if not target.exists():
        return {"error": f"La ruta no existe: {target}"}

    files_to_scan = []
    if target.is_file():
        files_to_scan.append(target)
        base_root = target.parent
    else:
        base_root = target
        for root, _, files in os.walk(target):
            for fname in files:
                files_to_scan.append(Path(root) / fname)

    all_findings: List[Dict[str, Any]] = []
    scanned_files = []
    binary_files = []
    has_skill_md = False

    for fpath in sorted(files_to_scan):
        rel_path = str(fpath.relative_to(base_root))
        if fpath.name == "SKILL.md":
            has_skill_md = True

        ext = fpath.suffix.lower()
        if ext in (".exe", ".dll", ".so", ".dylib", ".bin", ".pyc", ".pyo", ".jar", ".wasm"):
            binary_files.append(rel_path)
            all_findings.append({
                "severity": "CRÍTICA",
                "file": rel_path,
                "line": 0,
                "category": "Opaque Binary Artifact",
                "evidence": fpath.name,
                "description": "Binario compilado dentro de una Agent Skill; no es auditable en texto plano.",
            })
            continue

        try:
            content = fpath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            binary_files.append(rel_path)
            all_findings.append({
                "severity": "ALTA",
                "file": rel_path,
                "line": 0,
                "category": "Non-UTF8 / Binary File",
                "evidence": fpath.name,
                "description": "Archivo no legible como UTF-8; inspeccionar manualmente antes de confiar.",
            })
            continue

        scanned_files.append(rel_path)
        all_findings.extend(detect_unicode_anomalies(content, rel_path))
        all_findings.extend(inspect_base64_blobs(content, rel_path))
        all_findings.extend(scan_text_patterns(content, rel_path, ext))

        if ext == ".py":
            all_findings.extend(analyze_python_ast(content, rel_path))

    if target.is_dir() and not has_skill_md:
        all_findings.append({
            "severity": "BAJA",
            "file": ".",
            "line": 0,
            "category": "Structure Anomaly",
            "evidence": "Missing SKILL.md",
            "description": "La carpeta no contiene un archivo SKILL.md en su raíz.",
        })

    raw_score = sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in all_findings)
    risk_score = min(100, raw_score)

    if risk_score >= 50 or any(f["severity"] == "CRÍTICA" for f in all_findings):
        verdict = "BLOQUEADO - MALICIOSO / CRÍTICO"
    elif risk_score >= 16:
        verdict = "PRECAUCIÓN - REVISIÓN MANUAL"
    else:
        verdict = "APROBADO"

    return {
        "target": str(target),
        "verdict": verdict,
        "risk_score": risk_score,
        "files_scanned_count": len(scanned_files),
        "scanned_files": scanned_files,
        "binary_files": binary_files,
        "findings_count": len(all_findings),
        "findings": all_findings,
    }


def main():
    parser = argparse.ArgumentParser(description="Auditor Red Team para Agent Skills.")
    parser.add_argument("--target", required=True, help="Ruta a la carpeta de la skill o archivo individual")
    parser.add_argument("--json", action="store_true", help="Imprimir salida en formato JSON")
    args = parser.parse_args()

    result = scan_target(args.target)
    if "error" in result:
        print(json.dumps(result, indent=2, ensure_ascii=False) if args.json else f"ERROR: {result['error']}")
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print(f"AGENT RED TEAM REPORT | Target: {result['target']}")
        print(f"VEREDICTO: {result['verdict']} (Risk Score: {result['risk_score']}/100)")
        print(f"Archivos analizados: {result['files_scanned_count']} | Hallazgos: {result['findings_count']}")
        print("=" * 60)
        for idx, f in enumerate(result["findings"], 1):
            print(f"\n[{idx}] [{f['severity']}] {f['category']}")
            print(f"    Ubicación: {f['file']}:{f['line']}")
            print(f"    Detalle:   {f['description']}")
            print(f"    Evidencia: {f['evidence']}")

    if result["verdict"].startswith("BLOQUEADO"):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
