# -*- coding: utf-8 -*-
"""Modelo de documento HTML compartido por todos los módulos.

Un único parser (stdlib) evita que cada módulo reimplemente la lectura de
<title>, metadatos, encabezados, imágenes, JSON-LD, hreflang, etc.

Todo lo que expone `parse_html` es *observado*: se lee del HTML recibido.
Ninguna métrica de este módulo consulta la red.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urlparse, urlunparse

# Etiquetas cuyo texto no cuenta como contenido visible.
SKIP_TEXT = {"script", "style", "noscript", "template", "svg"}

# Palabras/conteo: incluye acentos (español) sin depender de regex Unicode.
WORD_RE = re.compile(r"[0-9A-Za-z\u00c0-\u024f]+")

HEADINGS = ("h1", "h2", "h3", "h4")


def normalize_url(url: str) -> str:
    """Normaliza una URL para comparar (sin fragmento, sin barra final)."""
    if not url:
        return ""
    p = urlparse(url.strip())
    path = p.path or "/"
    if len(path) > 1:
        path = path.rstrip("/")
    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, "", p.query, ""))


class _PageParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.title_parts = []
        self.in_title = False
        self.meta = []
        self.link_tags = []
        self.headings = {h: [] for h in HEADINGS}
        # Orden real del documento: sin esto la jerarquía se reconstruía
        # agrupando por nivel y `h1,h3,h2` no detectaba el salto.
        self.heading_sequence = []
        self._heading_stack = []
        self._heading_buf = []
        self.images = []
        self.iframes = []
        self.media = []
        self.scripts = []
        self.styles = []
        self.html_lang = ""
        self.jsonld = []
        self._jsonld_active = False
        self._jsonld_buf = []
        self.text_parts = []
        self.paragraphs = []
        self._in_paragraph = False
        self._paragraph_buf = []
        self._skip_depth = 0
        self._skip_tag = None
        self.anchors = []

    # -- inicio / fin de etiqueta -----------------------------------------
    # Despacho por etiqueta: mismo parser, pero ninguna rama vive dentro de
    # las demás (el anidamiento hacía ilegible `handle_starttag`).
    _START_TAGS = {
        "html": "_start_html",
        "title": "_start_title",
        "meta": "_start_meta",
        "link": "_start_link",
        "h1": "_start_heading",
        "h2": "_start_heading",
        "h3": "_start_heading",
        "h4": "_start_heading",
        "img": "_start_img",
        "iframe": "_start_media",
        "video": "_start_media",
        "audio": "_start_media",
        "source": "_start_media",
        "embed": "_start_media",
        "script": "_start_script",
        "style": "_start_style",
        "p": "_start_p",
        "a": "_start_anchor",
        "noscript": "_start_skipped",
        "template": "_start_skipped",
        "svg": "_start_skipped",
    }

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self._skip_depth:
            # Dentro de <template>/<svg>/<script>/<style> no se recoge nada:
            # sus imágenes y encabezados no forman parte del documento visible.
            if tag == self._skip_tag:
                self._skip_depth += 1
            return
        handler = self._START_TAGS.get(tag)
        if handler is not None:
            getattr(self, handler)(tag, dict(attrs))

    def _start_html(self, tag, a):
        self.html_lang = (a.get("lang") or "").strip()

    def _start_title(self, tag, a):
        self.in_title = True

    def _start_meta(self, tag, a):
        self.meta.append(a)

    def _start_link(self, tag, a):
        self.link_tags.append(a)

    def _start_heading(self, tag, a):
        self._heading_stack.append(tag)
        self.heading_sequence.append(int(tag[1]))
        self._heading_buf.append([])

    def _start_img(self, tag, a):
        self.images.append({
            "src": a.get("src", ""),
            "alt": a.get("alt") if "alt" in a else None,
            "width": a.get("width", ""),
            "height": a.get("height", ""),
            "loading": a.get("loading", ""),
        })

    def _start_media(self, tag, a):
        rec = {"tag": tag, "src": a.get("src", "")}
        if tag == "iframe":
            self.iframes.append(rec)
        self.media.append(rec)

    def _start_script(self, tag, a):
        stype = (a.get("type") or "").lower()
        if stype == "application/ld+json":
            self._jsonld_active = True
            self._jsonld_buf = []
            return
        if a.get("src"):
            self.scripts.append(a["src"])
        if self._skip_depth == 0:
            self._skip_tag = "script"
            self._skip_depth = 1

    def _start_style(self, tag, a):
        self.styles.append("inline")
        if self._skip_depth == 0:
            self._skip_tag = "style"
            self._skip_depth = 1

    def _start_p(self, tag, a):
        self._in_paragraph = True
        self._paragraph_buf = []

    def _start_anchor(self, tag, a):
        if a.get("href"):
            self.anchors.append(a["href"])

    def _start_skipped(self, tag, a):
        self._skip_tag = tag
        self._skip_depth = 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._skip_depth:
            if tag == self._skip_tag:
                self._skip_depth -= 1
                if self._skip_depth <= 0:
                    self._skip_depth = 0
                    self._skip_tag = None
            return
        if tag == "title":
            self.in_title = False
        elif tag in HEADINGS and self._heading_stack:
            idx = len(self._heading_stack) - 1
            text = " ".join("".join(self._heading_buf[idx]).split())
            self.headings[tag].append(text)
            self._heading_stack.pop()
            self._heading_buf.pop()
        elif tag == "script":
            if self._jsonld_active:
                self.jsonld.append("".join(self._jsonld_buf))
                self._jsonld_active = False
                self._jsonld_buf = []
            if self._skip_depth and self._skip_tag == "script":
                self._skip_depth = 0
                self._skip_tag = None
        elif tag == "p":
            text = " ".join("".join(self._paragraph_buf).split())
            if text:
                self.paragraphs.append(text)
            self._in_paragraph = False
            self._paragraph_buf = []

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
        if self._jsonld_active:
            self._jsonld_buf.append(data)
            return
        if self._skip_depth:
            return
        text = data.strip()
        if not text:
            return
        self.text_parts.append(text)
        if self._heading_stack:
            self._heading_buf[-1].append(data)
        if self._in_paragraph:
            self._paragraph_buf.append(data)


class Page(object):
    """Vista normalizada del documento HTML analizado."""

    def __init__(self, html):
        self.raw = html or ""
        p = _PageParser()
        try:
            p.feed(self.raw)
            p.close()
        except Exception:
            # HTML roto: conservamos lo ya parseado.
            pass

        def text_of(parts):
            return " ".join(str(x).strip() for x in parts if str(x).strip())

        self.title = text_of(p.title_parts)
        metas = {}
        for m in p.meta:
            key = (m.get("name") or m.get("property") or m.get("http-equiv") or "").lower()
            if key and key not in metas:
                metas[key] = m.get("content", "")
        self.meta = metas
        self.description = metas.get("description", "")
        self.robots_meta = metas.get("robots", "")
        self.og = {k: v for k, v in metas.items() if k.startswith("og:")}
        self.twitter = {k: v for k, v in metas.items() if k.startswith("twitter:")}
        self.canonicals = [tag.get("href", "") for tag in p.link_tags
                           if "canonical" in (tag.get("rel") or "").lower()]
        self.hreflangs = [(tag.get("hreflang", ""), tag.get("href", "")) for tag in p.link_tags
                          if tag.get("hreflang")]
        self.alternates = [tag for tag in p.link_tags if "alternate" in (tag.get("rel") or "").lower()]
        self.html_lang = p.html_lang
        self.headings = {h: list(v) for h, v in p.headings.items()}
        self.heading_sequence = list(p.heading_sequence)
        self.images = p.images
        self.iframes = p.iframes
        self.media = p.media
        self.scripts = p.scripts
        self.styles = [tag.get("href", "") for tag in p.link_tags
                       if "stylesheet" in (tag.get("rel") or "").lower()]
        self.jsonld = p.jsonld
        self.anchors = p.anchors
        self.text = text_of(p.text_parts)
        self.paragraphs = p.paragraphs
        self.words = WORD_RE.findall(self.text)
        self.word_count = len(self.words)
        self.text_chars = len(re.sub(r"\s+", " ", self.text).strip())
        self.html_chars = len(self.raw)
        self.html_bytes = len(self.raw.encode("utf-8", errors="replace"))

    # -- utilidades --------------------------------------------------------
    def ratio(self):
        """Ratio texto/HTML por caracteres. `estimate`: proxy, no es contenido útil."""
        if not self.html_chars:
            return 0.0
        return round(self.text_chars / float(self.html_chars), 4)

    def heading_counts(self):
        return {h: len(self.headings.get(h, [])) for h in HEADINGS}

    def images_without_alt(self):
        """Imágenes sin atributo `alt` (un `alt=""` es decorativo y es válido)."""
        return [img for img in self.images if img.get("alt") is None]

    def resources(self):
        """Recursos referenciados (para mixed content). Devuelve (tipo, url)."""
        out = []
        for src in self.scripts:
            out.append(("script", src))
        for href in self.styles:
            out.append(("stylesheet", href))
        for img in self.images:
            out.append(("image", img.get("src", "")))
        for frame in self.iframes:
            out.append(("iframe", frame.get("src", "")))
        for media in self.media:
            out.append((media.get("tag", "media"), media.get("src", "")))
        return [(t, u) for t, u in out if u]


def parse_html(html):
    return Page(html)


def parse_file(path, encoding=None):
    """Lee un HTML local respetando el charset que declara.

    `encoding` fuerza uno concreto; por defecto se usa el `<meta charset>` y
    UTF-8 como último recurso (antes todo se leía como UTF-8).
    """
    try:
        from .httpbody import decode_html
    except (ImportError, ValueError):
        from httpbody import decode_html
    with open(path, "rb") as fh:
        raw = fh.read()
    if encoding:
        return parse_html(raw.decode(encoding, errors="replace"))
    return parse_html(decode_html(raw))
