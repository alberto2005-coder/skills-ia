# -*- coding: utf-8 -*-
"""Modo Execute con dry-run.

Toda escritura propuesta se genera en `seo-auditor/output/` marcada **DRAFT**.
Nada se aplica al sitio sin `--apply` + confirmación explícita.

Se generan borradores de:
  - robots.txt (reglas actuales + allow-list de IA + Sitemap),
  - meta tags (snippet HTML, no una página completa),
  - JSON-LD (skeleton con solo datos observados),
  - llms.txt y llms-full.txt.

`apply_plan` solo copia los archivos completos (robots.txt, llms.txt,
llms-full.txt); los snippets (meta tags, JSON-LD) se integran a mano.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

try:
    from . import analyze, geo
except (ImportError, ValueError):
    import analyze
    import geo

DRAFT_HEADER = (
    "DRAFT — generado por seo-auditor. NO aplicado.\n"
    "Revisa cada línea antes de publicar: los valores marcados TODO requieren "
    "decisión humana.\n\n"
)

APPLICABLE = ("robots.txt", "llms.txt", "llms-full.txt")


class SnapshotPage(object):
    """Vista mínima de la página guardada en `audit.json`."""

    def __init__(self, data):
        self.title = data.get("title", "")
        self.description = data.get("description", "")
        self.og = data.get("og") or {}
        self.twitter = data.get("twitter") or {}
        self.jsonld = data.get("jsonld") or []
        self.text = data.get("text_head", "")
        self.paragraphs = data.get("paragraphs") or []
        self.html_lang = data.get("html_lang", "")
        self.canonicals = [data.get("canonical")] if data.get("canonical") else []
        self.robots_meta = data.get("robots_meta", "")
        self.word_count = data.get("word_count", 0)

    def resources(self):
        return []


def _snapshot(payload):
    data = (payload.get("data") or {}).get("page") or {}
    return SnapshotPage(data)


def _failed(payload):
    return [rec for rec in payload.get("checks") or [] if rec.get("status") == "fail"]


def build_plan(payload, output_dir):
    """Genera todos los borradores. Devuelve dict con rutas y acciones."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    page = _snapshot(payload)
    url = page.canonicals[0] if page.canonicals else (
        (payload.get("data") or {}).get("page", {}).get("url") or "")
    sitemaps = (payload.get("data") or {}).get("index", {}).get("sitemaps") or []
    sitemap_urls = [x for x in (_page_url(rec) for rec in payload.get("pages") or []) if x]

    generated = [_write_robots(out, sitemaps)]
    generated.append(_write_meta(out, page))
    generated.append(_write_jsonld(out, payload, page))
    generated += _write_llms(out, page, url, sitemap_urls)

    # PLAN.md con acciones priorizadas (se genera con lo ya escrito).
    plan_path = out / "PLAN.md"
    plan_path.write_text(render_plan(payload, generated), encoding="utf-8")
    generated.append(str(plan_path))

    return {
        "output_dir": str(out),
        "files": generated,
        "applicable": [name for name in APPLICABLE],
        "note": "Dry-run: nada se ha escrito fuera de %s." % out,
    }


def _page_url(rec):
    candidate = rec if isinstance(rec, str) else (rec or {}).get("url")
    if candidate and str(candidate).lower().startswith(("http://", "https://")):
        return candidate
    return None


def _write_robots(out, sitemaps):
    robots_lines = ["# DRAFT — propuesta de robots.txt (revisar antes de aplicar)", ""]
    if sitemaps:
        for item in sitemaps[:10]:
            robots_lines.append("Sitemap: %s" % item)
        robots_lines.append("")
    else:
        robots_lines.append("# TODO: añade la línea Sitemap: si publicas un sitemap.")
        robots_lines.append("")
    robots_lines.append(geo.recommended_robots_block(
        allow_search=True, allow_user_fetch=True, allow_training=False))
    robots_path = out / "robots.txt.draft"
    robots_path.write_text("\n".join(robots_lines), encoding="utf-8")
    return str(robots_path)


def _write_meta(out, page):
    title = page.title or "TODO: título único (45–60 caracteres)"
    description = page.description or "TODO: meta description (120–160 caracteres)"
    canonical = page.canonicals[0] if page.canonicals else "TODO: URL canónica absoluta"
    og_image = page.og.get("og:image") or "TODO: URL absoluta de imagen 1200×630"
    meta = [
        "<!-- DRAFT — snippet de metadatos; intégralo en el <head> de la plantilla -->",
        "<title>%s</title>" % _esc(title),
        "<meta name=\"description\" content=\"%s\">" % _esc(description),
        "<link rel=\"canonical\" href=\"%s\">" % _esc(canonical),
        "<meta property=\"og:title\" content=\"%s\">" % _esc(page.og.get("og:title") or title),
        "<meta property=\"og:description\" content=\"%s\">" % _esc(
            page.og.get("og:description") or description),
        "<meta property=\"og:image\" content=\"%s\">" % _esc(og_image),
        "<meta property=\"og:type\" content=\"%s\">" % _esc(
            page.og.get("og:type") or "website"),
        "<meta name=\"twitter:card\" content=\"%s\">" % _esc(
            page.twitter.get("twitter:card") or "summary_large_image"),
        "",
    ]
    meta_path = out / "meta-tags.html.draft"
    meta_path.write_text("\n".join(meta), encoding="utf-8")
    return str(meta_path)


def _write_jsonld(out, payload, page):
    types = (payload.get("data") or {}).get("schema", {}).get("types") or []
    jsonld = _jsonld_skeleton(page, types)
    jsonld_path = out / "jsonld.json.draft"
    jsonld_path.write_text(json.dumps(jsonld, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    return str(jsonld_path)


def _write_llms(out, page, url, sitemap_urls):
    paths = []
    for name, builder in (("llms.txt", geo.llms_txt), ("llms-full.txt", geo.llms_full_txt)):
        body = builder(page, url, sitemap_urls) if (page.title or url) else ""
        path = out / (name + ".draft")
        path.write_text("# DRAFT — " + name + "\n\n" + body, encoding="utf-8")
        paths.append(str(path))
    return paths


def _esc(value):
    return str(value or "").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _jsonld_skeleton(page, types):
    """JSON-LD mínimo con datos observados; nunca inventa precios ni valoraciones."""
    name = page.og.get("og:site_name") or page.title or "TODO: nombre de la organización"
    url = page.canonicals[0] if page.canonicals else "TODO: URL del sitio"
    graph = [{
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": name,
        "url": url,
        "sameAs": ["TODO: perfil oficial verificable"],
    }, {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": name,
        "url": url,
    }]
    if "Product" in types:
        graph.append({
            "@context": "https://schema.org",
            "@type": "Product",
            "name": page.title or "TODO: nombre del producto",
            "image": page.og.get("og:image") or "TODO: imagen absoluta",
            "offers": {
                "@type": "Offer",
                "price": "TODO",
                "priceCurrency": "TODO",
                "availability": "https://schema.org/InStock",
            },
        })
    if "FAQPage" in types:
        graph.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [{
                "@type": "Question",
                "name": "TODO: pregunta visible en la página",
                "acceptedAnswer": {"@type": "Answer",
                                   "text": "TODO: respuesta visible en la página"},
            }],
        })
    return {"@context": "https://schema.org", "@graph": graph,
            "_nota": "DRAFT: sustituye los TODO con datos visibles en la página."}


def render_plan(payload, files):
    lines = ["# Plan de ejecución (DRAFT)", "",
             "Veredicto actual: **%s**" % payload.get("verdict_line", ""),
             "Puntuación: **%s/100**" % payload.get("score"), "",
             "## Borradores generados", ""]
    for path in files:
        lines.append("- `%s`" % Path(path).name)
    lines += ["", "## Acciones priorizadas", "",
              "| Orden | Check | Severidad | Acción | Doc oficial |",
              "|---:|---|---|---|---|"]
    order = 0
    level_rank = {"must": 0, "should": 1, "nice": 2}
    for rec in sorted(_failed(payload), key=lambda r: (
            level_rank.get(r.get("severity_level"), 3), r.get("id", ""))):
        order += 1
        lines.append("| %d | `%s` | %s | %s | %s |" % (
            order, rec.get("id"), rec.get("severity_level"),
            analyze.recommendation_for(rec.get("id")).replace("|", "/"),
            rec.get("citation", "")))
    lines += ["", "## Cómo aplicar", "",
              "1. Revisa cada `.draft` (y sustituye los `TODO`).",
              "2. Solo `robots.txt`, `llms.txt` y `llms-full.txt` son aplicables "
              "automáticamente; los snippets de meta tags y JSON-LD se integran en la plantilla.",
              "3. Ejecuta `fix --apply --dest <carpeta>` y confirma la pregunta interactiva "
              "(o usa `--yes` en un entorno no interactivo).",
              "4. Se guarda una copia `.bak` de cualquier archivo que se sobrescriba.",
              ""]
    return "\n".join(lines)


def apply_plan(drafts_dir, dest, confirm=False):
    """Copia los borradores aplicables a `dest`. Exige confirmación explícita."""
    if not confirm:
        raise PermissionError(
            "Aplicación cancelada: se requiere confirmación explícita (--apply + sí).")
    source = Path(drafts_dir)
    target = Path(dest)
    if not source.is_dir():
        raise ValueError("No existe el directorio de borradores: %s" % source)
    target.mkdir(parents=True, exist_ok=True)
    applied = []
    skipped = []
    for draft in sorted(source.glob("*.draft")):
        name = draft.name[:-len(".draft")]
        if name not in APPLICABLE:
            skipped.append(name)
            continue
        destination = target / name
        if destination.exists():
            backup = target / (name + ".bak")
            shutil.copy2(destination, backup)
        shutil.copy2(draft, destination)
        applied.append(str(destination))
    return {"applied": applied, "skipped_snippets": skipped,
            "note": "Copia aplicada. Revisa el resultado y valida en Search Console."}
