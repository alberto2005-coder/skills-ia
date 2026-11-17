# -*- coding: utf-8 -*-
"""Módulo 7 (IndexPulse): auditoría on-page.

Ratio texto/HTML, jerarquía H1–H4, imágenes sin `alt` y tabla de densidad de
palabras clave. La densidad es **informativa**: las guías de esta skill
(`references/02-contenido.md`) prohíben usarla como objetivo SEO.
"""
from __future__ import annotations

import re
from collections import Counter

try:
    from .checks import check
except (ImportError, ValueError):
    from checks import check

STOPWORDS = set("""
de la que el en y a los se del las un por con no una su para es al lo como mas más pero sus le ya o
este si sí porque esta entre cuando muy sin sobre tambien también me hasta hay donde quien desde
todo nos durante todos uno les ni contra otros ese eso ante ellos e esto mi antes algunos que unos
yo otro otras otra él tanto esa estos mucho quienes nada muchos cual poco ella estar estas algunas
algo nosotros my mis tu tus te ti ellas nosotras vosotros vosotras os mio mío mia mía tuyos suyos
suya suyas nuestro nuestra nuestros nuestras vuestro vuestra vuestros vuestras esos esas estoy está
estan están ser son fue fueron era eran has han he ha hemos haber tiene tienen tener hacer hace
hacen puede pueden podria podría muy mas más menos sin sobre tras durante mediante desde hasta
para por con del las los una uno unos unas al a el la lo le les se su sus mi mis tu tus
the and for with that this from are was were has have had not but you your our its it is be been
of to in on at as by or an we they them their there which who what when where how all any
""".split())

TOKEN_RE = re.compile(r"[0-9A-Za-z\u00c0-\u024f]{3,}")


def text_ratio(page):
    """Ratio texto/HTML (0–1). `estimate`: proxy de contenido útil por caracteres."""
    return page.ratio()


def heading_hierarchy(page):
    """Devuelve (registros, problemas detectados) de la jerarquía H1–H4."""
    counts = page.heading_counts()
    issues = []
    if counts["h1"] == 0:
        issues.append("H1 ausente")
    if counts["h1"] > 1:
        issues.append("H1 duplicado (%d)" % counts["h1"])
    # Saltos: un H3 sin ningún H2 previo, o un H4 sin H3 previo.
    sequence = []
    for level in ("h1", "h2", "h3", "h4"):
        for _ in page.headings.get(level, []):
            sequence.append(int(level[1]))
    previous = 0
    for level in sequence:
        if previous and level > previous + 1:
            issues.append("Salto de H%d a H%d" % (previous, level))
            break
        previous = level
    records = []
    for level in ("h1", "h2", "h3", "h4"):
        for text in page.headings.get(level, []):
            records.append({"nivel": level.upper(), "texto": text,
                            "palabras": len(text.split())})
    return {"counts": counts, "issues": issues, "items": records}


def images_without_alt(page):
    """Lista de rutas de imagen sin `alt` útil (sin render, solo rutas)."""
    out = []
    for img in page.images_without_alt():
        out.append(img.get("src") or "(sin src)")
    return out


def keyword_density(page, limit=10):
    """Tabla de frecuencia de términos (informativa, no una métrica de calidad)."""
    tokens = [t.lower() for t in TOKEN_RE.findall(page.text)]
    tokens = [t for t in tokens if t not in STOPWORDS]
    total = len(tokens)
    counter = Counter(tokens)
    rows = []
    for word, count in counter.most_common(limit):
        rows.append({
            "termino": word,
            "apariciones": count,
            "densidad_pct": round(100.0 * count / total, 2) if total else 0.0,
        })
    return {"total_terminos": total, "terminos_unicos": len(counter), "filas": rows}


def analyze(page, url=""):
    """Checks on-page + datos medidos."""
    checks = []
    data = {}

    counts = page.heading_counts()
    hierarchy = heading_hierarchy(page)
    data["headings"] = hierarchy
    if counts["h1"] == 0:
        checks.append(check("SRC-H1-001", "fail", "No se detectó ningún <h1>.", url))
    else:
        checks.append(check("SRC-H1-001", "pass",
                            "H1: %r" % page.headings["h1"][0][:120], url))
    checks.append(check(
        "ONP-H1-001", "pass" if counts["h1"] == 1 else "fail",
        "H1 encontrados: %d%s" % (counts["h1"],
                                  "" if counts["h1"] <= 1 else " — " + " | ".join(
                                      repr(h[:80]) for h in page.headings["h1"])),
        url))

    missing = images_without_alt(page)
    data["images_without_alt"] = missing
    data["images_total"] = len(page.images)
    if page.images:
        checks.append(check(
            "ONP-ALT-001", "fail" if missing else "pass",
            "%d de %d imágenes sin alt%s" % (
                len(missing), len(page.images),
                (" — rutas: " + ", ".join(missing[:10])) if missing else ""),
            url))
    else:
        checks.append(check("ONP-ALT-001", "skip", "La página no contiene imágenes.", url))

    ratio = text_ratio(page)
    data["text_ratio"] = ratio
    data["word_count"] = page.word_count
    if page.word_count < 50:
        checks.append(check("ONP-RATIO-001", "skip",
                            "Muestra de texto demasiado pequeña para juzgar el ratio (%d palabras)."
                            % page.word_count, url, note="estimate"))
    else:
        checks.append(check(
            "ONP-RATIO-001", "pass" if ratio >= 0.15 else "fail",
            "Ratio texto/HTML %.1f%% (%d caracteres de texto / %d de HTML). "
            "Umbral orientativo 15%%." % (ratio * 100, page.text_chars, page.html_chars),
            url, note="estimate"))

    density = keyword_density(page)
    data["keyword_density"] = density
    # `skip` deliberado: es una tabla informativa, no una comprobación que
    # deba sumar un "pass" gratis a la dimensión de contenido.
    checks.append(check(
        "ONP-KW-001", "skip",
        "Términos analizados: %d (únicos: %d). Tabla informativa: la densidad no es "
        "una métrica de calidad ni un objetivo SEO." % (
            density["total_terminos"], density["terminos_unicos"]),
        url, note="informativo"))

    return checks, data
