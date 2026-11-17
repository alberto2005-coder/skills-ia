# Benchmark — Análisis de Referentes / Reference Analysis

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

> Trazabilidad: de qué proyecto viene cada *funcionalidad* (nunca código ajeno).  
> Los planes originales están en [`PLAN-MEJORA.md`](../../PLAN-MEJORA.md).

### Procedencia

- **`replica/` es trabajo original de este repositorio.** No es adaptación de `Jakeschincariol/replica-skill` ni de ningún otro. No volver a plantear.
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

| Funcionalidad | Llegada aquí |
|---|---|
| Modos *guidance* vs *auditoría completa* (solo si se pide) | `SKILL.md` |
| Verificación independiente de cada candidato (intenta refutarlo) | fase de verificación |
| Coverage ledger (qué se cubrió, qué falta) | `templates/coverage-ledger.json` |
| Esquema `confirmed / needs_validation / rejected` + severidad | `templates/report-schema.json` |
| Nivel REJECT por combinación de patrones | motor de `scan_skill.py` + `scripts/rules.json` |
| Ignorar patrones dentro de code fences | motor de `scan_skill.py` |
| Catálogo de ataques + checklist de defensa | `references/attack-catalog.md` |

Comparables: `screem500/prompt-injection-auditor`, `ki-stuff/skill-auditor`, `aliksir/claude-code-skill-security-check` (SARIF), `NovaCode37/claude-security-skills`.

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

### Fase 4 — `seo-auditor/` ← `seo-skills/geo-audit-skill`, `wishfy-ai` y **IndexPulse (propio)**

**Estado: implementada (v2.0.0).** 104 tests `unittest` + servidor HTTP local (gzip/deflate) para el camino de red.

| Funcionalidad | Llegada aquí | Estado |
|---|---|---|
| Rúbrica 0–100 con dimensiones + veredicto en 1 línea | `scripts/checks.py` (`compute_rubric`, `verdict_line`) | ✅ |
| Cada check con id + severidad `must/should/nice` + cita al doc oficial | `scripts/checks.py` + tablas en `references/00..05` | ✅ |
| `audit.json` (máquina) + `audit.md` (persona) + re-score sin red | `scripts/report.py` (`write_report`, `rescore`) | ✅ |
| Audit → Plan → Execute con dry-run | `scripts/execute.py` + `cli.py fix` + `SKILL.md` | ✅ (aplicación solo de robots/llms; snippets a mano) |
| GEO: `llms.txt`, allow-list de crawlers IA por motor | `scripts/geo.py` + `references/03-geo-ai.md` | ✅ (search / user-fetch / training) |
| `compare`/`monitor` entre dos auditorías | `scripts/compare.py` + `cli.py compare` | ✅ |
| Crawl respetuoso (robots.txt, 1 req/s, tope declarado) | `scripts/web_audit.py` (bloque `crawl`) | ✅ |
| **8 módulos IndexPulse** (`gestion_web`, de Alberto) | `indexcheck.py`, `serp.py`, `perf.py`, `security.py`, `schema_audit.py`, `hreflang.py`, `onpage.py`, `report.py` | ✅ 8/8 con límites declarados |

#### Correspondencia módulo → script (funcionalidad, no código)

| Módulo IndexPulse | Nuestro equivalente stdlib | Límite honesto |
|---|---|---|
| 1. Indexación | `indexcheck.analyze` + `check_presence` | `site:` es indirecto → `estimate`; sin Search Console no se afirma indexación |
| 1b. Directivas cruzadas | `indexcheck.is_allowed` + checks `IDX-*` | reglas Allow/Disallow y conflicto meta↔cabecera verificados |
| 2. Simulador SERP | `serp.build` | ancho en píxeles es `estimate` con métrica aproximada |
| 3. Velocidad/CWV | `perf.analyze` / `perf.measure` | LCP/CLS/TBT/Speed Index no medibles con stdlib → `estimate` o enlace a PSI |
| 4. Seguridad HTTP | `security.audit_headers` | score 0–100 reproducible con fórmula publicada |
| 5. Schema + rich preview | `schema_audit.analyze` / `rich_preview` | vista ilustrativa; no garantiza rich result |
| 6. hreflang | `hreflang.analyze` | retorno bidireccional requiere ≥ 2 páginas rastreadas |
| 7. On-page | `onpage.analyze` | galería visual de imágenes → lista de rutas (sin render) |
| 8. Checklist + PDF | `report.render_html` | PDF nativo exigiría dependencias → "Imprimir → PDF" |

### Fase 5 — transversal
Formato genérico multi-skill (índice `skills.json` raíz + `skills.json` por carpeta, sin `.claude-plugin`), tests en todas las skills, README bilingüe y CHANGELOG.

---

## 🇬🇧 English

> Traceability: origin of each *feature* (never third-party code).  
> Original improvement plans live in [`PLAN-MEJORA.md`](../../PLAN-MEJORA.md).

### Provenance

- **`replica/` is original work created for this repository.** It is not an adaptation of `Jakeschincariol/replica-skill` or any other project. Not up for re-evaluation.
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
| Generic packaging + tests | `replica/tests/` (standard format, no `.claude-plugin` manifests) |

Community comparables: `Jakeschincariol/replica-skill`, `aldushmedia/clonar` (master command + `progreso.md` + social/networks), `EncidXVII/claude-reverse-engineering-skill` (trigger evals).

### Phase 2 — `agent-red-team/` ← `cloudflare/security-audit-skill`

| Feature | How it lands here |
|---|---|
| *Guidance* vs *full audit* modes (only on explicit request) | `SKILL.md` |
| Independent verification of every candidate (attempts refutation) | verification phase |
| Coverage ledger (what was covered, what is missing) | `templates/coverage-ledger.json` |
| `confirmed / needs_validation / rejected` schema + severity | `templates/report-schema.json` |
| REJECT level via pattern combinations | `scan_skill.py` engine + `scripts/rules.json` |
| Ignore patterns inside non-executable code fences | `scan_skill.py` engine |
| Attack catalog + defense checklist | `references/attack-catalog.md` |

Comparables: `screem500/prompt-injection-auditor`, `ki-stuff/skill-auditor`, `aliksir/claude-code-skill-security-check` (SARIF), `NovaCode37/claude-security-skills`.

### Phase 3 — `humanizador-anti-ia/` ← `blader/humanizer`

| Feature | How it lands here |
|---|---|
| Numbered patterns from strongest to weakest with before/after pairs | `references/03-patrones-numerados.md` |
| Reproducible 0–100 score across 4 measurable signals | `scripts/audit_style.py` |
| Tiered vocabulary (Tier 1/2/3 by density) | numbered catalog |
| Quick / Full / Voice modes (calibrated with user sample) | `SKILL.md` |
| Register control (LinkedIn / email / article / report) | `SKILL.md` |
| Factual honesty: unsourced stats are flagged, never rewritten | hard rules |
| Code/frontmatter/link protection during rewrites | hard rules |
| **Spanish pattern pack** (key differentiator) | ES catalog |

Comparables: `Aboudjem/humanizer-skill` (55 patterns, 0–100 score), `keez97/humanizer` (structural first), `shir-danishyar/humanize` (register), `Aparnabuilds/humanizer`.

### Phase 4 — `seo-auditor/` ← `seo-skills/geo-audit-skill`, `wishfy-ai`, and **IndexPulse (proprietary)**

**Status: implemented (v2.0.0).** 104 `unittest` tests + local HTTP server (gzip/deflate) for the network path.

| Feature | How it lands here | Status |
|---|---|---|
| 0–100 rubric with dimensions + 1-line verdict | `scripts/checks.py` (`compute_rubric`, `verdict_line`) | ✅ |
| Each check with id + `must/should/nice` severity + official doc citation | `scripts/checks.py` + tables in `references/00..05` | ✅ |
| `audit.json` (machine) + `audit.md` (human) + offline re-score | `scripts/report.py` (`write_report`, `rescore`) | ✅ |
| Audit → Plan → Execute with dry-run | `scripts/execute.py` + `cli.py fix` + `SKILL.md` | ✅ (applies robots/llms only; manual snippets) |
| GEO: `llms.txt`, AI crawler allow-list per engine | `scripts/geo.py` + `references/03-geo-ai.md` | ✅ (search / user-fetch / training) |
| `compare`/`monitor` between two audits | `scripts/compare.py` + `cli.py compare` | ✅ |
| Polite crawl (robots.txt, 1 req/s, declared cap) | `scripts/web_audit.py` (`crawl` block) | ✅ |
| **8 IndexPulse modules** (`gestion_web`, by Alberto) | `indexcheck.py`, `serp.py`, `perf.py`, `security.py`, `schema_audit.py`, `hreflang.py`, `onpage.py`, `report.py` | ✅ 8/8 with declared limits |

#### Module → Script Mapping (capability, not code)

| IndexPulse Module | Stdlib Equivalent | Honest Limit |
|---|---|---|
| 1. Indexing | `indexcheck.analyze` + `check_presence` | `site:` is indirect → `estimate`; no indexing claim without Search Console |
| 1b. Cross directives | `indexcheck.is_allowed` + `IDX-*` checks | Allow/Disallow rules and meta↔header conflicts verified |
| 2. SERP Simulator | `serp.build` | pixel width is `estimate` using approximate metrics |
| 3. Speed/CWV | `perf.analyze` / `perf.measure` | LCP/CLS/TBT/Speed Index unmeasurable in stdlib → `estimate` or PSI link |
| 4. HTTP Security | `security.audit_headers` | reproducible 0–100 score with published formula |
| 5. Schema + rich preview | `schema_audit.analyze` / `rich_preview` | illustrative preview; does not guarantee rich results |
| 6. hreflang | `hreflang.analyze` | bidirectional return requires ≥ 2 crawled pages |
| 7. On-page | `onpage.analyze` | visual image gallery → path list (no rendering) |
| 8. Checklist + PDF | `report.render_html` | native PDF would require dependencies → "Print → PDF" |

### Phase 5 — Cross-cutting
Generic multi-skill format (root `skills.json` index + per-folder `skills.json`, no `.claude-plugin`), tests across all skills, bilingual README, and CHANGELOG.

---
*Última actualización / Last updated: 2026-11-17.*
