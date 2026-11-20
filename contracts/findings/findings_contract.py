"""Contrato común de hallazgos: `findings.json` v1.0.0.

Una sola definición para todos los auditores del catálogo. La huella deduplica
entre ejecuciones, la severidad y la confianza son escalas cerradas, y la
ubicación es híbrida: `file` puede llevar líneas y `url`/`resource`/`schema` no,
para no inventar números donde no existen (SEO, FinOps, esquemas de base de datos).

Vive en `contracts/findings/` a propósito: cada paquete se instala solo y no puede
depender de un módulo común, así que el contrato es herramienta del repositorio y
los auditores solo lo producen. Sin dependencias: solo la biblioteca estándar.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
SCHEMA_PATH = Path(__file__).resolve().parent / "findings.schema.json"

SEVERITIES = ("critical", "high", "medium", "low", "info")
SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
CONFIDENCES = ("high", "medium", "low")
LOCATION_TYPES = ("file", "url", "resource", "schema")
# Solo un fichero de código tiene líneas de verdad.
LINED_TYPES = ("file",)


def normalize(text: object) -> str:
    """Espacios colapsados y minúsculas: dos ejecuciones escriben igual la misma causa."""
    return " ".join(str(text).split()).lower()


def normalize_target(kind: object, target: object) -> str:
    """Ruta con barras normales: la misma causa en Windows y en Linux es el mismo hallazgo."""
    text = str(target)
    if kind != "file":
        return text
    text = text.replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def fingerprint(rule_id: str, location: dict, title: str) -> str:
    """Huella estable por regla + ubicación, sin la línea.

    Si el código se mueve 40 líneas el hallazgo sigue siendo el mismo; si cambia
    la causa (título) es otro hallazgo y aparece como nuevo. El validador
    recalcula la huella, así que un emisor que se desvíe del algoritmo se ve al
    instante.
    """
    raw = "%s|%s|%s|%s" % (
        rule_id,
        location.get("type"),
        normalize_target(location.get("type"), location.get("target")),
        normalize(title),
    )
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def make_location(kind: str, target: str, line: int | None = None, end_line: int | None = None) -> dict:
    """Ubicación canónica; descarta las líneas cuando el tipo no las admite."""
    if kind not in LINED_TYPES:
        line, end_line = None, None
    return {
        "type": kind,
        "target": normalize_target(kind, target),
        "line": line,
        "end_line": end_line,
    }


def make_finding(
    rule_id: str,
    severity: str,
    confidence: str,
    title: str,
    message: str,
    evidence: str,
    remediation: str,
    location: dict,
    references: list[dict] | None = None,
) -> dict:
    """Un hallazgo con la huella ya calculada."""
    finding = {
        "fingerprint": fingerprint(rule_id, location, title),
        "rule_id": rule_id,
        "severity": severity,
        "confidence": confidence,
        "title": title.strip(),
        "message": message,
        "evidence": evidence,
        "remediation": remediation,
        "location": location,
    }
    if references:
        finding["references"] = list(references)
    return finding


def summarize(findings: list[dict]) -> dict:
    """Recuento por severidad con las cinco claves siempre presentes."""
    by_severity = {severity: 0 for severity in SEVERITIES}
    for finding in findings:
        severity = finding.get("severity")
        if severity in by_severity:
            by_severity[severity] += 1
    return {"total": len(findings), "by_severity": by_severity}


def build_payload(
    tool: dict,
    findings: list[dict],
    target: str | None = None,
    generated_at: str | None = None,
    score: float | int | None = None,
    note: str | None = None,
) -> dict:
    """Informe completo; el resumen se calcula, nunca se declara a mano."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": dict(tool),
        "summary": dict(summarize(findings), score=score, note=note),
        "findings": list(findings),
    }
    if generated_at is not None:
        payload["generated_at"] = generated_at
    if target is not None:
        payload["target"] = target
    return payload


def load_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump(payload: dict) -> str:
    """JSON estable: dos espacios, UTF-8 literal y salto de línea final."""
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def severity_at_or_above(finding: dict, threshold: str) -> bool:
    """¿El hallazgo llega al umbral? `none` nunca dispara."""
    if threshold not in SEVERITY_RANK:
        return False
    return SEVERITY_RANK.get(finding.get("severity"), -1) >= SEVERITY_RANK[threshold]
