# -*- coding: utf-8 -*-
"""Módulo 5 (IndexPulse): Schema.org / JSON-LD + rich preview.

Inventario de todos los `@type`, validación de propiedades requeridas y
generación de una vista previa HTML de lo que Google *podría* mostrar.
Nunca garantiza un rich result: la elegibilidad la decide el buscador.
"""
from __future__ import annotations

import html as html_mod
import json
from pathlib import Path

try:
    from .checks import check
except (ImportError, ValueError):
    from checks import check

GOOGLE_RICH = "https://developers.google.com/search/docs/appearance/structured-data"

# Propiedades mínimas por tipo (documentadas en references/04-schema.md).
REQUIRED = {
    "Article": ("headline", "image", "datePublished", "author"),
    "BlogPosting": ("headline", "image", "datePublished", "author"),
    "NewsArticle": ("headline", "image", "datePublished", "author"),
    "Product": ("name", "image", "offers"),
    "Offer": ("price", "priceCurrency"),
    "AggregateRating": ("ratingValue", "ratingCount"),
    "FAQPage": ("mainEntity",),
    "Question": ("name", "acceptedAnswer"),
    "Organization": ("name", "url"),
    "LocalBusiness": ("name", "address"),
    "WebSite": ("name", "url"),
    "BreadcrumbList": ("itemListElement",),
    "Person": ("name",),
    "VideoObject": ("name", "thumbnailUrl", "uploadDate"),
    "Event": ("name", "startDate", "location"),
}

TYPE_DOC = {
    "Article": GOOGLE_RICH + "/article",
    "BlogPosting": GOOGLE_RICH + "/article",
    "NewsArticle": GOOGLE_RICH + "/article",
    "Product": GOOGLE_RICH + "/product",
    "Offer": GOOGLE_RICH + "/product",
    "AggregateRating": GOOGLE_RICH + "/review-snippet",
    "FAQPage": GOOGLE_RICH + "/faqpage",
    "Organization": "https://schema.org/Organization",
    "LocalBusiness": "https://schema.org/LocalBusiness",
    "BreadcrumbList": GOOGLE_RICH + "/breadcrumb",
    "WebSite": "https://schema.org/WebSite",
    "Person": "https://schema.org/Person",
    "VideoObject": GOOGLE_RICH + "/video",
    "Event": GOOGLE_RICH + "/event",
}


# --- Lectura de JSON-LD -----------------------------------------------------

def blocks_from_page(page):
    """Convierte los bloques crudos del parser en registros inspeccionables."""
    out = []
    for index, raw in enumerate(page.jsonld, 1):
        try:
            data = json.loads(raw)
            out.append({"block": index, "valid_json": True, "data": data,
                        "types": extract_types(data), "raw": raw})
        except ValueError as exc:
            out.append({"block": index, "valid_json": False, "data": None,
                        "types": [], "error": str(exc), "raw": raw})
    return out


def extract_types(obj):
    """Todos los `@type` presentes, en orden y sin duplicados."""
    found = []
    for node in _walk(obj):
        if isinstance(node, dict):
            value = node.get("@type")
            if isinstance(value, str):
                found.append(value)
            elif isinstance(value, list):
                found.extend(str(v) for v in value)
    seen = set()
    unique = []
    for item in found:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            for sub in _walk(value):
                yield sub
    elif isinstance(node, list):
        for value in node:
            for sub in _walk(value):
                yield sub


def find_by_type(blocks, type_name):
    out = []
    for block in blocks:
        if not block.get("valid_json"):
            continue
        for node in _walk(block["data"]):
            if isinstance(node, dict):
                t = node.get("@type")
                types = t if isinstance(t, list) else [t]
                if type_name in types:
                    out.append(node)
    return out


def missing_required(node, type_name):
    required = REQUIRED.get(type_name, ())
    return [prop for prop in required if not node.get(prop)]


# --- Checks -----------------------------------------------------------------

def analyze(page, url=""):
    """Checks de schema + inventario de tipos."""
    checks = []
    blocks = blocks_from_page(page)
    invalid = [b for b in blocks if not b["valid_json"]]
    all_types = []
    for block in blocks:
        for t in block["types"]:
            if t not in all_types:
                all_types.append(t)

    data = {
        "blocks": [{k: v for k, v in b.items() if k != "raw"} for b in blocks],
        "types": all_types,
        "type_count": len(all_types),
        "invalid_blocks": [b["block"] for b in invalid],
    }

    if not blocks:
        checks.append(check("SCHEMA-JSONLD-001", "fail",
                            "No se detectó ningún bloque application/ld+json.", url))
    elif invalid:
        checks.append(check(
            "SCHEMA-JSONLD-001", "fail",
            "JSON-LD inválido en bloque(s) %s: %s" % (
                ", ".join(str(b["block"]) for b in invalid), invalid[0].get("error", "")),
            url))
    else:
        checks.append(check(
            "SCHEMA-JSONLD-001", "pass",
            "%d bloque(s) JSON-LD válidos; tipos: %s." % (
                len(blocks), ", ".join(all_types) or "ninguno"),
            url))

    # Tipos condicionales: si no existen, no aplican (skip, no penaliza).
    conditional = (
        ("SCHEMA-FAQ-001", "FAQPage", _faq_ok, "FAQPage con mainEntity (Question/acceptedAnswer)"),
        ("SCHEMA-PRODUCT-001", "Product", _product_ok, "Product con offers (price, priceCurrency, availability)"),
        ("SCHEMA-RATING-001", "AggregateRating", _rating_ok, "AggregateRating con ratingValue y ratingCount"),
    )
    for cid, type_name, validator, label in conditional:
        nodes = find_by_type(blocks, type_name)
        if not nodes:
            checks.append(check(cid, "skip", "La página no declara %s." % type_name, url))
            continue
        ok, detail = validator(nodes[0])
        checks.append(check(cid, "pass" if ok else "fail",
                            "%s: %s" % (type_name, detail), url))

    return checks, data


def _faq_ok(node):
    entities = node.get("mainEntity") or []
    if isinstance(entities, dict):
        entities = [entities]
    if not entities:
        return False, "mainEntity vacío o ausente."
    incomplete = 0
    for item in entities:
        if not isinstance(item, dict):
            incomplete += 1
            continue
        if not item.get("name") or not item.get("acceptedAnswer"):
            incomplete += 1
    if incomplete:
        return False, "%d de %d preguntas sin name/acceptedAnswer." % (incomplete, len(entities))
    return True, "%d preguntas completas." % len(entities)


def _product_ok(node):
    offers = node.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if not isinstance(offers, dict) or not offers:
        return False, "Sin `offers`."
    missing = [p for p in ("price", "priceCurrency") if not offers.get(p)]
    if missing:
        return False, "`offers` sin " + ", ".join(missing) + "."
    availability = offers.get("availability")
    detail = "price=%s %s%s" % (offers.get("price"), offers.get("priceCurrency"),
                                "; availability=%s" % availability.rsplit("/", 1)[-1]
                                if availability else "; availability ausente")
    return bool(availability), detail


def _rating_ok(node):
    value = node.get("ratingValue")
    count = node.get("ratingCount") or node.get("reviewCount")
    if value and count:
        return True, "ratingValue=%s, ratingCount=%s." % (value, count)
    missing = [k for k, v in (("ratingValue", value), ("ratingCount", count)) if not v]
    return False, "Sin " + ", ".join(missing) + "."


# --- Rich preview -----------------------------------------------------------

def rich_preview(blocks, url=""):
    """HTML autocontenido con lo que Google *podría* mostrar y qué falta."""
    parts = []
    parts.append("<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\">"
                 "<title>Rich preview — seo-auditor</title>")
    parts.append("<style>"
                 "body{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;"
                 "background:#f8f9fa;color:#202124;margin:0;padding:24px}"
                 ".card{background:#fff;border:1px solid #dadce0;border-radius:8px;"
                 "padding:16px;margin:16px auto;max-width:680px}"
                 ".label{font-size:12px;color:#5f6368;text-transform:uppercase;"
                 "letter-spacing:.04em}"
                 ".title{color:#1a0dab;font-size:20px;margin:4px 0}"
                 ".url{color:#006621;font-size:13px}"
                 ".stars{color:#e7711b;letter-spacing:2px}"
                 ".price{font-weight:700}"
                 ".ok{color:#137333}.missing{color:#b3261e}"
                 "ul{margin:8px 0 0 18px;padding:0}li{margin:2px 0}"
                 ".tag{display:inline-block;background:#e8f0fe;color:#1967d2;"
                 "border-radius:10px;padding:1px 8px;font-size:12px;margin-right:4px}"
                 "</style></head><body>")
    parts.append("<h1 style=\"font-size:20px\">Rich preview (estimación)</h1>")
    parts.append("<p class=\"missing\">Vista ilustrativa: la presencia de datos "
                 "estructurados es un prerrequisito, no una garantía de que el "
                 "buscador muestre el resultado enriquecido.</p>")

    if not blocks:
        parts.append("<div class=\"card\">No se detectó JSON-LD.</div>")

    faqs = find_by_type(blocks, "FAQPage")
    products = find_by_type(blocks, "Product")
    ratings = find_by_type(blocks, "AggregateRating")
    articles = find_by_type(blocks, "Article") or find_by_type(blocks, "BlogPosting")

    if products:
        product = products[0]
        offers = product.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        parts.append("<div class=\"card\"><div class=\"label\">Producto</div>")
        parts.append("<div class=\"title\">%s</div>" % html_mod.escape(str(product.get("name", "(sin name)"))))
        if ratings:
            r = ratings[0]
            parts.append("<div class=\"stars\">%s %s <span style=\"color:#5f6368\">(%s)</span></div>"
                         % ("★" * 5, html_mod.escape(str(r.get("ratingValue", "?"))),
                            html_mod.escape(str(r.get("ratingCount", "?")))))
        if offers:
            parts.append("<div class=\"price\">%s %s</div>" % (
                html_mod.escape(str(offers.get("price", "?"))),
                html_mod.escape(str(offers.get("priceCurrency", "")))))
            if offers.get("availability"):
                parts.append("<div class=\"url\">%s</div>" % html_mod.escape(
                    str(offers["availability"]).rsplit("/", 1)[-1]))
        missing = missing_required(product, "Product")
        parts.append(_missing_html(missing, "Product"))
        parts.append("</div>")

    if faqs:
        faq = faqs[0]
        entities = faq.get("mainEntity") or []
        if isinstance(entities, dict):
            entities = [entities]
        parts.append("<div class=\"card\"><div class=\"label\">FAQPage — preguntas desplegables</div>")
        for item in entities[:6]:
            if isinstance(item, dict):
                answer = item.get("acceptedAnswer") or {}
                text = answer.get("text", "") if isinstance(answer, dict) else str(answer)
                parts.append("<p><strong>%s</strong><br>%s</p>" % (
                    html_mod.escape(str(item.get("name", "(sin name)"))),
                    html_mod.escape(str(text)[:240])))
        ok, detail = _faq_ok(faq)
        parts.append("<p class=\"%s\">%s</p>" % ("ok" if ok else "missing",
                                                 html_mod.escape(detail)))
        parts.append("</div>")

    if articles:
        article = articles[0]
        parts.append("<div class=\"card\"><div class=\"label\">Artículo</div>")
        parts.append("<div class=\"title\">%s</div>" % html_mod.escape(
            str(article.get("headline", "(sin headline)"))))
        parts.append("<div class=\"url\">%s</div>" % html_mod.escape(
            str(article.get("datePublished", "sin datePublished"))))
        author = article.get("author")
        if isinstance(author, dict):
            author = author.get("name")
        if isinstance(author, list) and author and isinstance(author[0], dict):
            author = author[0].get("name")
        parts.append("<div class=\"url\">Autor: %s</div>" % html_mod.escape(str(author or "ausente")))
        parts.append(_missing_html(missing_required(article, "Article"), "Article"))
        parts.append("</div>")

    if not (products or faqs or articles):
        parts.append("<div class=\"card\">Tipos detectados sin simulación específica. "
                     "Rich results soportados con preview: Product, FAQPage, "
                     "Article y AggregateRating.</div>")

    parts.append("<div class=\"card\"><div class=\"label\">Tipos en la página</div><p>%s</p></div>" % (
        " ".join("<span class=\"tag\">%s</span>" % html_mod.escape(t)
                 for t in extract_types([b["data"] for b in blocks if b.get("valid_json")])
                 ) or "ninguno"))
    parts.append("</body></html>")
    return "\n".join(parts)


def _missing_html(missing, type_name):
    if not missing:
        return "<p class=\"ok\">Todas las propiedades requeridas presentes.</p>"
    return "<p class=\"missing\">Falta para %s: %s</p>" % (
        html_mod.escape(type_name), html_mod.escape(", ".join(missing)))


def write_rich_preview(blocks, output_dir, url=""):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "rich-preview.html"
    path.write_text(rich_preview(blocks, url), encoding="utf-8")
    return str(path)


# --- Compatibilidad con la API anterior -------------------------------------

class JSONLDParser(object):
    """Parser legado (archivo -> bloques). Se mantiene por compatibilidad."""

    def __init__(self):
        from html.parser import HTMLParser

        class _P(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)
                self.active = False
                self.buf = []
                self.blocks = []

            def handle_starttag(self, tag, attrs):
                if tag == "script" and dict(attrs).get("type", "").lower() == "application/ld+json":
                    self.active = True
                    self.buf = []

            def handle_data(self, data):
                if self.active:
                    self.buf.append(data)

            def handle_endtag(self, tag):
                if tag == "script" and self.active:
                    self.blocks.append("".join(self.buf))
                    self.active = False

        self._impl = _P()

    def feed(self, data):
        self._impl.feed(data)

    @property
    def blocks(self):
        return self._impl.blocks


def inspect_html(path):
    """Compatibilidad: inspecciona un archivo y devuelve bloques + tipos."""
    parser = JSONLDParser()
    parser.feed(Path(path).read_text(encoding="utf-8", errors="replace"))
    out = []
    for index, raw in enumerate(parser.blocks, 1):
        try:
            data = json.loads(raw)
            out.append({"block": index, "valid_json": True, "types": extract_types(data)})
        except ValueError as exc:
            out.append({"block": index, "valid_json": False, "error": str(exc)})
    return out
