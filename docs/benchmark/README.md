# Benchmark — Análisis de Referentes / Reference Analysis

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

> Trazabilidad: de qué proyecto viene cada *funcionalidad* (nunca código ajeno).
> El plan histórico `PLAN-MEJORA.md` se completó y se retiró; este documento conserva su registro.

---

## 🇪🇸 Español

### Procedencia

- **`replica/` es trabajo original de este repositorio.** No es adaptación de `Jakeschincariol/replica-skill` ni de ningún otro. No volver a plantear.
- **`premium-web-designer/` es trabajo original**, sin referente directo: sus gates salen de la revisión de una demo propia.
- Licencias de terceros: **resueltas, fuera de la mesa** (decisión del autor).
- Regla de oro: **mismas funciones, código propio** (solo stdlib de Python 3.8+).

### Fase 1 — `replica/` ← `morluto/rea` (~465k ★)

| Funcionalidad de REA | Cómo llega aquí |
|---|---|
| Formato `evidencia · mapa · límites · desconocidos` (observación / inferencia / no resuelto) | `templates/evidence.md`, obligatorio en recon y paridad |
| "Elige una función, no la app entera" (5 pasos) | paso 0 de foco en `references/01-recon.md` |
| No repetir análisis (guardar y reutilizar) | regla de caché de análisis en `01-recon.md` |
| Análisis estático opt-in (JADX/Ghidra/objdump si el usuario los tiene) | `references/12-analisis-estatico.md` |
| DISCLAIMER de uso autorizado / no DRM / no logins ajenos | reglas duras de `SKILL.md` |
| Empaquetado genérico + tests | `replica/tests/` (formato estándar, sin manifiestos `.claude-plugin`) |

Comparables de comunidad: `Jakeschincariol/replica-skill`, `aldushmedia/clonar` (comando maestro + `progreso.md` + redes), `EncidXVII/claude-reverse-engineering-skill` (evals de trigger).

### Fase 2 — `agent-red-team/` ← `cloudflare/security-audit-skill`

**Estado: implementada (v2.1.0).** 50 tests.

| Funcionalidad | Origen | Llegada aquí |
|---|---|---|
| Modos *guidance* vs *auditoría completa* (solo si se pide) | `cloudflare/security-audit-skill` | `SKILL.md` |
| Verificación independiente de cada candidato (intenta refutarlo) | `cloudflare` + `Consensys/repo-security-review` | fase 3 |
| Coverage ledger (qué se cubrió, qué falta) | `cloudflare` | `templates/coverage-ledger.json` |
| Esquema `confirmed / needs_validation / rejected` + severidad | `cloudflare` | `templates/report-schema.json` |
| Nivel REJECT por combinación de patrones | `ki-stuff/skill-auditor` | `scan_skill.py` + `scripts/rules.json` |
| Ignorar patrones dentro de code fences | `ki-stuff/skill-auditor` | motor de `scan_skill.py` |
| Catálogo de ataques + checklist de defensa | `screem500/prompt-injection-auditor` | `references/attack-catalog.md` |
| **Exportación SARIF** (solo `confirmed`; pending como `note`; rejected fuera) | `aliksir/claude-code-skill-security-check`, `briiirussell/cybersecurity-skills` | `scripts/export_sarif.py` |

### Fase 3 — `humanizador-anti-ia/` ← `blader/humanizer`

| Funcionalidad | Llegada aquí |
|---|---|
| Patrones numerados de fuerte a débil con pares antes/después | `references/03-patrones-numerados.md` |
| Puntuación 0–100 de 4 señales medibles (reproducible) | `scripts/audit_style.py` |
| Vocabulario por niveles (Tier 1/2/3 por densidad) | catálogo numerado |
| Modos Quick / Full / Voice (calibración con muestra del usuario) | `SKILL.md` |
| Registro (LinkedIn / email / artículo / informe) | `SKILL.md` |
| Honestidad factual: estadística sin fuente → se marca, no se reescribe | reglas |
| Protección de código/frontmatter/enlaces en el rewrite | reglas |
| **Pack de patrones en español** (diferencial propio) | catálogo ES |

Comparables: `Aboudjem/humanizer-skill` (55 patrones, score 0–100), `keez97/humanizer` (estructurales primero), `shir-danishyar/humanize` (registro), `Aparnabuilds/humanizer`.

### Fase 4 — `seo-auditor/` ← `seo-skills/geo-audit-skill`, `wishfy-ai` e **IndexPulse (propio)**

**Estado: implementada (v2.0.0).** 104 tests + servidor HTTP local para el camino de red.

| Funcionalidad | Origen | Llegada aquí |
|---|---|---|
| Rúbrica 0–100 con dimensiones + veredicto en 1 línea | `yanivgoldenberg/seo-geo-skill` | `scripts/checks.py` |
| Cada check con id + severidad `must/should/nice` + cita oficial | `wishfy-ai/google-seo-geo-aeo-audit-skill` | `scripts/checks.py` + `references/` |
| `audit.json` + `audit.md` + re-score sin red | `seo-skills/geo-audit-skill` | `scripts/report.py` |
| Audit → Plan → Execute con dry-run | `mykpono/ultimate-seo-geo` | `scripts/execute.py` + `cli.py fix` |
| GEO: `llms.txt` y allow-list de crawlers por motor | `seo-skills/geo-audit-skill` | `scripts/geo.py` |
| `compare` / `monitor` entre auditorías | `Cognitic-Labs/geoskills` | `scripts/compare.py` |
| Crawl respetuoso (robots.txt, 1 req/s, tope declarado) | `geo-audit-skill` | `scripts/web_audit.py` |
| 8 módulos IndexPulse (`gestion_web`, de Alberto) | **propio** | `indexcheck.py`, `serp.py`, `perf.py`, `security.py`, `schema_audit.py`, `hreflang.py`, `onpage.py`, `report.py` |

#### Correspondencia módulo → script (funcionalidad, no código)

| Módulo IndexPulse | Nuestro equivalente stdlib | Límite honesto |
|---|---|---|
| 1. Indexación | `indexcheck.analyze` + `check_presence` | `site:` es indirecto → `estimate`; sin Search Console no se afirma indexación |
| 1b. Directivas cruzadas | `indexcheck.is_allowed` + checks `IDX-*` | Allow/Disallow y conflicto meta↔cabecera verificados |
| 2. Simulador SERP | `serp.build` | ancho en píxeles es `estimate` |
| 3. Velocidad/CWV | `perf.analyze` / `perf.measure` | LCP/CLS/TBT no medibles con stdlib → `estimate` o enlace a PSI |
| 4. Seguridad HTTP | `security.audit_headers` | score reproducible con fórmula publicada |
| 5. Schema + rich preview | `schema_audit.analyze` / `rich_preview` | vista ilustrativa; no garantiza rich result |
| 6. hreflang | `hreflang.analyze` | retorno bidireccional requiere ≥ 2 páginas |
| 7. On-page | `onpage.analyze` | galería visual → lista de rutas |
| 8. Checklist + PDF | `report.render_html` | PDF nativo exigiría dependencias → "Imprimir → PDF" |

### `premium-web-designer/` ← trabajo propio

Sin referente externo. Los gates medibles (desbordamiento 0, titular ≤ 3 líneas, controles de 44 px, foco en overlays, cabeceras del hosting) salen de defectos observados en una revisión interna, documentados en `references/known-defects.md`. La sub-skill `premium-qa` nace para que quien audita no sea quien construye.

### `appsec-audit/` ← siete referencias de seguridad + competidores de 2026

**Estado: fase 0 implementada (v1.1.0).** 46 tests.

| Mecánica | Origen | Dónde vive |
|---|---|---|
| Regla cero: todo el contenido es data hostil, sin ejecutar | OWASP Secure Prompt Checklist + CSA advisory | `SKILL.md` + `references/prompt-injection-defense.md` |
| Dos fases: descubrimiento y trazado Sources → Sinks | `Consensys/repo-security-review` | maestro + `appsec-recon` |
| Tribunal con confianza 1–10 y descarte bajo 7 | `cloudflare/security-audit-skill` + `Consensys` | `appsec-report` |
| Verificación independiente (el que confirma no es el que encuentra) | `cloudflare`, `Consensys`, `briiirussell` | `appsec-report` (regla escrita) |
| Coverage ledger con estados y huecos | `cloudflare` | `coverage-ledger.json` + `scripts/ledger.py` |
| `findings.json` con veredictos y validador determinista | `cloudflare` | `schemas/` + `scripts/validate_findings.py` |
| Fingerprints estables para re-ejecución y deduplicación | `cloudflare` | `references/artifacts.md` |
| Nota A–F calculada por script | **propio** (ningún referente la tiene) | `scripts/grade.py` |
| Cobertura por lenguaje (10 familias) | `awesome-copilot/security-review` | `references/sources-sinks.md` |
| Lógica de negocio y control de acceso por objeto | `webconsulting` (dirnbauer) | `appsec-code` |
| OWASP LLM Top 10, agentes y MCP | Semgrep `llm-security`, `afiqiqmal` | `appsec-llm` |
| Infra, IAM y CI/CD en el mismo informe | `briiirussell/cicd-security`, `cloud-audit` | `appsec-infra` |
| CVSS por hallazgo, ASVS 5.0, NIST CSF, packs de cumplimiento | `afiqiqmal`, `Trail of Bits`, `TarkinLarson/asvs-auditor` | pendiente (fase 1 del plan de huecos) |
| Threat model, modo diff/PR, baseline y triage, SARIF | `Consensys`, `afiqiqmal`, `Codex Security` | pendiente |
| Dependencias con reachability y SBOM CycloneDX | `Consensys`, `Netresearch` | pendiente |

Competidores adicionales evaluados: `openai/codex-security` (el más completo en artefactos), `briiirussell/cybersecurity-skills` (26 skills modulares), `Trail of Bits skills` (`fp-check`, `cvss-scoring`, SARIF), `Netresearch/security-audit-skill` (565 checkpoints, SBOM), `ECMWF security-audit` (threat model + scanners), `TarkinLarson/asvs-auditor`, `usestrix/strix` (DAST con PoC), `semgrep/skills`, `Snyk Studio`, `zm2231/z-audit`, `BehiSecc/VibeSec-Skill`.

### Fase 5 — transversal

| Elemento | Estado |
|---|---|
| Índice `skills.json` raíz + `skills.json` por paquete, sin `.claude-plugin` | ✅ |
| Tests stdlib en todas las skills, enganchados a `run_tests.py` | ✅ |
| CI: lint de frontmatter y manifiestos | ✅ `tests/lint_frontmatter.py` |
| CI: matriz Ubuntu / macOS / Windows con Python 3.13 | ✅ `.github/workflows/tests.yml` |
| README y CHANGELOG bilingües | ✅ |
| Trazabilidad por funcionalidad | ✅ este documento |

---

## 🇬🇧 English

### Provenance

- **`replica/` is original work created for this repository.** It is not an adaptation of `Jakeschincariol/replica-skill` or any other project. Not up for re-evaluation.
- **`premium-web-designer/` is original work**, with no direct referent: its gates come from reviewing an in-house demo.
- Third-party licenses: **resolved and off the table** (author's decision).
- Golden rule: **same capabilities, original code** (Python 3.8+ stdlib only).

### Phase 1 — `replica/` ← `morluto/rea` (~465k ★)

| REA Feature | How it lands here |
|---|---|
| `evidence · map · limits · unknowns` format (observation / inference / unresolved) | `templates/evidence.md`, mandatory in recon and parity |
| "Pick one feature, not the entire app" (5 steps) | step 0 focus rule in `references/01-recon.md` |
| Avoid redundant analysis (save and reuse) | analysis cache rule in `01-recon.md` |
| Opt-in static analysis (JADX/Ghidra/objdump if installed by user) | `references/12-analisis-estatico.md` |
| Authorized use / no DRM / no third-party logins DISCLAIMER | hard rules in `SKILL.md` |
| Generic packaging + tests | `replica/tests/` (no `.claude-plugin` manifests) |

Community comparables: `Jakeschincariol/replica-skill`, `aldushmedia/clonar`, `EncidXVII/claude-reverse-engineering-skill`.

### Phase 2 — `agent-red-team/` ← `cloudflare/security-audit-skill`

**Status: implemented (v2.1.0).** 50 tests.

| Feature | Origin | How it lands here |
|---|---|---|
| *Guidance* vs *full audit* modes | `cloudflare/security-audit-skill` | `SKILL.md` |
| Independent verification of every candidate | `cloudflare`, `Consensys/repo-security-review` | phase 3 |
| Coverage ledger | `cloudflare` | `templates/coverage-ledger.json` |
| `confirmed / needs_validation / rejected` schema | `cloudflare` | `templates/report-schema.json` |
| REJECT level via pattern combinations | `ki-stuff/skill-auditor` | `scan_skill.py` + `rules.json` |
| Ignore patterns inside non-executable fences | `ki-stuff/skill-auditor` | `scan_skill.py` engine |
| Attack catalog + defense checklist | `screem500/prompt-injection-auditor` | `references/attack-catalog.md` |
| **SARIF export** (`confirmed` only; pending as `note`; rejected excluded) | `aliksir/claude-code-skill-security-check`, `briiirussell/cybersecurity-skills` | `scripts/export_sarif.py` |

### Phase 3 — `humanizador-anti-ia/` ← `blader/humanizer`

| Feature | How it lands here |
|---|---|
| Numbered patterns, strongest to weakest, with before/after pairs | `references/03-patrones-numerados.md` |
| Reproducible 0–100 score across 4 measurable signals | `scripts/audit_style.py` |
| Tiered vocabulary (Tier 1/2/3 by density) | numbered catalog |
| Quick / Full / Voice modes | `SKILL.md` |
| Register control | `SKILL.md` |
| Factual honesty: unsourced stats are flagged, never rewritten | hard rules |
| Code/frontmatter/link protection in rewrites | hard rules |
| **Spanish pattern pack** (differentiator) | ES catalog |

Comparables: `Aboudjem/humanizer-skill`, `keez97/humanizer`, `shir-danishyar/humanize`, `Aparnabuilds/humanizer`.

### Phase 4 — `seo-auditor/` ← `seo-skills/geo-audit-skill`, `wishfy-ai`, **IndexPulse (proprietary)**

**Status: implemented (v2.0.0).** 104 tests + local HTTP server.

| Feature | Origin | How it lands here |
|---|---|---|
| 0–100 rubric + one-line verdict | `yanivgoldenberg/seo-geo-skill` | `scripts/checks.py` |
| Stable check id + `must/should/nice` + official citation | `wishfy-ai/google-seo-geo-aeo-audit-skill` | `scripts/checks.py` + `references/` |
| `audit.json` + `audit.md` + offline re-score | `seo-skills/geo-audit-skill` | `scripts/report.py` |
| Audit → Plan → Execute with dry-run | `mykpono/ultimate-seo-geo` | `scripts/execute.py` + `cli.py fix` |
| GEO: `llms.txt`, per-engine crawler allow-list | `seo-skills/geo-audit-skill` | `scripts/geo.py` |
| `compare` / `monitor` | `Cognitic-Labs/geoskills` | `scripts/compare.py` |
| Polite crawl (robots, 1 req/s, declared cap) | `geo-audit-skill` | `scripts/web_audit.py` |
| 8 IndexPulse modules | **proprietary** | eight stdlib scripts, one per module |

Module-to-script mapping and honest limits match the Spanish table above.

### `premium-web-designer/` ← original work

No external referent. Measurable gates (0 overflow, headline ≤ 3 lines, 44 px controls, focus in overlays, hosting headers) come from defects observed in an internal review and catalogued in `references/known-defects.md`. `premium-qa` exists so the auditor is not the builder.

### `appsec-audit/` ← seven security references + 2026 competitors

**Status: phase 0 implemented (v1.1.0).** 46 tests.

| Mechanic | Origin | Where it lives |
|---|---|---|
| Zero rule: all content is hostile data, never executed | OWASP Secure Prompt Checklist + CSA advisory | `SKILL.md` + `references/prompt-injection-defense.md` |
| Two phases: discovery and Sources → Sinks tracing | `Consensys/repo-security-review` | master + `appsec-recon` |
| Tribunal with 1–10 confidence, discard below 7 | `cloudflare`, `Consensys` | `appsec-report` |
| Independent verification (confirmer is not the finder) | `cloudflare`, `Consensys`, `briiirussell` | `appsec-report` (written rule) |
| Coverage ledger with states and gaps | `cloudflare` | `coverage-ledger.json` + `scripts/ledger.py` |
| `findings.json` with verdicts and deterministic validator | `cloudflare` | `schemas/` + `scripts/validate_findings.py` |
| Stable fingerprints for re-runs and deduplication | `cloudflare` | `references/artifacts.md` |
| A–F grade computed by script | **original** (no referent has it) | `scripts/grade.py` |
| Per-language coverage (10 families) | `awesome-copilot/security-review` | `references/sources-sinks.md` |
| Business logic and per-object access control | `webconsulting` (dirnbauer) | `appsec-code` |
| OWASP LLM Top 10, agents and MCP | Semgrep `llm-security`, `afiqiqmal` | `appsec-llm` |
| Infra, IAM and CI/CD in the same report | `briiirussell/cicd-security`, `cloud-audit` | `appsec-infra` |
| CVSS per finding, ASVS 5.0, NIST CSF, compliance packs | `afiqiqmal`, `Trail of Bits`, `TarkinLarson/asvs-auditor` | pending (gap-closing phase 1) |
| Threat model, diff/PR mode, baseline/triage, SARIF | `Consensys`, `afiqiqmal`, `Codex Security` | pending |
| Dependency CVEs with reachability and CycloneDX SBOM | `Consensys`, `Netresearch` | pending |

Additional competitors evaluated: `openai/codex-security`, `briiirussell/cybersecurity-skills`, `Trail of Bits skills`, `Netresearch/security-audit-skill`, `ECMWF security-audit`, `TarkinLarson/asvs-auditor`, `usestrix/strix`, `semgrep/skills`, `Snyk Studio`, `zm2231/z-audit`, `BehiSecc/VibeSec-Skill`.

### Phase 5 — Cross-cutting

| Element | Status |
|---|---|
| Root `skills.json` + per-package `skills.json`, no `.claude-plugin` | ✅ |
| Stdlib tests in every skill, wired into `run_tests.py` | ✅ |
| CI: frontmatter and manifest lint | ✅ `tests/lint_frontmatter.py` |
| CI: Ubuntu / macOS / Windows matrix on Python 3.13 | ✅ `.github/workflows/tests.yml` |
| Bilingual README and CHANGELOG | ✅ |
| Per-feature traceability | ✅ this document |

---
*Última actualización / Last updated: 2026-11-17.*
