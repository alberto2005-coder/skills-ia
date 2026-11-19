"""Utilidades compartidas por los scripts del paquete.

Vive dentro de `scripts/` a propósito: cada paquete se instala solo, así que no
puede depender de un módulo común en la raíz del repositorio.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Versión del formato de `findings.json`: sube cuando cambian sus claves o los
# valores de sus campos (2.0 = escala canónica de severidad).
FORMAT_VERSION = "2.0"

# Versión del paquete, la que declaran el SARIF (`tool.driver.version`) y el SBOM.
TOOL_VERSION = "2.0.0"


def force_utf8_output() -> None:
    """Emite UTF-8 aunque la consola de Windows use otra página de códigos."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def relative_parts(path: Path, root: Path) -> tuple[str, ...]:
    """Partes de `path` relativas a `root`: la raíz absoluta no se filtra.

    Con `path.parts`, un proyecto bajo `C:\\build\\` o `~/dist/` entero se
    descartaría por contener `build`/`dist` en la ruta absoluta.
    """
    try:
        return path.relative_to(root).parts
    except ValueError:
        return path.parts
