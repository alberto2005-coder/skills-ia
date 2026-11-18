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

Cada carpeta es un **paquete**: una skill maestra que orquesta y, cuando aplica, varias sub-skills con un corte de uso real. Se instalan juntas y comparten assets sin duplicarlos. El índice máquina-legible está en [`skills.json`](skills.json): 12 paquetes, 67 skills.

### Módulos y Sub-skills

| Módulo | Propósito | Skills |
| :--- | :--- | ---: |
| **[`replica`](replica/)** | Reconstrucción funcional *clean-room* de aplicaciones (desde SaaS hasta editores de alta complejidad). | 14 |
| **[`seo-auditor`](seo-auditor/)** | Auditoría SEO técnica, de contenido, datos estructurados, sitemaps y GEO, con rúbrica 0–100 y evidencia reproducible. | 6 |
| **[`appsec-audit`](appsec-audit/)** | Auditoría de ciberseguridad integral: código, APIs, infraestructura, cloud y LLM, con tribunal de validación, nota A–F, modelo de amenazas, dependencias, CI, remediación y escala. | 11 |
| **[`agent-red-team`](agent-red-team/)** | Auditoría de seguridad de skills, MCP y carpetas de instrucciones antes de instalarlas. | 3 |
| **[`humanizador-anti-ia`](humanizador-anti-ia/)** | Detección y reescritura de patrones de escritura de IA, con score 0–100 determinista. | 3 |
| **[`premium-web-designer`](premium-web-designer/)** | Diseño y desarrollo de sitios web premium con dirección de arte, UX/UI y QA independiente medible. | 2 |
| **[`skill-evals`](skill-evals/)** | Evaluación offline de skills: casos, triggers, colisiones, presupuesto de contexto y veredicto reproducible. | 4 |
| **[`finops-auditor`](finops-auditor/)** | Auditoría de costes cloud: recursos huérfanos, sobreaprovisionamiento, derechosizing, coste de LLM, infraestructura como código y CI. | 6 |
| **[`db-architect`](db-architect/)** | Auditoría de bases de datos sin motor: esquema, riesgo de migraciones, consultas N+1 y datos de siembra. | 5 |
| **[`api-contract-guard`](api-contract-guard/)** | Defensa del contrato de API: impacto SemVer, cruce de rutas backend/frontend y mock local. | 4 |
| **[`refactor-surgeon`](refactor-surgeon/)** | Refactor con red: métricas de complejidad, casos dorados, cortes por grafo de llamadas y verificación. | 5 |
| **[`docs-sync-engine`](docs-sync-engine/)** | Documentación sincronizada con el código: referencias, arquitectura regenerable y CHANGELOG. | 4 |

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

#### `appsec-audit` — maestro + 10 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `appsec-audit` | Maestro: alcance, dos fases, regla cero, severidad y entrega del informe. |
| `appsec-recon` | Autorización, activos, superficie de ataque, dependencias y secretos. |
| `appsec-code` | Trazado fuente→sumidero, control de acceso, cripto y lógica de negocio. |
| `appsec-infra` | Docker, Kubernetes, Terraform, cloud, IAM y CI/CD. |
| `appsec-llm` | OWASP LLM Top 10, agentes, MCP y RAG. |
| `appsec-report` | Tribunal con confianza 1–10, nota A–F, diffs y resumen ejecutivo. |
| `appsec-threat` | Modelo de amenazas, límites de confianza, OWASP 2025 y ASVS 5.0. |
| `appsec-deps` | SBOM CycloneDX, CVEs por componente y alcanzabilidad por imports. |
| `appsec-ci` | Workflow de CI, agente revisor, SARIF y `--fail-on`. |
| `appsec-fix` | Remediación con aprobación, sandbox y variantes. |
| `appsec-scale` | Multi-repo, proveedores, topología y coste. |

#### `skill-evals` — maestro + 3 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `skill-evals` | Maestro: diseño de casos, ejecución, puertas, comparación e informe. |
| `eval-design` | Casos desde `phrases.json`, límites, cobertura y split train/test. |
| `eval-run` | Precisión, recall, MRR, colisiones, presupuesto, regresiones y puertas. |

#### `finops-auditor` — maestro + 5 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `finops-auditor` | Maestro: modo, fases, rúbrica y entrega del informe. |
| `finops-scan` | Inventario de recursos, huérfanos, subutilización y anomalías de coste. |
| `finops-rightsize` | Redimensionado con ahorro, riesgo y métrica de verificación. |
| `finops-llm-scan` | Llamadas a APIs de LLM: `max_tokens`, modelo caro como clasificador y bucles de agente sin tope. |
| `finops-infra-scan` | Terraform y Kubernetes: buckets sin ciclo de vida, logs sin retención y contenedores sin límites. |
| `finops-ci-opt` | GitHub Actions: caché de dependencias y ejecución duplicada de push y pull_request. |

#### `db-architect` — maestro + 4 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `db-architect` | Maestro: modo, fases, severidades y entrega del informe. |
| `db-schema-audit` | Tablas sin clave primaria, claves foráneas sin índice, tipos y restricciones. |
| `db-migration-guard` | `DROP TABLE`, `DROP COLUMN`, columnas obligatorias y ausencia de reversión. |
| `db-query-trace` | Consultas al ORM dentro de bucles (N+1) con fichero y línea. |
| `db-seed-gen` | Datos de siembra deterministas desde el esquema, con semilla. |

#### `api-contract-guard` — maestro + 3 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `api-contract-guard` | Maestro: ordena diff, cruce y prueba, y firma el veredicto. |
| `api-diff` | Impacto SemVer entre dos contratos OpenAPI. |
| `api-code-sync` | Rutas del backend frente a llamadas del frontend. |
| `api-mock-server` | Servidor mock local con los ejemplos del contrato. |

#### `refactor-surgeon` — maestro + 4 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `refactor-surgeon` | Maestro: medir, congelar, cortar y verificar. |
| `refactor-metrics` | Complejidad `V(G)`, anidamiento, parámetros y mantenibilidad. |
| `refactor-harness` | Casos dorados grabados antes y reproducidos después. |
| `refactor-slice` | Componentes conexas del grafo de llamadas como cortes. |
| `refactor-verify` | Conducta sin cambios contra el snapshot. |

#### `docs-sync-engine` — maestro + 3 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `docs-sync-engine` | Maestro: verificar, regenerar y cerrar la documentación. |
| `docs-drift-check` | Referencias de la doc frente al árbol: rutas y enlaces. |
| `docs-arch-gen` | Borrador de arquitectura desde docstrings y entradas. |
| `docs-changelog` | CHANGELOG agrupado desde commits convencionales. |

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
- [Guía de AppSec Audit](docs/appsec-audit.md)
- [Guía de SEO Auditor](docs/seo-auditor.md)
- [Premium Web Designer](docs/premium-web-designer.md)
- [Guía de FinOps Auditor](docs/finops-auditor.md)
- [Guía de DB Architect](docs/db-architect.md)
- [Guía de API Contract Guard](docs/api-contract-guard.md)
- [Guía de Refactor Surgeon](docs/refactor-surgeon.md)
- [Guía de Docs Sync Engine](docs/docs-sync-engine.md)
- [Guía de Skill Evals](docs/skill-evals.md)

### Requisitos y Filosofía de Cero Dependencias
- **Python 3.9+** (utiliza únicamente la librería estándar de Python: `argparse`, `re`, `ast`, `math`, `urllib`, `html.parser`, `json`).
- Los tests usan `unittest`; las herramientas de pruebas y calidad (`pytest`, `PyYAML`, `pytest-json-report`, `ruff`) están en el grupo `dev` de `pyproject.toml` y se gestionan con [`uv`](https://docs.astral.sh/uv/).
- Para preparar el entorno `.venv` y ejecutar todos los tests desde la raíz: `uv sync` y `uv run python run_tests.py`.
- GitHub Actions ejecuta todas las suites en cada `push` mediante `.github/workflows/tests.yml`.
- Tests transversales en `tests/`: activación de las 67 skills (frases que deben y no deben activarlas, sin solapamientos entre hermanas) y coherencia maestro/sub-skill: `uv run python run_tests.py`.

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

Each folder is a **package**: one master skill that orchestrates and, where applicable, sub-skills split by real usage boundaries. Packages share assets without duplication. The machine-readable index is [`skills.json`](skills.json): 12 packages, 67 skills.

### Modules and Sub-skills

| Module | Purpose | Skills |
| :--- | :--- | ---: |
| **[`replica`](replica/)** | Clean-room functional reverse-engineering of software (from SaaS to complex engines like word processors). | 14 |
| **[`seo-auditor`](seo-auditor/)** | Technical, content, structured-data, sitemap and GEO audits with a 0–100 rubric and reproducible evidence. | 6 |
| **[`appsec-audit`](appsec-audit/)** | End-to-end security audit of code, APIs, infrastructure, cloud and LLM systems, with a validation tribunal, an A–F grade, threat modelling, dependencies, CI, remediation and scale. | 11 |
| **[`agent-red-team`](agent-red-team/)** | Security audit of skills, MCP servers and instruction folders before installing them. | 3 |
| **[`humanizador-anti-ia`](humanizador-anti-ia/)** | Detection and rewriting of AI writing patterns with a deterministic 0–100 score. | 3 |
| **[`premium-web-designer`](premium-web-designer/)** | Premium website design and development with art direction, UX/UI and measurable independent QA. | 2 |
| **[`skill-evals`](skill-evals/)** | Offline skill evaluation: cases, triggers, collisions, context budget and a reproducible verdict. | 4 |
| **[`finops-auditor`](finops-auditor/)** | Cloud cost audit: orphaned resources, overprovisioning, rightsizing, LLM spend, infrastructure as code and CI. | 6 |
| **[`db-architect`](db-architect/)** | Database audit without an engine: schema, migration risk, N+1 queries and seed data. | 5 |
| **[`api-contract-guard`](api-contract-guard/)** | API contract defence: SemVer impact, backend/frontend route sync and a local mock. | 4 |
| **[`refactor-surgeon`](refactor-surgeon/)** | Refactoring with a safety net: complexity metrics, golden cases, call-graph cuts and verification. | 5 |
| **[`docs-sync-engine`](docs-sync-engine/)** | Documentation synced with the code: references, regenerable architecture and CHANGELOG. | 4 |

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

#### `appsec-audit` — master + 10 sub-skills

| Sub-skill | Purpose |
|---|---|
| `appsec-audit` | Master: scope, two phases, zero rule, severity and report delivery. |
| `appsec-recon` | Authorization, assets, attack surface, dependencies and secrets. |
| `appsec-code` | Source-to-sink tracing, access control, crypto and business logic. |
| `appsec-infra` | Docker, Kubernetes, Terraform, cloud, IAM and CI/CD. |
| `appsec-llm` | OWASP LLM Top 10, agents, MCP and RAG. |
| `appsec-report` | 1–10 confidence tribunal, A–F grade, diffs and executive summary. |
| `appsec-threat` | Threat model, trust boundaries, OWASP 2025 and ASVS 5.0. |
| `appsec-deps` | CycloneDX SBOM, per-component CVEs and import reachability. |
| `appsec-ci` | CI workflow, review agent, SARIF and `--fail-on`. |
| `appsec-fix` | Remediation with approval, sandbox and variants. |
| `appsec-scale` | Multi-repo, vendors, topology and cost. |

#### `skill-evals` — master + 3 sub-skills

| Sub-skill | Purpose |
|---|---|
| `skill-evals` | Master: case design, run, gates, baseline comparison and report. |
| `eval-design` | Cases from `phrases.json`, boundary cases, coverage and train/test split. |
| `eval-run` | Precision, recall, MRR, collisions, budget, regressions and gates. |

#### `finops-auditor` — master + 5 sub-skills

| Sub-skill | Purpose |
|---|---|
| `finops-auditor` | Master: mode, phases, rubric and report delivery. |
| `finops-scan` | Resource inventory, orphans, underutilisation and cost anomalies. |
| `finops-rightsize` | Rightsizing with savings, risk and verification metric. |
| `finops-llm-scan` | LLM API calls: `max_tokens`, expensive model as classifier and unbounded agent loops. |
| `finops-infra-scan` | Terraform and Kubernetes: buckets without lifecycle, logs without retention and containers without limits. |
| `finops-ci-opt` | GitHub Actions: dependency cache and duplicated push and pull_request runs. |

#### `db-architect` — master + 4 sub-skills

| Sub-skill | Purpose |
|---|---|
| `db-architect` | Master: mode, phases, severities and report delivery. |
| `db-schema-audit` | Tables without a primary key, foreign keys without an index, types and constraints. |
| `db-migration-guard` | `DROP TABLE`, `DROP COLUMN`, mandatory columns and missing rollback. |
| `db-query-trace` | ORM queries inside loops (N+1) with file and line. |
| `db-seed-gen` | Deterministic seed data from the schema, with a seed. |

#### `api-contract-guard` — master + 3 sub-skills

| Sub-skill | Purpose |
|---|---|
| `api-contract-guard` | Master: orders diff, sync and test, then signs the verdict. |
| `api-diff` | SemVer impact between two OpenAPI contracts. |
| `api-code-sync` | Backend routes against frontend calls. |
| `api-mock-server` | Local mock server serving the contract examples. |

#### `refactor-surgeon` — master + 4 sub-skills

| Sub-skill | Purpose |
|---|---|
| `refactor-surgeon` | Master: measure, freeze, cut and verify. |
| `refactor-metrics` | `V(G)` complexity, nesting, parameters and maintainability. |
| `refactor-harness` | Golden cases recorded before and replayed after. |
| `refactor-slice` | Connected components of the call graph as cuts. |
| `refactor-verify` | Unchanged behaviour against the snapshot. |

#### `docs-sync-engine` — master + 3 sub-skills

| Sub-skill | Purpose |
|---|---|
| `docs-sync-engine` | Master: verify, regenerate and close the documentation. |
| `docs-drift-check` | Doc references against the tree: paths and links. |
| `docs-arch-gen` | Architecture draft from docstrings and entry functions. |
| `docs-changelog` | CHANGELOG grouped from conventional commits. |

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
- [AppSec Audit Guide](docs/appsec-audit.md)
- [SEO Auditor Guide](docs/seo-auditor.md)
- [Premium Web Designer](docs/premium-web-designer.md)
- [FinOps Auditor Guide](docs/finops-auditor.md)
- [DB Architect Guide](docs/db-architect.md)
- [API Contract Guard Guide](docs/api-contract-guard.md)
- [Refactor Surgeon Guide](docs/refactor-surgeon.md)
- [Docs Sync Engine Guide](docs/docs-sync-engine.md)
- [Skill Evals Guide](docs/skill-evals.md)

### Requirements and Zero-Dependency Philosophy
- **Python 3.9+** (uses only standard library modules: `argparse`, `re`, `ast`, `math`, `urllib`, `html.parser`, `json`).
- Tests use `unittest`; test and quality tools (`pytest`, `PyYAML`, `pytest-json-report`, `ruff`) are in the `dev` group in `pyproject.toml` and managed by [`uv`](https://docs.astral.sh/uv/).
- Prepare `.venv` and run every test from the repository root with `uv sync` and `uv run python run_tests.py`.
- GitHub Actions runs all suites on every `push` via `.github/workflows/tests.yml`.
- Cross-cutting tests in `tests/`: activation for all 67 skills (phrases that should and should not trigger them, no sibling overlaps) and master/sub-skill coherence: `uv run python run_tests.py`.

### License
Distributed under the [MIT License](LICENSE).
