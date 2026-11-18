import json
import re
from pathlib import Path

readme = Path("README.md")
text = readme.read_text(encoding="utf-8")
pairs = [
    ("Documentación sincronizada con el código: referencias, arquitectura regenerable y CHANGELOG. | 4 |",
     "Documentación sincronizada con el código: referencias, glosario, variables de entorno, arquitectura regenerable y CHANGELOG. | 6 |"),
    ("Documentation synced with the code: references, regenerable architecture and CHANGELOG. | 4 |",
     "Documentation synced with the code: references, glossary, environment variables, regenerable architecture and CHANGELOG. | 6 |"),
    ("12 paquetes, 76 skills", "12 paquetes, 78 skills"),
    ("12 packages, 76 skills", "12 packages, 78 skills"),
    ("activación de las 76 skills", "activación de las 78 skills"),
    ("activation for all 76 skills", "activation for all 78 skills"),
    ("#### `docs-sync-engine` — maestro + 3 sub-skills", "#### `docs-sync-engine` — maestro + 5 sub-skills"),
    ("#### `docs-sync-engine` — master + 3 sub-skills", "#### `docs-sync-engine` — master + 5 sub-skills"),
    ("| `docs-drift-check` | Referencias de la doc frente al árbol: rutas y enlaces. |",
     "| `docs-drift-check` | Referencias de la doc frente al árbol: rutas y enlaces. |\n"
     "| `docs-terms` | Glosario accept/reject y grafía canónica de cada término. |\n"
     "| `docs-env` | Variables de entorno frente a `.env.example` y los documentos. |"),
    ("| `docs-drift-check` | Documentation references against the tree: paths and links. |",
     "| `docs-drift-check` | Documentation references against the tree: paths and links. |\n"
     "| `docs-terms` | Accept/reject glossary and canonical spelling per term. |\n"
     "| `docs-env` | Environment variables against `.env.example` and the docs. |"),
]
for old, new in pairs:
    if text.count(old) != 1:
        raise SystemExit(f"README: {old[:60]!r} aparece {text.count(old)}")
    text = text.replace(old, new)
readme.write_text(text, encoding="utf-8")

docs_index = Path("docs/index.md")
text = docs_index.read_text(encoding="utf-8")
text = text.replace("**12 paquetes, 76 skills.**", "**12 paquetes, 78 skills.**")
text = text.replace("**12 packages, 76 skills.**", "**12 packages, 78 skills.**")
text, count = re.subn(
    r"\| `docs-sync-engine` \| 4 \| `docs-sync-engine` \| `docs-drift-check`, `docs-arch-gen`, `docs-changelog` \|",
    "| `docs-sync-engine` | 6 | `docs-sync-engine` | `docs-drift-check`, `docs-terms`, `docs-env`, `docs-arch-gen`, `docs-changelog` |",
    text)
docs_index.write_text(text, encoding="utf-8")

index = json.loads(Path("skills.json").read_text(encoding="utf-8"))
print("filas docs/index:", count, "· total:", index["skills_total"], "· version:", index["version"])
