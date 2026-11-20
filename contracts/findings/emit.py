"""Traduce la salida nativa de un auditor al contrato común `findings.json` v1.0.0.

Uso:
    py contracts/findings/emit.py <appsec|seo|db|api|finops> <informe nativo>
        [--output findings.json] [--root RUTA] [--skill NOMBRE] [--target RUTA]

Informes que entiende, por auditor:

- `appsec`: `<target>/.appsec-audit/findings.json`, formato propio 2.0. Solo pasan
  los `confirmed`: los `needs_validation` y los `rejected` siguen en el informe
  nativo, que no se toca.
- `seo`: `audit.json` del informe. Solo pasan las comprobaciones en `fail`.
- `db`: el `--json` de `db-architect` (`lock_audit`, `drift`, `schema_audit`,
  `migration_guard`, `sql_lint`, `query_trace`). Los hallazgos con `file` y `line`
  van a la ubicación `file`; los de `drift`, que señalan tabla o columna, a `schema`.
- `api`: el `--json` de `contract_diff` (`changes`), `auth_coverage` y `code_sync`
  (`findings`). Lo que tiene fichero va a `file`; una ruta o un endpoint, a `url`.
- `finops`: el `--json` de `llm_cost_scan`, `infra_cost_scan` y `ci_cost_scan`.

La confianza es `high` salvo que el informe nativo diga otra cosa: estos escáneres
son deterministas. La corrección sale del propio hallazgo (`fix`, `detail`) o de la
tabla de reglas; si la regla es nueva, se remite a la guía del paquete en vez de
inventar un consejo.

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
PACKAGES = {
    "api": "api-contract-guard",
    "appsec": "appsec-audit",
    "db": "db-architect",
    "finops": "finops-auditor",
    "seo": "seo-auditor",
}
CWE_RE = re.compile(r"^CWE-([0-9]+)$")
SEO_LEVELS = {"must": "high", "should": "medium", "nice": "low"}
# `migration_guard` llama `warning` a `medium` y usa `info` para lo informativo.
SEVERITY_ALIASES = {"warning": "medium"}
API_LEVELS = {"major": "high", "minor": "medium", "patch": "low", "none": "info"}
API_LEVEL_FIXES = {
    "major": "Mantén la compatibilidad: versiona el endpoint o publica un major del contrato.",
    "minor": "Documenta la adición y sube la versión minor del contrato.",
    "patch": "Cambio compatible: sube el patch del contrato.",
}

DB_FIXES = {
    "reescritura-de-tipo": "Divide en expand/contract: columna nueva, backfill por lotes y retirada posterior.",
    "columna-not-null-con-default": "Añade la columna nullable, rellena por lotes y pon NOT NULL después.",
    "set-not-null": "Rellena los nulos y valida con un conteo antes del SET NOT NULL.",
    "indice-sin-concurrently": "Crea el índice con CREATE INDEX CONCURRENTLY, fuera de la transacción.",
    "rename-inseguro": "Crea el nombre nuevo, escribe en ambos y retira el viejo tras el despliegue.",
    "fk-sin-not-valid": "Añade la FK con NOT VALID y valídala después con VALIDATE CONSTRAINT.",
    "check-sin-not-valid": "Añade el CHECK con NOT VALID y valídalo en una migración aparte.",
    "vacuum-full": "Programa VACUUM sin FULL o usa pg_repack: VACUUM FULL bloquea la tabla.",
    "delete-sin-where": "Acota el DELETE con WHERE, o usa TRUNCATE si de verdad se vacía la tabla.",
    "drop-table": "Renombra la tabla y retírala tras un periodo de gracia: un DROP es irreversible.",
    "drop-column": "Deja de escribir en la columna, despliega y elimínala en una migración posterior.",
    "truncate": "Borra por lotes con WHERE o archiva antes de truncar: TRUNCATE no se deshace.",
    "cambio-de-tipo": "Añade columna nueva con el tipo destino, migra por lotes y cambia lectores antes.",
    "sin-reversion": "Añade el bloque de reversión (downgrade o sección DOWN) a la migración.",
    "tabla-solo-en-esquema": "Añade la migración que crea la tabla, o retírala del esquema declarado.",
    "tabla-solo-en-migraciones": "Declara la tabla en el esquema, o retira la migración que la crea.",
    "columna-solo-en-esquema": "Añade la migración que crea la columna.",
    "columna-solo-en-migraciones": "Añade la columna al esquema declarado.",
    "tipo-distinto": "Unifica el tipo en esquema y migraciones; el replay dice cuál manda.",
    "sentencia-desconocida": "Revisa la sentencia a mano: el clasificador no sabe repartirla.",
    "consulta-en-bucle": "Saca la consulta del bucle y resuélvela con un IN o un join.",
    "tabla-sin-primary-key": "Declara PRIMARY KEY en la tabla.",
    "fk-sin-indice": "Crea el índice que propone el hallazgo sobre la columna de la clave foránea.",
    "sql-invalido": "Corrige el SQL: SQLite no puede ejecutar el esquema.",
}

API_FIXES = {
    "ruta-sin-guarda": "Añade la guarda de autenticación que exige el contrato o declara `security: []`.",
    "ruta-sin-spec": "Documenta la ruta en el contrato OpenAPI o retírala del código.",
    "spec-sin-security": "Declara `security` en el contrato o retira la guarda sobrante.",
    "spec-sin-codigo": "Implementa la operación declarada o elimínala del contrato.",
    "dead-call": "Elimina la llamada del cliente o restaura la ruta en el backend.",
    "metodo-distinto": "Unifica el método HTTP entre backend y cliente.",
    "sin-consumidor": "Retira la ruta si no tiene consumidor, o documenta por qué se conserva.",
}

FINOPS_FIXES = {
    "llm-sin-limite-tokens": "Añade `max_tokens` a la llamada al modelo.",
    "modelo-caro": "Baja a un modelo más barato o reserva el caro para lo que de verdad lo necesite.",
    "prompt-sin-cache": "Activa `cache_control` en el prompt de sistema para no pagarlo en cada llamada.",
    "bucle-sin-tope": "Pon un tope de iteraciones o un `break` con condición de salida.",
    "contenedor-sin-limites": "Declara `resources.limits` de CPU y memoria en el contenedor.",
    "s3-sin-ciclo-de-vida": "Añade `lifecycle_rule` al bucket para expirar o transicionar objetos.",
    "logs-sin-retencion": "Fija `retention_in_days` en el log group.",
    "rds-sin-autoscaling": "Activa `storage_autoscaling` con un máximo acotado.",
    "ci-doble-ejecucion": "Añade `concurrency` con `cancel-in-progress: true`.",
    "ci-sin-cache": "Activa la caché de dependencias (`setup-uv` o `actions/cache`).",
}


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
    """Referencia externa a partir de la cita: el host identifica la fuente."""
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return []
    host = urlparse(url).netloc.replace("www.", "") or "doc"
    return [{"id": host, "url": url}]


# --- AppSec -----------------------------------------------------------------

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


def from_appsec(payload: dict, skill: str, version: str, target: str | None = None) -> dict:
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
        findings=merge_duplicates(findings),
        target=target or payload.get("target"),
        generated_at=payload.get("created_at"),
        note=note,
    )


# --- SEO --------------------------------------------------------------------

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


def from_seo(payload: dict, skill: str, version: str, target: str | None = None) -> dict:
    findings = [
        seo_finding(item)
        for item in payload.get("findings") or []
        if isinstance(item, dict) and item.get("status", "fail") == "fail"
    ]
    return contract.build_payload(
        tool={"package": PACKAGES["seo"], "skill": skill, "version": version},
        findings=merge_duplicates(findings),
        target=target or payload.get("target"),
        generated_at=payload.get("generated_at"),
        score=payload.get("score"),
        note=payload.get("verdict_line"),
    )


# --- Compartido por db, api y finops ---------------------------------------

def finding_text(item: dict) -> str:
    """Texto del hallazgo nativo, sea `message`, `detail` o `issue`."""
    for key in ("message", "detail", "issue"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return " ".join(value.split())
    return ""


def title_for(text: str, rule: str) -> str:
    """Título corto: el propio mensaje, o la regla legible si no hay texto."""
    clean = text or rule.replace("-", " ")
    return clean if len(clean) <= 160 else clean[:157].rstrip() + "…"


def severity_for(item: dict) -> str:
    value = item.get("severity")
    if not isinstance(value, str):
        return "info"
    value = SEVERITY_ALIASES.get(value, value)
    return value if value in contract.SEVERITIES else "info"


def file_location(item: dict) -> dict | None:
    path = str(item.get("file") or "").strip()
    if not path:
        return None
    line = item.get("line")
    return contract.make_location("file", path, line if isinstance(line, int) and line > 0 else None)


def location_evidence(location: dict) -> str:
    """Dato observado cuando el informe no trae fragmento: el sitio que casó la regla."""
    line = location.get("line")
    return "%s:%s" % (location["target"], line) if line else str(location["target"])


def fallback_fix(rule: str, package: str) -> str:
    """Regla sin consejo propio: remite a la guía en vez de improvisar uno."""
    return "Aplica la corrección de «%s» que documenta docs/%s.md y repite la auditoría." % (rule, package)


def generic_finding(item: dict, fixes: dict, package: str, allow_schema: bool = False) -> dict | None:
    """Hallazgo de `{rule, severity, message}` con ubicación de fichero o de esquema."""
    rule = str(item.get("rule") or "sin-regla")
    text = finding_text(item)
    location = file_location(item)
    if location is None and allow_schema:
        target = str(item.get("target") or item.get("table") or "").strip()
        location = contract.make_location("schema", target) if target else None
    if location is None:
        return None
    return contract.make_finding(
        rule_id=rule,
        severity=severity_for(item),
        confidence=confidence_for(item.get("confidence")) if item.get("confidence") else "high",
        title=title_for(text, rule),
        message=text or title_for(text, rule),
        evidence=str(item.get("fix") or "").strip() or location_evidence(location),
        remediation=str(item.get("fix") or "").strip() or fixes.get(rule) or fallback_fix(rule, package),
        location=location,
    )


def findings_from(payload: dict, key: str) -> list:
    items = payload.get(key)
    return [item for item in items or [] if isinstance(item, dict)]


def site_of(finding: dict) -> str:
    location = finding.get("location") or {}
    line = location.get("line")
    return "%s:%s" % (location.get("target"), line) if line else str(location.get("target"))


def merge_duplicates(findings: list) -> list:
    """Une hallazgos con la misma huella y deja los sitios en la evidencia.

    La huella no lleva la línea a propósito: el mismo defecto sigue siéndolo
    cuando el código se mueve. El precio es que un fichero con dos llamadas
    idénticas en líneas distintas produce dos hallazgos iguales; fusionarlos
    conserva los dos sitios (en la evidencia) en vez de perder uno o repetir la
    huella que el validador rechaza.
    """
    merged: dict = {}
    order: list = []
    for finding in findings:
        key = finding["fingerprint"]
        if key not in merged:
            merged[key] = finding
            order.append(key)
            continue
        site = site_of(finding)
        evidence = str(merged[key].get("evidence") or "")
        if site not in evidence:
            merged[key]["evidence"] = "%s · también en %s" % (evidence, site) if evidence else site
    return [merged[key] for key in order]


# --- db-architect -----------------------------------------------------------

def from_db(payload: dict, skill: str, version: str, target: str | None = None) -> dict:
    findings = []
    for item in findings_from(payload, "findings"):
        finding = generic_finding(item, DB_FIXES, PACKAGES["db"], allow_schema=True)
        if finding is not None:
            findings.append(finding)
    return contract.build_payload(
        tool={"package": PACKAGES["db"], "skill": skill, "version": version},
        findings=merge_duplicates(findings),
        target=target,
    )


# --- api-contract-guard -----------------------------------------------------

def api_location(item: dict) -> dict | None:
    """Fichero si el hallazgo lo trae; si no, el endpoint como URL."""
    location = file_location(item)
    if location is not None:
        return location
    target = str(item.get("target") or "").strip()
    if not target and item.get("route"):
        target = "%s %s" % (str(item.get("method") or "GET").upper(), item["route"])
    if not target and item.get("path"):
        target = str(item["path"]).strip()
    return contract.make_location("url", target) if target else None


def api_change_finding(item: dict) -> dict | None:
    """Un cambio de `contract_diff`: `{level, path, detail}`."""
    path = str(item.get("path") or "").strip()
    detail = finding_text(item) or "cambio de contrato"
    level = str(item.get("level") or "none")
    if not path:
        return None
    return contract.make_finding(
        rule_id="contract-diff-%s" % level,
        severity=API_LEVELS.get(level, "info"),
        confidence="high",
        title=title_for(detail, "contract-diff"),
        message="%s: %s" % (detail, path),
        evidence="nivel %s · %s" % (level, path),
        remediation=API_LEVEL_FIXES.get(level) or "Sube la versión del contrato según el cambio.",
        location=contract.make_location("url", path),
    )


def api_finding(item: dict) -> dict | None:
    """Hallazgo de `auth_coverage` o `code_sync`: `{rule, severity, target|route}`."""
    rule = str(item.get("rule") or "sin-regla")
    text = finding_text(item) or rule
    location = api_location(item)
    if location is None:
        return None
    return contract.make_finding(
        rule_id=rule,
        severity=severity_for(item),
        confidence="high",
        title=title_for(text, rule),
        message=text,
        evidence=location_evidence(location),
        remediation=API_FIXES.get(rule) or fallback_fix(rule, PACKAGES["api"]),
        location=location,
    )


def from_api(payload: dict, skill: str, version: str, target: str | None = None) -> dict:
    changes = findings_from(payload, "changes")
    findings = [api_change_finding(item) for item in changes] if changes else []
    for item in findings_from(payload, "findings"):
        findings.append(api_finding(item))
    return contract.build_payload(
        tool={"package": PACKAGES["api"], "skill": skill, "version": version},
        findings=merge_duplicates([finding for finding in findings if finding is not None]),
        target=target,
        note="veredicto %s" % payload["version"] if isinstance(payload.get("version"), str) else None,
    )


# --- finops-auditor ---------------------------------------------------------

def from_finops(payload: dict, skill: str, version: str, target: str | None = None) -> dict:
    findings = []
    for item in findings_from(payload, "findings"):
        finding = generic_finding(item, FINOPS_FIXES, PACKAGES["finops"])
        if finding is not None:
            findings.append(finding)
    return contract.build_payload(
        tool={"package": PACKAGES["finops"], "skill": skill, "version": version},
        findings=merge_duplicates(findings),
        target=target,
    )


ADAPTERS = {
    "api": from_api,
    "appsec": from_appsec,
    "db": from_db,
    "finops": from_finops,
    "seo": from_seo,
}


def main(argv: list | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Convierte la salida de un auditor al contrato findings.json v1.0.0.")
    parser.add_argument("source", choices=sorted(PACKAGES), help="Auditor de origen")
    parser.add_argument("input", help="Informe nativo del auditor")
    parser.add_argument("--output", help="Fichero findings.json de salida; sin él se imprime en stdout")
    parser.add_argument("--root", default=str(ROOT), help="Raíz del repositorio para leer la versión del paquete")
    parser.add_argument("--skill", help="Skill concreta; por defecto, la maestra del paquete")
    parser.add_argument("--target", help="Objetivo auditado; si falta se toma del informe nativo")
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
    if not isinstance(payload, dict) or not any(
        isinstance(payload.get(key), list) for key in ("findings", "changes")
    ):
        print("Informe nativo inesperado: falta la lista «findings» o «changes»", file=sys.stderr)
        return 1

    try:
        version = package_version(Path(args.root), PACKAGES[args.source])
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"No se pudo leer la versión del paquete: {error}", file=sys.stderr)
        return 1

    emitted = ADAPTERS[args.source](payload, args.skill or PACKAGES[args.source], version, args.target)

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
