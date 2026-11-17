# -*- coding: utf-8 -*-
"""Capa GEO (Generative Engine Optimization).

Contiene:
  - allow-list de crawlers de IA separada por propósito (search / user-fetch /
    training), con la documentación de cada motor;
  - generación de `llms.txt` y `llms-full.txt` (plantilla reproducible);
  - señales E-E-A-T (autor, fechas, sameAs);
  - detección del bloque-respuesta de 134–167 palabras.

Ninguna función de este módulo consulta la red.
"""
from __future__ import annotations

import json
import re

try:
    from .checks import check
except (ImportError, ValueError):
    from checks import check

# Propósito declarado por cada motor. `search` = indexación para búsqueda,
# `user-fetch` = petición puntual disparada por el usuario, `training` =
# recolección para entrenamiento.
CRAWLERS = (
    {"bot": "OAI-SearchBot", "motor": "OpenAI (ChatGPT Search)", "proposito": "search",
     "doc": "https://platform.openai.com/docs/bots"},
    {"bot": "ChatGPT-User", "motor": "OpenAI (ChatGPT)", "proposito": "user-fetch",
     "doc": "https://platform.openai.com/docs/bots"},
    {"bot": "GPTBot", "motor": "OpenAI", "proposito": "training",
     "doc": "https://platform.openai.com/docs/bots"},
    {"bot": "ClaudeBot", "motor": "Anthropic", "proposito": "training",
     "doc": "https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler"},
    {"bot": "Claude-SearchBot", "motor": "Anthropic (búsqueda)", "proposito": "search",
     "doc": "https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler"},
    {"bot": "Claude-User", "motor": "Anthropic (usuario)", "proposito": "user-fetch",
     "doc": "https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler"},
    {"bot": "PerplexityBot", "motor": "Perplexity", "proposito": "search",
     "doc": "https://docs.perplexity.ai/guides/bots"},
    {"bot": "Perplexity-User", "motor": "Perplexity (usuario)", "proposito": "user-fetch",
     "doc": "https://docs.perplexity.ai/guides/bots"},
    {"bot": "Google-Extended", "motor": "Google (Gemini)", "proposito": "training",
     "doc": "https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers"},
    {"bot": "Bingbot", "motor": "Bing / Copilot", "proposito": "search",
     "doc": "https://www.bing.com/webmasters/help/which-crawlers-does-bing-use-8c184ec0"},
)

PURPOSE_LABEL = {
    "search": "búsqueda (indexación)",
    "user-fetch": "petición del usuario",
    "training": "entrenamiento",
}

# Grupos de bots por propósito: permitir búsqueda no obliga a permitir training.
ALLOWLIST_RECOMMENDED = {
    "search": [c["bot"] for c in CRAWLERS if c["proposito"] == "search"],
    "user-fetch": [c["bot"] for c in CRAWLERS if c["proposito"] == "user-fetch"],
    "training": [c["bot"] for c in CRAWLERS if c["proposito"] == "training"],
}


def crawler_status(robots, path="/"):
    """Estado de cada crawler de IA según robots.txt.

    `robots` es el resultado de `indexcheck.parse_robots`.
    Devuelve una lista de dicts con `allowed` (True/False/None si no se pudo
    determinar). No inventa: sin reglas explícitas se asume permitido por
    comodín, y se indica.
    """
    out = []
    for item in CRAWLERS:
        allowed = None
        try:
            from .indexcheck import is_allowed  # import diferido: evita ciclo
        except (ImportError, ValueError):
            from indexcheck import is_allowed
        if robots:
            allowed = is_allowed(robots, path, item["bot"])
        out.append({
            "bot": item["bot"],
            "motor": item["motor"],
            "proposito": item["proposito"],
            "proposito_label": PURPOSE_LABEL[item["proposito"]],
            "doc": item["doc"],
            "permitido": allowed,
        })
    return out


def analyze(robots, page, url="", llms_status=None, http_llms_status=None):
    """Checks GEO: allow-list de crawlers, E-E-A-T, bloque-respuesta y llms.txt."""
    checks = []
    data = {}

    status = crawler_status(robots, "/")
    data["crawlers"] = status
    blocked_search = [c["bot"] for c in status
                      if c["proposito"] in ("search", "user-fetch") and c["permitido"] is False]
    if robots is None:
        checks.append(check("GEO-CRAWLERS-001", "skip",
                            "Sin robots.txt disponible: no se puede evaluar la allow-list de IA.",
                            url))
    else:
        checks.append(check(
            "GEO-CRAWLERS-001", "fail" if blocked_search else "pass",
            ("Bots de búsqueda/petición bloqueados: " + ", ".join(blocked_search))
            if blocked_search else
            "Ningún crawler de búsqueda o petición de usuario está bloqueado "
            "(los de entrenamiento pueden bloquearse libremente).",
            url))

    # E-E-A-T desde JSON-LD.
    eat = eat_signals(page)
    data["eat"] = eat
    present = [k for k, v in eat.items() if v]
    checks.append(check(
        "GEO-EAT-001", "pass" if len(present) >= 2 else "fail",
        "Señales presentes: %s. Ausentes: %s." % (
            ", ".join(present) or "ninguna",
            ", ".join(k for k, v in eat.items() if not v) or "ninguna"),
        url))

    # Bloque-respuesta de 134–167 palabras.
    answer = answer_block(page.paragraphs)
    data["answer_block"] = answer
    checks.append(check(
        "GEO-ANSWER-001", "pass" if answer["ok"] else "fail",
        answer["evidence"], url, note="estimate"))

    # llms.txt
    if llms_status is None and http_llms_status is None:
        checks.append(check("GEO-LLMS-001", "skip",
                            "llms.txt no comprobado en este modo.", url))
        checks.append(check("GEO-LLMSFULL-001", "skip",
                            "llms-full.txt no comprobado en este modo.", url))
    else:
        for cid, flag, name in (("GEO-LLMS-001", llms_status, "llms.txt"),
                                ("GEO-LLMSFULL-001", http_llms_status, "llms-full.txt")):
            if flag is None:
                checks.append(check(cid, "skip", "%s no comprobado." % name, url))
            else:
                checks.append(check(
                    cid, "pass" if flag else "fail",
                    "%s %s en la raíz del sitio." % (name, "publicado" if flag else "ausente"),
                    url))

    return checks, data


def eat_signals(page):
    """Autor, fechas y sameAs observados en JSON-LD y texto visible."""
    author = False
    dates = False
    same_as = False
    for raw in page.jsonld:
        try:
            obj = json.loads(raw)
        except ValueError:
            continue
        for node in _walk(obj):
            if not isinstance(node, dict):
                continue
            if node.get("author") or node.get("creator"):
                author = True
            if node.get("datePublished") or node.get("dateModified"):
                dates = True
            if node.get("sameAs"):
                same_as = True
    visible_dates = bool(re.search(
        r"\b(?:20\d\d-\d\d-\d\d|\d{1,2}\s+de\s+[a-záéíóú]+\s+de\s+20\d\d)\b",
        page.text, re.I))
    return {
        "autor": author,
        "fechas": dates or visible_dates,
        "sameAs": same_as,
        "fechas_visibles": visible_dates,
    }


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


def answer_block(paragraphs, minimum=134, maximum=167):
    """Busca el primer párrafo con 134–167 palabras (heurística `estimate`)."""
    for index, paragraph in enumerate(paragraphs[:5]):
        words = len(re.findall(r"[0-9A-Za-z\u00c0-\u024f]+", paragraph))
        if minimum <= words <= maximum:
            return {
                "ok": True,
                "index": index,
                "words": words,
                "evidence": "Párrafo #%d con %d palabras, dentro de 134–167." % (index + 1, words),
            }
    if not paragraphs:
        return {"ok": False, "index": None, "words": 0,
                "evidence": "No se detectaron párrafos <p>: no hay bloque-respuesta."}
    words = len(re.findall(r"[0-9A-Za-z\u00c0-\u024f]+", paragraphs[0]))
    return {"ok": False, "index": 0, "words": words,
            "evidence": "Primer párrafo con %d palabras; el bloque-respuesta recomendado "
                        "es de 134–167 (estimate)." % words}


def llms_txt(page, url, sitemap_urls=None, site_name=None):
    """Plantilla de llms.txt (llmstxt.org) a partir de datos observados.

    No inventa secciones ni enlaces: solo incluye lo que existe en la página o
    en el sitemap entregado.
    """
    name = site_name or page.og.get("og:site_name") or page.title or "Sitio"
    summary = page.description or page.og.get("og:description") or ""
    lines = ["# %s" % name.strip(), ""]
    if summary:
        lines += ["> %s" % summary.strip(), ""]
    lines += ["## Páginas", ""]
    urls = list(sitemap_urls or [])
    if not urls and url:
        urls = [url]
    for item in urls[:200]:
        label = item.rstrip("/").rsplit("/", 1)[-1] or item
        lines.append("- [%s](%s)" % (label, item))
    lines += ["", "## Notas", "",
              "- Generado por seo-auditor a partir de datos observados.",
              ""]
    return "\n".join(lines)


def llms_full_txt(page, url, sitemap_urls=None, site_name=None):
    """`llms-full.txt`: mismo encabezado + contenido textual de la página."""
    base = llms_txt(page, url, sitemap_urls, site_name)
    body = ["", "---", "", "# Contenido: %s" % (page.title or url), "",
            page.text.strip()[:20000], ""]
    return base + "\n".join(body)


def recommended_robots_block(allow_search=True, allow_user_fetch=True, allow_training=False):
    """Bloque de robots.txt coherente con la allow-list por propósito."""
    lines = ["# --- Crawlers de IA (generado por seo-auditor; revisa antes de aplicar) ---"]
    for purpose, bots in ALLOWLIST_RECOMMENDED.items():
        allowed = {"search": allow_search, "user-fetch": allow_user_fetch,
                   "training": allow_training}.get(purpose, False)
        for bot in bots:
            lines.append("# %s (%s): %s" % (bot, PURPOSE_LABEL[purpose],
                                            "permitido" if allowed else "bloqueado"))
            lines.append("User-agent: %s" % bot)
            lines.append("Allow: /" if allowed else "Disallow: /")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
