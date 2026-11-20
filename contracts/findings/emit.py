"""Traduce la salida nativa de un auditor al contrato común `findings.json` v1.0.0.

Uso:
    py contracts/findings/emit.py <appsec|seo> <informe nativo> [--output findings.json]
        [--root RUTA] [--skill NOMBRE]

- `appsec`: `<target>/.appsec-audit/findings.json`, formato propio 2.0. Solo pasan
  los `confirmed`: los `needs_validation` y los `rejected` siguen viviendo en el
  informe nativo, que no se toca.
- `seo`: `audit.json` del informe. Solo pasan las comprobaciones en `fail`; las que
  pasan o no aplican no son hallazgos.

El contrato no se inventa nada: el mensaje se arma con la evidencia observada, la
ubicación no lleva línea si el auditor no la tiene y el resumen se recalcula. El
resultado se valida antes de escribirlo.

Código de salida: 0 escrito · 1 informe nativo inesperado o resultado inválido · 2 ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import findings_contract as contract
import validate_findings

ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGES = {"appsec": "appsec-audit", "seo": "seo-auditor"}
DEFAULT_SKILLS = {"appsec": "appsec-audit", "seo": "seo-auditor"}
CWE_RE = re.compile(r"^CWE-([0-9]+)$")
SEO_LEVELS = {"must": "high", "should": "medium", "nice": "low"}


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra página de códigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def package_version(root: Path, package: str) -> str:
    """Versión declarada en el manifiesto del paquete; el contrato exige semver."""
    manifest = json.loads((root / package / "skills.json").read_text(encoding="utf-8"))
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("el manifiesto de %s no declara «version»" % package)
    return version


def confidence_for(value: object) -> str:
    """La escala del contrato tiene tres niveles; appsec puntúa de 1 a 10."""
    if isinstance(value, str) and value in contract.CONFIDENCES:
        return value
    if isinstance(value, bool) or not isinstance(value, int):
        return "low"
    if value >= 8:
        return "high"
    return "medium" if value >= 5 else "low"


def cwe_reference(cwe: object) -> list:
    match = CWE_RE.match(str(cwe or ""))
    if not match:
        return []
    return [{"id": str(cwe), "url": "https://cwe.mitre.org/data/definitions/%s.html" % match.group(1)}]


def citation_reference(url: object) -> list:
    """Referencia externa a partir de la cita: el hostidentifica la fuente."""
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return []
    host = urlparse(url).netloc.replace("www.", "") or "doc"
    return [{"id": host, "url": url}]


def appsec_finding(item: dict) -> dict | None:
    """Un `confirmed` de appsec en el contrato común."""
    location = item.get("location") or {}
    target = str(location.get("file") or "").strip()
    if not target:
        return None
    line = location.get("line")
    references = cwe_reference(item.get("cwe"))
    if isinstance(item.get("owasp"), str) and item["owasp"].strip():
        references.append({"id": "OWASP %s" % item["owasp"].strip()})
    title = str(item.get("title") or "").strip() or str(item.get("cwe") or "hallazgo")
    evidence = str(item.get("evidence") or "").strip() or "Sin evidencia adjunta."
    message = str(item.get("root_cause") or "").strip() or title
    return contract.make_finding(
        rule_id=str(item.get("cwe") or "appsec-unspecified"),
        severity=item.get("severity") if item.get("severity") in contract.SEVERITIES else "info",
        confidence=confidence_for(item.get("confidence")),
        title=title,
        message=message,
        evidence=evidence,
        remediation=str(item.get("patch") or "").strip() or "Corregir la causa raíz y repetir la verificación.",
        location=contract.make_location("file", target, line if isinstance(line, int) else None),
        references=references,
    )


def from_appsec(payload: dict, skill: str, version: str) -> dict:
    findings = []
    for item in payload.get("findings") or []:
        if isinstance(item, dict) and item.get("verdict") == "confirmed":
            finding = appsec_finding(item)
            if finding is not None:
                findings.append(finding)
    note = None
    if isinstance(payload.get("profile"), str):
        note = "perfil %s" % payload["profile"]
    return contract.build_payload(
        tool={"package": PACKAGES["appsec"], "skill": skill, "version": version},
        findings=findings,
        target=payload.get("target"),
        generated_at=payload.get("created_at"),
        note=note,
    )


def seo_location(item: dict) -> dict:
    """URL si la hay; si no, la ruta del HTML, que nunca lleva línea inventada."""
    target = str(item.get("url") or "").strip()
    if target.startswith(("http://", "https://")):
        return contract.make_location("url", target)
    return contract.make_location("file", target or "sin-ubicacion")


def seo_finding(item: dict) -> dict:
    title = str(item.get("title") or item.get("id") or "hallazgo").strip()
    evidence = str(item.get("evidence") or "").strip() or "Sin evidencia adjunta."
    severity = SEO_LEVELS.get(str(item.get("severity_level")), None)
    if severity is None:
        severity = item.get("severity") if item.get("severity") in contract.SEVERITIES else "info"
    return contract.make_finding(
        rule_id=str(item.get("id") or "seo-unspecified"),
        severity=severity,
        confidence=confidence_for(item.get("confidence")),
        title=title,
        message="%s — %s" % (title, evidence) if evidence != title else title,
        evidence=evidence,
        remediation=str(item.get("recommendation") or "").strip()
        or "Corregir según la documentación oficial citada.",
        location=seo_location(item),
        references=citation_reference(item.get("citation")),
    )


def from_seo(payload: dict, skill: str, version: str) -> dict:
    findings = [
        seo_finding(item)
        for item in payload.get("findings") or []
        if isinstance(item, dict) and item.get("status", "fail") == "fail"
    ]
    return contract.build_payload(
        tool={"package": PACKAGES["seo"], "skill": skill, "version": version},
        findings=findings,
        target=payload.get("target"),
        generated_at=payload.get("generated_at"),
        score=payload.get("score"),
        note=payload.get("verdict_line"),
    )


def main(argv: list | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Convierte la salida de un auditor al contrato findings.json v1.0.0.")
    parser.add_argument("source", choices=sorted(PACKAGES), help="Auditor de origen")
    parser.add_argument("input", help="Informe nativo del auditor")
    parser.add_argument("--output", help="Fichero findings.json de salida; sin él se imprime en stdout")
    parser.add_argument("--root", default=str(ROOT), help="Raíz del repositorio para leer la versión del paquete")
    parser.add_argument("--skill", help="Skill concreta; por defecto, la maestra del paquete")
    args = parser.parse_args(argv)

    path = Path(args.input)
    if not path.is_file():
        print(f"No existe: {path}", file=sys.stderr)
        return 2
    try:
        payload = contract.load_json(path)
    except (json.JSONDecodeError, OSError) as error:
        print(f"No se pudo leer la entrada: {error}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict) or not isinstance(payload.get("findings"), list):
        print("Informe nativo inesperado: falta la lista «findings»", file=sys.stderr)
        return 1

    root = Path(args.root)
    try:
        version = package_version(root, PACKAGES[args.source])
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"No se pudo leer la versión del paquete: {error}", file=sys.stderr)
        return 1

    adapter = from_appsec if args.source == "appsec" else from_seo
    emitted = adapter(payload, args.skill or DEFAULT_SKILLS[args.source], version)

    errors = validate_findings.validate_payload(emitted)
    if errors:
        print(f"El resultado no cumple el contrato ({len(errors)} problema(s)):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    text = contract.dump(emitted)
    if not args.output:
        print(text, end="")
        return 0
    try:
        Path(args.output).write_text(text, encoding="utf-8")
    except OSError as error:
        print(f"No se pudo escribir {args.output}: {error}", file=sys.stderr)
        return 2
    counts = contract.summarize(emitted["findings"])
    print(
        "findings.json escrito en {out} ({total} hallazgo(s): {critical} critical · {high} high"
        " · {medium} medium · {low} low · {info} info)".format(out=args.output, **counts["by_severity"],
                                                              total=counts["total"])
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
