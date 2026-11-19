# -*- coding: utf-8 -*-
"""Módulo 6 (IndexPulse): SEO internacional — hreflang.

Comprueba códigos, autorreferencia, `x-default`, `<html lang>` y el retorno
bidireccional de pares cuando se dispone de varias páginas analizadas.
"""
from __future__ import annotations

import re

try:
    from .checks import check
    from .page import normalize_url
except (ImportError, ValueError):
    from checks import check
    from page import normalize_url

# ISO 639-1 (2 letras) + ISO 639-2 (3 letras) + región ISO 3166-1 alfa-2.
LANG_RE = re.compile(r"^(?:[a-z]{2,3})(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}|\d{3}))?$")
VALID_X_DEFAULT = "x-default"


def is_valid_hreflang(value):
    if not value:
        return False
    if value.lower() == VALID_X_DEFAULT:
        return True
    return bool(LANG_RE.match(value))


def html_lang_valid(value):
    if not value:
        return False
    return bool(LANG_RE.match(value))


def analyze(page, page_url="", page_map=None, url=""):
    """Checks hreflang.

    page_map: {url: [(hreflang, href), ...]} de todas las páginas rastreadas.
    Sin page_map, el retorno bidireccional no se puede verificar -> `skip`.
    """
    target = url or page_url
    data = {"entries": [{"hreflang": code, "href": href} for code, href in page.hreflangs],
            "html_lang": page.html_lang}
    checks = [
        _lang_check(page, target),
        _code_check(page, target, data),
        _self_check(page, page_url, target, data),
        _xdefault_check(page, target, data),
        _return_check(page, page_url, page_map, target, data),
    ]
    return checks, data


def _lang_check(page, target):
    return check("HREF-LANG-001",
                 "pass" if html_lang_valid(page.html_lang) else "fail",
                 "Atributo <html lang>=%r." % (page.html_lang or ""), target)


def _code_check(page, target, data):
    bad = [code for code, _ in page.hreflangs if not is_valid_hreflang(code)]
    data["invalid_codes"] = bad
    if not page.hreflangs:
        return check("HREF-CODE-001", "skip",
                     "La página no declara hreflang.", target)
    return check("HREF-CODE-001", "fail" if bad else "pass",
                 ("Códigos no válidos: " + ", ".join(bad)) if bad else
                 "Todos los códigos hreflang son válidos (%d)." % len(page.hreflangs),
                 target)


def _self_check(page, page_url, target, data):
    if not (page.hreflangs and page_url):
        return check("HREF-SELF-001", "skip",
                     "Sin URL absoluta de la página o sin hreflang: "
                     "autorreferencia no verificable.", target)
    own = normalize_url(page_url)
    self_refs = [h for _, h in page.hreflangs if normalize_url(h) == own]
    data["self_reference"] = bool(self_refs)
    return check("HREF-SELF-001", "pass" if self_refs else "fail",
                 ("Autorreferencia hacia %s." % own) if self_refs else
                 "Ningún hreflang apunta a la propia URL (%s)." % own, target)


def _xdefault_check(page, target, data):
    langs = {code.lower() for code, _ in page.hreflangs}
    if len([code for code in langs if code != VALID_X_DEFAULT]) <= 1:
        return check("HREF-XDEFAULT-001", "skip",
                     "Solo un idioma declarado: x-default no es necesario.", target)
    has_default = VALID_X_DEFAULT in langs
    data["x_default"] = has_default
    return check("HREF-XDEFAULT-001", "pass" if has_default else "fail",
                 "x-default %s." % ("declarado" if has_default else "ausente"), target)


def _return_check(page, page_url, page_map, target, data):
    if not (page_map and page_url and len(page_map) > 1):
        return check("HREF-RETURN-001", "skip",
                     "Retorno bidireccional no verificable con una sola página.", target)
    broken = _broken_return(page_map, page_url, page.hreflangs)
    data["broken_returns"] = broken
    return check("HREF-RETURN-001", "fail" if broken else "pass",
                 ("Sin retorno desde: " + "; ".join(broken[:8])) if broken else
                 "Los %d pares declaran retorno recíproco." % len(page.hreflangs), target)


def _broken_return(page_map, page_url, entries):
    """Pares cuyo destino no declara de vuelta la URL de origen."""
    broken = []
    own = normalize_url(page_url)
    normalized_map = {normalize_url(k): v for k, v in page_map.items()}
    for lang, href in entries:
        target = normalized_map.get(normalize_url(href))
        if target is None:
            broken.append("%s (%s: no rastreada)" % (href, lang))
            continue
        if not any(normalize_url(h) == own for _, h in target):
            broken.append("%s (%s)" % (href, lang))
    return broken


def analyze_orphans(page_map):
    """Detecta páginas que declaran hreflang pero no reciben retorno de nadie."""
    problems = []
    for url, entries in page_map.items():
        for lang, href in entries:
            target = page_map.get(href)
            if target is None:
                continue
            if not any(h == url for _, h in target):
                problems.append({"origen": url, "idioma": lang, "destino": href})
    return problems
