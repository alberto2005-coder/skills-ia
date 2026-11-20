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
- [**FinOps Auditor**](finops-auditor.md): auditoría de costes cloud con recursos huérfanos, derechosizing, rúbrica 0–100 y ahorro mensual reproducible.
- [**Premium Web Designer**](premium-web-designer.md): diseño y desarrollo de sitios web premium con dirección de arte, UX/UI y QA independiente.
- [**DB Architect**](db-architect.md): auditoría de bases de datos sin motor, con esquema, riesgo de migraciones, consultas N+1 y siembra determinista.
- [**API Contract Guard**](api-contract-guard.md): impacto SemVer de un cambio de contrato, cruce de rutas backend/frontend y mock local.
- [**Refactor Surgeon**](refactor-surgeon.md): refactor con métricas, casos dorados, cortes por grafo de llamadas y verificación de conducta.
- [**Docs Sync Engine**](docs-sync-engine.md): referencias de la documentación verificadas, arquitectura regenerable y CHANGELOG desde commits.
- [**Skill Evals**](skill-evals.md): evaluación offline del catálogo con casos desde frases reales, puertas de precisión/recall/MRR, informe reproducible y optimización de descripciones.

### Paquetes y Sub-skills

**12 paquetes, 79 skills.** El índice máquina-legible está en [`skills.json`](../skills.json).

| Paquete | Skills | Maestro | Sub-skills |
|---|---:|---|---|
| `replica` | 14 | `replica` | `replica-recon` (0-1b), `replica-architect`, `replica-design`, `replica-build`, `replica-backend`, `replica-test`, `replica-diff`, `replica-entrepreneur`, `replica-brand`, `replica-launch`, `replica-deploy`, `replica-static`, `replica-redes` |
| `seo-auditor` | 6 | `seo-auditor` | `seo-audit`, `seo-plan`, `seo-execute`, `seo-serp`, `seo-compare` |
| `appsec-audit` | 11 | `appsec-audit` | `appsec-recon`, `appsec-code`, `appsec-infra`, `appsec-llm`, `appsec-threat`, `appsec-deps`, `appsec-ci`, `appsec-fix`, `appsec-report`, `appsec-scale` |
| `agent-red-team` | 3 | `agent-red-team` | `red-scan`, `red-audit` |
| `humanizador-anti-ia` | 3 | `humanizador-anti-ia` | `humanizar`, `detector-ia` |
| `premium-web-designer` | 2 | `premium-web-designer` | `premium-qa` |
| `skill-evals` | 4 | `skill-evals` | `eval-design`, `eval-run`, `eval-report` |
| `finops-auditor` | 7 | `finops-auditor` | `finops-scan`, `finops-rightsize`, `finops-llm-scan`, `finops-infra-scan`, `finops-ci-opt`, `finops-diff` |
| `db-architect` | 9 | `db-architect` | `db-schema-audit`, `db-migration-guard`, `db-expand-contract`, `db-lock-audit`, `db-drift`, `db-sql-lint`, `db-query-trace`, `db-seed-gen` |
| `api-contract-guard` | 5 | `api-contract-guard` | `api-diff`, `api-code-sync`, `api-auth-coverage`, `api-mock-server` |
| `refactor-surgeon` | 9 | `refactor-surgeon` | `refactor-metrics`, `refactor-hotspots`, `refactor-harness`, `refactor-deadcode`, `refactor-clones`, `refactor-cycles`, `refactor-slice`, `refactor-verify` |
| `docs-sync-engine` | 6 | `docs-sync-engine` | `docs-drift-check`, `docs-terms`, `docs-env`, `docs-arch-gen`, `docs-changelog` |

Cada maestro elige el modo, fija los límites y reparte el trabajo; `premium-web-designer` suma `premium-qa` para auditar webs ya construidas y `appsec-audit` reparte la auditoría entre reconocimiento, código, infraestructura, LLM, amenazas, dependencias, CI, remediación, informe y escala, y `skill-evals` reparte el ciclo entre diseño de casos, ejecución e informe.

### Estructura de un Paquete

```text
paquete/
├── SKILL.md              # maestro: orquesta, decide modo y fija límites
├── <sub-skill>/SKILL.md  # una por bloque de uso real
├── references/           # compartidas — solo si el paquete las necesita
├── scripts/              # Python stdlib, deterministas, sin red
├── templates/            # salidas estructuradas — solo si hacen falta
├── tests/                # unittest, sin red
└── skills.json           # array con todas las skills del paquete
```

Las sub-skills **no duplican assets**: referencian `../references/`, `../scripts/` y `../templates/`, así que se instala la carpeta completa. `scripts/`, `tests/` y `skills.json` están en todos los paquetes; `references/` y `templates/` aparecen solo cuando hay material compartido que merezca separarse. Cada `SKILL.md` lleva frontmatter YAML: `name` y `description` son obligatorios (la descripción es la señal de activación) y admite además los campos portables `license`, `allowed-tools`, `compatibility` y `metadata`. Aquí `metadata` lleva `package`, `version` y `author`, y las skills de solo lectura declaran `allowed-tools` con lectura y sus propios scripts. Si un paquete necesita helpers compartidos, viven en `scripts/<paquete>_util.py`; no hay módulo común entre paquetes, porque cada uno se instala solo.

### Tests

```bash
uv sync
uv run python run_tests.py
uv run pytest -q
uv run ruff check .
uv run python tests/lint_frontmatter.py
uv run python tests/version_guard.py
uv run python tests/metrics_gate.py
uv run python tests/audit_docs.py
```

`tests/lint_frontmatter.py` valida el bloque de cada `SKILL.md` con un parser YAML real (PyYAML, del grupo `dev`), además de `name`, `description`, manifiestos, enlaces relativos, índice y marketplace. La versión de cada paquete sale de su manifiesto y `tests/version_guard.py` falla si un paquete cambia sin subirla, comparando contra el commit anterior. `tests/metrics_gate.py` falla si crecen los hallazgos `high` o los clones respecto al techo de `tests/metrics_baseline.json`. `tests/audit_docs.py` contrasta la documentación con el repo: rutas citadas, flags de cada paquete, tablas de paquetes, cabeceras «maestro + N», recuentos de skills y de tests, y anclas internas. `run_tests.py` la ejecuta también como puerta local al terminar las suites («Resumen: N/M suites y N/M puertas»), así que el comando de siempre cubre el mismo contraste que el job de lint. El contrato común de hallazgos vive en `contracts/findings/`: `emit.py` adapta la salida nativa de `appsec-audit` y `seo-auditor` al esquema `findings.schema.json` v1.0.0, `validate_findings.py` lo valida (con `--fail-on` para CI) y `findings_to_sarif.py` lo exporta a SARIF 2.1.0. GitHub Actions ejecuta las puertas de lint en Python 3.14 y las suites en la matriz 3.9/3.14 sobre Linux, macOS y Windows. El job de lint valida además los workflows con `actionlint` (versión fijada y verificada por checksum), que reproduce el rechazo de GitHub al cargarlos: un `matrix` en un `if` de job invalida el workflow entero. Cada descripción debe declarar su caso de uso («Úsala cuando…») y cubrir los dos idiomas, porque es la única señal de activación automática que leen los agentes. `markdownlint-cli2` es una comprobación local opcional.

### Empaquetado

```bash
make dist                 # todos los paquetes
make dist PACKAGE=replica # uno solo
```

`scripts/build_package.py` genera `dist/<paquete>-<version>.zip` con el paquete completo y un `manifest.json` en la raíz (versión, commit y skills incluidas), más un `.sha256` con formato `sha256sum`. Las entradas van ordenadas y con fecha fija, así que dos builds del mismo árbol dan el mismo hash. Excluye `tests/`, `__pycache__`, `.ruff_cache`, `.venv` y las salidas de auditoría, y rechaza cualquier fichero que no sea texto UTF-8. Antes de dar el zip por bueno lo descomprime en un temporal y le pasa `tests/lint_frontmatter.py`; si falla, borra el artefacto y sale con error.

### Publicación

Publicar es subir la versión, commitear y hacer push; el resto lo hace el workflow.

```bash
uv run --locked python scripts/bump_version.py db-architect 2.1.1  # 1. sube la versión en los cuatro sitios
git add -A && git commit -m "feat(db-architect): ..."             # 2. commit
git push origin main                                              # 3. push
```

`scripts/bump_version.py` mueve a la vez el manifiesto del paquete, el `metadata.version` de sus `SKILL.md`, la entrada del índice raíz y el plugin del marketplace; además sube el índice raíz un parche (la versión del bundle) salvo que se pase `--no-bundle`. Con `--dry-run` enseña los ficheros que tocaría sin escribir nada, y rechaza una versión que no sea `X.Y.Z` o que no sea mayor que la actual. Tocar un paquete sin subir su versión rompe `tests/version_guard.py`, así que este comando es el camino normal.

En cada push a `main`, `tag-release.yml` compara el índice y los manifiestos con el commit anterior (`github.event.before`) y crea un tag `<paquete>-v<version>` por cada subida y `bundle-v<version>` si cambió la versión del índice raíz. Los tags son idempotentes: si ya existen, no se reescriben.

`release-package.yml` (tags `<paquete>-v*`) empaqueta y valida ese paquete, genera las notas en español e inglés con `scripts/release_notes.py` a partir de los commits que tocaron su carpeta y publica el zip y el `SHA256SUMS`. `release-bundle.yml` (tags `bundle-v*`) hace lo mismo con todos los paquetes y añade `skills.json`. Ambos tienen `permissions: contents: write`, `concurrency` por tag y son idempotentes (`gh release upload --clobber`).

Los tags creados con `GITHUB_TOKEN` no disparan otros workflows. Si existe el secreto `RELEASE_TOKEN` (PAT o token de GitHub App) se usa para empujarlos y el `push: tags` dispara la publicación; si no, `tag-release.yml` llama directamente a los workflows reutilizables y avisa con un `::warning::`. Los dos workflows de release también admiten `workflow_dispatch` con `package`, `version` y `tag`. `tag-release.yml` añade el suyo con `base`: es la vía de recuperación cuando un run falla a medias, porque el `before` del siguiente push ya no vería esos bumps. Salta lo que ya está publicado, reintenta cada tag tres veces y termina con la lista de lo que quedó pendiente, así que relanzarlo basta para completar la publicación.

### Severidad y `--fail-on`

La escala canónica de `severity` es **`critical` → `high` → `medium` → `low`**, más `info` donde la herramienta distingue informativo y `reject` en `agent-red-team` (un nivel que bloquea siempre). La salida no mezcla idiomas; las herramientas que leen hallazgos siguen aceptando las variantes antiguas (`critica`, `alta`, `media`, `baja`) como alias de entrada.

`must`/`should`/`nice` es otro eje: el de la **puerta**. Se llama `severity_level` en `seo-auditor` y `gate` en `premium-web-designer`.

`--fail-on` no es uniforme porque cada herramienta solo puede romper el pipeline con lo que emite de verdad:

| Valores | Herramientas |
|---|---|
| `low \| medium \| high \| none` | `auth_coverage.py`, `env_check.py`, `terms_check.py`, `code_metrics.py`, `dead_code.py`, `llm_cost_scan.py`, `infra_cost_scan.py`, `ci_cost_scan.py`, `lock_audit.py` |
| `low \| medium \| none` | `sql_lint.py` |
| `medium \| none` | `query_trace.py` |
| `medium \| high \| none` | `schema_audit.py` |
| `info \| medium \| critical \| none` | `migration_guard.py` (`warning` sigue aceptándose como alias de `medium`) |
| `high \| none` | `docs_drift.py` |
| `low \| medium \| high \| critical \| none` | `normalize_sarif.py` |
| `dead \| none` | `code_sync.py` |
| `patch \| minor \| major \| none` | `contract_diff.py` |
| `new \| none` | `diff_reports.py` |
| `reachable \| none` | `sbom.py audit` |
| `drift \| none` | `drift.py` |
| `unsafe \| none` | `expand_contract.py` |
| `guardrail \| none` | `cost_diff.py` |
| `clone \| none` | `clone_detect.py` |
| `cycle \| none` | `import_cycles.py` |
| `hotspot \| none` | `hotspots.py` |

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
- [**FinOps Auditor**](finops-auditor.md): cloud cost audit with orphaned resources, rightsizing, a 0–100 rubric and reproducible monthly savings.
- [**Premium Web Designer**](premium-web-designer.md): premium website design and development with art direction, UX/UI and independent QA.
- [**DB Architect**](db-architect.md): database audit without an engine, covering schema, migration risk, N+1 queries and deterministic seeding.
- [**API Contract Guard**](api-contract-guard.md): SemVer impact of a contract change, backend/frontend route sync and a local mock.
- [**Refactor Surgeon**](refactor-surgeon.md): refactoring with metrics, golden cases, call-graph cuts and behaviour verification.
- [**Docs Sync Engine**](docs-sync-engine.md): verified documentation references, regenerable architecture and a CHANGELOG from commits.
- [**Skill Evals**](skill-evals.md): offline catalog evaluation with cases from real phrases, precision/recall/MRR gates, a reproducible report and description optimisation.

### Packages and Sub-skills

**12 packages, 79 skills.** The machine-readable index lives in [`skills.json`](../skills.json).

| Package | Skills | Master | Sub-skills |
|---|---:|---|---|
| `replica` | 14 | `replica` | `replica-recon` (0-1b), `replica-architect`, `replica-design`, `replica-build`, `replica-backend`, `replica-test`, `replica-diff`, `replica-entrepreneur`, `replica-brand`, `replica-launch`, `replica-deploy`, `replica-static`, `replica-redes` |
| `seo-auditor` | 6 | `seo-auditor` | `seo-audit`, `seo-plan`, `seo-execute`, `seo-serp`, `seo-compare` |
| `appsec-audit` | 11 | `appsec-audit` | `appsec-recon`, `appsec-code`, `appsec-infra`, `appsec-llm`, `appsec-threat`, `appsec-deps`, `appsec-ci`, `appsec-fix`, `appsec-report`, `appsec-scale` |
| `agent-red-team` | 3 | `agent-red-team` | `red-scan`, `red-audit` |
| `humanizador-anti-ia` | 3 | `humanizador-anti-ia` | `humanizar`, `detector-ia` |
| `premium-web-designer` | 2 | `premium-web-designer` | `premium-qa` |
| `skill-evals` | 4 | `skill-evals` | `eval-design`, `eval-run`, `eval-report` |
| `finops-auditor` | 7 | `finops-auditor` | `finops-scan`, `finops-rightsize`, `finops-llm-scan`, `finops-infra-scan`, `finops-ci-opt`, `finops-diff` |
| `db-architect` | 9 | `db-architect` | `db-schema-audit`, `db-migration-guard`, `db-expand-contract`, `db-lock-audit`, `db-drift`, `db-sql-lint`, `db-query-trace`, `db-seed-gen` |
| `api-contract-guard` | 5 | `api-contract-guard` | `api-diff`, `api-code-sync`, `api-auth-coverage`, `api-mock-server` |
| `refactor-surgeon` | 9 | `refactor-surgeon` | `refactor-metrics`, `refactor-hotspots`, `refactor-harness`, `refactor-deadcode`, `refactor-clones`, `refactor-cycles`, `refactor-slice`, `refactor-verify` |
| `docs-sync-engine` | 6 | `docs-sync-engine` | `docs-drift-check`, `docs-terms`, `docs-env`, `docs-arch-gen`, `docs-changelog` |

Each master picks the mode, sets boundaries and splits the work; `premium-web-designer` adds `premium-qa` to audit sites that already exist and `appsec-audit` splits the audit across recon, code, infrastructure, LLM, threats, dependencies, CI, remediation, report and scale, while `skill-evals` splits the loop across case design, run and report.

### Package Structure

```text
package/
├── SKILL.md              # master: orchestrates, picks mode, sets limits
├── <sub-skill>/SKILL.md  # one per real usage block
├── references/           # shared — only when the package needs them
├── scripts/              # deterministic Python stdlib, offline
├── templates/            # structured outputs — only when needed
├── tests/                # unittest, offline
└── skills.json           # array with every skill in the package
```

Sub-skills **do not duplicate assets**: they reference `../references/`, `../scripts/` and `../templates/`, so the whole folder is installed. `scripts/`, `tests/` and `skills.json` are present in every package; `references/` and `templates/` appear only when there is shared material worth splitting out. Every `SKILL.md` carries YAML frontmatter: `name` and `description` are required (the description is the activation signal), plus the portable `license`, `allowed-tools`, `compatibility` and `metadata` fields. Here `metadata` holds `package`, `version` and `author`, and read-only skills declare `allowed-tools` with read access plus their own scripts. Helpers shared inside a package live in `scripts/<package>_util.py`; there is no common module across packages, because each one is installed on its own.

### Tests

```bash
uv sync
uv run python run_tests.py
uv run pytest -q
uv run ruff check .
uv run python tests/lint_frontmatter.py
uv run python tests/version_guard.py
uv run python tests/metrics_gate.py
uv run python tests/audit_docs.py
```

`tests/lint_frontmatter.py` validates every `SKILL.md` block with a real YAML parser (PyYAML, from the `dev` group), plus `name`, `description`, manifests, relative links, the index and the marketplace. Each package version comes from its manifest, and `tests/version_guard.py` fails when a package changes without bumping it, comparing against the previous commit. `tests/metrics_gate.py` fails when `high` findings or clones grow past the ceiling in `tests/metrics_baseline.json`. `tests/audit_docs.py` checks the documentation against the repo: cited paths, each package's flags, package tables, “master + N” headings, skill and test counts, and internal anchors. `run_tests.py` also runs it as a local gate after the suites (“Summary: N/M suites and N/M gates”), so the usual command covers the same comparison as the lint job. The shared findings contract lives in `contracts/findings/`: `emit.py` adapts the native output of `appsec-audit` and `seo-auditor` to `findings.schema.json` v1.0.0, `validate_findings.py` validates it (with `--fail-on` for CI) and `findings_to_sarif.py` exports it to SARIF 2.1.0. GitHub Actions runs the lint gates on Python 3.14 and the suites on the 3.9/3.14 matrix across Linux, macOS and Windows. The lint job also validates the workflows with `actionlint` (pinned version, checksum-verified), which reproduces GitHub's refusal to load them: a `matrix` inside a job `if` invalidates the whole workflow. Every description must state its use case ("Use when…") and cover both languages, since that is the only automatic-activation signal agents read. `markdownlint-cli2` is an optional local check.

### Packaging

```bash
make dist                 # every package
make dist PACKAGE=replica # a single one
```

`scripts/build_package.py` writes `dist/<package>-<version>.zip` with the whole package and a root `manifest.json` (version, commit and included skills), plus a `.sha256` file in `sha256sum` format. Entries are sorted and carry a fixed timestamp, so two builds of the same tree produce the same hash. It leaves out `tests/`, `__pycache__`, `.ruff_cache`, `.venv` and audit outputs, and rejects any file that is not UTF-8 text. Before accepting the archive it unpacks it into a temporary directory and runs `tests/lint_frontmatter.py`; on failure it deletes the artifact and exits with an error.

### Publishing

Publishing is bumping the version, committing and pushing; the workflow does the rest.

```bash
uv run --locked python scripts/bump_version.py db-architect 2.1.1  # 1. bump the version in all four places
git add -A && git commit -m "feat(db-architect): ..."             # 2. commit
git push origin main                                              # 3. push
```

`scripts/bump_version.py` moves the package manifest, the `metadata.version` of its `SKILL.md` files, the root index entry and the marketplace plugin together; it also raises the root index by a patch (the bundle version) unless `--no-bundle` is passed. `--dry-run` lists the files it would touch without writing anything, and it rejects a version that is not `X.Y.Z` or not greater than the current one. Changing a package without bumping its version breaks `tests/version_guard.py`, so this is the normal path.

On every push to `main`, `tag-release.yml` compares the index and the manifests against the previous commit (`github.event.before`) and creates one `<package>-v<version>` tag per bump plus `bundle-v<version>` when the root index version changed. Tags are idempotent: existing ones are never rewritten.

`release-package.yml` (tags `<package>-v*`) packages and validates that package, builds bilingual notes with `scripts/release_notes.py` from the commits that touched its folder, and publishes the zip plus `SHA256SUMS`. `release-bundle.yml` (tags `bundle-v*`) does the same for every package and adds `skills.json`. Both use `permissions: contents: write`, per-tag `concurrency` and are idempotent (`gh release upload --clobber`).

Tags pushed with `GITHUB_TOKEN` do not trigger other workflows. When the `RELEASE_TOKEN` secret exists (PAT or GitHub App token) it is used to push them and `push: tags` triggers publishing; otherwise `tag-release.yml` calls the reusable workflows directly and prints a `::warning::`. Both release workflows also accept `workflow_dispatch` with `package`, `version` and `tag`. `tag-release.yml` has its own with `base`: that is the recovery path when a run fails halfway, since the next push's `before` would no longer see those bumps. It skips what is already published, retries each tag three times and ends with the list of what stayed pending, so relaunching it is enough to finish the job.

### Severity and `--fail-on`

The canonical `severity` scale is **`critical` → `high` → `medium` → `low`**, plus `info` where a tool distinguishes informational findings and `reject` in `agent-red-team` (a level that always blocks). Output never mixes languages; tools that read findings still accept the old variants (`critica`, `alta`, `media`, `baja`) as input aliases.

`must`/`should`/`nice` is a different axis: the **gate**. It is called `severity_level` in `seo-auditor` and `gate` in `premium-web-designer`.

`--fail-on` is not uniform because each tool can only break the pipeline with what it actually emits:

| Values | Tools |
|---|---|
| `low \| medium \| high \| none` | `auth_coverage.py`, `env_check.py`, `terms_check.py`, `code_metrics.py`, `dead_code.py`, `llm_cost_scan.py`, `infra_cost_scan.py`, `ci_cost_scan.py`, `lock_audit.py` |
| `low \| medium \| none` | `sql_lint.py` |
| `medium \| none` | `query_trace.py` |
| `medium \| high \| none` | `schema_audit.py` |
| `info \| medium \| critical \| none` | `migration_guard.py` (`warning` is still accepted as an alias of `medium`) |
| `high \| none` | `docs_drift.py` |
| `low \| medium \| high \| critical \| none` | `normalize_sarif.py` |
| `dead \| none` | `code_sync.py` |
| `patch \| minor \| major \| none` | `contract_diff.py` |
| `new \| none` | `diff_reports.py` |
| `reachable \| none` | `sbom.py audit` |
| `drift \| none` | `drift.py` |
| `unsafe \| none` | `expand_contract.py` |
| `guardrail \| none` | `cost_diff.py` |
| `clone \| none` | `clone_detect.py` |
| `cycle \| none` | `import_cycles.py` |
| `hotspot \| none` | `hotspots.py` |

### Safety and Execution Guidelines

1. All tools operate in read-only mode by default.
2. No destructive commands or unauthorized outbound network requests are performed.
3. Python 3.9+ standard library compatibility without `pip install`.
