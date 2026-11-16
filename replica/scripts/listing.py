#!/usr/bin/env python3
"""listing.py - Valida el listing de App Store / Google Play antes de publicar.

listing.json:
{
  "platform": "ios" | "android" | "both",
  "avoid": ["OriginalApp", "originalapp.com"],
  "ios":     {"title": "...", "subtitle": "...", "promotional_text": "...",
              "keywords": "a,b,c", "description": "...", "screenshots": 5},
  "android": {"title": "...", "short_description": "...",
              "full_description": "...", "screenshots": 6}
}

Comprueba limites oficiales, claims de ranking, desperdicio de keywords,
nombre del original y capturas. Errores => codigo 1. Avisos => codigo 0.

Uso:
    python listing.py replica/launch/listing.json
    python listing.py listing.json --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LIMITS = {
    "ios": {
        "title": (30, "App Store name"),
        "subtitle": (30, "Subtitle"),
        "promotional_text": (170, "Promotional text"),
        "keywords": (100, "Keywords"),
        "description": (4000, "Description"),
    },
    "android": {
        "title": (30, "Play title"),
        "short_description": (80, "Short description"),
        "full_description": (4000, "Full description"),
    },
}

RANKING_CLAIMS = re.compile(
    r"(#\s*1\b|n[º°]\s*1\b|number\s*one|n[uú]mero\s*1|the\s+best\b|el\s+mejor\b|"
    r"world'?s\s+best|top\s*\d|leading\b|l[ií]der\b|fastest|el\s+m[aá]s\s+r[aá]pido)",
    re.IGNORECASE,
)
SCREENSHOT_RANGES = {"ios": (3, 10), "android": (2, 8)}


def find_avoid(texts: dict[str, str], terms: list[str]) -> list[tuple[str, str]]:
    hits = []
    for field, value in texts.items():
        for term in terms:
            parts = re.findall(r"[A-Za-z0-9]+", term)
            core = r"[^A-Za-z0-9]{0,3}".join(re.escape(p) for p in parts) if parts else re.escape(term)
            if re.search(r"(?<![A-Za-z0-9])" + core, value or "", re.IGNORECASE):
                hits.append((field, term))
    return hits


def check_platform(platform: str, data: dict, avoid: list[str]) -> dict:
    limits = LIMITS[platform]
    errors: list[str] = []
    warnings: list[str] = []

    for field, (limit, label) in limits.items():
        value = data.get(field) or ""
        if field == "description" and not value and data.get("full_description"):
            value = data["full_description"]
        if not value:
            if field in {"title", "description", "full_description", "short_description"}:
                errors.append(f"{label} vacio")
            continue
        if len(value) > limit:
            errors.append(f"{label}: {len(value)}/{limit} caracteres (te pasas {len(value) - limit})")
        elif field in {"title", "subtitle", "short_description"} and len(value) > limit * 0.95:
            warnings.append(f"{label}: {len(value)}/{limit} caracteres, muy al limite")

        if field in {"title", "subtitle", "short_description"} and RANKING_CLAIMS.search(value):
            warnings.append(f"{label}: claim de ranking ('{RANKING_CLAIMS.search(value).group(0)}'), suele provocar rechazo")

    keywords = (data.get("keywords") or "").strip()
    if platform == "ios" and keywords:
        if re.search(r",\s", keywords):
            errors.append("Keywords: hay espacios tras las comas, App Store los cuenta")
        items = [k.strip().lower() for k in keywords.split(",") if k.strip()]
        duplicates = sorted({k for k in items if items.count(k) > 1})
        if duplicates:
            errors.append(f"Keywords repetidas: {', '.join(duplicates)}")
        title_words = {w.lower() for w in re.findall(r"[A-Za-z0-9]+", data.get("title", ""))}
        overlap = sorted(set(items) & title_words)
        if overlap:
            warnings.append(f"Keywords ya presentes en el title (desperdician espacio): {', '.join(overlap)}")
        if len(set(items)) < 3:
            warnings.append("Keywords: menos de 3 terminos distintos")

    shots = data.get("screenshots")
    if isinstance(shots, int):
        low, high = SCREENSHOT_RANGES[platform]
        if not low <= shots <= high:
            warnings.append(f"Capturas: {shots} (recomendado {low}-{high} para {platform})")

    texts = {k: v for k, v in data.items() if isinstance(v, str)}
    for field, term in find_avoid(texts, avoid):
        errors.append(f"{field}: contiene '{term}', rastro de la app original")

    return {"platform": platform, "errors": errors, "warnings": warnings}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint de listing para App Store / Google Play.")
    parser.add_argument("listing", nargs="?", default="listing.json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        with open(args.listing, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[x] No se pudo leer {args.listing}: {exc}", file=sys.stderr)
        return 2

    platform = str(data.get("platform", "both")).lower()
    platforms = ["ios", "android"] if platform in {"both", "ambos"} else [platform]
    avoid = data.get("avoid", [])

    reports = []
    for name in platforms:
        block = data.get(name)
        if not isinstance(block, dict):
            print(f"[!] Falta el bloque '{name}' en el JSON", file=sys.stderr)
            continue
        reports.append(check_platform(name, block, avoid))

    if not reports:
        print("[x] Nada que validar.", file=sys.stderr)
        return 2

    total_errors = sum(len(r["errors"]) for r in reports)
    if args.json:
        print(json.dumps({"reports": reports, "errors": total_errors}, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            print(f"[*] {report['platform']}")
            for err in report["errors"]:
                print(f"    [x] {err}")
            for warn in report["warnings"]:
                print(f"    [!] {warn}")
            if not report["errors"] and not report["warnings"]:
                print("    [+] Limpio")
        print(f"\n{'[x]' if total_errors else '[+]'} {total_errors} error(es), "
              f"{sum(len(r['warnings']) for r in reports)} aviso(s)")

    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
