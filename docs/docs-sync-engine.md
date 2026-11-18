# Docs Sync Engine

> Documentación pegada al código: referencias verificadas, arquitectura regenerable y CHANGELOG armado desde los commits.
> Documentation glued to the code: verified references, regenerable architecture and a CHANGELOG built from commits.

[Español](#español) · [English](#english)

---

## Español

### Índice
1. Propósito
2. Modos
3. Arquitectura
4. Referencias
5. Herramientas
6. Instalación y uso
7. Tests
8. Límites

### Propósito
`docs-sync-engine` evita que la documentación mienta. Comprueba que cada ruta citada exista, regenera la tabla de arquitectura desde los AST y arma el CHANGELOG desde los commits convencionales. Nada se reescribe a mano: si el borrador difiere del documento vigente, manda el código.

### Modos
El maestro no usa flags: el alcance de la petición fija las fases.

| Modo | Fases | Entrega |
|---|---|---|
| **Verificación** | `docs-drift-check` | Referencias rotas con fichero y línea |
| **Terminología** | `docs-terms` | Términos rechazados y grafías no canónicas |
| **Entorno** | `docs-env` | Variables sin ejemplo o sin documentar |
| **Arquitectura** | `docs-arch-gen` | Borrador con módulos, responsabilidades y comando de regeneración |
| **Release** | `docs-changelog` | CHANGELOG agrupado por tipo y versión |

### Arquitectura
Un maestro y cinco sub-skills con scripts compartidos. Se instala la carpeta completa.

| Sub-skill | Qué hace |
|---|---|
| `docs-sync-engine` | Maestro: verifica, regenera y cierra la documentación |
| `docs-drift-check` | Rutas entre backticks y enlaces relativos contra el árbol |
| `docs-terms` | Glosario accept/reject y grafía canónica |
| `docs-env` | Variables de entorno frente a `.env.example` y los documentos |
| `docs-arch-gen` | Tabla de módulos desde docstrings y funciones de entrada |
| `docs-changelog` | Agrupa commits convencionales por sección |

### Referencias
Se revisan dos formas de cita:

| Origen | Ejemplo |
|---|---|
| Rutas entre backticks | `` `pkg/scripts/x.py` `` |
| Enlaces relativos | `[guía](../docs-sync-engine/SKILL.md)` |
| Enlaces externos | Se ignoran |

Una referencia sin fichero se reporta con severidad alta y la línea exacta. Las guías históricas que citan rutas antiguas a propósito se excluyen con `--exclude`.

### Herramientas

```bash
py docs-sync-engine/scripts/docs_drift.py --docs docs/ --root . --json
py docs-sync-engine/scripts/terms_check.py --path docs/ --accept accept.txt --reject reject.txt --json
py docs-sync-engine/scripts/env_check.py --path src/ --env-example .env.example --docs README.md --json
py docs-sync-engine/scripts/arch_gen.py --root db-architect --out docs/arquitectura.md --title "Arquitectura"
py docs-sync-engine/scripts/changelog_gen.py --range v3.1.0..HEAD --version 3.2.0 --out CHANGELOG.md
```

El cuarto script de la familia es el propio lint del repositorio, que comparte la comprobación de enlaces. Salida del drift:

```json
{
  "findings": [
    {"file": "docs/guia.md", "line": 42, "rule": "referencia-rota", "severity": "high", "message": "la doc cita pkg/falta.py, que no existe"}
  ],
  "by_severity": {"low": 0, "medium": 0, "high": 1}
}
```

Códigos de salida: `0` limpio · `1` umbral superado · `2` ruta o entrada ilegible. Sin red: `changelog_gen.py` lee `git log` local o un fichero de commits.

### Instalación y uso
Copia la carpeta `docs-sync-engine/` completa. Ejemplos de petición:
- «Comprueba que la documentación no cita ficheros que ya no existen».
- «Regenera el documento de arquitectura del paquete».
- «Arma el CHANGELOG de esta release desde los commits».
- «Revisa las referencias antes de publicar la doc».

### Tests

```bash
uv run python -m unittest discover -s docs-sync-engine/tests -t docs-sync-engine/tests
```

27 pruebas: referencia existente limpia, referencia ausente detectada con su línea, enlaces externos ignorados, ruta de docs inexistente, tabla de arquitectura con docstring y entradas, módulos de `tests/` excluidos, escritura a fichero, commits agrupados por tipo, commits sin convención en `Otros`, entrada vacía, fichero de commits ausente, y dieciséis del glosario (documento limpio, término rechazado con su reemplazo, grafía no canónica, bloques y código en línea ignorados, `--fail-on none`, documento y glosario ausentes) y de entorno (variable consistente, sin ejemplo, sin documentar, ejemplo sin uso, `process.env`, `import.meta.env`, `--fail-on none` y ruta ausente).

### Límites
El drift comprueba existencia, no contenido: un comando obsoleto dentro de un fichero existente sigue pasando. No resuelve anclas (`#seccion`) ni rutas absolutas. `arch_gen` solo lee docstrings de módulo de Python e ignora las carpetas de entorno y `tests/`; no dibuja diagramas ni describe el flujo entre módulos. `changelog_gen` no calcula la versión: la recibe y no la deduce de los commits.

---

## English

### Index
1. Purpose
2. Modes
3. Architecture
4. References
5. Tools
6. Install and use
7. Tests
8. Limits

### Purpose
`docs-sync-engine` keeps documentation from lying. It checks that every cited path exists, regenerates the architecture table from the ASTs and builds the CHANGELOG from conventional commits. Nothing is rewritten by hand: if the draft differs from the document in force, the code wins.

### Modes
The master takes no flags: the request's scope sets the phases.

| Mode | Phases | Deliverable |
|---|---|---|
| **Verification** | `docs-drift-check` | Broken references with file and line |
| **Terminology** | `docs-terms` | Rejected terms and non-canonical spellings |
| **Environment** | `docs-env` | Variables without an example or without docs |
| **Architecture** | `docs-arch-gen` | Draft with modules, responsibilities and regeneration command |
| **Release** | `docs-changelog` | CHANGELOG grouped by type and version |

### Architecture
One master and five sub-skills with shared scripts. The whole folder is installed.

| Sub-skill | What it does |
|---|---|
| `docs-sync-engine` | Master: verify, regenerate and close the documentation |
| `docs-drift-check` | Backticked paths and relative links against the tree |
| `docs-terms` | Accept/reject glossary and canonical spelling |
| `docs-env` | Environment variables against `.env.example` and the docs |
| `docs-arch-gen` | Module table from docstrings and entry functions |
| `docs-changelog` | Groups conventional commits by section |

### References
Two kinds of citation are checked:

| Source | Example |
|---|---|
| Backticked paths | `` `pkg/scripts/x.py` `` |
| Relative links | `[guide](../docs-sync-engine/SKILL.md)` |
| External links | Ignored |

A reference with no file is reported as high severity with its exact line. Historical guides that cite old paths on purpose are excluded with `--exclude`.

### Tools

```bash
py docs-sync-engine/scripts/docs_drift.py --docs docs/ --root . --json
py docs-sync-engine/scripts/terms_check.py --path docs/ --accept accept.txt --reject reject.txt --json
py docs-sync-engine/scripts/env_check.py --path src/ --env-example .env.example --docs README.md --json
py docs-sync-engine/scripts/arch_gen.py --root db-architect --out docs/arquitectura.md --title "Arquitectura"
py docs-sync-engine/scripts/changelog_gen.py --range v3.1.0..HEAD --version 3.2.0 --out CHANGELOG.md
```

The repository lint is the fourth member of the family and shares the link check. Drift output:

```json
{
  "findings": [
    {"file": "docs/guia.md", "line": 42, "rule": "referencia-rota", "severity": "high", "message": "la doc cita pkg/falta.py, que no existe"}
  ],
  "by_severity": {"low": 0, "medium": 0, "high": 1}
}
```

Exit codes: `0` clean · `1` threshold exceeded · `2` unreadable path or input. Offline: `changelog_gen.py` reads local `git log` or a commits file.

### Install and use
Copy the whole `docs-sync-engine/` folder. Example requests:
- "Check the docs do not cite files that no longer exist".
- "Regenerate the package architecture document".
- "Build this release's CHANGELOG from the commits".
- "Review the references before publishing the docs".

### Tests

```bash
uv run python -m unittest discover -s docs-sync-engine/tests -t docs-sync-engine/tests
```

27 tests: existing reference clean, missing reference detected with its line, external links ignored, missing docs path, architecture table with docstring and entries, `tests/` modules excluded, writing to a file, commits grouped by type, commits without convention under `Otros`, empty entry, missing commits file, and sixteen for the glossary (clean document, rejected term with its replacement, non-canonical spelling, code fences and inline code ignored, `--fail-on none`, missing document and glossary) and for the environment check (consistent variable, missing example, missing docs, example without use, `process.env`, `import.meta.env`, `--fail-on none` and missing path).

### Limits
Drift checks existence, not content: an obsolete command inside an existing file still passes. It resolves neither anchors (`#section`) nor absolute paths. `arch_gen` reads Python module docstrings only and ignores environment folders and `tests/`; it draws no diagrams and describes no data flow. `changelog_gen` does not compute the version: it receives it instead of inferring it from commits.
