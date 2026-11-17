#!/usr/bin/env python3
"""
Agent Red Team - Motor de Análisis Estático y AST para Agent Skills.
Detecta esteganografía Unicode, Prompt Injection oculto, payloads Base64/Hex,
alta entropía, primitivas RCE en AST Python y exfiltración de credenciales.

Incluye (Fase 2 del plan de mejora):
  - Excepción de code fences: el texto documentado dentro de un bloque de
    Markdown no cuenta como hallazgo vivo de inyección/exfiltración textual.
    Los bloques bash/shell/python sí se revisan como comandos reales.
  - Nivel RECHAZO (REJECT): combinaciones de señales que fallan siempre,
    aunque cada señal por separado sea MEDIA.

Uso:
  python3 scripts/scan_skill.py --target ./ruta-skill
  python3 scripts/scan_skill.py --target ./ruta-skill --json
  py scripts/scan_skill.py --target .\\ruta-skill --json
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
from typing import Any, Dict, List, Optional, Tuple

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

SEVERITY_WEIGHTS = {"RECHAZO": 100, "CRÍTICA": 45, "ALTA": 25, "MEDIA": 10, "BAJA": 3}

# 6. Excepción de code fences (solo Markdown)
MARKDOWN_EXTS = (".md", ".markdown", ".mdx")

# Lenguajes de fence que se ejecutan de verdad: su contenido se revisa como
# comandos reales. El resto de fences (text, markdown, json, ...) es texto
# documentado y no genera hallazgos de inyección/exfiltración textual.
EXECUTABLE_FENCE_LANGS = {
    "bash", "sh", "shell", "zsh", "ksh", "fish",
    "console", "shell-session", "terminal",
    "powershell", "ps1", "pwsh", "cmd", "bat",
    "python", "py", "python3", "py3",
    "js", "javascript", "ts", "typescript", "node",
}

FENCE_MARKER_RE = re.compile(r"^(`{3,}|~{3,})([^\s`~]*)")


def _blank_line(line: str) -> str:
    """Sustituye una línea por otra vacía conservando el número de línea."""
    return "\n" if line.endswith("\n") else ""


def _fence_marker(line: str) -> Optional[Tuple[str, str]]:
    """Devuelve (marcador, lenguaje) si la línea abre o cierra un bloque de código."""
    match = FENCE_MARKER_RE.match(line.lstrip())
    if not match:
        return None
    return match.group(1), match.group(2).strip().lower()


def build_markdown_views(text: str) -> Tuple[str, str, str]:
    """Separa un Markdown en tres vistas con la misma numeración de líneas.

    - ``masked``: solo prosa (frontmatter y texto fuera de fences).
    - ``live``:   prosa + contenido de fences ejecutables (bash/shell/python/...).
    - ``exec``:   solo contenido de fences ejecutables.

    Así, un payload documentado en un fence de texto no es un hallazgo vivo,
    pero un comando real dentro de un fence bash sí se audita.
    """
    masked_lines: List[str] = []
    live_lines: List[str] = []
    exec_lines: List[str] = []

    in_fence = False
    fence_char = ""
    fence_len = 0
    fence_exec = False

    for line in text.splitlines(keepends=True):
        marker = _fence_marker(line)

        if marker:
            marker_str, lang = marker
            if not in_fence:
                in_fence = True
                fence_char = marker_str[0]
                fence_len = len(marker_str)
                fence_exec = lang in EXECUTABLE_FENCE_LANGS
                masked_lines.append(_blank_line(line))
                live_lines.append(_blank_line(line))
                exec_lines.append(_blank_line(line))
                continue
            if marker_str[0] == fence_char and len(marker_str) >= fence_len and not lang:
                in_fence = False
                fence_exec = False
                masked_lines.append(_blank_line(line))
                live_lines.append(_blank_line(line))
                exec_lines.append(_blank_line(line))
                continue

        if in_fence and not fence_exec:
            # Texto documentado: invisible para inyección/exfiltración textual.
            masked_lines.append(_blank_line(line))
            live_lines.append(_blank_line(line))
            exec_lines.append(_blank_line(line))
        elif in_fence and fence_exec:
            # Comando real: se audita como shell/código.
            masked_lines.append(_blank_line(line))
            live_lines.append(line)
            exec_lines.append(line)
        else:
            masked_lines.append(line)
            live_lines.append(line)
            exec_lines.append(_blank_line(line))

    return "".join(masked_lines), "".join(live_lines), "".join(exec_lines)


def load_rules(rules_path: Optional[str] = None) -> Dict[str, Any]:
    path = Path(rules_path).resolve() if rules_path else Path(__file__).resolve().parent / "rules.json"
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de reglas en: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def inspect_base64_blobs(text: str, rel_path: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = []
    b64_regex = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{28,}={0,2}(?![A-Za-z0-9+/=])")
    suspicious_keywords = tuple(rules.get("base64_suspicious_keywords", []))

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


def analyze_python_ast(code: str, rel_path: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    dangerous_imports = rules.get("dangerous_imports", {})
    network_imports = set(rules.get("network_imports", []))
    dangerous_calls = rules.get("dangerous_calls", {})
    reflection_targets = {k.split(".")[-1] for k in dangerous_calls.keys()}

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
                if mod in dangerous_imports or base_mod in dangerous_imports:
                    sev = dangerous_imports.get(mod, dangerous_imports.get(base_mod, "MEDIA"))
                    findings.append({
                        "severity": sev,
                        "file": rel_path,
                        "line": node.lineno,
                        "category": "AST Dangerous Import",
                        "evidence": f"import {mod}",
                        "description": f"Importación de módulo con capacidad de ejecución de comandos, memoria o red baja ({mod}).",
                    })
                elif mod in network_imports or base_mod in network_imports:
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
            if mod in dangerous_imports or base_mod in dangerous_imports:
                sev = dangerous_imports.get(mod, dangerous_imports.get(base_mod, "MEDIA"))
                findings.append({
                    "severity": sev,
                    "file": rel_path,
                    "line": node.lineno,
                    "category": "AST Dangerous ImportFrom",
                    "evidence": f"from {mod} import ...",
                    "description": f"Importación desde módulo crítico ({mod}).",
                })
            elif mod in network_imports or base_mod in network_imports:
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

            if call_name in dangerous_calls:
                sev = dangerous_calls[call_name]
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
                if isinstance(node.args[1], ast.Constant) and str(node.args[1].value) in reflection_targets:
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


def _iter_pattern_hits(pattern: str, text: str) -> List[Tuple[int, str]]:
    hits = []
    for match in re.finditer(pattern, text, re.IGNORECASE):
        line_num = text[: match.start()].count("\n") + 1
        hits.append((line_num, match.group(0).strip()))
    return hits


def _first_pattern_hit(pattern: str, text: str) -> Optional[Tuple[int, str]]:
    hits = _iter_pattern_hits(pattern, text)
    return hits[0] if hits else None


def detect_reject_combos(text: str, rel_path: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Evalúa las combinaciones REJECT sobre el texto de un único fichero."""
    findings: List[Dict[str, Any]] = []
    if not text.strip():
        return findings

    for combo in rules.get("reject_combos", []):
        matched: List[Tuple[str, int, str]] = []
        fired = True
        for grupo in combo["grupos"]:
            hit = None
            for patron in grupo["patrones"]:
                found = _first_pattern_hit(patron, text)
                if found:
                    hit = (grupo["etiqueta"], found[0], found[1])
                    break
            if not hit:
                fired = False
                break
            matched.append(hit)

        if not fired:
            continue

        line = min(m[1] for m in matched)
        evidence = " + ".join(f"{label}: '{snippet[:60]}'" for label, _, snippet in matched)
        findings.append({
            "severity": "RECHAZO",
            "file": rel_path,
            "line": line,
            "category": f"REJECT Combination [{combo['id']}] {combo['nombre']}",
            "combo": combo["id"],
            "signals": [label for label, _, _ in matched],
            "evidence": evidence[:300],
            "description": combo["descripcion"],
            "recommendation": combo["recomendacion"],
        })

    return findings


def scan_text_patterns(
    text: str,
    rel_path: str,
    ext: str,
    rules: Dict[str, Any],
    live_text: Optional[str] = None,
    exec_text: Optional[str] = None,
) -> List[Dict[str, Any]]:

    """Busca patrones textuales.

    ``text``      prosa / texto fuera de fences (inyección y comentarios).
    ``live_text`` prosa + fences ejecutables (rutas sensibles).
    ``exec_text`` solo fences ejecutables (comandos shell reales).
    """
    findings: List[Dict[str, Any]] = []
    if live_text is None:
        live_text = text
    if exec_text is None:
        exec_text = text

    for pattern, sev, desc in rules.get("prompt_injection_patterns", []):
        for line_num, snippet in _iter_pattern_hits(pattern, text):
            findings.append({
                "severity": sev,
                "file": rel_path,
                "line": line_num,
                "category": "Prompt Injection / Instruction Hijack",
                "evidence": snippet[:120],
                "description": desc,
            })

    for line_num, line in enumerate(live_text.splitlines(), start=1):
        if not line.strip():
            continue
        for path_pat in rules.get("sensitive_paths", []):
            if re.search(path_pat, line):
                findings.append({
                    "severity": "ALTA",
                    "file": rel_path,
                    "line": line_num,
                    "category": "Sensitive Credential / Path Access",
                    "evidence": line.strip()[:120],
                    "description": f"Referencia a archivo o variable sensible ({path_pat}).",
                })

    if ext in (".sh", ".bash", ".zsh", ".md", ".markdown", ".mdx", ".py", ".js", ".ts"):
        for pattern, sev, desc in rules.get("shell_danger_patterns", []):
            for line_num, snippet in _iter_pattern_hits(pattern, exec_text):
                findings.append({
                    "severity": sev,
                    "file": rel_path,
                    "line": line_num,
                    "category": "Dangerous Shell / Execution Pattern",
                    "evidence": snippet[:120],
                    "description": desc,
                })

    return findings


def scan_target(target_path: str, rules_path: Optional[str] = None) -> Dict[str, Any]:
    try:
        rules = load_rules(rules_path)
    except Exception as e:
        return {"error": f"Error cargando reglas: {e}"}
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
    fences_maskados = 0

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

        if ext in MARKDOWN_EXTS:
            prose, live, exec_only = build_markdown_views(content)
            if live != content:
                fences_maskados += 1
        else:
            prose = live = exec_only = content

        all_findings.extend(detect_unicode_anomalies(content, rel_path))
        all_findings.extend(inspect_base64_blobs(prose, rel_path, rules))

        all_findings.extend(inspect_base64_blobs(prose, rel_path, rules))
        all_findings.extend(scan_text_patterns(prose, rel_path, ext, rules, live_text=live, exec_text=exec_only))
        all_findings.extend(detect_reject_combos(exec_only, rel_path, rules))

        if ext == ".py":
            all_findings.extend(analyze_python_ast(content, rel_path, rules))

    if target.is_dir() and not has_skill_md:
        all_findings.append({
            "severity": "BAJA",
            "file": ".",
            "line": 0,
            "category": "Structure Anomaly",
            "evidence": "Missing SKILL.md",
            "description": "La carpeta no contiene un archivo SKILL.md en su raíz.",
        })

    reject_findings = [f for f in all_findings if f["severity"] == "RECHAZO"]
    raw_score = sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in all_findings)
    risk_score = min(100, raw_score)

    if reject_findings or risk_score >= 50 or any(f["severity"] == "CRÍTICA" for f in all_findings):
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
        "markdown_files_with_fences": fences_maskados,
        "reject_triggered": bool(reject_findings),
        "reject_combos": sorted({f.get("combo", "") for f in reject_findings if f.get("combo")}),
        "findings_count": len(all_findings),
        "findings": all_findings,
    }


def _configurar_salida_utf8() -> None:
    """Fuerza UTF-8 en stdout/stderr (pipes y consolas de Windows)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def main():
    _configurar_salida_utf8()
    parser = argparse.ArgumentParser(
        description="Auditor Red Team para Agent Skills (análisis estático, sin ejecutar el objetivo).",
        epilog="Salida JSON compatible con templates/report-schema.json. "
               "Código de salida: 0 = apto, 2 = BLOQUEADO/RECHAZO, 1 = error de ruta.",
    )
    parser.add_argument("--target", required=True, help="Ruta a la carpeta de la skill o archivo individual")
    parser.add_argument("--json", action="store_true", help="Imprimir salida en formato JSON")
    parser.add_argument("--rules", default=None, help="Ruta opcional al archivo rules.json")
    args = parser.parse_args()

    result = scan_target(args.target, args.rules)
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
        if result["reject_triggered"]:
            print(f"NIVEL REJECT: combinaciones disparadas: {', '.join(result['reject_combos'])}")
        print("=" * 60)
        for idx, f in enumerate(result["findings"], 1):
            print(f"\n[{idx}] [{f['severity']}] {f['category']}")
            print(f"    Ubicación: {f['file']}:{f['line']}")
            print(f"    Detalle:   {f['description']}")
            print(f"    Evidencia: {f['evidence']}")
            if f["severity"] == "RECHAZO":
                print(f"    Acción:    {f.get('recommendation', 'Rechazar la instalación.')}")

    if result["verdict"].startswith("BLOQUEADO"):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
