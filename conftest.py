"""Configuración de pytest para el monorepo de skills.

Cada skill tiene su propia carpeta `tests/` con helpers que se importan por
nombre (`config`, `support`, `helpers`). Ejecutar `pytest` desde la raíz en un
único proceso fallaba porque:

- `config.py` existía en tres suites con contenidos distintos y pytest
  importaba el primero que encontraba (el de `appsec-audit`), así que
  `premium-web-designer` y `skill-evals` no encontraban sus constantes;
- `test_structure.py`, `test_report.py`, `test_templates.py` y
  `test_security.py` repetían nombre y pytest los trataba como el mismo módulo.

Aquí se añade cada `tests/` al `sys.path` y `pyproject.toml` fija
`--import-mode=importlib`, de modo que dos ficheros con el mismo nombre ya no
comparten módulo. `run_tests.py` sigue lanzando cada suite en su propio proceso
y no depende de este fichero.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# La raíz primero y luego cada suite; sin duplicados.
for tests_dir in sorted(ROOT.glob("*/tests")) + [ROOT / "tests"]:
    entry = str(tests_dir)
    if tests_dir.is_dir() and entry not in sys.path:
        sys.path.insert(0, entry)
