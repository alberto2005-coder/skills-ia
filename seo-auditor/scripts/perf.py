# -*- coding: utf-8 -*-
"""Módulo 3 (IndexPulse): velocidad y Core Web Vitals.

Medido sin dependencias: TTFB, peso del HTML, compresión (cabeceras) y número
de CSS/JS externos.

LCP / CLS / TBT / Speed Index **no se pueden medir** con stdlib: solo se
aceptan si el usuario aporta un dato externo (PageSpeed Insights) o se marcan
`estimate`. Nunca se inventa un número.
"""
from __future__ import annotations

import time
from urllib.parse import quote

try:
    from .checks import check
    from .httpbody import charset_of, decode_body, decode_html
    from .page import parse_html
except (ImportError, ValueError):
    from checks import check
    from httpbody import charset_of, decode_body, decode_html
    from page import parse_html

PSI_URL = "https://pagespeed.web.dev/analysis?url=%s"

TTFB_LIMIT_MS = 800
HTML_LIMIT_BYTES = 100 * 1024
RESOURCE_LIMIT = 20
CWV_TARGETS = {
    "lcp_ms": 2500,
    "cls": 0.1,
    "tbt_ms": 200,
    "fcp_ms": 1800,
}


def tbt_estimate(js_bytes, js_requests):
    """Estimación grosera de TBT a partir de bytes de JS. Marcada `estimate`."""
    if not js_bytes:
        return None
    return round(min(2000.0, js_bytes / 1024.0 * 3.2 + js_requests * 12.0), 1)


def analyze(headers, html_bytes, ttfb_ms=None, total_ms=None, page=None,
            external_cwv=None, url="", js_bytes=None, js_requests=None):
    """Checks de rendimiento desde datos ya medidos."""
    checks = []
    low = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    encoding = low.get("content-encoding", "").lower()
    psi = PSI_URL % quote(url, safe="") if url else PSI_URL % ""

    data = {
        "ttfb_ms": ttfb_ms,
        "total_ms": total_ms,
        "html_bytes": html_bytes,
        "content_encoding": encoding or None,
        "css_externos": len(page.styles) if page else 0,
        "js_externos": len(page.scripts) if page else 0,
        "psi_url": psi,
        "cwv_source": "external" if external_cwv else "estimate",
    }

    if ttfb_ms is None:
        checks.append(check("PERF-TTFB-001", "skip",
                            "TTFB no medido en este modo.", url))
    else:
        checks.append(check(
            "PERF-TTFB-001", "pass" if ttfb_ms <= TTFB_LIMIT_MS else "fail",
            "TTFB %d ms (objetivo ≤ %d ms)." % (ttfb_ms, TTFB_LIMIT_MS),
            url, note="medido"))

    checks.append(check(
        "PERF-WEIGHT-001", "pass" if html_bytes <= HTML_LIMIT_BYTES else "fail",
        "HTML %d bytes (%.1f KB; objetivo ≤ 100 KB)." % (
            html_bytes, html_bytes / 1024.0),
        url, note="medido"))

    compressed = any(token in encoding for token in ("gzip", "br", "brotli", "deflate"))
    checks.append(check(
        "PERF-COMPRESS-001", "pass" if compressed else "fail",
        "Content-Encoding=%r." % (encoding or "ausente"),
        url, note="medido"))

    if page is None:
        checks.append(check("PERF-RESOURCES-001", "skip",
                            "Sin HTML parseado: no se pudo contar CSS/JS.", url))
    else:
        total = len(page.styles) + len(page.scripts)
        checks.append(check(
            "PERF-RESOURCES-001", "pass" if total <= RESOURCE_LIMIT else "fail",
            "%d CSS y %d JS externos (total %d; objetivo ≤ %d)." % (
                len(page.styles), len(page.scripts), total, RESOURCE_LIMIT),
            url, note="medido"))

    cwv = external_cwv or {}
    if cwv:
        problems = []
        if cwv.get("lcp_ms") is not None and cwv["lcp_ms"] > CWV_TARGETS["lcp_ms"]:
            problems.append("LCP %s ms > %s" % (cwv["lcp_ms"], CWV_TARGETS["lcp_ms"]))
        if cwv.get("cls") is not None and cwv["cls"] > CWV_TARGETS["cls"]:
            problems.append("CLS %s > %s" % (cwv["cls"], CWV_TARGETS["cls"]))
        if cwv.get("tbt_ms") is not None and cwv["tbt_ms"] > CWV_TARGETS["tbt_ms"]:
            problems.append("TBT %s ms > %s" % (cwv["tbt_ms"], CWV_TARGETS["tbt_ms"]))
        data["cwv"] = cwv
        checks.append(check(
            "PERF-CWV-001", "fail" if problems else "pass",
            ("Fuera de objetivo: " + "; ".join(problems)) if problems else
            "Core Web Vitals dentro de objetivo (dato externo aportado).",
            url, note="medido (externo)"))
    else:
        estimate = tbt_estimate(js_bytes, js_requests or 0) if js_bytes else None
        data["tbt_estimate_ms"] = estimate
        data["cwv_estimate"] = {
            "lcp_ms": None, "cls": None, "tbt_ms": estimate, "speed_index": None,
        }
        checks.append(check(
            "PERF-CWV-001", "skip",
            "Sin dato externo de PageSpeed Insights no se mide LCP/CLS/TBT/Speed "
            "Index; TBT estimado=%s. Enlaces: %s" % (
                ("%s ms (estimate)" % estimate) if estimate else "no calculable",
                psi),
            url, note="estimate"))

    return checks, data


def measure(url, timeout=15, allow_local=False):
    """Mide TTFB, tiempo total y cabeceras de una URL (red explícita)."""
    from urllib.request import Request

    try:
        from .security import build_safe_opener, validate_target
    except (ImportError, ValueError):
        from security import build_safe_opener, validate_target
    validate_target(url, allow_local=allow_local)
    request = Request(url, headers={
        "User-Agent": "SEOAuditor/1.0 (+auditoria autorizada)",
        "Accept-Encoding": "gzip, deflate",
        "Accept": "text/html,*/*;q=0.8",
    })
    start = time.time()
    response = build_safe_opener(allow_local).open(request, timeout=timeout)
    first = response.read(1)
    ttfb_ms = int((time.time() - start) * 1000)
    raw = first + response.read(2_000_000)
    total_ms = int((time.time() - start) * 1000)
    headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
    return {
        "url": url,
        "final_url": response.geturl(),
        "status": getattr(response, "status", None),
        "headers": headers,
        "body": decode_body(raw, headers),
        "charset": charset_of(headers, decode_body(raw, headers)),
        "encoded_bytes": len(raw),
        "ttfb_ms": ttfb_ms,
        "total_ms": total_ms,
    }


def analyze_url(url, timeout=15, allow_local=False, external_cwv=None):
    """Mide y analiza una URL. Devuelve (checks, data, page)."""
    measured = measure(url, timeout=timeout, allow_local=allow_local)
    page = parse_html(decode_html(measured["body"], measured["headers"]))
    checks, data = analyze(
        measured["headers"], len(measured["body"]), measured["ttfb_ms"],
        measured["total_ms"], page, external_cwv=external_cwv,
        url=measured["final_url"],
    )
    data["final_url"] = measured["final_url"]
    data["status"] = measured["status"]
    return checks, data, page
