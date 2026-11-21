"""Riesgo de un diff por fichero, sin ejecutar nada.

Uso:
    py pr-reviewer/scripts/review_risk.py --diff PARCHE [--json] [--out RUTA]
        [--max-files N] [--max-lines N] [--fail-on low|medium|high|none]

Lee un parche unificado y puntúa cada fichero por dominio sensible, tamaño,
secretos añadidos, dependencias tocadas y checks desactivados. Es determinista:
el mismo parche produce el mismo informe.

Código de salida: 0 limpio o por debajo del umbral · 1 umbral superado · 2
parche ilegible.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pr_review_util as util  # noqa: E402

SENSITIVE = (
    ("auth", "autenticación o sesión"),
    ("login", "autenticación o sesión"),
    ("session", "autenticación o sesión"),
    ("permission", "permisos"),
    ("rbac", "permisos"),
    ("payment", "cobro"),
    ("billing", "cobro"),
    ("checkout", "cobro"),
    ("migration", "migración de datos"),
    ("migrations", "migración de datos"),
    ("terraform", "infraestructura"),
    ("k8s", "infraestructura"),
    ("helm", "infraestructura"),
    ("dockerfile", "infraestructura"),
    (".github/workflows", "CI"),
    ("deploy", "despliegue"),
)
DEPENDENCIES = (
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "go.mod",
    "go.sum",
    "cargo.toml",
    "cargo.lock",
    "pom.xml",
    "build.gradle",
)
SECRETS = (
    re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
)
SUPPRESSIONS = (
    re.compile(r"\b(?:pytest\.mark\.)?skip(?:if)?\b"),
    re.compile(r"\bxfail\b"),
    re.compile(r"#\s*noqa\b"),
    re.compile(r"#\s*type:\s*ignore\b"),
    re.compile(r"eslint-disable"),
    re.compile(r"@ts-ignore"),
)


def classify(path, max_lines, added_lines):
    """(severidad, regla, mensaje) de la señal más grave del fichero."""
    lowered = path.lower()
    for needle, domain in SENSITIVE:
        if needle in lowered:
            return "high", "ruta-sensible", "toca %s: %s" % (domain, path)
    for line, text in added_lines:
        for pattern in SECRETS:
            if pattern.search(text):
                return "high", "secreto-expuesto", "posible credencial añadida en la línea %d" % line
    if lowered.rsplit("/", 1)[-1] in DEPENDENCIES:
        return "high", "dependencia-tocada", "cambia un manifiesto o un lock de dependencias"
    if len(added_lines) > max_lines:
        return "medium", "diff-grande", "%d líneas añadidas; presupuesto %d" % (len(added_lines), max_lines)
    for line, text in added_lines:
        for pattern in SUPPRESSIONS:
            if pattern.search(text):
                return "medium", "check-desactivado", "supresión añadida en la línea %d" % line
    return None, None, None


def analyze(files, max_lines):
    findings = []
    for item in files:
        added = item["added"]
        severity, rule, message = classify(item["path"], max_lines, added)
        if rule == "diff-grande" and item["removed"] > 2 * len(added) + 50:
            rule, message = "borrado-masivo", "%d líneas quitadas frente a %d añadidas" % (
                item["removed"], len(added)
            )
        if not rule:
            continue
        findings.append(util.finding(item["path"], added[0][0] if added else 1, rule, severity, message, FIXES[rule]))
    return util.sort_findings(findings)


FIXES = {
    "ruta-sensible": "Revisión humana dedicada y un test que cubra el caso antes de mergear.",
    "secreto-expuesto": "Rotar la credencial y moverla a un gestor de secretos.",
    "dependencia-tocada": "Revisar versión, licencia, alcance y el lock correspondiente.",
    "diff-grande": "Partir el PR o justificar el tamaño con el motivo escrito.",
    "borrado-masivo": "Confirmar que el borrado es intencional y que no se pierde cobertura.",
    "check-desactivado": "Justificar la supresión o retirarla antes de mergear.",
}


def main(argv=None):
    util.force_utf8()
    parser = argparse.ArgumentParser(description="Riesgo de un diff por fichero.")
    parser.add_argument("--diff", required=True, help="parche unificado de entrada")
    parser.add_argument("--max-files", type=int, default=15, help="ficheros por encima de este número son diff grande")
    parser.add_argument("--max-lines", type=int, default=400, help="líneas añadidas por fichero antes de diff grande")
    parser.add_argument("--json", action="store_true", help="imprime el informe en JSON")
    parser.add_argument("--out", help="escribe el informe en esta ruta")
    parser.add_argument("--fail-on", choices=("low", "medium", "high", "none"), default="high")
    args = parser.parse_args(argv)

    text = util.read_diff(args.diff)
    if text is None:
        print("review_risk: no se pudo leer %s" % args.diff, file=sys.stderr)
        return 2

    files = util.parse_diff(text)
    if not files:
        print("review_risk: el parche no contiene ficheros", file=sys.stderr)
        return 2

    findings = analyze(files, args.max_lines)
    if len(files) > args.max_files:
        findings.insert(
            0,
            util.finding(
                files[0]["path"], 1, "diff-grande", "medium",
                "el PR toca %d ficheros; presupuesto %d" % (len(files), args.max_files),
                FIXES["diff-grande"],
            ),
        )
    findings = util.sort_findings(findings)
    payload = {
        "source": "pr-risk",
        "files": [{"path": item["path"], "added": len(item["added"]), "removed": item["removed"]} for item in files],
        "summary": util.summarize(findings),
        "findings": findings,
    }
    util.emit(payload, args.out)
    return 1 if util.exceeds(findings, args.fail_on) else 0


if __name__ == "__main__":
    sys.exit(main())
