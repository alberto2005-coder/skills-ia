# -*- coding: utf-8 -*-
"""Seguridad: validación de destino (anti-SSRF) y módulo 4 (IndexPulse).

`audit_headers()` puntúa las cabeceras HTTP de seguridad 0–100 de forma
reproducible:

    score = suma de pesos de las cabeceras que pasan
            (HSTS 20 + CSP 25 + XFO 15 + XCTO 15 + RP 10 + PP 15)
    mixed content confirmado resta 20 puntos (mínimo 0).

La fórmula se escribe en `data["formula"]` para que sea auditable.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, build_opener

try:
    from .checks import check
except (ImportError, ValueError):
    from checks import check


def is_loopback_host(host):
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def validate_target(url, allow_local=False):
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ValueError("URL no válida: utiliza http:// o https://")
    host = p.hostname.lower()
    if allow_local:
        if not is_loopback_host(host):
            raise ValueError("El modo local solo permite localhost/loopback.")
        return
    if host == "localhost":
        raise ValueError("Destino local bloqueado en modo web.")
    try:
        infos = socket.getaddrinfo(host, p.port or (443 if p.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise ValueError("No se pudo resolver el host: %s" % exc) from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if not ip.is_global:
            raise ValueError("Destino no público bloqueado: %s" % ip)


class ValidatingRedirectHandler(HTTPRedirectHandler):
    """Sigue una redirección solo si el destino pasa `validate_target`.

    `urlopen` valida la URL inicial y después acepta cualquier `Location`:
    una página pública puede redirigir a `http://169.254.169.254/` o a
    `http://127.0.0.1:8080/` y el rastreador la seguiría. Este handler cierra
    ese hueco validando cada salto con la misma política del modo activo.
    """

    def __init__(self, allow_local=False):
        self.allow_local = allow_local
        HTTPRedirectHandler.__init__(self)

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_target(newurl, allow_local=self.allow_local)
        return HTTPRedirectHandler.redirect_request(
            self, req, fp, code, msg, headers, newurl)


def build_safe_opener(allow_local=False):
    """Opener de urllib que valida también cada redirección."""
    return build_opener(ValidatingRedirectHandler(allow_local=allow_local))


# --- Módulo 4: cabeceras de seguridad ---------------------------------------

REFERRER_VALUES = ("no-referrer", "no-referrer-when-downgrade", "origin",
                   "origin-when-cross-origin", "same-origin", "strict-origin",
                   "strict-origin-when-cross-origin", "unsafe-url")

HEADER_RULES = (
    {"id": "SEC-HSTS-001", "header": "strict-transport-security", "weight": 20},
    {"id": "SEC-CSP-001", "header": "content-security-policy", "weight": 25},
    {"id": "SEC-XFO-001", "header": "x-frame-options", "weight": 15},
    {"id": "SEC-XCTO-001", "header": "x-content-type-options", "weight": 15},
    {"id": "SEC-RP-001", "header": "referrer-policy", "weight": 10},
    {"id": "SEC-PP-001", "header": "permissions-policy", "weight": 15},
)


def _lower(headers):
    if not headers:
        return {}
    if hasattr(headers, "items"):
        return {str(k).lower(): str(v) for k, v in headers.items()}
    return {str(k).lower(): str(v) for k, v in dict(headers).items()}


def hsts_ok(value):
    match = re.search(r"max-age\s*=\s*(\d+)", value or "", re.I)
    if not match:
        return False, "sin `max-age`"
    seconds = int(match.group(1))
    if seconds <= 0:
        return False, "`max-age=0` desactiva HSTS"
    note = "max-age=%d" % seconds
    if "includesubdomains" in (value or "").lower():
        note += ", includeSubDomains"
    if "preload" in (value or "").lower():
        note += ", preload"
    return True, note


def csp_ok(value):
    low = (value or "").lower()
    if not low.strip():
        return False, "vacía"
    weak = [token for token in ("unsafe-inline", "unsafe-eval", "*") if token in low]
    note = "definida"
    if weak:
        note += " (contiene %s; revisar)" % ", ".join(weak)
    if "frame-ancestors" in low:
        note += " con frame-ancestors"
    return True, note


def xfo_ok(value, csp):
    value = (value or "").strip().upper()
    if value in ("DENY", "SAMEORIGIN"):
        return True, value
    if "frame-ancestors" in (csp or "").lower():
        return True, "ausente, cubierta por CSP frame-ancestors"
    if value:
        return False, "valor no válido: %s" % value
    return False, "ausente"


def xcto_ok(value):
    if (value or "").strip().lower() == "nosniff":
        return True, "nosniff"
    return (False, "ausente" if not value else "valor no válido: %s" % value)


def referrer_ok(value):
    value = (value or "").strip().lower()
    if value in REFERRER_VALUES:
        return True, value
    return (False, "ausente" if not value else "valor no válido: %s" % value)


def permissions_ok(value):
    if (value or "").strip():
        return True, value.strip()[:120]
    return False, "ausente"


def mixed_content(page, page_url):
    """Recursos `http://` servidos desde una página HTTPS (o URL relativa a HTTPS)."""
    if page is None or not page_url or not page_url.lower().startswith("https://"):
        return []
    found = []
    for kind, resource in page.resources():
        if resource.lower().startswith("http://"):
            found.append({"tipo": kind, "url": resource})
    return found


def audit_headers(headers, page=None, url="", page_url=""):
    """Audita las 6 cabeceras + mixed content. Devuelve (checks, data)."""
    checks = []
    low = _lower(headers)
    if not low:
        for rule in HEADER_RULES:
            checks.append(check(rule["id"], "skip",
                                "Sin cabeceras HTTP capturadas.", url or page_url))
        checks.append(check("SEC-MIXED-001", "skip",
                            "Sin HTML/URL HTTPS para evaluar mixed content.",
                            url or page_url))
        return checks, {"score": None, "headers": {},
                        "formula": "sin cabeceras no hay puntuación"}

    csp = low.get("content-security-policy", "")
    results = {}
    score = 0
    for rule in HEADER_RULES:
        name = rule["header"]
        value = low.get(name, "")
        if rule["id"] == "SEC-HSTS-001":
            ok, detail = hsts_ok(value)
        elif rule["id"] == "SEC-CSP-001":
            ok, detail = csp_ok(value)
        elif rule["id"] == "SEC-XFO-001":
            ok, detail = xfo_ok(value, csp)
        elif rule["id"] == "SEC-XCTO-001":
            ok, detail = xcto_ok(value)
        elif rule["id"] == "SEC-RP-001":
            ok, detail = referrer_ok(value)
        else:
            ok, detail = permissions_ok(value)
        if ok:
            score += rule["weight"]
        results[name] = {"presente": bool(value), "valor": value, "ok": ok,
                         "detalle": detail, "peso": rule["weight"]}
        checks.append(check(
            rule["id"], "pass" if ok else "fail",
            "%s: %s (peso %d)." % (name, detail, rule["weight"]),
            url or page_url, note="medido"))

    mixed = mixed_content(page, page_url or url)
    if mixed:
        score = max(0, score - 20)
        checks.append(check(
            "SEC-MIXED-001", "fail",
            "%d recurso(s) HTTP en página HTTPS: %s" % (
                len(mixed), ", ".join("%s %s" % (m["tipo"], m["url"]) for m in mixed[:8])),
            url or page_url, note="medido"))
    elif page_url and page_url.lower().startswith("https://") and page is not None:
        checks.append(check("SEC-MIXED-001", "pass",
                            "Ningún recurso http:// en la página HTTPS.",
                            url or page_url, note="medido"))
    else:
        checks.append(check("SEC-MIXED-001", "skip",
                            "Mixed content no evaluable (página no HTTPS o sin HTML).",
                            url or page_url))

    data = {
        "score": score,
        "headers": results,
        "mixed_content": mixed,
        "formula": "suma de pesos de cabeceras correctas (HSTS 20, CSP 25, "
                   "XFO 15, XCTO 15, RP 10, PP 15); mixed content confirmado resta 20.",
    }
    return checks, data
