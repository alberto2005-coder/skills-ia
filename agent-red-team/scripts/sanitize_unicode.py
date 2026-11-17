#!/usr/bin/env python3
"""
Agent Red Team - Utilidad de Saneamiento (Unicode invisible y comentarios ocultos).
Crea una copia limpia (.sanitized) sin modificar el original hasta que el usuario lo apruebe.

Uso:
  python3 scripts/sanitize_unicode.py --file ruta/al/SKILL.md
"""

import argparse
import re
from pathlib import Path
from typing import Tuple

INVISIBLE_CODEPOINTS = set(range(0x200B, 0x2010)) | set(range(0x202A, 0x202F)) | set(range(0x2060, 0x2065)) | set(range(0x2066, 0x206A)) | set(range(0xE0000, 0xE0080))


def sanitize_content(text: str) -> Tuple[str, int, int]:
    cleaned_chars = []
    removed_unicode = 0
    for idx, ch in enumerate(text):
        cp = ord(ch)
        if idx == 0 and cp == 0xFEFF:
            cleaned_chars.append(ch)
            continue
        if cp in INVISIBLE_CODEPOINTS or cp == 0xFEFF:
            removed_unicode += 1
            continue
        cleaned_chars.append(ch)

    step1 = "".join(cleaned_chars)
    step2, removed_comments = re.subn(r"<!--[\s\S]*?-->", "", step1)
    return step2, removed_unicode, removed_comments


def main():
    parser = argparse.ArgumentParser(description="Elimina caracteres Unicode invisibles y comentarios HTML ocultos.")
    parser.add_argument("--file", required=True, help="Archivo Markdown o texto a sanear")
    args = parser.parse_args()

    src = Path(args.file)
    if not src.exists():
        print(f"ERROR: No existe {src}")
        return

    original = src.read_text(encoding="utf-8")
    clean_text, u_count, c_count = sanitize_content(original)

    out_path = src.with_suffix(src.suffix + ".sanitized")
    out_path.write_text(clean_text, encoding="utf-8")
    print(f"Archivo saneado guardado en: {out_path}")
    print(f"Caracteres Unicode ocultos eliminados: {u_count}")
    print(f"Comentarios HTML eliminados: {c_count}")


if __name__ == "__main__":
    main()
