"""Detecta coste desperdiciado en infraestructura declarada, sin red.

Uso:
    py finops-auditor/scripts/infra_cost_scan.py --path <ruta> [--json] [--fail-on high]

Revisa Terraform (`.tf`) y manifiestos Kubernetes (`.yaml`, `.yml`) con reglas
de texto: buckets sin ciclo de vida, grupos de logs sin retención y contenedores
sin límites de CPU o memoria.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado · 2 ruta
ilegible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from finops_util import iter_files

SEVERITIES = {"low": 1, "medium": 2, "high": 3}
SKIP_PARTS = {"tests", "fixtures", "__pycache__", ".venv", ".git", "node_modules"}

TERRAFORM_RULES = (
    (re.compile(r'resource\s+"aws_s3_bucket"'), "lifecycle_rule", "s3-sin-ciclo-de-vida", "high",
     "bucket S3 sin lifecycle_rule: el almacenamiento crece para siempre"),
    (re.compile(r'resource\s+"aws_cloudwatch_log_group"'), "retention_in_days", "logs-sin-retencion", "medium",
     "log group sin retention_in_days: los logs se guardan y se facturan sin fin"),
    (re.compile(r'resource\s+"aws_db_instance"'), "storage_autoscaling", "rds-sin-autoscaling", "medium",
     "RDS sin storage_autoscaling: o se queda corto o se sobreaprovisiona a mano"),
)
CONTAINERS = re.compile(r"^\s*containers:\s*$", re.M)
LIMITS = re.compile(r"^\s*limits:\s*$", re.M)


def scan_terraform(path: Path, text: str) -> list[dict]:
    findings = []
    lines = text.splitlines()
    for pattern, required, rule, severity, message in TERRAFORM_RULES:
        if not pattern.search(text) or required in text:
            continue
        line = next(
            (index for index, content in enumerate(lines, start=1) if pattern.search(content)),
            1,
        )
        findings.append({
            "file": path.as_posix(),
            "line": line,
            "rule": rule,
            "severity": severity,
            "message": message,
        })
    return findings


def scan_kubernetes(path: Path, text: str) -> list[dict]:
    if "kind:" not in text or not CONTAINERS.search(text):
        return []
    if LIMITS.search(text):
        return []
    line = next(
        (index for index, content in enumerate(text.splitlines(), start=1) if CONTAINERS.search(content)),
        1,
    )
    return [{
        "file": path.as_posix(),
        "line": line,
        "rule": "contenedor-sin-limites",
        "severity": "medium",
        "message": "contenedores sin resources.limits: el pod puede pedir de más y pagarse",
    }]


def scan_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".tf":
        return scan_terraform(path, text)
    return scan_kubernetes(path, text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Escáner de coste de infraestructura declarada.")
    parser.add_argument("--path", required=True, help="fichero o directorio a revisar")
    parser.add_argument("--json", action="store_true", help="salida JSON")
    parser.add_argument("--fail-on", default="high", choices=["low", "medium", "high", "none"])
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"ruta inexistente: {target}")
        return 2

    files = iter_files(target, {".tf", ".yaml", ".yml"}, frozenset(SKIP_PARTS))
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
    return 1 if any(SEVERITIES[item["severity"]] >= threshold for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
