"""Utilidades comunes de los tests de `replica/scripts` (solo stdlib).

- Deja `replica/scripts` en `sys.path` para importar los scripts como modulos.
- `run_capture` ejecuta el `main(argv)` de un script capturando stdout/stderr y
  devuelve (codigo, stdout, stderr) sin depender de subprocess.
- `write_png` genera un PNG minimo (color type 2 o 6, 8 bits) con zlib + struct,
  para probar `imgdiff.py` sin imagenes externas.
"""

from __future__ import annotations

import contextlib
import io
import os
import struct
import sys
import zlib

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def run_capture(func, argv):
    """Llama a `func(argv)` capturando su salida. Devuelve (codigo, out, err)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = func(list(argv))
    return code, out.getvalue(), err.getvalue()


def write_text(path, text, encoding="utf-8"):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding=encoding, newline="") as fh:
        fh.write(text)
    return path


def _chunk(tag, payload):
    return (
        struct.pack(">I", len(payload))
        + tag
        + payload
        + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    )


def png_bytes(width, height, pixel, color_type=2):
    """PNG 8 bits por canal. `pixel(x, y)` devuelve bytes de 3 (RGB) o 4 (RGBA)."""
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color_type]
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filtro None
        for x in range(width):
            value = pixel(x, y)
            if len(value) != channels:
                raise ValueError("pixel() debe devolver %d bytes" % channels)
            raw.extend(value)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )


def write_png(path, width, height, pixel, color_type=2):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(png_bytes(width, height, pixel, color_type))
    return path


def band_pixel(rows, color=(255, 255, 255)):
    """Pixel RGB blanco dentro de las filas indicadas y negro fuera (para bordes)."""
    def pixel(x, y):
        return color if y in rows else (0, 0, 0)

    return pixel
