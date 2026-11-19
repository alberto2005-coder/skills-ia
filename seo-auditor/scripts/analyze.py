# -*- coding: utf-8 -*-
"""Pipeline de un documento: HTML + cabeceras -> comprobaciones + datos.

Es el punto único que usan `source_audit`, `web_audit` y los comandos de
módulo, para que el mismo HTML produzca el mismo resultado en cualquier modo.
"""
from __future__ import annotations

try:
    from . import geo, hreflang, indexcheck, onpage, schema_audit, serp
    from .checks import catalog, check
except (ImportError, ValueError):
    import geo
    import hreflang
    import indexcheck
    import onpage
    import schema_audit
    import serp
    from checks import catalog, check

RECOMMENDATIONS = {
    "SRC-TITLE-001": "Añade un <title> único y descriptivo (45–60 caracteres).",
    "SRC-TITLE-002": "Acorta el <title> o reescribe la parte que se recorta en la SERP.",
    "SRC-H1-001": "Incluye un <h1> visible que describa el propósito de la página.",
    "ONP-H1-001": "Deja exactamente un <h1>; usa <h2>–<h4> para las secciones.",
    "SRC-META-001": "Añade una meta description útil (120–160 caracteres) con valor diferencial.",
    "SRC-CANON-001": "Declara <link rel=canonical> con URL absoluta y autorreferencial.",
    "SRC-ROBOTS-001": "Confirma el noindex; si la página debe indexarse, elimínalo.",
    "SERP-TITLE-001": "Reduce el título a ~60 caracteres o mueve la palabra clave al inicio.",
    "SERP-DESC-001": "Ajusta la descripción a 120–160 caracteres y evita frases cortadas.",
    "SERP-OG-001": "Añade og:title, og:description y og:image absolutos para las tarjetas sociales.",
    "SERP-TW-001": "Declara twitter:card (summary_large_image) y twitter:image.",
    "ONP-ALT-001": "Añade alt descriptivo a las imágenes informativas y alt=\"\" a las decorativas.",
    "ONP-RATIO-001": "Reduce HTML/JS embebido o amplía el contenido útil del HTML inicial.",
    "IDX-ROBOTS-001": "Revisa la regla de robots.txt que bloquea esta URL.",
    "IDX-ROBOTS-002": "Elimina el `Disallow: /` global si el sitio debe indexarse.",
    "IDX-META-001": "Elimina noindex de <meta robots> en páginas que deben indexarse.",
    "IDX-XROBOTS-001": "Revisa X-Robots-Tag: noindex en la respuesta del servidor.",
    "IDX-CONFLICT-001": "Unifica meta robots y X-Robots-Tag para que no se contradigan.",
    "IDX-CANON-001": "Corrige el canonical para que apunte a la propia URL canónica.",
    "IDX-SITEMAP-001": "Declara `Sitemap:` en robots.txt y publica un sitemap válido.",
    "IDX-PRESENCE-001": "Trata el resultado de `site:` como indirecto; confirma en Search Console/Bing Webmaster.",
    "SCHEMA-JSONLD-001": "Corrige el JSON-LD inválido o añade datos estructurados del tipo adecuado.",
    "SCHEMA-FAQ-001": "Completa mainEntity con Question.name y acceptedAnswer.text.",
    "SCHEMA-PRODUCT-001": "Completa offers con price, priceCurrency y availability visibles en la página.",
    "SCHEMA-RATING-001": "Añade ratingValue y ratingCount reales y visibles.",
    "HREF-LANG-001": "Declara <html lang> con un código BCP 47 válido.",
    "HREF-CODE-001": "Corrige los códigos hreflang no válidos (ISO 639-1/2 + región ISO 3166-1).",
    "HREF-SELF-001": "Incluye un hreflang autorreferencial en la propia página.",
    "HREF-RETURN-001": "Añade el enlace de retorno hreflang en cada página de destino.",
    "HREF-XDEFAULT-001": "Declara x-default apuntando a la versión por defecto.",
    "GEO-LLMS-001": "Publica /llms.txt con la estructura de llmstxt.org.",
    "GEO-LLMSFULL-001": "Opcional: publica /llms-full.txt con el contenido completo para LLMs.",
    "GEO-CRAWLERS-001": "Revisa la allow-list de crawlers de IA: no bloquees búsqueda ni petición de usuario.",
    "GEO-EAT-001": "Añade autor, fechas de publicación/actualización y sameAs verificables.",
    "GEO-ANSWER-001": "Escribe un bloque-respuesta directo de 134–167 palabras al inicio.",
    "SEC-HSTS-001": "Activa HSTS con max-age alto, includeSubDomains y preload si procede.",
    "SEC-CSP-001": "Define Content-Security-Policy sin unsafe-inline/unsafe-eval.",
    "SEC-XFO-001": "Añade X-Frame-Options: SAMEORIGIN o CSP frame-ancestors.",
    "SEC-XCTO-001": "Añade X-Content-Type-Options: nosniff.",
    "SEC-RP-001": "Añade Referrer-Policy: strict-origin-when-cross-origin.",
    "SEC-PP-001": "Añade Permissions-Policy restringiendo APIs no usadas.",
    "SEC-MIXED-001": "Sirve todos los recursos por HTTPS.",
    "PERF-TTFB-001": "Reduce TTFB: caché de página, CDN o consultas más rápidas en origen.",
    "PERF-WEIGHT-001": "Reduce el HTML inicial: mueve markup repetido a componentes/plantillas.",
    "PERF-COMPRESS-001": "Activa gzip o brotli en el servidor/CDN.",
    "PERF-RESOURCES-001": "Agrupa y difiere CSS/JS no críticos.",
    "PERF-CWV-001": "Mide con PageSpeed Insights y prioriza LCP/CLS/TBT según el dato real.",
}

PREFIX_RECOMMENDATIONS = (
    ("SRC-ALT-", "Añade alt descriptivo a las imágenes informativas."),
    ("WEB-ALT-", "Añade alt descriptivo a las imágenes informativas."),
)


def recommendation_for(check_id):
    if check_id in RECOMMENDATIONS:
        return RECOMMENDATIONS[check_id]
    for prefix, text in PREFIX_RECOMMENDATIONS:
        if check_id.startswith(prefix):
            return text
    return "Corrige según la documentación oficial citada."


LEGACY_SEVERITY = {"must": "high", "should": "medium", "nice": "low"}


def document_checks(page, url="", page_url="", headers=None, robots=None,
                    sitemap_urls=None, page_map=None, llms_status=None,
                    http_llms_status=None, presence=None, sitemap_found=None):
    """Todas las comprobaciones de un documento.

    `url` es la etiqueta que aparece en el informe (ruta o URL).
    `page_url` es la URL absoluta de la página, si existe.
    """
    label = url or page_url
    checks = []

    # --- metadatos base
    if page.title:
        checks.append(check("SRC-TITLE-001", "pass", "Título: %r" % page.title[:160], label))
    else:
        checks.append(check("SRC-TITLE-001", "fail", "No se detectó <title>.", label))

    if page.description:
        checks.append(check("SRC-META-001", "pass",
                            "Descripción de %d caracteres." % len(page.description), label))
    else:
        checks.append(check("SRC-META-001", "fail", "No se detectó meta description.", label))

    serp_checks, serp_data = serp.analyze(page, label)
    checks.extend(serp_checks)

    onpage_checks, onpage_data = onpage.analyze(page, label)
    checks.extend(onpage_checks)

    index_checks, index_data = indexcheck.analyze(
        page, label, headers=headers, robots=robots,
        sitemap_urls=sitemap_urls, presence=presence)
    checks.extend(index_checks)

    schema_checks, schema_data = schema_audit.analyze(page, label)
    checks.extend(schema_checks)

    geo_checks, geo_data = geo.analyze(
        robots, page, label, llms_status=llms_status,
        http_llms_status=http_llms_status)
    checks.extend(geo_checks)

    # Si no hay URL de página, el canonical absoluto observado sirve para
    # comprobar la autorreferencia hreflang (es evidencia del propio HTML).
    effective_url = page_url
    if not effective_url and page.canonicals:
        candidate = page.canonicals[0]
        if candidate.lower().startswith(("http://", "https://")):
            effective_url = candidate
    href_checks, href_data = hreflang.analyze(
        page, effective_url, page_map=page_map, url=label)
    checks.extend(href_checks)

    data = {
        "serp": serp_data,
        "onpage": onpage_data,
        "index": index_data,
        "schema": schema_data,
        "geo": geo_data,
        "hreflang": href_data,
        "page": snapshot(page, effective_url or label),
    }

    if headers:
        sec_checks, sec_data = security_checks(page, headers, label, page_url)
        checks.extend(sec_checks)
        data["security"] = sec_data
    else:
        data["security"] = {"score": None,
                            "note": "Sin cabeceras HTTP en este modo."}

    return checks, data


def security_checks(page, headers, label, page_url=""):
    try:
        from .security import audit_headers
    except (ImportError, ValueError):
        from security import audit_headers
    return audit_headers(headers, page=page, url=label, page_url=page_url)


def snapshot(page, page_url=""):
    """Instantánea de evidencia para poder generar borradores sin re-rastrear."""
    return {
        "url": page_url,
        "title": page.title,
        "description": page.description,
        "html_lang": page.html_lang,
        "canonical": page.canonicals[0] if page.canonicals else "",
        "robots_meta": page.robots_meta,
        "og": dict(page.og),
        "twitter": dict(page.twitter),
        "jsonld": list(page.jsonld),
        "headings": {k: list(v) for k, v in page.headings.items()},
        "paragraphs": list(page.paragraphs[:10]),
        "word_count": page.word_count,
        "text_head": page.text[:4000],
        "images_total": len(page.images),
        "images_without_alt": [img.get("src", "") for img in page.images_without_alt()],
    }


def to_findings(checks):
    """Convierte los checks fallidos en hallazgos compatibles con el informe."""
    findings = []
    for rec in checks:
        if rec.get("status") != "fail":
            continue
        meta = catalog(rec["id"])
        severity_level = rec.get("severity_level") or meta["severity_level"]
        findings.append({
            "id": rec["id"],
            "category": rec.get("dimension") or meta["dimension"],
            "dimension": rec.get("dimension") or meta["dimension"],
            "severity": LEGACY_SEVERITY.get(severity_level, "medium"),
            "severity_level": severity_level,
            "status": "fail",
            "title": rec.get("title") or meta["title"],
            "evidence": rec.get("evidence", ""),
            "recommendation": recommendation_for(rec["id"]),
            "url": rec.get("url", ""),
            "citation": rec.get("citation") or meta["citation"],
            "confidence": "medium" if rec.get("note") in ("estimate",) else "high",
            "effort": "low" if severity_level == "nice" else "medium",
            "impact": "high" if severity_level == "must" else (
                "medium" if severity_level == "should" else "low"),
        })
    return findings
