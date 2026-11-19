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

SEVERITY_WEIGHTS = {"reject": 100, "critical": 45, "high": 25, "medium": 10, "low": 3}

# La salida habla una sola escala. Las reglas heredadas (o un `--rules` de otra
# instalación) pueden venir en español y se traducen al cargar: un hallazgo con
# una severidad que nadie puntúa cuenta cero, así que el escáner lo encontraba y
# el veredicto seguía saliendo APROBADO con el payload delante.
SEVERITY_ALIASES = {
    "reject": "reject", "rechazo": "reject",
    "critical": "critical", "critica": "critical", "crítica": "critical",
    "high": "high", "alta": "high",
    "medium": "medium", "media": "medium",
    "low": "low", "baja": "low",
}


def canonical_severity(value: Any) -> str:
    """Traduce una severidad declarada en las reglas, o falla si no existe."""
    key = str(value).strip().lower()
    if key not in SEVERITY_ALIASES:
        raise ValueError(f"severidad desconocida en las reglas: {value!r}")
    return SEVERITY_ALIASES[key]

# 6. Excepción de code fences (solo Markdown)
MARKDOWN_EXTS = (".md", ".markdown", ".mdx")

# Directorios que nunca son parte de una skill: sin esta poda, un
# __pycache__/mod.cpython-313.pyc (generado al importar cualquier script)
# se clasifica como "Opaque Binary Artifact" CRÍTICA y da veredicto
# BLOQUEADO-MALICIOSO sobre una skill completamente limpia.
PRUNE_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", ".venv", "venv", "node_modules",
}

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


def _validate_rules(rules: Dict[str, Any]) -> None:
    """Compila todas las regex y valida la forma de los combos al cargar.

    Sin esto, un `--rules` ajeno con un patrón inválido reventaba con
    `re.error` en mitad del escaneo, y un combo sin `grupos` con `KeyError`:
    ambos con traceback, fuera de los códigos de salida documentados.
    """
    if not isinstance(rules, dict):
        raise ValueError("las reglas deben ser un objeto JSON")

    for key in ("prompt_injection_patterns", "shell_danger_patterns",
                "comment_injection_patterns"):
        _validate_entries(rules.get(key, []), key)

    for key in ("sensitive_paths", "base64_suspicious_keywords"):
        _validate_paths(rules.get(key, []), key)

    for combo in rules.get("reject_combos", []):
        _validate_combo(combo)

    for key in ("dangerous_imports", "network_imports", "dangerous_calls"):
        # `network_imports` es una lista y las otras dos son mapas; omitir una
        # clave opcional no puede invalidar el fichero entero.
        _validate_mapping(rules.get(key, [] if key == "network_imports" else {}), key)


def _validate_entries(entries, key):
    for entry in entries:
        # El consumidor desempaqueta (patrón, severidad, descripción).
        if not (isinstance(entry, (list, tuple)) and len(entry) >= 3):
            raise ValueError(f"entrada malformada en «{key}»: {entry!r}")
        _compile_pattern(entry[0], key)
        canonical_severity(entry[1])


def _validate_paths(entries, key):
    if key != "sensitive_paths":
        return
    for entry in entries:
        _compile_pattern(entry, key)


def _compile_pattern(pattern, label):
    try:
        re.compile(pattern)
    except re.error as error:
        raise ValueError(f"regex inválida en «{label}»: {pattern!r} ({error})") from error


def _validate_combo(combo):
    if not isinstance(combo, dict):
        raise ValueError(f"combo malformado: {combo!r}")
    combo_id = combo.get("id", "?")
    groups = combo.get("grupos")
    if not isinstance(groups, list) or not groups:
        raise ValueError(f"combo «{combo_id}» sin campo «grupos» o vacío")
    for grupo in groups:
        _validate_combo_group(grupo, combo_id)


def _validate_combo_group(grupo, combo_id):
    if not isinstance(grupo, dict) or not grupo.get("patrones"):
        raise ValueError(f"combo «{combo_id}» con grupo sin «patrones»")
    for patron in grupo["patrones"]:
        try:
            re.compile(patron)
        except re.error as error:
            raise ValueError(
                f"regex inválida en combo «{combo_id}»: {patron!r} ({error})"
            ) from error


def _validate_mapping(value, key):
    if key == "network_imports":
        if not isinstance(value, list):
            raise ValueError("«network_imports» debe ser una lista")
        return
    if not isinstance(value, dict):
        raise ValueError(f"«{key}» debe ser un objeto")
    for severity in value.values():
        canonical_severity(severity)


def _canonicalize_severities(rules: Dict[str, Any]) -> None:
    """Deja toda severidad declarada en las reglas en la escala canónica."""
    for key in ("prompt_injection_patterns", "shell_danger_patterns",
                "comment_injection_patterns"):
        for entry in rules.get(key, []):
            entry[1] = canonical_severity(entry[1])
    for key in ("dangerous_imports", "dangerous_calls"):
        mapping = rules.get(key, {})
        for name, severity in list(mapping.items()):
            mapping[name] = canonical_severity(severity)


def load_rules(rules_path: Optional[str] = None) -> Dict[str, Any]:
    path = Path(rules_path).resolve() if rules_path else Path(__file__).resolve().parent / "rules.json"
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de reglas en: {path}")
    with path.open("r", encoding="utf-8") as f:
        rules = json.load(f)
    _validate_rules(rules)
    _canonicalize_severities(rules)
    return rules


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
                "severity": "critical",
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
                            "severity": "critical",
                            "file": rel_path,
                            "line": line_num,
                            "category": "Obfuscated Payload (Base64)",
                            "evidence": f"{blob[:40]}... -> '{decoded[:80]}'",
                            "description": "Cadena Base64 decodifica a una URL, comando o instrucción sospechosa.",
                        })
                    elif shannon_entropy(blob) > 4.7 and len(blob) > 60:
                        findings.append({
                            "severity": "medium",
                            "file": rel_path,
                            "line": line_num,
                            "category": "High-Entropy Encoded Blob",
                            "evidence": f"{blob[:50]}...",
                            "description": "Bloque Base64 largo embebido en el texto; requiere revisión manual.",
                        })
            except Exception:
                continue
    return findings


def inspect_hex_blobs(text: str, rel_path: str, rules: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detecta payloads hex, la otra mitad de la promesa "Base64/Hex".

    Un blob hex largo que además decodifica a texto imprimible con palabras
    clave sospechosas es un payload ofuscado; si solo es largo y con entropía
    alta, es material para revisión manual. Los hashes (sha256, md5) son de
    32/64 dígitos pero no decodifican a texto, así que no disparan la regla
    crítica.
    """
    findings = []
    hex_regex = re.compile(r"(?<![0-9a-fA-F])(?:[0-9a-fA-F]{2}){32,}(?![0-9a-fA-F])")
    suspicious_keywords = tuple(rules.get("base64_suspicious_keywords", []))

    for line_num, line in enumerate(text.splitlines(), start=1):
        for match in hex_regex.finditer(line):
            blob = match.group(0)
            if len(blob) % 2:
                continue
            try:
                raw = bytes.fromhex(blob)
                decoded = raw.decode("utf-8", errors="ignore")
            except ValueError:
                continue
            printable = decoded and sum(c.isprintable() for c in decoded) / len(decoded) > 0.8
            if printable and len(decoded) >= 8:
                lower_dec = decoded.lower()
                if any(kw in lower_dec for kw in suspicious_keywords):
                    findings.append({
                        "severity": "critical",
                        "file": rel_path,
                        "line": line_num,
                        "category": "Obfuscated Payload (Hex)",
                        "evidence": f"{blob[:40]}... -> '{decoded[:80]}'",
                        "description": "Cadena hex larga que decodifica a una URL, comando o instrucción sospechosa.",
                    })
                    continue
            if shannon_entropy(blob) > 3.9 and len(blob) >= 80:
                findings.append({
                    "severity": "medium",
                    "file": rel_path,
                    "line": line_num,
                    "category": "High-Entropy Hex Blob",
                    "evidence": f"{blob[:50]}...",
                    "description": "Cadena hex larga embebida en el texto; requiere revisión manual.",
                })
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
            "severity": "medium",
            "file": rel_path,
            "line": e.lineno or 1,
            "category": "Python Syntax Error",
            "evidence": str(e),
            "description": "El archivo Python no pudo parsearse con AST (posible ofuscación o código corrupto).",
        })
        return findings

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            findings.extend(_import_findings(node, rel_path, dangerous_imports, network_imports))
        elif isinstance(node, ast.ImportFrom) and node.module:
            findings.extend(_importfrom_findings(node, rel_path, dangerous_imports, network_imports))
        elif isinstance(node, ast.Call):
            findings.extend(_call_findings(node, rel_path, dangerous_calls, reflection_targets))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            findings.extend(_url_findings(node, rel_path))

    return findings


def _import_findings(node, rel_path, dangerous_imports, network_imports):
    findings = []
    for alias in node.names:
        mod = alias.name
        base_mod = mod.split(".")[0]
        if mod in dangerous_imports or base_mod in dangerous_imports:
            sev = dangerous_imports.get(mod, dangerous_imports.get(base_mod, "medium"))
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
                "severity": "medium",
                "file": rel_path,
                "line": node.lineno,
                "category": "AST Network Capability",
                "evidence": f"import {mod}",
                "description": f"El script importa librerías de red ({mod}). Verificar si la Skill realmente requiere salida a Internet.",
            })
    return findings


def _importfrom_findings(node, rel_path, dangerous_imports, network_imports):
    mod = node.module
    base_mod = mod.split(".")[0]
    if mod in dangerous_imports or base_mod in dangerous_imports:
        sev = dangerous_imports.get(mod, dangerous_imports.get(base_mod, "medium"))
        return [{
            "severity": sev,
            "file": rel_path,
            "line": node.lineno,
            "category": "AST Dangerous ImportFrom",
            "evidence": f"from {mod} import ...",
            "description": f"Importación desde módulo crítico ({mod}).",
        }]
    if mod in network_imports or base_mod in network_imports:
        return [{
            "severity": "medium",
            "file": rel_path,
            "line": node.lineno,
            "category": "AST Network Capability",
            "evidence": f"from {mod} import ...",
            "description": f"Capacidad de red detectada vía {mod}.",
        }]
    return []


def _call_name(node):
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return f"{node.func.value.id}.{node.func.attr}"
    return ""


def _call_findings(node, rel_path, dangerous_calls, reflection_targets):
    call_name = _call_name(node)
    findings = []
    if call_name in dangerous_calls:
        sev = dangerous_calls[call_name]
        extra = ""
        if call_name.startswith("subprocess."):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    sev = "critical"
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
                "severity": "critical",
                "file": rel_path,
                "line": node.lineno,
                "category": "AST Reflection Obfuscation",
                "evidence": f"getattr(..., '{node.args[1].value}')",
                "description": "Uso de getattr() para evadir detección estática de llamadas peligrosas.",
            })
    return findings


def _url_findings(node, rel_path):
    val = node.value
    if not re.match(r"^https?://", val.strip(), re.IGNORECASE):
        return []
    return [{
        "severity": "low",
        "file": rel_path,
        "line": node.lineno,
        "category": "AST Hardcoded URL",
        "evidence": val[:100],
        "description": "URL hardcodeada dentro del código Python; confirmar que sea un endpoint legítimo y documentado.",
    }]


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
        # `combo["grupos"]` y `combo["id"]` se piden aquí mismo: un rules.json
        # ajeno malformado provocaba KeyError con traceback en vez de exit 1.
        groups = combo.get("grupos")
        combo_id = combo.get("id", "?")
        if not isinstance(groups, list) or not groups:
            raise ValueError(f"combo «{combo_id}» sin campo «grupos» o vacío")
        for grupo in groups:
            if not isinstance(grupo, dict) or not grupo.get("patrones"):
                raise ValueError(f"combo «{combo_id}» con grupo sin «patrones»")
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
            "severity": "reject",
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
                    "severity": "high",
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

    base_root, files_to_scan = _collect_target_files(target)
    all_findings: List[Dict[str, Any]] = []
    scanned_files = []
    binary_files = []
    has_skill_md = False
    fences_maskados = 0

    for fpath in sorted(files_to_scan):
        rel_path = str(fpath.relative_to(base_root))
        if fpath.name == "SKILL.md":
            has_skill_md = True

        file_findings, kind, fences = _scan_one_file(fpath, rel_path, rules)
        all_findings.extend(file_findings)
        fences_maskados += fences
        if kind == "binary":
            binary_files.append(rel_path)
        elif kind == "scanned":
            scanned_files.append(rel_path)

    if target.is_dir() and not has_skill_md:
        all_findings.append({
            "severity": "low",
            "file": ".",
            "line": 0,
            "category": "Structure Anomaly",
            "evidence": "Missing SKILL.md",
            "description": "La carpeta no contiene un archivo SKILL.md en su raíz.",
        })

    reject_findings = [f for f in all_findings if f["severity"] == "reject"]
    raw_score = sum(SEVERITY_WEIGHTS.get(f["severity"], 0) for f in all_findings)
    risk_score = min(100, raw_score)

    return {
        "target": str(target),
        "verdict": _verdict(all_findings, risk_score, reject_findings),
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


def _collect_target_files(target):
    files_to_scan = []
    if target.is_file():
        files_to_scan.append(target)
        return target.parent, files_to_scan
    for root, dirs, files in os.walk(target):
        # Podar directorios de dependencias/artefactos: sin esto, un
        # __pycache__/mod.pyc normal se clasifica como "binario opaco
        # CRÍTICA" y bloquea una skill limpia (falso BLOQUEADO).
        dirs[:] = [d for d in dirs if d not in PRUNE_DIRS]
        for fname in files:
            if fname.endswith((".pyc", ".pyo")):
                continue
            files_to_scan.append(Path(root) / fname)
    return target, files_to_scan


def _scan_one_file(fpath, rel_path, rules):
    """Devuelve (hallazgos, tipo, fences enmascarados)."""
    ext = fpath.suffix.lower()
    if ext in (".exe", ".dll", ".so", ".dylib", ".bin", ".pyc", ".pyo", ".jar", ".wasm"):
        return ([{
            "severity": "critical",
            "file": rel_path,
            "line": 0,
            "category": "Opaque Binary Artifact",
            "evidence": fpath.name,
            "description": "Binario compilado dentro de una Agent Skill; no es auditable en texto plano.",
        }], "binary", 0)

    try:
        content = fpath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ([{
            "severity": "high",
            "file": rel_path,
            "line": 0,
            "category": "Non-UTF8 / Binary File",
            "evidence": fpath.name,
            "description": "Archivo no legible como UTF-8; inspeccionar manualmente antes de confiar.",
        }], "binary", 0)

    findings, fences = _content_findings(content, rel_path, ext, rules)
    return findings, "scanned", fences


def _content_findings(content, rel_path, ext, rules):
    if ext in MARKDOWN_EXTS:
        prose, live, exec_only = build_markdown_views(content)
        fences = 1 if live != content else 0
    else:
        prose = live = exec_only = content
        fences = 0

    findings = []
    findings.extend(detect_unicode_anomalies(content, rel_path))
    # Una sola pasada: la llamada duplicada inflaba el score (cada
    # hallazgo contaba el doble y podía cruzar el umbral solo).
    # `live` = prosa + fences ejecutables, o sea el fichero entero: con
    # `exec_only` una señal puesta fuera de un fence nunca combinaba con
    # otra dentro, contra lo que promete SKILL.md:108 ("por fichero").
    findings.extend(inspect_base64_blobs(prose, rel_path, rules))
    findings.extend(inspect_hex_blobs(prose, rel_path, rules))
    findings.extend(scan_text_patterns(prose, rel_path, ext, rules, live_text=live, exec_text=exec_only))
    findings.extend(detect_reject_combos(live, rel_path, rules))
    if ext == ".py":
        findings.extend(analyze_python_ast(content, rel_path, rules))
    return findings, fences


def _verdict(all_findings, risk_score, reject_findings):
    if reject_findings or risk_score >= 50 or any(f["severity"] == "critical" for f in all_findings):
        return "BLOQUEADO - MALICIOSO / CRÍTICO"
    if risk_score >= 16:
        return "PRECAUCIÓN - REVISIÓN MANUAL"
    return "APROBADO"


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
        epilog="Salida JSON cruda del motor (verdict/risk_score en español); el "
               "informe conforme a templates/report-schema.json se construye en "
               "la Fase 5. "
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
            if f["severity"] == "reject":
                print(f"    Acción:    {f.get('recommendation', 'Rechazar la instalación.')}")

    if result["verdict"].startswith("BLOQUEADO"):
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
