# Skills IA

> Repositorio universal de habilidades modulares para agentes y asistentes de IA.  
> Universal repository of modular skills for AI agents and assistants.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice

1. [Visión General](#visión-general)
2. [Módulos y Sub-skills](#módulos-y-sub-skills)
3. [Instalación](#instalación)
4. [Estructura Estándar de cada Paquete](#estructura-estándar-de-cada-paquete)
5. [Documentación Técnica](#documentación-técnica)
6. [Requisitos y Filosofía de Cero Dependencias](#requisitos-y-filosofía-de-cero-dependencias)
7. [Licencia](#licencia)

### Visión General

**Skills IA** es una colección de habilidades modulares, deterministas e independientes diseñadas para ser integradas en cualquier asistente de Inteligencia Artificial (Claude, Gemini, ChatGPT, Antigravity, Cursor, etc.). Cada habilidad es autosuficiente y opera sin alterar paquetes globales ni requerir dependencias complejas.

Cada carpeta es un **paquete**: una skill maestra que orquesta y, cuando aplica, varias sub-skills con un corte de uso real. Se instalan juntas y comparten assets sin duplicarlos. El índice máquina-legible está en [`skills.json`](skills.json): 12 paquetes, 79 skills.

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
| **[`finops-auditor`](finops-auditor/)** | Auditoría de costes cloud: recursos huérfanos, sobreaprovisionamiento, derechosizing, coste de LLM, infraestructura como código, CI y diff con guardrails. | 7 |
| **[`db-architect`](db-architect/)** | Auditoría de bases de datos sin motor: esquema, riesgo y bloqueo de migraciones, plan de dos fases, deriva, estilo SQL, consultas N+1 y datos de siembra. | 9 |
| **[`api-contract-guard`](api-contract-guard/)** | Defensa del contrato de API: impacto SemVer, cruce de rutas backend/frontend, cobertura de autenticación y mock local. | 5 |
| **[`refactor-surgeon`](refactor-surgeon/)** | Refactor con red: métricas de complejidad, hotspots por churn, código muerto, detección de clones, ciclos de imports, casos dorados, cortes por grafo de llamadas y verificación. | 9 |
| **[`docs-sync-engine`](docs-sync-engine/)** | Documentación sincronizada con el código: referencias, glosario, variables de entorno, arquitectura regenerable y CHANGELOG. | 6 |

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
| `eval-report` | Informe Markdown o HTML autónomo: fallos con esperado y ganador, colisiones, presupuesto y regresiones frente a la línea base. |

#### `finops-auditor` — maestro + 6 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `finops-auditor` | Maestro: modo, fases, rúbrica y entrega del informe. |
| `finops-scan` | Inventario de recursos, huérfanos, subutilización y anomalías de coste. |
| `finops-rightsize` | Redimensionado con ahorro, riesgo y métrica de verificación. |
| `finops-llm-scan` | Llamadas a APIs de LLM: `max_tokens`, modelo caro como clasificador y bucles de agente sin tope. |
| `finops-infra-scan` | Terraform y Kubernetes: buckets sin ciclo de vida, logs sin retención y contenedores sin límites. |
| `finops-ci-opt` | GitHub Actions: caché de dependencias y ejecución duplicada de push y pull_request. |
| `finops-diff` | Coste entre dos inventarios con guardrails de CI. |

#### `db-architect` — maestro + 8 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `db-architect` | Maestro: modo, fases, severidades y entrega del informe. |
| `db-schema-audit` | Tablas sin clave primaria, claves foráneas sin índice, tipos y restricciones. |
| `db-migration-guard` | `DROP TABLE`, `DROP COLUMN`, columnas obligatorias y ausencia de reversión. |
| `db-expand-contract` | Plan de dos fases expand/contract con avisos de lo no divisible. |
| `db-lock-audit` | Bloqueo y reescritura por operación, con su alternativa segura. |
| `db-drift` | Esquema declarado frente a migraciones reproducidas. |
| `db-sql-lint` | Estilo SQL: clave primaria, `SELECT *`, palabras clave y snake_case. |
| `db-query-trace` | Consultas al ORM dentro de bucles (N+1) con fichero y línea. |
| `db-seed-gen` | Datos de siembra deterministas desde el esquema, con semilla. |

#### `api-contract-guard` — maestro + 4 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `api-contract-guard` | Maestro: ordena diff, cruce y prueba, y firma el veredicto. |
| `api-diff` | Impacto SemVer entre dos contratos OpenAPI. |
| `api-code-sync` | Rutas del backend frente a llamadas del frontend. |
| `api-auth-coverage` | Seguridad del contrato frente a las guardas del código. |
| `api-mock-server` | Servidor mock local con los ejemplos del contrato. |

#### `refactor-surgeon` — maestro + 8 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `refactor-surgeon` | Maestro: medir, congelar, cortar y verificar. |
| `refactor-metrics` | Complejidad `V(G)`, anidamiento, parámetros y mantenibilidad. |
| `refactor-hotspots` | Churn de `git log` × complejidad, con «no medido» explícito. |
| `refactor-harness` | Casos dorados grabados antes y reproducidos después. |
| `refactor-deadcode` | Imports y definiciones privadas que nadie referencia. |
| `refactor-clones` | Duplicación por shingles normalizados del AST. |
| `refactor-cycles` | Ciclos de imports entre módulos, con sus ficheros. |
| `refactor-slice` | Componentes conexas del grafo de llamadas como cortes. |
| `refactor-verify` | Conducta sin cambios contra el snapshot. |

#### `docs-sync-engine` — maestro + 5 sub-skills

| Sub-skill | Qué hace |
|---|---|
| `docs-sync-engine` | Maestro: verificar, regenerar y cerrar la documentación. |
| `docs-drift-check` | Referencias de la doc frente al árbol: rutas y enlaces. |
| `docs-terms` | Glosario accept/reject y grafía canónica de cada término. |
| `docs-env` | Variables de entorno frente a `.env.example` y los documentos. |
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

### Instalación

Cada paquete se instala completo: el maestro, sus sub-skills y los `scripts/` compartidos. Hay tres vías y las tres dan el mismo contenido.

**1. Marketplace de Claude Code** (recomendada: actualiza y versiona sola)

```text
/plugin marketplace add alberto2005-coder/skills-ia
/plugin install db-architect@skills-ia
```

El catálogo vive en [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json): un plugin por paquete, con su versión y la lista de skills, así que `/plugin` instala exactamente lo que publica el tag.

**2. `npx skills` (skills.sh)** para cualquier agente que lea `SKILL.md`

```bash
npx skills add alberto2005-coder/skills-ia --skill db-architect
npx skills add alberto2005-coder/skills-ia --skill seo-auditor --global
```

Instala la carpeta del paquete en la ruta del agente que elijas. No instales una sub-skill suelta: referencia `../scripts/` y `../references/` del paquete.

**3. Descarga del release**, verificada con su checksum

```bash
curl -LO https://github.com/alberto2005-coder/skills-ia/releases/download/db-architect-v2.1.0/db-architect-2.1.0.zip
curl -LO https://github.com/alberto2005-coder/skills-ia/releases/download/db-architect-v2.1.0/SHA256SUMS
sha256sum -c SHA256SUMS --ignore-missing
unzip db-architect-2.1.0.zip -d ~/.claude/skills
rm ~/.claude/skills/manifest.json
```

El zip trae `manifest.json` (paquete, versión, commit y skills) y un prefijo con el nombre del paquete; el `manifest.json` es solo para verificar, no se instala. La versión de los comandos es un ejemplo: sustituye `2.1.0` por la que declare [`db-architect/skills.json`](db-architect/skills.json). El bundle `bundle-v<versión>` publica los 12 paquetes, el `SHA256SUMS` global y el índice `skills.json`.

**Requisito:** Python 3.9+ en el agente que ejecute los `scripts/`. Los `SKILL.md` no necesitan nada.

### Estructura Estándar de cada Paquete

```text
paquete/
├── SKILL.md              # maestro: orquesta y fija límites
├── sub-skill/SKILL.md    # una por bloque de uso real
├── references/           # compartidas — solo si el paquete las necesita
├── scripts/              # stdlib de Python, deterministas
├── templates/            # salidas estructuradas — solo si hacen falta
├── tests/                # unittest, sin red
└── skills.json           # array con todas las skills del paquete
```

Cada `SKILL.md` lleva frontmatter YAML: `name` y `description` son obligatorios (la descripción es la señal de activación) y admite además los campos portables `license`, `allowed-tools`, `compatibility` y `metadata`. Aquí `metadata` lleva `package`, `version` y `author`, y las skills de solo lectura declaran `allowed-tools` con lectura y sus propios scripts. Las sub-skills referencian los assets compartidos con rutas relativas al paquete (`../references/`, `../scripts/`), así que **se instala la carpeta completa**. `scripts/`, `tests/` y `skills.json` están en todos los paquetes; `references/` y `templates/` aparecen solo cuando hay material compartido que merezca separarse.

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
- GitHub Actions ejecuta todas las suites en cada `push` mediante `.github/workflows/tests.yml`, y además un gate de métricas (`tests/metrics_gate.py`) que falla si crecen los hallazgos `high` de `code_metrics` o los clones de `clone_detect`; el techo aceptado vive en `tests/metrics_baseline.json`. Una guardia de versiones (`tests/version_guard.py`) falla si cambia un paquete sin subir su `version` en el manifiesto, y una auditoría de documentación (`tests/audit_docs.py`) falla si los docs citan rutas, flags, recuentos o anclas que ya no cuadran.
- Tests transversales en `tests/`: activación de las 79 skills (frases que deben y no deben activarlas, sin solapamientos entre hermanas) y coherencia maestro/sub-skill: `uv run python run_tests.py`.

### Licencia

Distribuido bajo la [Licencia MIT](LICENSE).

---

## 🇬🇧 English

### Table of Contents

1. [Overview](#overview)
2. [Modules and Sub-skills](#modules-and-sub-skills)
3. [Installation](#installation)
4. [Standard Package Structure](#standard-package-structure)
5. [Technical Documentation](#technical-documentation)
6. [Requirements and Zero-Dependency Philosophy](#requirements-and-zero-dependency-philosophy)
7. [License](#license)

### Overview

**Skills IA** is a collection of modular, deterministic, and self-contained agent skills designed for integration with any AI assistant (Claude, Gemini, ChatGPT, Antigravity, Cursor, etc.). Each skill is independent and operates without modifying global packages or requiring third-party libraries.

Each folder is a **package**: one master skill that orchestrates and, where applicable, sub-skills split by real usage boundaries. Packages share assets without duplication. The machine-readable index is [`skills.json`](skills.json): 12 packages, 79 skills.

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
| **[`finops-auditor`](finops-auditor/)** | Cloud cost audit: orphaned resources, overprovisioning, rightsizing, LLM spend, infrastructure as code, CI and diff with guardrails. | 7 |
| **[`db-architect`](db-architect/)** | Database audit without an engine: schema, migration risk and locking, two-phase plans, drift, SQL style, N+1 queries and seed data. | 9 |
| **[`api-contract-guard`](api-contract-guard/)** | API contract defence: SemVer impact, backend/frontend route sync, authentication coverage and a local mock. | 5 |
| **[`refactor-surgeon`](refactor-surgeon/)** | Refactoring with a safety net: complexity metrics, churn hotspots, dead code, clone detection, import cycles, golden cases, call-graph cuts and verification. | 9 |
| **[`docs-sync-engine`](docs-sync-engine/)** | Documentation synced with the code: references, glossary, environment variables, regenerable architecture and CHANGELOG. | 6 |

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
| `eval-report` | Markdown or standalone HTML report: failures with expected and winner, collisions, context budget and regressions against the baseline. |

#### `finops-auditor` — master + 6 sub-skills

| Sub-skill | Purpose |
|---|---|
| `finops-auditor` | Master: mode, phases, rubric and report delivery. |
| `finops-scan` | Resource inventory, orphans, underutilisation and cost anomalies. |
| `finops-rightsize` | Rightsizing with savings, risk and verification metric. |
| `finops-llm-scan` | LLM API calls: `max_tokens`, expensive model as classifier and unbounded agent loops. |
| `finops-infra-scan` | Terraform and Kubernetes: buckets without lifecycle, logs without retention and containers without limits. |
| `finops-ci-opt` | GitHub Actions: dependency cache and duplicated push and pull_request runs. |
| `finops-diff` | Cost between two inventories with CI guardrails. |

#### `db-architect` — master + 8 sub-skills

| Sub-skill | Purpose |
|---|---|
| `db-architect` | Master: mode, phases, severities and report delivery. |
| `db-schema-audit` | Tables without a primary key, foreign keys without an index, types and constraints. |
| `db-migration-guard` | `DROP TABLE`, `DROP COLUMN`, mandatory columns and missing rollback. |
| `db-expand-contract` | Two-phase expand/contract plan with warnings for what cannot be split. |
| `db-lock-audit` | Locking and rewrite per operation, with its safe alternative. |
| `db-drift` | Declared schema against replayed migrations. |
| `db-sql-lint` | SQL style: primary key, `SELECT *`, keywords and snake_case. |
| `db-query-trace` | ORM queries inside loops (N+1) with file and line. |
| `db-seed-gen` | Deterministic seed data from the schema, with a seed. |

#### `api-contract-guard` — master + 4 sub-skills

| Sub-skill | Purpose |
|---|---|
| `api-contract-guard` | Master: orders diff, sync and test, then signs the verdict. |
| `api-diff` | SemVer impact between two OpenAPI contracts. |
| `api-code-sync` | Backend routes against frontend calls. |
| `api-auth-coverage` | Contract security against the guards in the code. |
| `api-mock-server` | Local mock server serving the contract examples. |

#### `refactor-surgeon` — master + 8 sub-skills

| Sub-skill | Purpose |
|---|---|
| `refactor-surgeon` | Master: measure, freeze, cut and verify. |
| `refactor-metrics` | `V(G)` complexity, nesting, parameters and maintainability. |
| `refactor-hotspots` | `git log` churn × complexity, with an explicit "not measured". |
| `refactor-harness` | Golden cases recorded before and replayed after. |
| `refactor-deadcode` | Imports and private definitions nothing references. |
| `refactor-clones` | Duplication by normalised AST shingles. |
| `refactor-cycles` | Import cycles between modules, with their files. |
| `refactor-slice` | Connected components of the call graph as cuts. |
| `refactor-verify` | Unchanged behaviour against the snapshot. |

#### `docs-sync-engine` — master + 5 sub-skills

| Sub-skill | Purpose |
|---|---|
| `docs-sync-engine` | Master: verify, regenerate and close the documentation. |
| `docs-drift-check` | Doc references against the tree: paths and links. |
| `docs-terms` | Accept/reject glossary and canonical spelling per term. |
| `docs-env` | Environment variables against `.env.example` and the docs. |
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

### Installation

Every package installs as a whole: the master skill, its sub-skills and the shared `scripts/`. All three routes deliver the same content.

**1. Claude Code marketplace** (recommended: updates and versioning come for free)

```text
/plugin marketplace add alberto2005-coder/skills-ia
/plugin install db-architect@skills-ia
```

The catalogue lives in [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json): one plugin per package, with its version and skill list, so `/plugin` installs exactly what the tag publishes.

**2. `npx skills` (skills.sh)** for any agent that reads `SKILL.md`

```bash
npx skills add alberto2005-coder/skills-ia --skill db-architect
npx skills add alberto2005-coder/skills-ia --skill seo-auditor --global
```

It installs the package folder into the route of the agent you pick. Do not install a sub-skill on its own: it references the package's `../scripts/` and `../references/`.

**3. Release download**, verified against its checksum

```bash
curl -LO https://github.com/alberto2005-coder/skills-ia/releases/download/db-architect-v2.1.0/db-architect-2.1.0.zip
curl -LO https://github.com/alberto2005-coder/skills-ia/releases/download/db-architect-v2.1.0/SHA256SUMS
sha256sum -c SHA256SUMS --ignore-missing
unzip db-architect-2.1.0.zip -d ~/.claude/skills
rm ~/.claude/skills/manifest.json
```

The zip carries a `manifest.json` (package, version, commit and skills) and a prefix with the package name; `manifest.json` is only for verification, do not install it. The version in the commands is an example: replace `2.1.0` with the one declared in [`db-architect/skills.json`](db-architect/skills.json). The `bundle-v<version>` release publishes all 12 packages, the global `SHA256SUMS` and the `skills.json` index.

**Requirement:** Python 3.9+ in the agent that runs the `scripts/`. The `SKILL.md` files need nothing.

### Standard Package Structure

```text
package/
├── SKILL.md              # master: orchestrates and sets limits
├── sub-skill/SKILL.md    # one per real usage boundary
├── references/           # shared — only when the package needs them
├── scripts/              # deterministic Python stdlib
├── templates/            # structured outputs — only when needed
├── tests/                # unittest, offline
└── skills.json           # array with every skill in the package
```

Every `SKILL.md` carries YAML frontmatter: `name` and `description` are required (the description is the activation signal), plus the portable `license`, `allowed-tools`, `compatibility` and `metadata` fields. Here `metadata` holds `package`, `version` and `author`, and read-only skills declare `allowed-tools` with read access plus their own scripts. Sub-skills reference shared assets relative to the package (`../references/`, `../scripts/`), so **install the whole folder**. `scripts/`, `tests/` and `skills.json` are present in every package; `references/` and `templates/` appear only when there is shared material worth splitting out.

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
- GitHub Actions runs all suites on every `push` via `.github/workflows/tests.yml`, plus a metrics gate (`tests/metrics_gate.py`) that fails when `code_metrics` `high` findings or `clone_detect` clones grow; the accepted ceiling lives in `tests/metrics_baseline.json`. A version guard (`tests/version_guard.py`) fails when a package changes without bumping its `version` in the manifest, and a documentation audit (`tests/audit_docs.py`) fails when the docs cite paths, flags, counts or anchors that no longer match.
- Cross-cutting tests in `tests/`: activation for all 79 skills (phrases that should and should not trigger them, no sibling overlaps) and master/sub-skill coherence: `uv run python run_tests.py`.

### License

Distributed under the [MIT License](LICENSE).
