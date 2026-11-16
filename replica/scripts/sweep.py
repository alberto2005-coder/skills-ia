#!/usr/bin/env python3
"""sweep.py - Busca rastros de la app original (marca, dominio, identificadores, colores).

Uso:
    python sweep.py . --avoid "Original App" --avoid originalapp.com
    python sweep.py . --avoid "Original App" --color "#1DB954" --json
    python sweep.py . --avoid "Original App" --exclude replica,dist,node_modules

Salida: fichero:linea: fragmento, agrupado por fichero.
Codigo de salida: 0 limpio, 1 hallazgos, 2 error de uso.

Exenciones (para docs de clean-room que si deben nombrar el original):
    - una linea con  sweep:ignore  se ignora
    - un fichero con  sweep:ignore-file  en sus 5 primeras lineas se ignora entero
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "dist", "build", "out", ".next",
    "target", "vendor", ".venv", "venv", "__pycache__", ".idea", ".vscode",
    "coverage", ".turbo", ".cache", ".mypy_cache", ".pytest_cache",
}

SKIP_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp", ".ico", ".svgz",
    ".pdf", ".zip", ".gz", ".tar", ".rar", ".7z", ".exe", ".dll", ".so", ".dylib",
    ".woff", ".woff2", ".ttf", ".otf", ".eot", ".mp3", ".mp4", ".mov", ".wav",
    ".sqlite", ".db", ".lockb", ".class", ".pyc", ".wasm",
}

MAX_BYTES = 2_000_000
WAIVER_LINE = "sweep:ignore"
WAIVER_FILE = "sweep:ignore-file"


def build_term_patterns(terms: list[str]) -> list[tuple[str, re.Pattern]]:
    """Genera un patron por termino que tambien pilla OriginalApp, original_app, original-app."""
    patterns = []
    for term in terms:
        term = term.strip()
        if not term:
            continue
        parts = re.findall(r"[A-Za-z0-9]+", term)
        core = (
            r"[^A-Za-z0-9]{0,3}".join(re.escape(p) for p in parts)
            if parts
            else re.escape(term)
        )
        # Sin frontera final a proposito: queremos ver OriginalAppEmbed.
        patterns.append((term, re.compile(r"(?<![A-Za-z0-9])" + core, re.IGNORECASE)))
    return patterns


def build_color_patterns(colors: list[str]) -> list[tuple[str, re.Pattern]]:
    patterns = []
    for raw in colors:
        value = raw.strip().lower()
        m = re.fullmatch(r"#?([0-9a-f]{6})", value)
        if not m:
            print(f"[!] Color no valido, se ignora: {raw!r}", file=sys.stderr)
            continue
        h = m.group(1)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        rgb = rf"rgba?\(\s*{r}\s*,\s*{g}\s*,\s*{b}\b"
        patterns.append((f"#{h}", re.compile(rf"#{h}\b|{rgb}", re.IGNORECASE)))
    return patterns


def is_binary(head: bytes) -> bool:
    return b"\x00" in head


def scan_file(path: str, patterns: list[tuple[str, re.Pattern]]) -> list[dict]:
    try:
        size = os.path.getsize(path)
        if size == 0 or size > MAX_BYTES:
            return []
        with open(path, "rb") as fh:
            head = fh.read(8192)
            if is_binary(head):
                return []
            fh.seek(0)
            text = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return []

    lines = text.splitlines()
    if any(WAIVER_FILE in line for line in lines[:5]):
        return []

    hits = []
    for lineno, line in enumerate(lines, 1):
        if WAIVER_LINE in line:
            continue
        for label, pattern in patterns:
            match = pattern.search(line)
            if match:
                snippet = line.strip()
                if len(snippet) > 160:
                    snippet = snippet[:157] + "..."
                hits.append(
                    {
                        "file": path,
                        "line": lineno,
                        "col": match.start() + 1,
                        "term": label,
                        "snippet": snippet,
                    }
                )
                break
    return hits


def iter_files(root: str, excluded: set[str]):
    if os.path.isfile(root):
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in SKIP_DIRS and d not in excluded
        )
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() in SKIP_EXT:
                continue
            yield os.path.join(dirpath, name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Escaneo anti-plagio: marca, dominio, identificadores y colores del original."
    )
    parser.add_argument("path", nargs="?", default=".", help="Directorio o fichero a escanear")
    parser.add_argument(
        "--avoid", action="append", default=[], metavar="TEXTO",
        help="Nombre, marca, dominio o identificador a prohibir (repetible)",
    )
    parser.add_argument(
        "--color", action="append", default=[], metavar="#RRGGBB",
        help="Color de marca del original a prohibir (repetible)",
    )
    parser.add_argument(
        "--exclude", default="", help="Directorios extra a excluir, separados por comas"
    )
    parser.add_argument(
        "--ignore-case-in-snippet", action="store_true", help=argparse.SUPPRESS
    )
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    parser.add_argument(
        "--no-fail", action="store_true", help="Salir con 0 aunque haya hallazgos"
    )
    args = parser.parse_args(argv)

    if not args.avoid and not args.color:
        parser.error("Indica al menos un --avoid o un --color")

    patterns = build_term_patterns(args.avoid) + build_color_patterns(args.color)
    excluded = {d.strip() for d in args.exclude.split(",") if d.strip()}

    if not os.path.exists(args.path):
        print(f"[x] No existe: {args.path}", file=sys.stderr)
        return 2

    hits: list[dict] = []
    scanned = 0
    for file_path in iter_files(args.path, excluded):
        scanned += 1
        hits.extend(scan_file(file_path, patterns))

    by_term: dict[str, int] = {}
    for hit in hits:
        by_term[hit["term"]] = by_term.get(hit["term"], 0) + 1

    if args.json:
        print(
            json.dumps(
                {
                    "root": os.path.abspath(args.path),
                    "scanned_files": scanned,
                    "hits": hits,
                    "by_term": by_term,
                    "clean": not hits,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"[*] Escaneados {scanned} ficheros en {os.path.abspath(args.path)}")
        current = None
        for hit in hits:
            if hit["file"] != current:
                current = hit["file"]
                print(f"\n{hit['file']}")
            print(f"  {hit['line']}:{hit['col']}  [{hit['term']}]  {hit['snippet']}")
        if hits:
            resumen = ", ".join(f"{term}: {n}" for term, n in sorted(by_term.items()))
            print(f"\n[x] {len(hits)} hallazgo(s) en {len({h['file'] for h in hits})} fichero(s) -> {resumen}")
            print("    Renombra, reescribe o justifica con 'sweep:ignore' antes de desplegar.")
        else:
            print("\n[+] Limpio: sin rastros de la app original.")

    if hits and not args.no_fail:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
