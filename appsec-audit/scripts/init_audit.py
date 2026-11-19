"""Inicializa los artefactos de una auditoría en `<target>/.appsec-audit/`.

Uso:
    py appsec-audit/scripts/init_audit.py <target> [--id ID] [--profile standard]
        [--now ISO] [--force]

Crea `findings.json`, `coverage-ledger.json` y `architecture.md` vacíos pero
válidos, listos para que los validadores los acepten. No sobrescribe nada sin
`--force`. Código de salida: 0 creado · 1 ya existe · 2 target inválido.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from appsec_util import FORMAT_VERSION, force_utf8_output

OUTPUT_DIR = ".appsec-audit"
PROFILES = ("quick", "standard", "deep")

ARCHITECTURE = """# Arquitectura y superficie — {target}

## Límites de confianza
- TODO: qué entra de fuera, dónde se valida y qué confía en qué.

## Superficies de entrada
- TODO: rutas HTTP, colas, webhooks, cron, uploads y CLI.

## Almacenes de datos
- TODO: bases, buckets, cachés e índices, con su control de acceso.

## Componentes de terceros
- TODO: servicios externos, modelos, agentes y servidores MCP.

## Notas del revisor
- Una unidad del ledger por cada combinación de superficie × clase de ataque.
- Un hallazgo sin `ruta:línea` y sin evidencia no entra en `findings.json`.
"""


def stamp(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def audit_id_for(target: Path) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", target.name.lower()).strip("-")
    return f"audit-{slug or 'target'}"


def build_findings(audit_id: str, target: str, created_at: str, profile: str) -> dict:
    return {
        "audit_id": audit_id,
        "format_version": FORMAT_VERSION,
        "target": target,
        "created_at": created_at,
        "profile": profile,
        "findings": [],
    }


def build_ledger(audit_id: str, target: str, created_at: str) -> dict:
    return {
        "audit_id": audit_id,
        "target": target,
        "created_at": created_at,
        "updated_at": created_at,
        "units": [],
    }


def main(argv: list[str] | None = None) -> int:
    force_utf8_output()
    parser = argparse.ArgumentParser(description="Inicializa los artefactos de una auditoría.")
    parser.add_argument("target", help="Carpeta o repositorio que se va a auditar")
    parser.add_argument("--id", help="audit_id explícito (por defecto, derivado del target)")
    parser.add_argument("--profile", default="standard", choices=PROFILES)
    parser.add_argument("--now", help="Fecha ISO fija, para ejecuciones reproducibles")
    parser.add_argument("--force", action="store_true", help="Sobrescribe los artefactos existentes")
    args = parser.parse_args(argv)

    target = Path(args.target)
    if not target.is_dir():
        print(f"No es una carpeta: {target}", file=sys.stderr)
        return 2

    outdir = target / OUTPUT_DIR
    created_at = stamp(args.now)
    audit_id = args.id or audit_id_for(target)
    target_label = str(target.resolve())

    files = {
        "findings.json": build_findings(audit_id, target_label, created_at, args.profile),
        "coverage-ledger.json": build_ledger(audit_id, target_label, created_at),
    }

    # architecture.md también se sobrescribe, así que entra en la misma
    # comprobación: sin esto perderíamos notas de un revisor en silencio.
    existing = [name for name in (*files, "architecture.md") if (outdir / name).exists()]
    if existing and not args.force:
        print(
            f"Ya existen artefactos en {outdir} ({', '.join(sorted(existing))}). "
            "Usa --force para sobrescribirlos.",
            file=sys.stderr,
        )
        return 1

    outdir.mkdir(parents=True, exist_ok=True)
    for name, payload in files.items():
        (outdir / name).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    (outdir / "architecture.md").write_text(
        ARCHITECTURE.format(target=target_label), encoding="utf-8"
    )

    print(f"Auditoría {audit_id} inicializada en {outdir}")
    for name in ("findings.json", "coverage-ledger.json", "architecture.md"):
        print(f"  {name}")
    print("\nSiguiente paso:")
    print(
        "  py appsec-audit/scripts/ledger.py add "
        f"{outdir / 'coverage-ledger.json'} --surface \"<entrada>\" "
        "--subsystem <módulo> --class injection"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
