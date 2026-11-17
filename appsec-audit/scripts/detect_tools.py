"""Detecta herramientas de seguridad disponibles y audita el workflow que las usa.

Uso:
    py appsec-audit/scripts/detect_tools.py [--require semgrep,trivy] [--json]
    py appsec-audit/scripts/detect_tools.py --workflow .github/workflows/ci.yml
        [--fail-on-critical] [--json]

**No instala ni ejecuta nada**: los binarios se buscan en `PATH` con `which` y
las librerías se consultan por metadatos del entorno. El workflow se analiza
como texto, sin interpretarlo ni lanzar sus pasos.

Código de salida: 0 correcto · 1 falta una herramienta requerida, el workflow
tiene un crítico con `--fail-on-critical`, o no se pudo leer.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

CATALOG = (
    {"name": "semgrep", "kind": "binary", "sarif": True, "note": "SAST multi-lenguaje"},
    {"name": "trivy", "kind": "binary", "sarif": True, "note": "imágenes, IaC y dependencias"},
    {"name": "grype", "kind": "binary", "sarif": True, "note": "vulnerabilidades de imagen"},
    {"name": "syft", "kind": "binary", "sarif": False, "note": "SBOM CycloneDX/SPDX"},
    {"name": "gitleaks", "kind": "binary", "sarif": True, "note": "secretos en git"},
    {"name": "trufflehog", "kind": "binary", "sarif": False, "note": "secretos verificados"},
    {"name": "codeql", "kind": "binary", "sarif": True, "note": "análisis semántico"},
    {"name": "osv-scanner", "kind": "binary", "sarif": True, "note": "dependencias contra OSV"},
    {"name": "tfsec", "kind": "binary", "sarif": True, "note": "Terraform"},
    {"name": "hadolint", "kind": "binary", "sarif": True, "note": "Dockerfile"},
    {"name": "nuclei", "kind": "binary", "sarif": False, "note": "plantillas DAST"},
    {"name": "bandit", "kind": "python", "sarif": True, "note": "Python AST"},
    {"name": "pip-audit", "kind": "python", "sarif": False, "note": "dependencias Python"},
    {"name": "checkov", "kind": "python", "sarif": True, "note": "IaC"},
)

WRITE_SCOPES = ("write", "write-all")
PINNED_ACTION = re.compile(r"@[0-9a-f]{40}$")
UNTRUSTED_INTERPOLATION = re.compile(
    r"\$\{\{\s*github\.event\.(?:pull_request|issue|comment)\.(?:title|body|head\.ref|head\.label)"
)


def _force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra pagina de codigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def detect(tool: dict) -> dict:
    found: dict = {
        "name": tool["name"],
        "kind": tool["kind"],
        "sarif": tool["sarif"],
        "note": tool["note"],
        "available": False,
        "path": None,
        "version": None,
    }
    if tool["kind"] == "binary":
        path = shutil.which(tool["name"])
        found["available"] = path is not None
        found["path"] = path
        return found

    module = tool["name"].replace("-", "_")
    try:
        found["version"] = importlib.metadata.version(tool["name"])
        found["available"] = True
    except importlib.metadata.PackageNotFoundError:
        found["available"] = importlib.util.find_spec(module) is not None
    return found


def detect_all(names: list[str] | None = None) -> list[dict]:
    catalog = [tool for tool in CATALOG if not names or tool["name"] in names]
    found = [detect(tool) for tool in catalog]
    known = {tool["name"] for tool in CATALOG}
    for name in names or []:
        if name not in known:
            found.append({
                "name": name, "kind": "unknown", "sarif": False,
                "note": "fuera del catálogo", "available": False,
                "path": None, "version": None,
            })
    return found


def audit_workflow(text: str) -> list[dict]:
    """Hallazgos de un workflow, por heurística de texto y sin ejecutarlo."""
    findings: list[dict] = []
    lines = text.splitlines()
    permissions_write = []
    uses_pull_request_target = False

    for position, line in enumerate(lines, start=1):
        stripped = line.strip()
        if re.match(r"^(on|true):?\s*$", stripped) or stripped in ("on:", "true:"):
            continue
        if re.match(r"^pull_request_target\s*:", stripped):
            uses_pull_request_target = True
        scope = re.match(r"^([a-z-]+)\s*:\s*(write|write-all)\s*$", stripped)
        if scope:
            permissions_write.append((position, scope.group(1)))

    if uses_pull_request_target:
        findings.append({
            "severity": "critica",
            "rule": "CI-PRTARGET",
            "line": next(
                (i for i, line in enumerate(lines, start=1) if "pull_request_target" in line), 1
            ),
            "message": "pull_request_target ejecuta el workflow con los permisos y secretos del repositorio base",
        })

    for position, scope in permissions_write:
        if uses_pull_request_target:
            findings.append({
                "severity": "critica",
                "rule": "CI-WRITE-TOKEN",
                "line": position,
                "message": f"permiso «{scope}: write» junto a pull_request_target: el PR controla código con token de escritura",
            })
        else:
            findings.append({
                "severity": "media",
                "rule": "CI-WRITE-TOKEN",
                "line": position,
                "message": f"permiso «{scope}: write» en un workflow: mínimo privilegio salvo justificación",
            })

    for position, line in enumerate(lines, start=1):
        stripped = line.strip()
        if "ref:" in stripped and "pull_request.head" in stripped:
            findings.append({
                "severity": "critica" if uses_pull_request_target else "alta",
                "rule": "CI-UNTRUSTED-CHECKOUT",
                "line": position,
                "message": "checkout del head del PR: el código del contribuyente se ejecuta en el contexto del repositorio",
            })
        if stripped.startswith("uses:") and not PINNED_ACTION.search(stripped.split("#")[0].strip()):
            findings.append({
                "severity": "media",
                "rule": "CI-ACTION-UNPINNED",
                "line": position,
                "message": f"acción sin pin por SHA: {stripped[5:].strip()}",
            })
        if UNTRUSTED_INTERPOLATION.search(stripped):
            findings.append({
                "severity": "alta",
                "rule": "CI-SCRIPT-INJECTION",
                "line": position,
                "message": "interpolación de datos del PR en un paso: inyección de comandos en el runner",
            })
        if uses_pull_request_target and "secrets." in stripped:
            findings.append({
                "severity": "alta",
                "rule": "CI-SECRETS-PRTARGET",
                "line": position,
                "message": "un secreto del repositorio base queda expuesto a un workflow disparado por un PR",
            })

    return findings


def main(argv: list[str] | None = None) -> int:
    _force_utf8_output()
    parser = argparse.ArgumentParser(description="Detecta herramientas y audita un workflow de CI.")
    parser.add_argument("--require", help="Lista separada por comas de herramientas imprescindibles")
    parser.add_argument("--workflow", help="Workflow de GitHub Actions a auditar")
    parser.add_argument("--fail-on-critical", action="store_true",
                        help="Sale 1 si el workflow tiene un hallazgo crítico")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    required = [item.strip() for item in (args.require or "").split(",") if item.strip()]
    tools = detect_all(required or None)
    missing = [tool["name"] for tool in tools if not tool["available"]] if required else []

    workflow_findings: list[dict] = []
    if args.workflow:
        path = Path(args.workflow)
        if not path.is_file():
            print(f"No existe el workflow: {path}", file=sys.stderr)
            return 1
        workflow_findings = audit_workflow(path.read_text(encoding="utf-8", errors="replace"))

    critical = [item for item in workflow_findings if item["severity"] == "critica"]
    result = {
        "policy": "las herramientas se detectan por PATH y metadatos; no se instalan ni se ejecutan",
        "tools": tools,
        "summary": {
            "available": sum(1 for tool in tools if tool["available"]),
            "missing": len(tools) - sum(1 for tool in tools if tool["available"]),
        },
        "required_missing": missing,
        "workflow": {
            "path": args.workflow,
            "findings": workflow_findings,
            "critical": len(critical),
        },
    }

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for tool in tools:
            state = "sí" if tool["available"] else "no"
            version = f" {tool['version']}" if tool["version"] else ""
            print(f"  {'[x]' if tool['available'] else '[ ]'} {tool['name']:<12} {state}{version} · {tool['note']}")
        print(f"\n{result['summary']['available']} disponible(s) · {result['summary']['missing']} ausente(s)")
        if args.workflow:
            print(f"\nWorkflow {args.workflow}: {len(workflow_findings)} hallazgo(s)")
            for item in workflow_findings:
                print(f"  {item['severity']:<8} línea {item['line']:<4} {item['rule']}: {item['message']}")
        if missing:
            print(f"\nFALTAN: {', '.join(missing)}", file=sys.stderr)

    if missing:
        return 1
    if args.fail_on_critical and critical:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
