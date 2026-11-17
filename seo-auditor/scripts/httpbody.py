# -*- coding: utf-8 -*-
"""Descompresión HTTP mínima (stdlib): gzip y deflate.

Los módulos de red anuncian `Accept-Encoding: gzip, deflate`, así que el
cuerpo recibido llega comprimido. Sin descomprimirlo, `parse_html()` leería
bytes binarios como si fueran UTF-8 y todos los checks de contenido fallarían.

No se anuncia `br` (brotli) porque no es decodificable sin dependencias: pedir
un formato que no se puede leer convertiría cada respuesta en basura.
"""
from __future__ import annotations

import gzip
import zlib


def content_encoding(headers):
    """Valor de `Content-Encoding` en minúsculas, o cadena vacía."""
    for key, value in (headers or {}).items():
        if str(key).lower() == "content-encoding":
            return str(value).strip().lower()
    return ""


def decode_body(body, headers):
    """Devuelve el cuerpo descomprimido según `Content-Encoding`.

    Si la codificación es desconocida o el bloque está corrupto, devuelve el
    cuerpo tal cual: es preferible un análisis parcial a una excepción de red.
    """
    if not body:
        return body
    encoding = content_encoding(headers)
    if not encoding:
        return body
    if "gzip" in encoding:
        try:
            return gzip.decompress(body)
        except (OSError, EOFError):
            return body
    if "deflate" in encoding:
        # `deflate` llega con cabecera zlib o en deflate crudo, según servidor.
        try:
            return zlib.decompress(body)
        except zlib.error:
            try:
                return zlib.decompress(body, -zlib.MAX_WBITS)
            except zlib.error:
                return body
    return body
