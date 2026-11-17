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
    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self._skip_depth:
            # Dentro de <template>/<svg>/<script>/<style> no se recoge nada:
            # sus imágenes y encabezados no forman parte del documento visible.
            if tag == self._skip_tag:
                self._skip_depth += 1
            return
        a = dict(attrs)
        if tag == "html":
            self.html_lang = (a.get("lang") or "").strip()
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            self.meta.append(a)
        elif tag == "link":
            self.link_tags.append(a)
        elif tag in HEADINGS:
            self._heading_stack.append(tag)
            self._heading_buf.append([])
        elif tag == "img":
            self.images.append({
                "src": a.get("src", ""),
                "alt": a.get("alt") if "alt" in a else None,
                "width": a.get("width", ""),
                "height": a.get("height", ""),
                "loading": a.get("loading", ""),
            })
        elif tag in ("iframe", "video", "audio", "source", "embed"):
            rec = {"tag": tag, "src": a.get("src", "")}
            if tag == "iframe":
                self.iframes.append(rec)
            self.media.append(rec)
        elif tag == "script":
            stype = (a.get("type") or "").lower()
            if stype == "application/ld+json":
                self._jsonld_active = True
                self._jsonld_buf = []
            else:
                if a.get("src"):
                    self.scripts.append(a["src"])
                if self._skip_depth == 0:
                    self._skip_tag = "script"
                    self._skip_depth = 1
        elif tag == "style":
            self.styles.append("inline")
            if self._skip_depth == 0:
                self._skip_tag = "style"
                self._skip_depth = 1
        elif tag == "p":
            self._in_paragraph = True
            self._paragraph_buf = []
        elif tag == "a" and a.get("href"):
            self.anchors.append(a["href"])
        elif tag in SKIP_TEXT:
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


def parse_file(path, encoding="utf-8"):
    with open(path, "r", encoding=encoding, errors="replace") as fh:
        return parse_html(fh.read())
