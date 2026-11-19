# -*- coding: utf-8 -*-
"""Catálogo central de comprobaciones de la skill seo-auditor.

Cada comprobación tiene:
  - id estable (se usa en hallazgos, informes y comparaciones),
  - dimensión de la rúbrica,
  - severidad `must` | `should` | `nice`,
  - cita al documento oficial que la respalda.

Funciones puras (sin red): todo lo que calcula este módulo se puede
reproducir desde la evidencia guardada en `audit.json` (re-score offline).
"""
from __future__ import annotations

# --- Constantes de la rúbrica -------------------------------------------------

DIMENSIONS = ("tecnico", "contenido", "schema", "geo", "seguridad", "rendimiento")

DIM_WEIGHTS = {
    "tecnico": 25,
    "contenido": 20,
    "schema": 15,
    "geo": 15,
    "seguridad": 10,
    "rendimiento": 15,
}

SEVERITIES = ("must", "should", "nice")

# Mapeo de severidad/estado a icono en el informe.
#   🔴 crítico -> falla con severidad `must`
#   🟡 aviso   -> falla con severidad `should`
#   🟢 aprobado -> pasa la comprobación (las fallas `nice` se muestran como
#                   🟢 "mejora opcional": no bloquean nada)
ICON_FAIL = {"must": "🔴", "should": "🟡", "nice": "🟢"}
ICON_PASS = "🟢"
ICON_SKIP = "⚪"

# Umbrales del veredicto (documentados en el informe y en SKILL.md).
VERDICT_LEADING = 85
VERDICT_COMPETITIVE = 60

GOOGLE = "https://developers.google.com/search/docs"
MDN = "https://developer.mozilla.org/en-US/docs/Web"

# --- Catálogo ---------------------------------------------------------------
# id -> (dimensión, severidad, cita, título corto)
#
# Referencias oficiales utilizadas:
#   Google Search Central, MDN (cabeceras HTTP), schema.org / Google Rich
#   Results, llmstxt.org (estándar llms.txt) y ogp.me (Open Graph).
CHECKS = {
    # ---- Contenido / metadatos ----
    "SRC-TITLE-001": ("contenido", "must", GOOGLE + "/appearance/title-link", "Falta la etiqueta <title>"),
    "SRC-TITLE-002": ("contenido", "nice", GOOGLE + "/appearance/title-link", "<title> posiblemente largo"),
    "SRC-H1-001": ("contenido", "should", MDN + "/HTML/Element/Heading_Elements", "No se detecta H1"),
    "SRC-META-001": ("contenido", "should", GOOGLE + "/appearance/meta-description", "Falta meta description"),
    "SRC-ROBOTS-001": ("tecnico", "must", GOOGLE + "/crawling-indexing/robots-meta-tag", "Directiva noindex en el código"),
    "SRC-CANON-001": ("tecnico", "nice", GOOGLE + "/crawling-indexing/consolidate-duplicate-urls", "No se detecta canonical"),
    "SRC-EMPTY-001": ("contenido", "should", GOOGLE + "/fundamentals/seo-starter-guide", "Archivo HTML vacío"),
    "SRC-ALT-": ("contenido", "should", MDN + "/HTML/Element/img", "Imagen sin atributo alt"),
    "WEB-TITLE-001": ("contenido", "must", GOOGLE + "/appearance/title-link", "Falta <title>"),
    "WEB-H1-001": ("contenido", "should", MDN + "/HTML/Element/Heading_Elements", "No se detecta H1"),
    "WEB-META-001": ("contenido", "should", GOOGLE + "/appearance/meta-description", "Falta meta description"),
    "WEB-NOINDEX-001": ("tecnico", "must", GOOGLE + "/crawling-indexing/robots-meta-tag", "Directiva noindex"),
    "WEB-ALT-": ("contenido", "should", MDN + "/HTML/Element/img", "Imagen sin atributo alt"),
    "WEB-FETCH-001": ("tecnico", "should", GOOGLE + "/crawling-indexing/http-network-issues", "No se pudo recuperar la URL"),
    # ---- Módulo 1: indexación y directivas cruzadas ----
    "IDX-ROBOTS-001": ("tecnico", "must", GOOGLE + "/crawling-indexing/robots/robots_txt", "robots.txt no bloquea esta URL"),
    "IDX-ROBOTS-002": ("tecnico", "should", GOOGLE + "/crawling-indexing/robots/robots_txt", "robots.txt accesible y sin `Disallow: /` global"),
    "IDX-META-001": ("tecnico", "must", GOOGLE + "/crawling-indexing/robots-meta-tag", "Sin noindex en <meta robots>"),
    "IDX-XROBOTS-001": ("tecnico", "must", GOOGLE + "/crawling-indexing/robots-meta-tag", "Sin noindex en la cabecera X-Robots-Tag"),
    "IDX-CONFLICT-001": ("tecnico", "must", GOOGLE + "/crawling-indexing/robots-meta-tag", "Directivas cruzadas sin conflicto (meta vs cabecera vs robots.txt)"),
    "IDX-CANON-001": ("tecnico", "should", GOOGLE + "/crawling-indexing/consolidate-duplicate-urls", "Canonical presente y autorreferencial"),
    "IDX-SITEMAP-001": ("tecnico", "should", GOOGLE + "/crawling-indexing/sitemaps/overview", "Sitemap declarado o detectado"),
    "IDX-PRESENCE-001": ("tecnico", "nice", GOOGLE + "/crawling-indexing/intro-crawling-basics", "Presencia de la URL por motor (site:, estimada)"),
    # ---- Módulo 2: simulador SERP y tarjetas sociales ----
    "SERP-TITLE-001": ("contenido", "should", GOOGLE + "/appearance/title-link", "Título dentro del ancho de la SERP (~60 caracteres / ~580 px)"),
    "SERP-DESC-001": ("contenido", "should", GOOGLE + "/appearance/meta-description", "Descripción de 120–160 caracteres sin truncar"),
    "SERP-OG-001": ("contenido", "nice", "https://ogp.me/", "Etiquetas Open Graph para tarjeta social"),
    "SERP-TW-001": ("contenido", "nice", "https://developer.x.com/en/docs/twitter-for-websites/cards/overview/summary-card", "Twitter Card para vista previa en X"),
    # ---- Módulo 3: velocidad / rendimiento ----
    "PERF-TTFB-001": ("rendimiento", "should", "https://web.dev/articles/optimize-ttfb", "TTFB por debajo de 800 ms (medido)"),
    "PERF-WEIGHT-001": ("rendimiento", "should", "https://web.dev/articles/optimize-byte-efficiency", "Peso del HTML por debajo de 100 KB (medido)"),
    "PERF-COMPRESS-001": ("rendimiento", "should", "https://web.dev/articles/serve-compressed", "Respuesta comprimida (gzip o brotli)"),
    "PERF-RESOURCES-001": ("rendimiento", "nice", "https://web.dev/articles/render-blocking-resources", "Nº de CSS/JS externos razonable (≤ 20)"),
    "PERF-CWV-001": ("rendimiento", "nice", GOOGLE + "/core/core-web-vitals", "Core Web Vitals (LCP/CLS/TBT/Speed Index) sin dato externo: marcado `estimate`"),
    # ---- Módulo 4: seguridad HTTP ----
    "SEC-HSTS-001": ("seguridad", "should", MDN + "/HTTP/Headers/Strict-Transport-Security", "Cabecera Strict-Transport-Security"),
    "SEC-CSP-001": ("seguridad", "should", MDN + "/HTTP/Headers/Content-Security-Policy", "Cabecera Content-Security-Policy"),
    "SEC-XFO-001": ("seguridad", "should", MDN + "/HTTP/Headers/X-Frame-Options", "Cabecera X-Frame-Options o CSP frame-ancestors"),
    "SEC-XCTO-001": ("seguridad", "should", MDN + "/HTTP/Headers/X-Content-Type-Options", "Cabecera X-Content-Type-Options: nosniff"),
    "SEC-RP-001": ("seguridad", "nice", MDN + "/HTTP/Headers/Referrer-Policy", "Cabecera Referrer-Policy"),
    "SEC-PP-001": ("seguridad", "nice", MDN + "/HTTP/Headers/Permissions-Policy", "Cabecera Permissions-Policy"),
    "SEC-MIXED-001": ("seguridad", "must", MDN + "/Web/Security/Mixed_content", "Sin recursos HTTP cargados desde una página HTTPS"),
    # ---- Módulo 5: JSON-LD y rich results ----
    "SCHEMA-JSONLD-001": ("schema", "should", GOOGLE + "/appearance/structured-data/intro-structured-data", "JSON-LD presente y con JSON válido"),
    "SCHEMA-FAQ-001": ("schema", "nice", GOOGLE + "/appearance/rich-results/faq", "FAQPage con mainEntity (Question/acceptedAnswer)"),
    "SCHEMA-PRODUCT-001": ("schema", "nice", GOOGLE + "/appearance/rich-results/product", "Product con offers (price, priceCurrency, availability)"),
    "SCHEMA-RATING-001": ("schema", "nice", GOOGLE + "/appearance/rich-results/review-snippets", "AggregateRating con ratingValue y ratingCount"),
    # ---- Módulo 6: hreflang / SEO internacional ----
    "HREF-LANG-001": ("tecnico", "must", MDN + "/HTML/Global_attributes/lang", "<html lang> presente"),
    "HREF-CODE-001": ("tecnico", "should", GOOGLE + "/sitelinks#hreflang", "Códigos hreflang válidos (ISO 639-1 / 639-2 y región ISO 3166)"),
    "HREF-SELF-001": ("tecnico", "should", GOOGLE + "/sitelinks#hreflang", "Autorreferencia hreflang en la propia URL"),
    "HREF-RETURN-001": ("tecnico", "should", GOOGLE + "/sitelinks#hreflang", "Retorno bidireccional de pares hreflang"),
    "HREF-XDEFAULT-001": ("tecnico", "nice", GOOGLE + "/sitelinks#hreflang", "Declaración x-default"),
    # ---- Módulo 7: on-page ----
    "ONP-H1-001": ("contenido", "must", MDN + "/HTML/Element/Heading_Elements", "Exactamente un H1 por página"),
    "ONP-ALT-001": ("contenido", "should", MDN + "/HTML/Element/img", "Imágenes sin atributo alt"),
    "ONP-RATIO-001": ("contenido", "nice", GOOGLE + "/fundamentals/seo-starter-guide", "Ratio texto/HTML (estimado: umbral orientativo 15 %)"),
    "ONP-KW-001": ("contenido", "nice", GOOGLE + "/fundamentals/seo-starter-guide", "Tabla de densidad de palabras clave (informativa, no objetivo SEO)"),
    # ---- Módulo GEO ----
    "GEO-LLMS-001": ("geo", "should", "https://llmstxt.org/", "Archivo llms.txt publicado en la raíz"),
    "GEO-LLMSFULL-001": ("geo", "nice", "https://llmstxt.org/", "Archivo llms-full.txt (contenido completo para LLMs)"),
    "GEO-CRAWLERS-001": ("geo", "should", "https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers", "Allow-list de crawlers de IA por propósito (search / user-fetch / training)"),
    "GEO-EAT-001": ("geo", "should", "https://static.googleusercontent.com/media/guidelines.raterhub.com/en/searchqualityevaluatorguidelines.pdf", "Señales E-E-A-T: autor, fechas y sameAs"),
    "GEO-ANSWER-001": ("geo", "nice", GOOGLE + "/fundamentals/seo-starter-guide", "Bloque de respuesta directa (134–167 palabras, heurística interna `estimate`)"),
    # ---- Rastreo ----
    "CRAWL-ROBOTS-001": ("tecnico", "should", GOOGLE + "/crawling-indexing/robots/robots_txt", "Crawl respetuoso: robots.txt respetado y 1 petición/segundo"),
}

# Prefijos para ids dinámicos (p. ej. SRC-ALT-003, WEB-ALT-012).
_PREFIXES = sorted((k for k in CHECKS if k.endswith("-")), key=len, reverse=True)


def catalog(check_id):
    """Devuelve metadatos del check; acepta ids con sufijo numérico."""
    if check_id in CHECKS:
        key = check_id
    else:
        key = next((p for p in _PREFIXES if check_id.startswith(p)), None)
        if key is None:
            return {
                "id": check_id,
                "dimension": "tecnico",
                "severity_level": "nice",
                "citation": "",
                "title": check_id,
                "known": False,
            }
    dim, sev, cite, title = CHECKS[key]
    return {"id": check_id, "dimension": dim, "severity_level": sev,
            "citation": cite, "title": title, "known": True}


def check(check_id, status, evidence="", url="", note=""):
    """Construye un registro de comprobación.

    status: "pass" | "fail" | "skip"  (skip = no aplicable/no ejecutable)
    """
    meta = catalog(check_id)
    if status not in ("pass", "fail", "skip"):
        raise ValueError("status inválido: %r" % status)
    rec = {"id": meta["id"], "status": status, "evidence": evidence, "url": url,
           "dimension": meta["dimension"], "severity_level": meta["severity_level"],
           "citation": meta["citation"], "title": meta["title"],
           "known": meta["known"]}
    if note:
        rec["note"] = note
    return rec


def icon_for(rec):
    """Icono 🔴/🟡/🟢/⚪ para un registro de comprobación."""
    if rec.get("status") == "skip":
        return ICON_SKIP
    if rec.get("status") == "pass":
        return ICON_PASS
    return ICON_FAIL.get(rec.get("severity_level", "nice"), "🟢")


def severity_label(sev):
    return {"must": "crítico", "should": "aviso", "nice": "mejora opcional"}.get(sev, sev)


def verdict(total):
    """Veredicto en una línea a partir de la puntuación total 0–100."""
    if total >= VERDICT_LEADING:
        return "Leading"
    if total >= VERDICT_COMPETITIVE:
        return "Competitive"
    return "Not Ready"


def verdict_line(total, forced=None, must_fail_count=0):
    """Veredicto en una línea. Un fallo `must` impide `Leading`."""
    v = forced or verdict(total)
    if v == "Leading":
        return "Leading — por delante de la competencia en las comprobaciones ejecutadas."
    if v == "Competitive":
        if must_fail_count:
            return ("Competitive — %d bloqueo(s) `must` pendientes impiden el "
                    "veredicto Leading." % must_fail_count)
        return "Competitive — competitivo, con margen de mejora en los puntos señalados."
    return ("Not Ready — aún no está listo: %d bloqueo(s) `must` y puntuación "
            "por debajo de %d." % (must_fail_count, VERDICT_COMPETITIVE))


def merge_checks(result_checks, findings):
    """Fusiona los checks registrados por los módulos con los hallazgos.

    - Un hallazgo sin check registrado se convierte en `fail`.
    - No se duplica: clave (id, url).
    """
    merged = {}
    for rec in result_checks or []:
        merged[(rec.get("id", ""), rec.get("url", ""))] = dict(rec)
    for f in findings or []:
        fid = f.get("id", "")
        url = f.get("url", "")
        key = (fid, url)
        if key in merged:
            continue
        meta = catalog(fid)
        merged[key] = {
            "id": fid, "status": "fail", "evidence": f.get("evidence", ""),
            "url": url, "dimension": meta["dimension"], "severity_level": meta["severity_level"],
            "citation": meta["citation"], "title": f.get("title") or meta["title"],
            "known": meta["known"],
        }
    return list(merged.values())


def compute_rubric(checks):
    """Rúbrica 0–100 por dimensiones a partir de los registros de comprobación.

    Score de dimensión = 100 * pass / (pass + fail). Las dimensiones sin
    comprobaciones ejecutadas quedan como `null` y su peso se redistribuye
    entre las dimensiones evaluadas (para no penalizar lo no medido).
    """
    stats = {d: {"pass": 0, "fail": 0, "skip": 0} for d in DIMENSIONS}
    for rec in checks:
        d = rec.get("dimension")
        if d not in stats:
            continue
        st = rec.get("status")
        if st in ("pass", "fail"):
            stats[d][st] += 1
        else:
            stats[d]["skip"] += 1

    dims = {}
    evaluated_weight = 0
    total = 0.0
    for d in DIMENSIONS:
        p, f, s = stats[d]["pass"], stats[d]["fail"], stats[d]["skip"]
        applicable = p + f
        if applicable:
            score = round(100.0 * p / applicable, 1)
            weight = DIM_WEIGHTS[d]
            evaluated_weight += weight
            total += score * weight / 100.0
            dims[d] = {"score": score, "pass": p, "fail": f, "skip": s,
                       "weight": weight, "evaluated": True}
        else:
            dims[d] = {"score": None, "pass": p, "fail": f, "skip": s,
                       "weight": DIM_WEIGHTS[d], "evaluated": False}
    if evaluated_weight:
        total = round(total * 100.0 / evaluated_weight, 1)
    else:
        total = 0.0

    must_fails = [c for c in checks
                  if c.get("status") == "fail" and c.get("severity_level") == "must"]
    # Regla documentada: un fallo `must` no permite `Leading`.
    final_verdict = verdict(total)
    if must_fails and final_verdict == "Leading":
        final_verdict = "Competitive"
    return {
        "total": total,
        "verdict": final_verdict,
        "verdict_line": verdict_line(total, forced=final_verdict,
                                     must_fail_count=len(must_fails)),
        "verdict_capped_by_must": bool(must_fails) and verdict(total) == "Leading",
        "dimensions": dims,
        "weights": dict(DIM_WEIGHTS),
        "must_fail_count": len(must_fails),
        "thresholds": {"leading": VERDICT_LEADING, "competitive": VERDICT_COMPETITIVE},
        "formula": "score_dimensión = 100 * aprobados / (aprobados + fallidos); "
                   "total = media ponderada de las dimensiones evaluadas (pesos en `weights`); "
                   "dimensiones sin comprobaciones ejecutadas se excluyen y su peso se redistribuye.",
    }
