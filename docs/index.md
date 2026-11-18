# Índice de Documentación / Documentation Index

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice
1. [Guías de Paquetes](#guías-de-paquetes)
2. [Paquetes y Sub-skills](#paquetes-y-sub-skills)
3. [Estructura de un Paquete](#estructura-de-un-paquete)
4. [Tests](#tests)
5. [Reglas de Seguridad y Ejecución](#reglas-de-seguridad-y-ejecución)

### Guías de Paquetes
- [**Agent Red Team**](agent-red-team.md): auditoría de seguridad de skills, MCP y carpetas de instrucciones, con escaneo rápido y auditoría completa verificada.
- [**Humanizador Anti-IA**](humanizador-anti-ia.md): detección y reescritura de patrones de escritura de IA, con catálogo de 40 patrones y score 0–100 determinista.
- [**Replica**](replica.md): reconstrucción funcional *clean-room* por fases, con evidencia obligatoria, paridad y rebrand.
- [**SEO Auditor**](seo-auditor.md): auditoría SEO/GEO con rúbrica 0–100, simulador de SERP y evidencia reproducible.
- [**AppSec Audit**](appsec-audit.md): auditoría de ciberseguridad integral con trazado fuente→sumidero, tribunal de validación, nota A–F y parches en diff.
- [**Premium Web Designer**](premium-web-designer.md): diseño y desarrollo de sitios web premium con dirección de arte, UX/UI y QA independiente.

### Paquetes y Sub-skills
**8 paquetes, 46 skills.** El índice máquina-legible está en [`skills.json`](../skills.json).

| Paquete | Skills | Maestro | Sub-skills |
|---|---:|---|---|
| `replica` | 14 | `replica` | `replica-recon` (0-1b), `replica-architect`, `replica-design`, `replica-build`, `replica-backend`, `replica-test`, `replica-diff`, `replica-entrepreneur`, `replica-brand`, `replica-launch`, `replica-deploy`, `replica-static`, `replica-redes` |
| `seo-auditor` | 6 | `seo-auditor` | `seo-audit`, `seo-plan`, `seo-execute`, `seo-serp`, `seo-compare` |
| `appsec-audit` | 11 | `appsec-audit` | `appsec-recon`, `appsec-code`, `appsec-infra`, `appsec-llm`, `appsec-threat`, `appsec-deps`, `appsec-ci`, `appsec-fix`, `appsec-report`, `appsec-scale` |
| `agent-red-team` | 3 | `agent-red-team` | `red-scan`, `red-audit` |
| `humanizador-anti-ia` | 3 | `humanizador-anti-ia` | `humanizar`, `detector-ia` |
| `premium-web-designer` | 2 | `premium-web-designer` | `premium-qa` |
| `skill-evals` | 4 | `skill-evals` | `eval-design`, `eval-run`, `eval-report` |
| `finops-auditor` | 3 | `finops-auditor` | `finops-scan`, `finops-rightsize` |

Cada maestro elige el modo, fija los límites y reparte el trabajo; `premium-web-designer` suma `premium-qa` para auditar webs ya construidas y `appsec-audit` reparte la auditoría entre reconocimiento, código, infraestructura, LLM, amenazas, dependencias, CI, remediación, informe y escala, y `skill-evals` reparte el ciclo entre diseño de casos, ejecución e informe.

### Estructura de un Paquete
```text
paquete/
├── SKILL.md              # maestro: orquesta, decide modo y fija límites
├── <sub-skill>/SKILL.md  # una por bloque de uso real
├── references/           # compartidas por todas las skills del paquete
├── scripts/              # Python stdlib, deterministas, sin red
├── templates/            # salidas estructuradas
├── tests/                # unittest, sin red
└── skills.json           # array con todas las skills del paquete
```

Las sub-skills **no duplican assets**: referencian `../references/`, `../scripts/` y `../templates/`, así que se instala la carpeta completa. Cada `SKILL.md` lleva frontmatter `name` + `description` para activación automática.

### Tests
```bash
uv sync
uv run python run_tests.py
```

### Reglas de Seguridad y Ejecución
1. Todas las herramientas funcionan en modo solo lectura por defecto.
2. No se ejecutan comandos destructivos ni llamadas de red salientes no autorizadas.
3. Compatibilidad con la librería estándar de Python 3.9+ sin `pip install`.

---

## 🇬🇧 English

### Table of Contents
1. [Package Guides](#package-guides)
2. [Packages and Sub-skills](#packages-and-sub-skills)
3. [Package Structure](#package-structure)
4. [Tests](#tests-1)
5. [Safety and Execution Guidelines](#safety-and-execution-guidelines)

### Package Guides
- [**Agent Red Team**](agent-red-team.md): security audit of skills, MCP servers and instruction folders, with quick scan and verified full audit.
- [**Humanizador Anti-IA**](humanizador-anti-ia.md): detection and rewriting of AI writing patterns, with a 40-pattern catalog and a deterministic 0–100 score.
- [**Replica**](replica.md): clean-room functional reconstruction by phases, with mandatory evidence, parity and rebrand.
- [**SEO Auditor**](seo-auditor.md): SEO/GEO audit with a 0–100 rubric, SERP simulator and reproducible evidence.
- [**AppSec Audit**](appsec-audit.md): end-to-end security audit with source-to-sink tracing, a validation tribunal, an A–F grade and diff patches.
- [**Premium Web Designer**](premium-web-designer.md): premium website design and development with art direction, UX/UI and independent QA.

### Packages and Sub-skills
**8 packages, 46 skills.** The machine-readable index lives in [`skills.json`](../skills.json).

| Package | Skills | Master | Sub-skills |
|---|---:|---|---|
| `replica` | 14 | `replica` | `replica-recon` (0-1b), `replica-architect`, `replica-design`, `replica-build`, `replica-backend`, `replica-test`, `replica-diff`, `replica-entrepreneur`, `replica-brand`, `replica-launch`, `replica-deploy`, `replica-static`, `replica-redes` |
| `seo-auditor` | 6 | `seo-auditor` | `seo-audit`, `seo-plan`, `seo-execute`, `seo-serp`, `seo-compare` |
| `appsec-audit` | 11 | `appsec-audit` | `appsec-recon`, `appsec-code`, `appsec-infra`, `appsec-llm`, `appsec-threat`, `appsec-deps`, `appsec-ci`, `appsec-fix`, `appsec-report`, `appsec-scale` |
| `agent-red-team` | 3 | `agent-red-team` | `red-scan`, `red-audit` |
| `humanizador-anti-ia` | 3 | `humanizador-anti-ia` | `humanizar`, `detector-ia` |
| `premium-web-designer` | 2 | `premium-web-designer` | `premium-qa` |
| `skill-evals` | 4 | `skill-evals` | `eval-design`, `eval-run`, `eval-report` |
| `finops-auditor` | 3 | `finops-auditor` | `finops-scan`, `finops-rightsize` |

Each master picks the mode, sets boundaries and splits the work; `premium-web-designer` adds `premium-qa` to audit sites that already exist and `appsec-audit` splits the audit across recon, code, infrastructure, LLM, threats, dependencies, CI, remediation, report and scale, while `skill-evals` splits the loop across case design, run and report.

### Package Structure
```text
package/
├── SKILL.md              # master: orchestrates, picks mode, sets limits
├── <sub-skill>/SKILL.md  # one per real usage block
├── references/           # shared by every skill in the package
├── scripts/              # deterministic Python stdlib, offline
├── templates/            # structured outputs
├── tests/                # unittest, offline
└── skills.json           # array with every skill in the package
```

Sub-skills **do not duplicate assets**: they reference `../references/`, `../scripts/` and `../templates/`, so the whole folder is installed. Every `SKILL.md` carries `name` + `description` frontmatter for automatic activation.

### Tests
```bash
uv sync
uv run python run_tests.py
```

### Safety and Execution Guidelines
1. All tools operate in read-only mode by default.
2. No destructive commands or unauthorized outbound network requests are performed.
3. Python 3.9+ standard library compatibility without `pip install`.
