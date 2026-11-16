#!/usr/bin/env python3
"""imgdiff.py - Compara el layout de dos capturas (ignora color) sin dependencias.

Convierte cada PNG a un mapa de bordes, lo reduce a una rejilla y compara donde
estan las cosas. Dos temas distintos con la misma estructura puntuan alto.

Uso:
    python imgdiff.py original.png clon.png
    python imgdiff.py original.png clon.png --out replica/diff.png --grid 32 --json
    python imgdiff.py original.png clon.png --min-similarity 85   # falla por debajo

Codigo de salida: 0 similar, 1 por debajo del umbral, 2 error.
Soporta PNG de 8 bits por canal, color types 0/2/4/6 (no paleta).
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PNG_SIG = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


def read_png(path: str) -> tuple[int, int, int, bytes]:
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:8] != PNG_SIG:
        raise ValueError(f"{path}: no es un PNG")

    pos, idat = 8, []
    width = height = depth = color_type = None
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            if interlace:
                raise ValueError(f"{path}: PNG entrelazado no soportado")
        elif ctype == b"IDAT":
            idat.append(chunk)
        elif ctype == b"IEND":
            break

    if width is None or height is None:
        raise ValueError(f"{path}: IHDR ausente")
    if depth != 8:
        raise ValueError(f"{path}: solo 8 bits por canal (es {depth})")
    if color_type not in CHANNELS:
        raise ValueError(f"{path}: color type {color_type} no soportado (usa RGB/RGBA/gris)")

    bpp = CHANNELS[color_type]
    stride = width * bpp
    raw = zlib.decompress(b"".join(idat))
    out = bytearray(height * stride)
    prev = bytearray(stride)
    offset = 0

    for y in range(height):
        filt = raw[offset]
        offset += 1
        line = bytearray(raw[offset:offset + stride])
        offset += stride
        if filt == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif filt == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filt == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif filt == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                up = prev[i]
                upleft = prev[i - bpp] if i >= bpp else 0
                p = left + up - upleft
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upleft)
                pred = left if (pa <= pb and pa <= pc) else (up if pb <= pc else upleft)
                line[i] = (line[i] + pred) & 0xFF
        elif filt != 0:
            raise ValueError(f"{path}: filtro PNG {filt} invalido")
        out[y * stride:(y + 1) * stride] = line
        prev = line

    return width, height, bpp, bytes(out)


def luma_map(width: int, height: int, bpp: int, pixels: bytes) -> list[float]:
    """Luminancia 0..255 por pixel (ignora alfa)."""
    gray = [0.0] * (width * height)
    idx = 0
    for i in range(width * height):
        base = i * bpp
        if bpp >= 3:
            r, g, b = pixels[base], pixels[base + 1], pixels[base + 2]
            gray[i] = 0.299 * r + 0.587 * g + 0.114 * b
        else:
            gray[i] = float(pixels[base])
        idx += 1
    return gray


def edge_magnitude(gray: list[float], width: int, height: int) -> list[float]:
    edges = [0.0] * (width * height)
    for y in range(1, height - 1):
        row = y * width
        up, down = row - width, row + width
        for x in range(1, width - 1):
            i = row + x
            gx = (gray[up + x + 1] + 2 * gray[i + 1] + gray[down + x + 1]) - (
                gray[up + x - 1] + 2 * gray[i - 1] + gray[down + x - 1]
            )
            gy = (gray[down + x - 1] + 2 * gray[down + x] + gray[down + x + 1]) - (
                gray[up + x - 1] + 2 * gray[up + x] + gray[up + x + 1]
            )
            edges[i] = abs(gx) + abs(gy)
    return edges


def to_grid(edges: list[float], width: int, height: int, cols: int) -> tuple[list[list[float]], int, int]:
    cell_w = width / cols
    cell_h = cell_w
    rows = max(1, round(height / cell_h))
    cell_h = height / rows
    grid = [[0.0] * cols for _ in range(rows)]
    counts = [[0] * cols for _ in range(rows)]
    for y in range(height):
        gy = min(rows - 1, int(y / cell_h))
        row = y * width
        grid_row = grid[gy]
        count_row = counts[gy]
        for x in range(width):
            gx = min(cols - 1, int(x / cell_w))
            grid_row[gx] += edges[row + x]
            count_row[gx] += 1
    for gy in range(rows):
        for gx in range(cols):
            n = counts[gy][gx]
            grid[gy][gx] = grid[gy][gx] / n if n else 0.0
    mean = sum(sum(r) for r in grid) / (rows * cols) or 1.0
    return [[v / mean for v in row] for row in grid], rows, cols


def write_png(path: str, width: int, height: int, rgb: bytes) -> None:
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw.extend(rgb[y * stride:(y + 1) * stride])

    def chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    with open(path, "wb") as fh:
        fh.write(PNG_SIG)
        fh.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)))
        fh.write(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
        fh.write(chunk(b"IEND", b""))


def compare(a_path: str, b_path: str, cols: int, heatmap_path: str | None) -> dict:
    aw, ah, abpp, apx = read_png(a_path)
    bw, bh, bbpp, bpx = read_png(b_path)

    a_grid, rows, cols_used = to_grid(edge_magnitude(luma_map(aw, ah, abpp, apx), aw, ah), aw, ah, cols)
    b_grid, brows, _ = to_grid(edge_magnitude(luma_map(bw, bh, bbpp, bpx), bw, bh), bw, bh, cols)
    rows = min(rows, brows)

    diffs = []
    for gy in range(rows):
        for gx in range(cols_used):
            a, b = a_grid[gy][gx], b_grid[gy][gx]
            denom = max(a + b, 1e-6)
            diffs.append((abs(a - b) / denom, gy, gx))

    mean_diff = sum(d for d, _, _ in diffs) / len(diffs) if diffs else 0.0
    similarity = max(0.0, min(100.0, 100.0 * (1.0 - mean_diff)))

    worst = []
    for d, gy, gx in sorted(diffs, reverse=True)[:8]:
        if d < 0.35:
            continue
        worst.append(
            {
                "x_pct": round(gx / cols_used * 100, 1),
                "y_pct": round(gy / rows * 100, 1),
                "w_pct": round(100 / cols_used, 1),
                "h_pct": round(100 / rows, 1),
                "difference": round(d, 2),
                "box_original_px": [
                    int(gx * aw / cols_used), int(gy * ah / rows),
                    int((gx + 1) * aw / cols_used), int((gy + 1) * ah / rows),
                ],
            }
        )

    if heatmap_path:
        diff_lookup = {(gy, gx): d for d, gy, gx in diffs}
        gray = luma_map(aw, ah, abpp, apx)
        rgb = bytearray(aw * ah * 3)
        cell_w = aw / cols_used
        cell_h = ah / rows
        for y in range(ah):
            gy = min(rows - 1, int(y / cell_h))
            base_row = y * aw
            for x in range(aw):
                gx = min(cols_used - 1, int(x / cell_w))
                d = diff_lookup.get((gy, gx), 0.0)
                v = int(gray[base_row + x] * 0.55)
                i = (base_row + x) * 3
                rgb[i] = min(255, int(v + 255 * d))
                rgb[i + 1] = min(255, int(v + 40 * d))
                rgb[i + 2] = min(255, int(v))
        write_png(heatmap_path, aw, ah, bytes(rgb))

    return {
        "original": {"path": a_path, "width": aw, "height": ah},
        "clone": {"path": b_path, "width": bw, "height": bh},
        "grid": f"{cols_used}x{rows}",
        "similarity": round(similarity, 1),
        "regions": worst,
        "heatmap": heatmap_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diff de layout entre dos capturas PNG.")
    parser.add_argument("original")
    parser.add_argument("clone")
    parser.add_argument("--out", help="Escribir mapa de calor PNG")
    parser.add_argument("--grid", type=int, default=32, help="Columnas de la rejilla (def. 32)")
    parser.add_argument("--min-similarity", type=float, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.grid < 4:
        parser.error("--grid debe ser >= 4")

    try:
        result = compare(args.original, args.clone, args.grid, args.out)
    except (OSError, ValueError, zlib.error) as exc:
        print(f"[x] {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"[*] Similitud de layout: {result['similarity']}%  (rejilla {result['grid']})")
        if args.out:
            print(f"[+] Mapa de calor: {args.out}")
        if not result["regions"]:
            print("[+] Estructura practicamente identica.")
        else:
            print("\n[#] Regiones que mas difieren (coords en % de la imagen):")
            for region in result["regions"]:
                print(
                    f"    x={region['x_pct']:>5}%  y={region['y_pct']:>5}%  "
                    f"w={region['w_pct']}%  h={region['h_pct']}%  diff={region['difference']}"
                )

    if args.min_similarity is not None and result["similarity"] < args.min_similarity:
        print(f"\n[x] Por debajo del umbral {args.min_similarity}%. Revisa las regiones marcadas.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
