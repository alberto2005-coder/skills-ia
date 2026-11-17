# -*- coding: utf-8 -*-
"""Auditoría de código fuente local.

Reutiliza el pipeline de `analyze` (mismo HTML -> mismos checks que en web)
y añade detección de framework, robots.txt, sitemap y llms.txt del proyecto.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

try:
    from . import analyze, indexcheck
    from .page import parse_file
except (ImportError, ValueError):
    import analyze
    import indexcheck
    from page import parse_file

EXCLUDED_DIRS = {".git", "node_modules", "vendor", "dist", "build", "coverage",
                 ".next", ".nuxt", ".venv", "venv", "__pycache__", ".idea",
                 "output", "reports"}
SENSITIVE_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
                   "credentials.json", "secrets.json"}
HTML_EXTS = {".html", ".htm", ".php", ".twig", ".njk", ".liquid", ".jsx", ".tsx",
             ".vue", ".svelte"}


def analyze_html(path, rel):
    """Analiza un archivo HTML y devuelve hallazgos (compatibilidad)."""
    page = parse_file(str(path))
    checks, _data = analyze.document_checks(page, url=rel)
    return analyze.to_findings(checks)


def detect_framework(root):
    checks = {
        "Next.js": ["next.config.js", "next.config.mjs", "next.config.ts"],
        "Astro": ["astro.config.mjs", "astro.config.ts"],
        "Vite/React": ["vite.config.js", "vite.config.ts"],
        "Laravel": ["artisan"],
        "WordPress": ["wp-config.php"],
        "Shopify theme": ["config/settings_schema.json"],
    }
    found = []
    for name, markers in checks.items():
        if any((root / marker).exists() for marker in markers):
            found.append(name)
    if (root / "package.json").exists():
        try:
            pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
            deps = {}
            deps.update(pkg.get("dependencies", {}))
            deps.update(pkg.get("devDependencies", {}))
            if "next" in deps and "Next.js" not in found:
                found.append("Next.js")
            if "astro" in deps and "Astro" not in found:
                found.append("Astro")
            if "react" in deps and not any(x in found for x in ("Next.js", "Vite/React")):
                found.append("React")
        except Exception:
            pass
    return found or ["HTML/CSS/JS o framework no identificado"]


def _site_files(base):
    """Lee robots.txt / sitemap.xml / llms.txt del proyecto como raíz de sitio."""
    robots = None
    robots_path = base / "robots.txt"
    if robots_path.exists():
        robots = indexcheck.parse_robots(
            robots_path.read_text(encoding="utf-8", errors="replace"))
    sitemap_urls = []
    for name in ("sitemap.xml", "sitemap_index.xml", "sitemap-index.xml"):
        candidate = base / name
        if candidate.exists():
            sitemap_urls.append("/%s" % name)
    if robots:
        sitemap_urls.extend(robots.get("sitemaps", []))
    llms = (base / "llms.txt").exists()
    llms_full = (base / "llms-full.txt").exists()
    return robots, sitemap_urls, llms, llms_full


def audit_source(root, max_files=500):
    base = Path(root).resolve()
    if not base.is_dir():
        raise ValueError("No es un directorio: %s" % base)
    robots, sitemap_urls, llms, llms_full = _site_files(base)

    checks = []
    pages = []
    files_data = []
    first_page = None
    count = 0

    for current, dirs, names in os.walk(base):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]
        for name in sorted(names):
            if name.lower() in SENSITIVE_NAMES or name.startswith(".env"):
                continue
            path = Path(current) / name
            if path.suffix.lower() not in HTML_EXTS:
                continue
            count += 1
            if count > max_files:
                break
            rel = str(path.relative_to(base)).replace("\\", "/")
            pages.append(rel)
            page = parse_file(str(path))
            if first_page is None:
                first_page = (page, rel)
            site_path = "/" + rel
            file_checks, _data = analyze.document_checks(
                page, url=rel, page_url="", headers=None, robots=robots,
                sitemap_urls=sitemap_urls, page_map=None,
                llms_status=llms, http_llms_status=llms_full)
            checks.extend(file_checks)
            files_data.append({
                "archivo": rel,
                "title": page.title,
                "palabras": page.word_count,
                "ratio_texto_html": page.ratio(),
                "h1": len(page.headings.get("h1", [])),
                "sin_alt": len(page.images_without_alt()),
                "path": site_path,
            })
        if count > max_files:
            break

    if first_page is None:
        page, rel = None, ""
    else:
        page, rel = first_page

    data = {
        "files": files_data,
        "robots": {"present": robots is not None,
                   "groups": len((robots or {}).get("groups", [])),
                   "sitemaps": (robots or {}).get("sitemaps", [])},
        "sitemap_urls": sitemap_urls,
        "llms_txt": llms,
        "llms_full_txt": llms_full,
    }
    if page is not None:
        data["page"] = analyze.snapshot(page, rel)

    return {
        "mode": "source",
        "target": str(base),
        "root": str(base),
        "frameworks": detect_framework(base),
        "files_scanned": len(pages),
        "pages": pages,
        "checks": checks,
        "findings": analyze.to_findings(checks),
        "data": data,
    }
