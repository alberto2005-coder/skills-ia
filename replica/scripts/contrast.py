#!/usr/bin/env python3
"""contrast.py - Verifica contraste WCAG de tus tokens de color (AA/AAA).

tokens.json:
{
  "colors": {"background": "#0B0B0F", "surface": "#16161D", "text": "#F5F5F7",
             "muted": "#9A9AA5", "primary": "#5B8DEF", "on_primary": "#FFFFFF"},
  "pairs": [["text", "background"], ["muted", "surface", "normal"],
            ["on_primary", "primary", "normal"]]
}
pairs[2] opcional: "normal" (por defecto, AA 4.5) | "large" (AA 3.0).

Uso:
    python contrast.py replica/design/tokens.json
    python contrast.py tokens.json --json --min 4.5

Codigo de salida: 0 todo AA, 1 algun par por debajo, 2 error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

NAMED = {
    "white": (255, 255, 255), "black": (0, 0, 0), "transparent": (0, 0, 0),
}
AA_NORMAL, AA_LARGE, AAA_NORMAL, AAA_LARGE = 4.5, 3.0, 7.0, 4.5


def parse_color(value: str) -> tuple[int, int, int]:
    text = str(value).strip().lower()
    if text in NAMED:
        return NAMED[text]
    m = re.fullmatch(r"#([0-9a-f]{3,8})", text)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            return tuple(int(c * 2, 16) for c in h[:3])  # type: ignore[return-value]
        if len(h) in (6, 8):
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    m = re.fullmatch(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*[\d.]+\s*)?\)", text)
    if m:
        return tuple(min(255, int(g)) for g in m.groups())  # type: ignore[return-value]
    raise ValueError(f"color no reconocido: {value!r}")


def luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        s = c / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    a, b = luminance(fg), luminance(bg)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)


def hex_of(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Contraste WCAG de tokens de diseno.")
    parser.add_argument("tokens", nargs="?", default="tokens.json")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--min", type=float, default=None, help="Umbral propio para texto normal")
    args = parser.parse_args(argv)

    try:
        with open(args.tokens, encoding="utf-8-sig") as fh:
            data = json.load(fh)
        colors = {k: parse_color(v) for k, v in data.get("colors", {}).items()}
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"[x] No se pudo leer {args.tokens}: {exc}", file=sys.stderr)
        return 2
    if len(colors) < 2:
        print("[x] Necesito al menos dos colores en 'colors'.", file=sys.stderr)
        return 2

    pairs = data.get("pairs")
    if not pairs:
        candidates = [("text", "background"), ("muted", "background"), ("primary", "background")]
        if "on_primary" in colors:
            candidates.append(("on_primary", "primary"))
        pairs = [list(p) for p in candidates if p[0] in colors and p[1] in colors]

    results = []
    failures = 0
    for pair in pairs:
        if len(pair) < 2:
            continue
        fg_name, bg_name = pair[0], pair[1]
        kind = (pair[2] if len(pair) > 2 else "normal").lower()
        if fg_name not in colors or bg_name not in colors:
            print(f"[!] Par ignorado, color desconocido: {fg_name}/{bg_name}", file=sys.stderr)
            continue
        value = ratio(colors[fg_name], colors[bg_name])
        threshold = args.min if args.min is not None else (AA_LARGE if kind == "large" else AA_NORMAL)
        passes = value >= threshold
        if not passes:
            failures += 1
        results.append(
            {
                "foreground": fg_name,
                "background": bg_name,
                "fg_hex": hex_of(colors[fg_name]),
                "bg_hex": hex_of(colors[bg_name]),
                "kind": kind,
                "ratio": round(value, 2),
                "aa": value >= (AA_LARGE if kind == "large" else AA_NORMAL),
                "aaa": value >= (AAA_LARGE if kind == "large" else AAA_NORMAL),
                "threshold": threshold,
                "passes": passes,
            }
        )

    if args.json:
        print(json.dumps({"pairs": results, "failures": failures}, indent=2))
    else:
        print(f"[*] Contraste WCAG en {args.tokens}\n")
        print(f"    {'par':<28} {'ratio':>6}  AA   AAA")
        for r in sorted(results, key=lambda r: r["ratio"]):
            pair = f"{r['foreground']} / {r['background']}"
            print(
                f"    {pair:<28} {r['ratio']:>6.2f}  "
                f"{'ok ' if r['aa'] else 'NO ':<4} {'ok' if r['aaa'] else '--':<4}"
            )
        if failures:
            print(f"\n[x] {failures} par(es) no cumplen AA. Ajusta los tokens antes de construir.")
        else:
            print("\n[+] Todos los pares cumplen AA.")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
