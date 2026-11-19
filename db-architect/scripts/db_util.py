"""Utilidades compartidas por los scripts del paquete.

Vive dentro de `scripts/` a propósito: cada paquete se instala solo, así que no
puede depender de un módulo común en la raíz del repositorio.
"""

from __future__ import annotations

from pathlib import Path


def split_top_level(text: str) -> list[str]:
    """Separa por comas ignorando las que están dentro de paréntesis.

    `text.split(",")` parte `DECIMAL(10,2)` en dos trozos y convierte `2)` en
    una columna inventada, con INSERT inválidos detrás.
    """
    parts, depth, current = [], 0, []
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [part.strip() for part in parts if part.strip()]


def iter_files(path: Path, suffixes: set[str], skip_parts: frozenset[str] = frozenset()) -> list[Path]:
    """Ficheros del árbol con alguna de esas extensiones, saltando esas carpetas."""
    if path.is_file():
        return [path]
    return sorted(
        item for item in path.rglob("*")
        if item.is_file() and item.suffix in suffixes
        and not skip_parts & set(item.relative_to(path).parts)
    )
