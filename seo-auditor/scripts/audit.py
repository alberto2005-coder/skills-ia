#!/usr/bin/env python3
"""
Punto de entrada directo para auditorías SEO.
Permite ejecutar sin necesidad del flag -m:
    python scripts/audit.py https://example.com --mode web
    python scripts/audit.py . --mode source
"""
import sys
from pathlib import Path

scripts_dir = Path(__file__).resolve().parent
project_dir = scripts_dir.parent

for p in (str(scripts_dir), str(project_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from scripts.cli import main
except ImportError:
    from cli import main

if __name__ == "__main__":
    main()
