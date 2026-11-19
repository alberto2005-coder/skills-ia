# -*- coding: utf-8 -*-
"""Módulo 2 (IndexPulse): simulador de SERP y tarjetas sociales.

Genera un único `preview.html` autocontenido (CSS inline, sin JS externo, sin
recursos remotos) con:

  - Google escritorio y Google móvil,
  - Bing,
  - tarjetas sociales Open Graph / Twitter para WhatsApp, Facebook, LinkedIn y X,
  - medidor de ancho de título y descripción con aviso de truncamiento.

El ancho en píxeles se **estima** con una métrica aproximada de fuente
(`estimate`): no es una medición del renderizador de Google.
"""
from __future__ import annotations

import html as html_mod
from pathlib import Path
from urllib.parse import urlparse

try:
    from .checks import check
except (ImportError, ValueError):
    from checks import check

# Métrica aproximada para la fuente de resultados de Google (Arial ~20px).
TITLE_PX_PER_CHAR = 9.4
DESC_PX_PER_CHAR = 7.0
MAX_TITLE_PX = 580
MAX_DESC_PX = 990
TITLE_CHARS_SOFT = 60
DESC_CHARS_SOFT = 160
# Por debajo de esto la descripción no describe: truncar no es el único fallo.
MIN_DESCRIPTION_CHARS = 70


def estimate_title_px(text):
    """Ancho estimado del título en píxeles (`estimate`)."""
    return round(len(text or "") * TITLE_PX_PER_CHAR, 1)


def estimate_desc_px(text):
    return round(len(text or "") * DESC_PX_PER_CHAR, 1)


def title_truncated(text):
    return estimate_title_px(text) > MAX_TITLE_PX


def desc_truncated(text):
    return len(text or "") > DESC_CHARS_SOFT


def metrics(page, title=None, description=None):
    used_title = page.title if title is None else title
    used_desc = (page.description or page.og.get("og:description", "")
                 if description is None else description)
    return {
        "title": used_title,
        "description": used_desc,
        "title_overridden": title is not None,
        "description_overridden": description is not None,
        "title_chars": len(used_title or ""),
        "title_px": estimate_title_px(used_title),
        "title_limit_px": MAX_TITLE_PX,
        "title_truncated": title_truncated(used_title),
        "description_chars": len(used_desc or ""),
        "description_px": estimate_desc_px(used_desc),
        "description_limit_chars": DESC_CHARS_SOFT,
        "description_truncated": desc_truncated(used_desc),
        "measure": "estimate: %s px/carácter para el título y %s px/carácter para "
                   "la descripción; Google recorta según el renderizado real."
                   % (TITLE_PX_PER_CHAR, DESC_PX_PER_CHAR),
    }


def analyze(page, url="", title=None, description=None):
    """Checks de SERP + tarjetas sociales."""
    m = metrics(page, title, description)
    checks = []
    checks.append(check(
        "SERP-TITLE-001",
        "pass" if (m["title"] and not m["title_truncated"]) else "fail",
        ("%d caracteres (~%s px, límite ~%d px)." % (
            m["title_chars"], m["title_px"], MAX_TITLE_PX)) if m["title"]
        else "Sin título que simular.",
        url, note="estimate"))
    # Una descripción de 10 caracteres no se trunca, pero tampoco sirve: sin
    # mínimo, `SERP-DESC-001` aprobaba cualquier cosa que cupiera.
    description_ok = (bool(m["description"]) and not m["description_truncated"]
                      and m["description_chars"] >= MIN_DESCRIPTION_CHARS)
    description_note = "Sin meta description."
    if m["description"]:
        description_note = "%d caracteres (mínimo %d, recomendado 120–160)." % (
            m["description_chars"], MIN_DESCRIPTION_CHARS)
    checks.append(check(
        "SERP-DESC-001", "pass" if description_ok else "fail",
        description_note, url, note="estimate"))

    missing_og = [k for k in ("og:title", "og:description", "og:image")
                  if not page.og.get(k)]
    checks.append(check(
        "SERP-OG-001", "fail" if missing_og else "pass",
        "Faltan: " + ", ".join(missing_og) if missing_og
        else "og:title, og:description y og:image presentes.",
        url))
    twitter_card = page.twitter.get("twitter:card", "")
    checks.append(check(
        "SERP-TW-001", "pass" if twitter_card else "fail",
        "twitter:card=%r." % twitter_card if twitter_card
        else "Sin twitter:card (X mostrará una tarjeta básica).",
        url))

    m["og_missing"] = missing_og
    return checks, m


# --- Render -----------------------------------------------------------------

def _crumbs(url):
    parsed = urlparse(url or "")
    host = parsed.netloc or "ejemplo.com"
    segments = [s for s in (parsed.path or "/").split("/") if s]
    crumb = host
    if segments:
        crumb += " › " + " › ".join(segments[:3])
    return crumb, host


def _esc(value):
    return html_mod.escape(str(value or ""))


def build(page, url, title=None, description=None):
    """Devuelve (html, metricas). Autocontenido, sin red."""
    m = metrics(page, title, description)
    m["og_missing"] = [key for key in ("og:title", "og:description", "og:image")
                       if not page.og.get(key)]
    title_text = m["title"] or "(sin título)"
    desc_text = m["description"] or "(sin meta description)"
    host = urlparse(url or "").netloc or "ejemplo.com"
    letter = host.replace("www.", "")[:1].upper() or "W"
    crumbs, _ = _crumbs(url)
    og_image = page.og.get("og:image", "")
    image_label = og_image or "sin og:image"

    parts = []
    parts.append("<!DOCTYPE html><html lang=\"es\"><head><meta charset=\"utf-8\">"
                 "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                 "<title>Simulador SERP — %s</title>" % _esc(host))
    parts.append("""<style>
body{font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;margin:0;
background:#f1f3f4;color:#202124}
header{background:#fff;border-bottom:1px solid #dadce0;padding:16px 24px}
h1{font-size:18px;margin:0 0 4px 0}
.sub{color:#5f6368;font-size:13px}
main{max-width:1100px;margin:0 auto;padding:24px;display:grid;
grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}
section{background:#fff;border:1px solid #dadce0;border-radius:8px;padding:16px}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#5f6368;
margin:0 0 12px 0}
.serp{max-width:600px}
.favicon{width:26px;height:26px;border-radius:50%;background:#1a73e8;color:#fff;
display:inline-flex;align-items:center;justify-content:center;font-size:14px;
font-weight:700;vertical-align:middle;margin-right:10px}
.g-title{color:#1a0dab;font-size:20px;line-height:1.3;margin:2px 0}
.g-url{color:#4d5156;font-size:14px;margin:2px 0 4px 0;word-break:break-all}
.g-desc{color:#4d5156;font-size:14px;line-height:1.58}
.mobile{max-width:360px}
.mobile .g-title{font-size:18px}
.bing-title{color:#0b50a0;font-size:20px;margin:2px 0}
.bing-url{color:#0d7a3e;font-size:14px}
.meter{height:8px;background:#e8eaed;border-radius:4px;overflow:hidden;margin:6px 0}
.meter span{display:block;height:100%;background:#1e8e3e}
.meter.warn span{background:#e37400}
.meter.bad span{background:#d93025}
.meta{font-size:12px;color:#5f6368}
.warn{color:#b3261e;font-weight:600}
.ok{color:#137333;font-weight:600}
.social{max-width:420px;border:1px solid #dadce0;border-radius:8px;overflow:hidden}
.social .img{height:150px;background:#dadce0;display:flex;align-items:center;
justify-content:center;color:#5f6368;font-size:12px;padding:8px;text-align:center;
word-break:break-all}
.social .body{padding:12px}
.social .domain{font-size:11px;color:#5f6368;text-transform:uppercase}
.social .s-title{font-weight:700;font-size:16px;margin:4px 0}
.social .s-desc{font-size:13px;color:#5f6368}
.wa{display:flex;gap:10px;align-items:flex-start}
.wa .img{width:80px;height:80px;border-radius:6px;flex:0 0 80px}
.wa .s-title{font-size:14px}
.wa .s-desc{font-size:12px}
pre{background:#f8f9fa;border:1px solid #dadce0;border-radius:6px;padding:12px;
overflow:auto;font-size:12px}
@media print{body{background:#fff}header{display:none}main{display:block}
section{page-break-inside:avoid;margin-bottom:12px}}
</style></head><body>""")
    parts.append("<header><h1>Simulador de SERP y tarjetas sociales</h1>"
                 "<div class=\"sub\">%s · vista ilustrativa; los anchos son "
                 "<strong>estimate</strong>, no el render real de cada motor.</div>"
                 "</header><main>" % _esc(url or host))

    # --- Google escritorio
    parts.append("<section class=\"serp\"><h2>Google — escritorio</h2>")
    parts.append("<div><span class=\"favicon\">%s</span><span class=\"g-url\">%s</span></div>"
                 % (_esc(letter), _esc(crumbs)))
    parts.append("<div class=\"g-title\">%s</div>" % _esc(
        _truncate_chars(title_text, 70) if m["title_truncated"] else title_text))
    parts.append("<div class=\"g-desc\">%s</div>" % _esc(
        _truncate_chars(desc_text, 170) if m["description_truncated"] else desc_text))
    parts.append(_meter(m["title_px"], MAX_TITLE_PX, "Título"))
    parts.append(_meter(m["description_px"], MAX_DESC_PX, "Descripción"))
    parts.append("</section>")

    # --- Google móvil
    parts.append("<section class=\"serp mobile\"><h2>Google — móvil</h2>")
    parts.append("<div><span class=\"favicon\">%s</span><span class=\"g-url\">%s</span></div>"
                 % (_esc(letter), _esc(host)))
    parts.append("<div class=\"g-title\">%s</div>" % _esc(_truncate_chars(title_text, 60)))
    parts.append("<div class=\"g-desc\">%s</div>" % _esc(_truncate_chars(desc_text, 120)))
    parts.append("</section>")

    # --- Bing
    parts.append("<section class=\"serp\"><h2>Bing</h2>")
    parts.append("<div class=\"bing-url\">%s</div>" % _esc(crumbs))
    parts.append("<div class=\"bing-title\">%s</div>" % _esc(title_text))
    parts.append("<div class=\"g-desc\">%s</div>" % _esc(desc_text))
    parts.append("</section>")

    # --- Tarjetas sociales
    social = [
        ("WhatsApp", "wa"),
        ("Facebook", ""),
        ("LinkedIn", ""),
        ("X (Twitter)", ""),
    ]
    for name, extra in social:
        parts.append("<section><h2>%s</h2><div class=\"social\">" % _esc(name))
        if name == "WhatsApp":
            parts.append("<div class=\"img\">%s</div><div class=\"body\">"
                         "<div class=\"s-title\">%s</div><div class=\"s-desc\">%s</div>"
                         "<div class=\"domain\">%s</div></div>"
                         % (_esc(image_label), _esc(title_text), _esc(desc_text), _esc(host)))
        else:
            parts.append("<div class=\"img\">%s</div><div class=\"body\">"
                         "<div class=\"domain\">%s</div><div class=\"s-title\">%s</div>"
                         "<div class=\"s-desc\">%s</div></div>"
                         % (_esc(image_label), _esc(host),
                            _esc(page.og.get("og:title") or title_text),
                            _esc(page.og.get("og:description") or desc_text)))
        if page.twitter.get("twitter:card"):
            parts.append("<div class=\"meta\">twitter:card=%s</div>"
                         % _esc(page.twitter["twitter:card"]))
        else:
            parts.append("<div class=\"meta warn\">Sin twitter:card</div>")
        parts.append("</div></section>")

    # --- Panel de métricas
    parts.append("<section style=\"grid-column:1/-1\"><h2>Medidor</h2>")
    parts.append("<table style=\"border-collapse:collapse;font-size:13px\">")
    rows = [
        ("Título", "%d caracteres · ~%s px (límite ~%d px)" % (
            m["title_chars"], m["title_px"], MAX_TITLE_PX),
         "warning" if m["title_truncated"] else "ok",
         "Se recortará" if m["title_truncated"] else "Cabe"),
        ("Descripción", "%d caracteres · ~%s px" % (
            m["description_chars"], m["description_px"]),
         "warning" if m["description_truncated"] else "ok",
         "Se recortará" if m["description_truncated"] else "Cabe"),
        ("Open Graph", "faltan: %s" % ", ".join(m["og_missing"]) if m["og_missing"]
         else "completo", "warning" if m["og_missing"] else "ok",
         "revisar" if m["og_missing"] else "correcto"),
    ]
    for label, value, cls, verdict in rows:
        parts.append("<tr><td style=\"padding:6px 14px 6px 0\"><strong>%s</strong></td>"
                     "<td style=\"padding:6px 14px 6px 0\">%s</td>"
                     "<td class=\"%s\">%s</td></tr>" % (
                         _esc(label), _esc(value),
                         cls, _esc(verdict)))
    parts.append("</table>")
    parts.append("<p class=\"meta\">%s</p>" % _esc(m["measure"]))
    parts.append("<p class=\"meta\">Para iterar: <code>--title \"...\" "
                 "--description \"...\"</code></p>")
    parts.append("<pre>%s</pre>" % _esc(
        "Título: %s\nDescripción: %s\nURL: %s" % (title_text, desc_text, url)))
    parts.append("</section>")
    parts.append("</main></body></html>")
    return "\n".join(parts), m


def _truncate_chars(text, limit):
    text = text or ""
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _meter(value, limit, label):
    pct = max(0.0, min(100.0, 100.0 * value / limit))
    cls = "" if value <= limit else " bad"
    if not cls and value > limit * 0.9:
        cls = " warn"
    return ("<div class=\"meta\">%s: %.0f%% del límite</div>"
            "<div class=\"meter%s\"><span style=\"width:%.0f%%\"></span></div>"
            % (label, pct, cls, pct))


def write(page, url, output_dir, title=None, description=None):
    """Escribe `output/serp/preview.html` y devuelve (ruta, metricas)."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    html_text, m = build(page, url, title, description)
    path = out / "preview.html"
    path.write_text(html_text, encoding="utf-8")
    return str(path), m
