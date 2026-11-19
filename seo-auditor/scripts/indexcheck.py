# -*- coding: utf-8 -*-
"""Módulo 1 (IndexPulse): diagnóstico de indexación y directivas cruzadas.

Dos partes independientes:

1. `analyze()` — directivas cruzadas reproducibles sin red: reglas de
   robots.txt, `<meta robots>`, cabecera `X-Robots-Tag`, `<link canonical>` y
   detección de sitemap.
2. `check_presence()` — presencia de la URL por motor. **Opt-in**, solo si el
   usuario lo pide: sin API oficial el resultado de `site:` es *indirecto* y
   todos los valores se marcan `estimate`.
"""
from __future__ import annotations

import re
import socket
import time
from urllib.error import URLError, HTTPError
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

try:
    from .checks import check
    from .httpbody import decode_body, decode_html
    from .page import normalize_url
except (ImportError, ValueError):
    from checks import check
    from httpbody import decode_body, decode_html
    from page import normalize_url

ENGINES = {
    "google": {"label": "Google", "url": "https://www.google.com/search?q=site%3A{host}"},
    "bing": {"label": "Bing", "url": "https://www.bing.com/search?q=site%3A{host}"},
    "duckduckgo": {"label": "DuckDuckGo", "url": "https://html.duckduckgo.com/html/?q=site%3A{host}"},
    "yahoo": {"label": "Yahoo", "url": "https://search.yahoo.com/search?p=site%3A{host}"},
    "yandex": {"label": "Yandex", "url": "https://yandex.com/search/?text=site%3A{host}"},
}

BLOCK_MARKERS = ("captcha", "unusual traffic", "tráfico inusual", "access denied",
                 "before you continue", "robot check")

CRAWLER_UA = "SEOAuditor/1.0 (+diagnostico de indexacion; solo lectura)"
# El token con el que robots.txt debe evaluar a ESTE cliente.
AUDITOR_AGENT = "SEOAuditor"


# --- robots.txt -------------------------------------------------------------

def parse_robots(text):
    """Parser mínimo de robots.txt (grupos, reglas Allow/Disallow, Sitemap)."""
    groups = []
    sitemaps = []
    delays = []
    current = None
    for raw in (text or "").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "user-agent":
            if current is None or current["rules"]:
                current = {"agents": [], "rules": []}
                groups.append(current)
            current["agents"].append(value)
        elif key in ("allow", "disallow"):
            if current is None:
                current = {"agents": ["*"], "rules": []}
                groups.append(current)
            current["rules"].append({"type": key, "path": value})
        elif key == "sitemap":
            sitemaps.append(value)
        elif key == "crawl-delay":
            try:
                delays.append(float(value))
            except ValueError:
                pass
    return {"groups": groups, "sitemaps": sitemaps, "crawl_delays": delays,
            "raw_length": len(text or "")}


def _agent_matches(agents, agent):
    low = (agent or "").lower()
    for value in agents:
        if value == "*":
            return True
        token = value.split("/")[0].strip().lower()
        if token and token in low:
            return True
    return False


def _pattern_matches(pattern, path):
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    regex = "^" + re.escape(body).replace("\\*", ".*")
    regex += "$" if anchored else ".*"
    return re.match(regex, path) is not None


def is_allowed(robots, path, agent="Googlebot"):
    """True/False según la regla de mayor longitud (Allow gana en empate)."""
    if not robots:
        return True
    best_len = -1
    best_allow = True
    matched = False
    for group in robots.get("groups", []):
        if not _agent_matches(group["agents"], agent):
            continue
        for rule in group["rules"]:
            if not rule["path"]:
                continue
            if _pattern_matches(rule["path"], path):
                matched = True
                length = len(rule["path"].replace("*", "").replace("$", ""))
                allow = rule["type"] == "allow"
                if length > best_len or (length == best_len and allow and not best_allow):
                    best_len = length
                    best_allow = allow
    return True if not matched else best_allow


def global_disallow(robots):
    """Detecta `Disallow: /` para el grupo comodín."""
    if not robots:
        return False
    for group in robots.get("groups", []):
        if "*" not in group["agents"]:
            continue
        for rule in group["rules"]:
            if rule["type"] == "disallow" and rule["path"] == "/":
                return True
    return False


def fetch_robots(url, timeout=10, allow_local=False):
    """Descarga robots.txt del origen de `url`. Devuelve (texto, url_robots)."""
    parsed = urlparse(url)
    robots_url = "%s://%s/robots.txt" % (parsed.scheme, parsed.netloc)
    try:
        from .security import build_safe_opener, validate_target
    except (ImportError, ValueError):
        from security import build_safe_opener, validate_target
    validate_target(robots_url, allow_local=allow_local)
    request = Request(robots_url, headers={"User-Agent": CRAWLER_UA})
    try:
        with build_safe_opener(allow_local).open(request, timeout=timeout) as response:
            raw = response.read(1_000_000)
            body = decode_body(raw, dict(response.headers))
            return decode_html(body, dict(response.headers)), robots_url
    except (HTTPError, URLError, TimeoutError, socket.timeout, OSError) as error:
        # `TimeoutError` no es `URLError`: un robots.txt lento rompía
        # `audit --mode page` con stack trace en vez de seguir sin robots.
        del error
        return "", robots_url


# --- Directivas cruzadas ----------------------------------------------------

def analyze(page, url="", headers=None, robots=None, sitemap_urls=None,
            robots_url="", presence=None):
    """Checks del módulo 1 sobre evidencia ya recogida (sin red)."""
    data = {"robots_url": robots_url, "robots_sitemaps": list((robots or {}).get("sitemaps", [])),
            "meta_robots": page.robots_meta, "canonicals": list(page.canonicals)}

    headers = _lower_headers(headers)
    x_robots = headers.get("x-robots-tag", "")
    data["x_robots_tag"] = x_robots

    parsed = urlparse(url) if url else None
    path = (parsed.path or "/") if parsed and parsed.scheme else "/"

    meta_noindex = "noindex" in page.robots_meta.lower()
    sitemaps = _collect_sitemaps(sitemap_urls, robots)
    data["sitemaps"] = sitemaps

    checks = _robots_checks(robots, path, url, data)
    checks.append(_meta_robots_check(page, meta_noindex, url))
    checks += _header_checks(headers, page, x_robots, meta_noindex, url)
    checks += _canonical_checks(page, url, parsed, data)
    checks.append(_sitemap_check(sitemaps, robots, url))
    checks.append(_presence_check(presence, url, data))
    return checks, data


def _robots_checks(robots, path, url, data):
    if robots is None:
        return [check("IDX-ROBOTS-001", "skip",
                      "robots.txt no disponible en este modo.", url),
                check("IDX-ROBOTS-002", "skip",
                      "robots.txt no disponible en este modo.", url)]
    # El UA propio es el que hace las peticiones: decidir con el grupo de
    # Googlebot daba por permitido lo que a este auditor se le prohíbe.
    allowed = is_allowed(robots, path, AUDITOR_AGENT)
    data["robots_allows_url"] = allowed
    data["robots_allows_googlebot"] = is_allowed(robots, path, "Googlebot")
    blocked = global_disallow(robots)
    return [
        check("IDX-ROBOTS-001", "pass" if allowed else "fail",
              "%s %s rastrear %s según robots.txt." % (
                  AUDITOR_AGENT, "puede" if allowed else "NO puede", path),
              url),
        check("IDX-ROBOTS-002", "fail" if blocked else "pass",
              "robots.txt con `Disallow: /` global para `*`." if blocked else
              "robots.txt accesible sin bloqueo global (%d grupos, %d sitemaps)." % (
                  len(robots.get("groups", [])), len(robots.get("sitemaps", []))),
              url),
    ]


def _meta_robots_check(page, meta_noindex, url):
    return check(
        "IDX-META-001", "fail" if meta_noindex else "pass",
        "<meta name=robots content=%r>." % page.robots_meta if page.robots_meta
        else "Sin <meta name=robots> (indexación por defecto).",
        url)


def _header_checks(headers, page, x_robots, meta_noindex, url):
    if not headers:
        return [check("IDX-XROBOTS-001", "skip",
                      "Sin cabeceras HTTP capturadas.", url),
                check("IDX-CONFLICT-001", "skip",
                      "Conflicto meta/cabecera no evaluable sin cabeceras.", url)]
    header_noindex = "noindex" in x_robots.lower()
    out = [check(
        "IDX-XROBOTS-001", "fail" if header_noindex else "pass",
        "X-Robots-Tag: %r." % x_robots if x_robots
        else "Sin cabecera X-Robots-Tag.", url)]
    if x_robots or page.robots_meta:
        conflict = meta_noindex != header_noindex
        out.append(check(
            "IDX-CONFLICT-001", "fail" if conflict else "pass",
            ("Conflicto: meta=%r y X-Robots-Tag=%r apuntan en direcciones "
             "distintas." % (page.robots_meta, x_robots)) if conflict
            else "Meta y cabecera coherentes (noindex=%s)." % meta_noindex,
            url))
    else:
        out.append(check("IDX-CONFLICT-001", "pass",
                         "Ni meta ni cabecera imponen directivas.", url))
    return out


def _canonical_checks(page, url, parsed, data):
    # Canonical: coherencia y autorreferencia.
    if not page.canonicals:
        if len(page.canonicals) > 1:
            return [check("SRC-CANON-001", "fail",
                          "Se detectaron %d canonicals; debe haber uno."
                          % len(page.canonicals), url)]
        return [check("SRC-CANON-001", "fail",
                      "No se detectó <link rel=canonical>.", url)]
    canonical = page.canonicals[0]
    data["canonical"] = canonical
    same = True
    if url and parsed and parsed.scheme and canonical.startswith(("http://", "https://")):
        same = normalize_url(canonical) == normalize_url(url)
    return [check(
        "IDX-CANON-001", "pass" if same else "fail",
        ("Canonical autorreferencial: %s." % canonical) if same else
        ("Canonical apunta a otra URL: %s (página: %s)." % (canonical, url)),
        url)]


def _collect_sitemaps(sitemap_urls, robots):
    # Sin duplicados: el llamador puede pasar los mismos que robots.txt.
    sitemaps = []
    for item in list(sitemap_urls or []) + list((robots or {}).get("sitemaps", [])):
        if item and item not in sitemaps:
            sitemaps.append(item)
    return sitemaps


def _sitemap_check(sitemaps, robots, url):
    if sitemaps:
        return check("IDX-SITEMAP-001", "pass",
                     "Sitemap detectado: %s" % ", ".join(sitemaps[:3]), url)
    if robots is not None:
        return check("IDX-SITEMAP-001", "fail",
                     "robots.txt no declara ningún `Sitemap:` y no se "
                     "detectó /sitemap.xml.", url)
    return check("IDX-SITEMAP-001", "skip",
                 "Sitemap no comprobable en este modo.", url)


def _presence_check(presence, url, data):
    if not presence:
        return check("IDX-PRESENCE-001", "skip",
                     "Presencia por motor no solicitada (sin API oficial, "
                     "`site:` es indirecto).", url)
    data["presence"] = presence
    found = [p for p in presence if p.get("status") == "found"]
    return check(
        "IDX-PRESENCE-001", "pass" if found else "fail",
        "Presencia indirecta (`site:`, estimate): %s" % "; ".join(
            "%s=%s (%s)" % (p["engine"], p["status"], p.get("results", "?"))
            for p in presence),
        url, note="estimate")


def _lower_headers(headers):
    if not headers:
        return {}
    if hasattr(headers, "items"):
        return {str(k).lower(): str(v) for k, v in headers.items()}
    return {str(k).lower(): str(v) for k, v in dict(headers).items()}


# --- Presencia por motor (opt-in, indirecta) --------------------------------

def _default_fetch(url, timeout):
    request = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; SEOAuditor/1.0; +diagnostico)",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.6",
    })
    with urlopen(request, timeout=timeout) as response:
        return response.read(600_000).decode("utf-8", errors="replace")


def check_presence(url, engines=None, fetch=None, timeout=10, delay=1.0):
    """Comprueba `site:<host>` por motor.

    Todos los resultados son **indirectos**: sin API oficial (Search Console,
    Bing Webmaster) no se puede afirmar indexación. Se marcan `estimate`.
    `fetch` es inyectable para tests sin red.
    """
    host = urlparse(url).netloc
    if not host:
        raise ValueError("Se necesita una URL absoluta para comprobar presencia")
    engines = engines or list(ENGINES)
    fetch = fetch or _default_fetch
    results = []
    for index, engine in enumerate(engines):
        template = ENGINES.get(engine, {}).get("url")
        if not template:
            results.append({"engine": engine, "status": "unsupported", "results": 0,
                            "indirect": True, "confidence": "estimate",
                            "note": "Motor no soportado."})
            continue
        query_url = template.format(host=host, q=quote_plus("site:" + host))
        if index:
            time.sleep(delay)
        try:
            body = fetch(query_url, timeout)
        except Exception as exc:  # red bloqueada, captcha, timeout...
            results.append({"engine": engine, "status": "thin", "results": 0,
                            "indirect": True, "confidence": "estimate",
                            "query": query_url, "note": "Sin respuesta fiable: %s" % exc})
            continue
        low = body.lower()
        blocked = any(marker in low for marker in BLOCK_MARKERS)
        hits = set()
        for found in re.findall(r"https?://([^/\"'\s<>]+)", body):
            found = found.lower()
            if host.lower().replace("www.", "") in found:
                hits.add(found)
        status = "thin" if blocked else ("found" if hits else "not_found")
        results.append({
            "engine": engine,
            "status": status,
            "results": len(hits),
            "indirect": True,
            "confidence": "estimate",
            "query": query_url,
            "note": "Resultado de `site:` sin API oficial: indirecto, no prueba indexación."
                    if not blocked else "Respuesta de bloqueo/captcha: no concluyente.",
        })
    return results
