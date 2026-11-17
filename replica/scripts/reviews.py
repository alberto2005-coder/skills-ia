#!/usr/bin/env python3
"""reviews.py - Convierte resenas reales en temas y citas verificables.

reviews.csv:  source,url,rating,text,date
themes.json:  {"themes": {"precio por asiento": ["per seat", "per-seat", "expensive"]}}

Reglas duras (anti-invencion):
  - toda fila sin URL http(s) se descarta y se cuenta
  - cada cita impresa se copia literalmente de una fila, con su URL
  - un tema con <3 resenas o de una sola fuente se marca THIN

Uso:
    python reviews.py replica/reviews.csv --themes themes.json
    python reviews.py reviews.csv --themes themes.json --json --out replica/themes.md

Codigo de salida: 0 ok, 2 error de lectura.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

MAX_QUOTE = 260


def keyword_pattern(keyword: str) -> re.Pattern:
    """Tolera plurales y sufijos cortos: 'cancel' pilla 'cancelar', 'seat' pilla 'seats'."""
    return re.compile(rf"\b{re.escape(keyword.strip())}[a-z]{{0,3}}\b", re.IGNORECASE)


def load_reviews(path: str) -> tuple[list[dict], int]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        delimiter = "\t" if path.lower().endswith(".tsv") else ","
        rows = list(csv.DictReader(fh, delimiter=delimiter))
    if not rows and sample.count("\t") > sample.count(","):
        fh.seek(0)
        rows = list(csv.DictReader(fh, delimiter="\t"))

    valid, dropped = [], 0
    for raw in rows:
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        url = row.get("url") or row.get("link") or row.get("source_url") or ""
        text = row.get("text") or row.get("review") or row.get("body") or ""
        if not re.match(r"https?://", url, re.IGNORECASE) or len(text) < 15:
            dropped += 1
            continue
        try:
            rating = float(row.get("rating") or row.get("stars") or 0)
        except ValueError:
            rating = 0.0
        valid.append(
            {
                "source": row.get("source") or row.get("platform") or "desconocida",
                "url": url,
                "rating": rating,
                "text": text,
                "date": row.get("date") or row.get("fecha") or "",
            }
        )
    return valid, dropped


def load_themes(path: str) -> dict[str, list[str]]:
    with open(path, encoding="utf-8-sig") as fh:
        data = json.load(fh)
    themes = data.get("themes", data)
    if not isinstance(themes, dict):
        raise ValueError("themes.json debe ser un objeto {tema: [palabras]}")
    return {str(k): [str(w) for w in v] for k, v in themes.items()}


def analyze(reviews: list[dict], themes: dict[str, list[str]]) -> dict:
    results = []
    for name, keywords in themes.items():
        patterns = [keyword_pattern(k) for k in keywords if k.strip()]
        matches = []
        for review in reviews:
            if any(p.search(review["text"]) for p in patterns):
                matches.append(review)
        sources = sorted({m["source"] for m in matches})
        ratings = [m["rating"] for m in matches if m["rating"]]
        quotes = sorted(matches, key=lambda m: (m["rating"] or 5, -len(m["text"])))[:2]
        results.append(
            {
                "theme": name,
                "count": len(matches),
                "sources": sources,
                "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
                "thin": len(matches) < 3 or len(sources) < 2,
                "quotes": [
                    {
                        "text": (q["text"][:MAX_QUOTE] + "...") if len(q["text"]) > MAX_QUOTE else q["text"],
                        "truncated": len(q["text"]) > MAX_QUOTE,
                        "source": q["source"],
                        "url": q["url"],
                        "rating": q["rating"] or None,
                    }
                    for q in quotes
                ],
            }
        )
    results.sort(key=lambda r: (-r["count"], r["theme"]))
    return {"reviews": len(reviews), "themes": results}


def report_markdown(data: dict, dropped: int, sample: int) -> str:
    lines = [
        "# Lo que odian los usuarios",
        "",
        f"Base: **{data['reviews']}** resenas con enlace valido de **{sample}** filas "
        f"({dropped} descartadas sin URL o sin texto).",
        "",
        "| Tema | Resenas | Fuentes | Rating medio | Solidez |",
        "| --- | --- | --- | --- | --- |",
    ]
    for t in data["themes"]:
        rating = "—" if t["avg_rating"] is None else f"{t['avg_rating']}/5"
        lines.append(
            f"| {t['theme']} | {t['count']} | {', '.join(t['sources']) or '—'} | {rating} | "
            f"{'THIN' if t['thin'] else 'ok'} |"
        )
    lines += ["", "## Citas", ""]
    for t in data["themes"]:
        lines.append(f"### {t['theme']} ({t['count']})")
        if not t["quotes"]:
            lines.append("_Sin citas: no hay resenas que lo respalden._")
        for q in t["quotes"]:
            lines.append(f"> {q['text']}")
            lines.append(f"> — {q['source']}{' (' + str(q['rating']) + '/5)' if q['rating'] else ''} · {q['url']}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Temas y citas verificables a partir de resenas.")
    parser.add_argument("reviews", nargs="?", default="reviews.csv")
    parser.add_argument("--themes", default="themes.json", help="JSON {tema: [palabras]}")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Escribir informe Markdown en este fichero")
    args = parser.parse_args(argv)

    try:
        reviews, dropped = load_reviews(args.reviews)
        themes = load_themes(args.themes)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[x] {exc}", file=sys.stderr)
        return 2

    if not reviews:
        print("[x] Ninguna resena con URL valida: no se puede analizar sin fuentes.", file=sys.stderr)
        return 2

    data = analyze(reviews, themes)
    if args.json:
        print(json.dumps({**data, "dropped": dropped}, ensure_ascii=False, indent=2))
    else:
        print(f"[*] {len(reviews)} resenas validas, {dropped} descartadas")
        for t in data["themes"]:
            flag = "  [THIN: muestra insuficiente]" if t["thin"] else ""
            print(f"    {t['count']:>3}  {t['theme']:<34} fuentes: {', '.join(t['sources']) or '-'}{flag}")
        if data["themes"]:
            print("\n" + report_markdown(data, dropped, len(reviews) + dropped))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report_markdown(data, dropped, len(reviews) + dropped))
        print(f"[+] Informe escrito en {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
