# Skills IA

> Repositorio universal de habilidades modulares para agentes y asistentes de IA.  
> Universal repository of modular skills for AI agents and assistants.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice
1. [Visión General](#visión-general)
2. [Módulos y Sub-skills](#módulos-y-sub-skills)
3. [Estructura Estándar de cada Paquete](#estructura-estándar-de-cada-paquete)
4. [Documentación Técnica](#documentación-técnica)
5. [Requisitos y Filosofía de Cero Dependencias](#requisitos-y-filosofía-de-cero-dependencias)
6. [Licencia](#licencia)

### Visión General
**Skills IA** es una colección de habilidades modulares, deterministas e independientes diseñadas para ser integradas en cualquier asistente de Inteligencia Artificial (Claude, Gemini, ChatGPT, Antigravity, Cursor, etc.). Cada habilidad es autosuficiente y opera sin alterar paquetes globales ni requerir dependencias complejas.

Cada carpeta es un **paquete**: una skill maestra que orquesta y, cuando aplica, varias sub-skills con un corte de uso real. Se instalan juntas y comparten assets sin duplicarlos. El índice máquina-legible está en [`skills.json`](skills.json): 5 paquetes, 28 skills.

### Módulos y Sub-skills

| Módulo | Propósito | Skills |
| :--- | :--- | ---: |
| **[`replica`](replica/)** | Reconstrucción funcional *clean-room* de aplicaciones (desde SaaS hasta editores de alta complejidad). | 14 |
| **[`seo-auditor`](seo-auditor/)** | Auditoría SEO técnica, de contenido, datos estructurados, sitemaps y GEO, con rúbrica 0–100 y evidencia reproducible. | 6 |
| **[`agent-red-team`](agent-red-team/)** | Auditoría de seguridad de skills, MCP y carpetas de instrucciones antes de instalarlas. | 3 |
| **[`humanizador-anti-ia`](humanizador-anti-ia/)** | Detección y reescritura de patrones de escritura de IA, con score 0–100 determinista. | 3 |
| **[`premium-web-designer`](premium-web-designer/)** | Diseño y desarrollo de sitios web premium con dirección de arte, UX/UI y QA independiente medible. | 2 |

#### `replica` — maestro + 13 fases

| Sub-skill | Fases | Qué hace |
|---|---|---|
| `replica` | — | Maestro: orquesta, guarda `progreso.md` y pide aprobación fase a fase. |
| `replica-recon` | 0, 1, 1b | Límites, alcance, inventario de funciones con evidencia y apps complejas. |
| `replica-architect` | 2 | Stack, módulos, invariantes y contratos. |
| `replica-design` | 3 | Tokens, componentes y contraste WCAG. |
| `replica-build` | 4 | Construcción por incrementos `must`. |
| `replica-backend` | 5 | Auth, datos, permisos, pagos y jobs. |
| `replica-test` | 6 | Pruebas, invariantes y bugs S1/S2/S3. |
| `replica-diff` | 7 | Paridad funcional y visual con evidencia. |
| `replica-entrepreneur` | 8 | Reseñas reales, temas y plan de mejoras. |
| `replica-brand` | 9 | Rebrand y `sweep.py` a 0. |
| `replica-launch` | 10 | Landing, listing y precios por país. |
| `replica-deploy` | 11 | Preflight, backups y publicación verificada. |
| `replica-static` | 12 (opt-in) | Análisis estático autorizado. |
| `replica-redes` | 13 | Reels, captions y banco de ganchos. |

#### `seo-auditor` — maestro + 5 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `seo-auditor` | Maestro: modos, rúbrica, veredicto y flujo Audit → Plan → Execute. |
| `seo-audit` | Auditoría completa y módulos (index, perf, headers, schema, hreflang, onpage) + `rescore`. |
| `seo-plan` | `PLAN.md` priorizado y borradores `DRAFT`, sin tocar el sitio. |
| `seo-execute` | Aplica con backup `.bak` y verifica con nueva auditoría. |
| `seo-serp` | Simulador de SERP y tarjetas sociales. |
| `seo-compare` | Diff entre auditorías y monitorización. |

#### `agent-red-team` — maestro + 2 sub-skills

| Sub-skill | Qué hace | Escribe ficheros |
|---|---|---|
| `agent-red-team` | Maestro: modo, protocolo 0–5, REJECT, ledger y límites. | — |
| `red-scan` | Escaneo rápido (guidance): veredicto en el chat. | No |
| `red-audit` | Auditoría completa con verificación independiente y ledger. | Sí, los pedidos |

#### `humanizador-anti-ia` — maestro + 2 sub-skills

| Sub-skill | Qué hace | Toca el texto |
|---|---|---|
| `humanizador-anti-ia` | Maestro: modos Quick/Full/Voice, registro y honestidad factual. | — |
| `humanizar` | Reescritura con catálogo de 40 patrones y recorte de relleno. | Sí |
| `detector-ia` | Solo puntuar y detectar. | No |

#### `premium-web-designer` — maestro + 1 sub-skill

| Sub-skill | Qué hace |
|---|---|
| `premium-web-designer` | Maestro: dirección de arte, UX/UI, desarrollo y gates medibles. |
| `premium-qa` | QA independiente: medición en cinco anchos, gates numéricos e informe de entrega. |

### Estructura Estándar de cada Paquete
```text
paquete/
├── SKILL.md              # maestro: orquesta y fija límites
├── sub-skill/SKILL.md    # una por bloque de uso real
├── references/           # compartidas, sin duplicar
├── scripts/              # stdlib de Python, deterministas
├── templates/            # salidas estructuradas
├── tests/                # unittest, sin red
└── skills.json           # array con todas las skills del paquete
```

Cada `SKILL.md` (maestro y sub-skills) lleva frontmatter YAML con `name` y `description` para activación automática. Las sub-skills referencian los assets compartidos con rutas relativas al paquete (`../references/`, `../scripts/`), así que **se instala la carpeta completa**.

### Documentación Técnica
Las guías completas de cada módulo se encuentran en la carpeta [`docs/`](docs/):
- [Índice de Documentación](docs/index.md)
- [Guía de Agent Red Team](docs/agent-red-team.md)
- [Guía de Humanizador Anti-IA](docs/humanizador-anti-ia.md)
- [Guía de Replica](docs/replica.md)
- [Guía de SEO Auditor](docs/seo-auditor.md)
- [Premium Web Designer](docs/premium-web-designer.md)

### Requisitos y Filosofía de Cero Dependencias
- **Python 3.8+** (utiliza únicamente la librería estándar de Python: `argparse`, `re`, `ast`, `math`, `urllib`, `html.parser`, `json`).
- Los tests usan `unittest`; las herramientas de pruebas y calidad (`pytest`, `PyYAML`, `pytest-json-report`, `ruff`) están en el grupo `dev` de `pyproject.toml` y se gestionan con [`uv`](https://docs.astral.sh/uv/).
- Para preparar el entorno `.venv` y ejecutar todos los tests desde la raíz: `uv sync` y `uv run python run_tests.py`.
- GitHub Actions ejecuta todas las suites en cada `push` mediante `.github/workflows/tests.yml`.
- Tests transversales en `tests/`: activación de las 28 skills (frases que deben y no deben activarlas, sin solapamientos entre hermanas) y coherencia maestro/sub-skill: `uv run python run_tests.py`.

### Licencia
Distribuido bajo la [Licencia MIT](LICENSE).

---

## 🇬🇧 English

### Table of Contents
1. [Overview](#overview)
2. [Modules and Sub-skills](#modules-and-sub-skills)
3. [Standard Package Structure](#standard-package-structure)
4. [Technical Documentation](#technical-documentation)
5. [Requirements and Zero-Dependency Philosophy](#requirements-and-zero-dependency-philosophy)
6. [License](#license)

### Overview
**Skills IA** is a collection of modular, deterministic, and self-contained agent skills designed for integration with any AI assistant (Claude, Gemini, ChatGPT, Antigravity, Cursor, etc.). Each skill is independent and operates without modifying global packages or requiring third-party libraries.

Each folder is a **package**: one master skill that orchestrates and, where applicable, sub-skills split by real usage boundaries. Packages share assets without duplication. The machine-readable index is [`skills.json`](skills.json): 5 packages, 28 skills.

### Modules and Sub-skills

| Module | Purpose | Skills |
| :--- | :--- | ---: |
| **[`replica`](replica/)** | Clean-room functional reverse-engineering of software (from SaaS to complex engines like word processors). | 14 |
| **[`seo-auditor`](seo-auditor/)** | Technical, content, structured-data, sitemap and GEO audits with a 0–100 rubric and reproducible evidence. | 6 |
| **[`agent-red-team`](agent-red-team/)** | Security audit of skills, MCP servers and instruction folders before installing them. | 3 |
| **[`humanizador-anti-ia`](humanizador-anti-ia/)** | Detection and rewriting of AI writing patterns with a deterministic 0–100 score. | 3 |
| **[`premium-web-designer`](premium-web-designer/)** | Premium website design and development with art direction, UX/UI and measurable independent QA. | 2 |

#### `replica` — master + 13 phases

| Sub-skill | Phases | Purpose |
|---|---|---|
| `replica` | — | Master: orchestrates, stores `progreso.md` and asks for approval phase by phase. |
| `replica-recon` | 0, 1, 1b | Boundaries, scope, evidence-backed feature inventory and complex apps. |
| `replica-architect` | 2 | Stack, modules, invariants and contracts. |
| `replica-design` | 3 | Tokens, components and WCAG contrast. |
| `replica-build` | 4 | Incremental construction of `must` flows. |
| `replica-backend` | 5 | Auth, data, permissions, payments and jobs. |
| `replica-test` | 6 | Tests, invariants and S1/S2/S3 bugs. |
| `replica-diff` | 7 | Functional and visual parity with evidence. |
| `replica-entrepreneur` | 8 | Real reviews, themes and fix plan. |
| `replica-brand` | 9 | Rebrand and `sweep.py` at 0. |
| `replica-launch` | 10 | Landing, store listing and per-country pricing. |
| `replica-deploy` | 11 | Preflight, backups and verified deployment. |
| `replica-static` | 12 (opt-in) | Authorized static analysis. |
| `replica-redes` | 13 | Reels scripts, captions and hook bank. |

#### `seo-auditor` — master + 5 sub-skills

| Sub-skill | Purpose |
|---|---|
| `seo-auditor` | Master: modes, rubric, verdict and Audit → Plan → Execute flow. |
| `seo-audit` | Full audit plus modules (index, perf, headers, schema, hreflang, onpage) + `rescore`. |
| `seo-plan` | Prioritized `PLAN.md` and `DRAFT` files, without touching the site. |
| `seo-execute` | Applies with `.bak` backups and verifies with a new audit. |
| `seo-serp` | SERP and social-card simulator. |
| `seo-compare` | Audit diff and monitoring. |

#### `agent-red-team` — master + 2 sub-skills

| Sub-skill | Purpose | Writes files |
|---|---|---|
| `agent-red-team` | Master: mode, protocol 0–5, REJECT, ledger and limits. | — |
| `red-scan` | Quick guidance scan: verdict in chat. | No |
| `red-audit` | Full audit with independent verification and ledger. | Only requested ones |

#### `humanizador-anti-ia` — master + 2 sub-skills

| Sub-skill | Purpose | Edits text |
|---|---|---|
| `humanizador-anti-ia` | Master: Quick/Full/Voice modes, register and factual honesty. | — |
| `humanizar` | Rewrite with the 40-pattern catalog and filler trimming. | Yes |
| `detector-ia` | Score and detect only. | No |

#### `premium-web-designer` — master + 1 sub-skill

| Sub-skill | Purpose |
|---|---|
| `premium-web-designer` | Master: art direction, UX/UI, development and measurable gates. |
| `premium-qa` | Independent QA: five-width measurement, numeric gates and delivery report. |

### Standard Package Structure
```text
package/
├── SKILL.md              # master: orchestrates and sets limits
├── sub-skill/SKILL.md    # one per real usage boundary
├── references/           # shared, no duplication
├── scripts/              # deterministic Python stdlib
├── templates/            # structured outputs
├── tests/                # unittest, offline
└── skills.json           # array with every skill in the package
```

Every `SKILL.md` (master and sub-skills) carries YAML frontmatter with `name` and `description` for automatic activation. Sub-skills reference shared assets relative to the package (`../references/`, `../scripts/`), so **install the whole folder**.

### Technical Documentation
Comprehensive module documentation is available in the [`docs/`](docs/) directory:
- [Documentation Index](docs/index.md)
- [Agent Red Team Guide](docs/agent-red-team.md)
- [Humanizador Anti-IA Guide](docs/humanizador-anti-ia.md)
- [Replica Guide](docs/replica.md)
- [SEO Auditor Guide](docs/seo-auditor.md)
- [Premium Web Designer](docs/premium-web-designer.md)

### Requirements and Zero-Dependency Philosophy
- **Python 3.8+** (uses only standard library modules: `argparse`, `re`, `ast`, `math`, `urllib`, `html.parser`, `json`).
- Tests use `unittest`; test and quality tools (`pytest`, `PyYAML`, `pytest-json-report`, `ruff`) are in the `dev` group in `pyproject.toml` and managed by [`uv`](https://docs.astral.sh/uv/).
- Prepare `.venv` and run every test from the repository root with `uv sync` and `uv run python run_tests.py`.
- GitHub Actions runs all suites on every `push` via `.github/workflows/tests.yml`.
- Cross-cutting tests in `tests/`: activation for all 28 skills (phrases that should and should not trigger them, no sibling overlaps) and master/sub-skill coherence: `uv run python run_tests.py`.

### License
Distributed under the [MIT License](LICENSE).
