# -*- coding: utf-8 -*-
"""Rastreador HTTP con crawl respetuoso.

Reglas duras implementadas:
  - respeta robots.txt (Allow/Disallow por agente) antes de encolar cada URL;
  - 1 petición por segundo por defecto (`requests_per_second`);
  - tope de páginas y profundidad declarado en el informe (`crawl`).

Todo lo medido se guarda para que `--rescore` no necesite volver a la red.
"""
from __future__ import annotations

import re
import time
from collections import deque
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request

try:
    from . import analyze, indexcheck, perf
    from .httpbody import decode_body, decode_html
    from .page import parse_html
    from .security import build_safe_opener, validate_target
except (ImportError, ValueError):
    import analyze
    import indexcheck
    import perf
    from httpbody import decode_body, decode_html
    from page import parse_html
    from security import build_safe_opener, validate_target

USER_AGENT = "SEOAuditor/1.0 (+authorized SEO audit; respeta robots.txt)"
MAX_BYTES = 2_000_000


def fetch(url, timeout=10, allow_local=False):
    """Una petición GET con tiempos y cabeceras. Devuelve dict."""
    validate_target(url, allow_local=allow_local)
    request = Request(url, headers={"User-Agent": USER_AGENT,
                                    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                                    "Accept-Encoding": "gzip, deflate"})
    start = time.time()
    response = build_safe_opener(allow_local).open(request, timeout=timeout)
    # El primer byte mide TTFB; leer todo antes de parar el reloj convertía
    # "TTFB" en el tiempo de descarga completa.
    first = response.read(1)
    ttfb_ms = int((time.time() - start) * 1000)
    raw = first + response.read(MAX_BYTES)
    total_ms = int((time.time() - start) * 1000)
    headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
    return {
        "status": getattr(response, "status", None),
        "final_url": response.geturl(),
        "headers": headers,
        "body": decode_body(raw, headers),
        "encoded_bytes": len(raw),
        "ttfb_ms": ttfb_ms,
        "total_ms": total_ms,
    }


def _origin(url):
    parsed = urlparse(url)
    return "%s://%s" % (parsed.scheme, parsed.netloc)


def audit_web(start_url, max_pages=30, max_depth=3, timeout=10, allow_local=False,
              rate=1.0, respect_robots=True):
    validate_target(start_url, allow_local=allow_local)
    limit = max(1, min(int(max_pages), 500))
    if rate is None or float(rate) <= 0:
        raise ValueError("rate debe ser mayor que 0 peticiones por segundo")
    if timeout is None or int(timeout) <= 0:
        raise ValueError("timeout debe ser mayor que 0 segundos")
    rate = float(rate)
    interval = 1.0 / rate

    origin = urlparse(start_url)
    origin_host = origin.netloc

    # robots.txt una sola vez por origen.
    robots = None
    robots_url = _origin(start_url) + "/robots.txt"
    if respect_robots:
        try:
            robots_text, robots_url = indexcheck.fetch_robots(
                start_url, timeout=timeout, allow_local=allow_local)
            robots = indexcheck.parse_robots(robots_text)
        except Exception:
            robots = None

    sitemap_urls = list((robots or {}).get("sitemaps", []))
    llms_status = None
    llms_full_status = None
    try:
        for name, setter in (("llms.txt", "llms"), ("llms-full.txt", "llms_full")):
            try:
                response = fetch(_origin(start_url) + "/" + name, timeout=timeout,
                                 allow_local=allow_local)
                ok = 200 <= (response["status"] or 0) < 300 and len(response["body"]) > 0
            except (HTTPError, URLError, ValueError):
                ok = False
            if setter == "llms":
                llms_status = ok
            else:
                llms_full_status = ok
    except Exception:
        pass

    queue = deque([(start_url, 0)])
    seen = set()
    records = []
    parsed_pages = []
    skipped = []
    last_request = 0.0
    fetched = 0

    while queue and fetched < limit:
        url, depth = queue.popleft()
        url = urldefrag(url)[0]
        if url in seen:
            continue
        seen.add(url)

        if respect_robots and robots is not None and not indexcheck.is_allowed(
                robots, urlparse(url).path or "/", indexcheck.AUDITOR_AGENT):
            skipped.append(url)
            continue

        wait = interval - (time.time() - last_request)
        if last_request and wait > 0:
            time.sleep(wait)
        last_request = time.time()

        try:
            response = fetch(url, timeout=timeout, allow_local=allow_local)
        except (HTTPError, URLError, ValueError, OSError) as exc:
            records.append({"url": url, "status": None, "error": str(exc)})
            continue

        fetched += 1
        content_type = response["headers"].get("content-type", "")
        record = {
            "url": url,
            "final_url": response["final_url"],
            "status": response["status"],
            "content_type": content_type,
            "ttfb_ms": response["ttfb_ms"],
            "bytes": len(response["body"]),
        }
        records.append(record)

        # Sin `Content-Type` la página desaparecía del crawl. Si el cuerpo
        # empieza por `<`, es HTML y se analiza igual.
        if "html" not in content_type.lower() and not (
                not content_type and response["body"].lstrip()[:1] == b"<"):
            continue

        page = parse_html(decode_html(response["body"], response["headers"]))
        parsed_pages.append((url, page, response["headers"], record))

        if depth < max_depth:
            for href in page.anchors:
                absolute = urljoin(response["final_url"], href)
                parsed = urlparse(absolute)
                if parsed.scheme in ("http", "https") and parsed.netloc == origin_host:
                    clean = urldefrag(absolute)[0]
                    if clean not in seen:
                        queue.append((clean, depth + 1))

    # Sitemap: si robots no lo declara, se prueba /sitemap.xml.
    sitemap_count = None
    if not sitemap_urls:
        try:
            candidate = _origin(start_url) + "/sitemap.xml"
            response = fetch(candidate, timeout=timeout, allow_local=allow_local)
            if 200 <= (response["status"] or 0) < 300:
                text = decode_html(response["body"], response["headers"])
                sitemap_count = len(re.findall(r"<loc>", text))
                sitemap_urls.append(candidate)
        except Exception:
            sitemap_count = None

    page_map = {url: page.hreflangs for url, page, _h, _r in parsed_pages}

    checks = []
    data = {
        "crawl": {
            "max_pages": limit,
            "max_depth": max_depth,
            "requests_per_second": rate,
            "robots_respected": bool(respect_robots),
            "robots_url": robots_url,
            "pages_fetched": fetched,
            "skipped_by_robots": len(skipped),
            "limit_declared": True,
        },
        "sitemap": {"urls": sitemap_urls, "loc_count": sitemap_count},
        "pages": records,
    }

    for index, (url, page, headers, record) in enumerate(parsed_pages):
        page_checks, page_data = analyze.document_checks(
            page, url=url, page_url=record["final_url"], headers=headers,
            robots=robots, sitemap_urls=sitemap_urls, page_map=page_map,
            llms_status=llms_status, http_llms_status=llms_full_status)
        checks.extend(page_checks)

        perf_checks, perf_data = perf.analyze(
            headers, record["bytes"], record["ttfb_ms"], record["ttfb_ms"], page,
            url=record["final_url"])
        checks.extend(perf_checks)

        if index == 0:
            data.update({k: v for k, v in page_data.items() if k != "page"})
            data["page"] = page_data["page"]
            data["perf"] = perf_data
            data["index"] = page_data.get("index", {})
        data.setdefault("per_page", []).append({
            "url": url,
            "status": record["status"],
            "ttfb_ms": record["ttfb_ms"],
            "bytes": record["bytes"],
            "security_score": (page_data.get("security") or {}).get("score"),
        })

    # Crawl respetuoso como check explícito.
    checks.append({
        "id": "CRAWL-ROBOTS-001", "status": "pass" if respect_robots else "fail",
        "evidence": "robots.txt respetado=%s; %.1f req/s; tope %d páginas; "
                    "%d URLs omitidas por robots." % (
                        respect_robots, rate, limit, len(skipped)),
        "url": start_url, "dimension": "tecnico", "severity_level": "should",
        "citation": "https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt",
        "title": "Crawl respetuoso: robots.txt respetado y 1 petición/segundo",
        "known": True,
    })

    return {
        "mode": "local" if allow_local else "web",
        "target": start_url,
        "start_url": start_url,
        "pages_scanned": len(records),
        "pages": records,
        "skipped_by_robots": skipped,
        "crawl": data["crawl"],
        "checks": checks,
        "findings": analyze.to_findings(checks),
        "data": data,
    }
