# SEO Auditor

> Auditoría SEO/GEO con rúbrica 0–100 y evidencia reproducible.  
> SEO/GEO audit with a 0–100 rubric and reproducible evidence.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice
1. [Visión General](#visión-general)
2. [Modos](#modos)
3. [Rúbrica y Veredicto](#rúbrica-y-veredicto)
4. [Módulos y Comandos](#módulos-y-comandos)
5. [Sub-skills](#sub-skills)
6. [Artefactos y Flujo](#artefactos-y-flujo)
7. [Límites Declarados](#límites-declarados)
8. [Uso y Tests](#uso-y-tests)

### Visión General
`seo-auditor` audita sitios públicos, código local, servidores en desarrollo y páginas sueltas. El motor calcula y el modelo explica: cada hallazgo tiene id estable, severidad y cita oficial; la puntuación se recalcula desde la evidencia guardada, sin volver a la red.

**Paquete de 6 skills:** maestro + `seo-audit`, `seo-plan`, `seo-execute`, `seo-serp`, `seo-compare`.

### Modos
| Modo | Objetivo |
|---|---|
| `web` | Sitio público con crawl respetuoso (`--max-pages`, `--rate`) |
| `source` | Código local sin levantar servidor |
| `local` | Servidor en loopback |
| `hybrid` | Código + servidor local |
| `page` | Una página o URL suelta |

### Rúbrica y Veredicto
Pesos: Técnico 25 · Contenido 20 · Schema 15 · GEO 15 · Seguridad 10 · Rendimiento 15.

```
score_dimensión = 100 * aprobados / (aprobados + fallidos)
total = media ponderada de las dimensiones evaluadas
```

| Puntuación | Veredicto |
|---|---|
| ≥ 85 | `Leading` |
| 60–84.9 | `Competitive` |
| < 60 | `Not Ready` |

Un fallo `must` impide `Leading` y lo degrada a `Competitive`: un `noindex` no convive con un «Leading». Los `skip` no penalizan; las dimensiones sin comprobaciones se excluyen y su peso se redistribuye.

### Módulos y Comandos
| # | Bloque | Comando |
|---|---|---|
| 1 | Indexación + directivas cruzadas | `index` |
| 2 | SERP + tarjetas sociales | `serp` |
| 3 | Velocidad observable | `perf` |
| 4 | Seguridad HTTP | `headers` |
| 5 | JSON-LD + rich preview | `schema --rich-preview` |
| 6 | hreflang | `hreflang` |
| 7 | On-page | `onpage` |
| 8 | Checklist + HTML imprimible | `audit` → `report.html` |

CLI de 11 comandos: `audit`, `rescore`, `compare`, `serp`, `perf`, `headers`, `schema`, `hreflang`, `onpage`, `index`, `fix`.

### Sub-skills
| Sub-skill | Qué hace |
|---|---|
| `seo-audit` | Auditoría completa y módulos de diagnóstico, rúbrica y re-score sin red. |
| `seo-plan` | Convierte `audit.json` en `PLAN.md` priorizado y borradores `DRAFT`, sin tocar el sitio. |
| `seo-execute` | Aplica lo aplicable con `--apply` y backups `.bak`; verifica con una nueva auditoría. |
| `seo-serp` | Simulador de Google escritorio/móvil, Bing y tarjetas OG. |
| `seo-compare` | Diff entre auditorías (mejorado/empeorado/nuevo/resuelto) y monitorización. |

### Artefactos y Flujo
Cada auditoría produce `audit.json` (máquina), `audit.md` (persona) y `report.html` (imprimible con filtros 🔴🟡🟢⚪).

1. **Audit** → `seo-audit`.
2. **Plan** → `seo-plan` (`PLAN.md` + `robots.txt.draft`, `llms.txt.draft`, `meta-tags.html.draft`, `jsonld.json.draft`).
3. **Execute** → `seo-execute` (solo `robots.txt`, `llms.txt` y `llms-full.txt` se copian; los snippets se integran a mano).
4. **Verificar** → nueva auditoría + `seo-compare`.

### Límites Declarados
- No se consultan rankings, Search Console ni Analytics salvo que el usuario los aporte.
- Sin API externa no hay Core Web Vitals: se mide TTFB, peso, compresión y recursos, y se marca lo demás `estimate`.
- La presencia con `site:` es indirecta y no prueba indexación.
- GEO se evalúa por señales estructurales; no se infiere posición en respuestas de IA.
- El HTML recibido puede no incluir contenido generado por JavaScript.
- No hay PDF nativo (rompería cero dependencias): `report.html` incluye **Imprimir → Guardar como PDF**.

### Uso y Tests
```bash
py seo-auditor/scripts/cli.py audit https://example.com --mode web --max-pages 30 --rate 1
py seo-auditor/scripts/cli.py audit . --mode source
py seo-auditor/scripts/cli.py audit pagina.html --mode page
py seo-auditor/scripts/cli.py fix --input reports/mi-sitio/20260101-120000/audit.json --output output
py seo-auditor/scripts/cli.py compare audit-antes.json audit-despues.json

py -m unittest discover -s seo-auditor/tests -v
```

---

## 🇬🇧 English

### Table of Contents
1. [Overview](#overview)
2. [Modes](#modes)
3. [Rubric and Verdict](#rubric-and-verdict)
4. [Modules and Commands](#modules-and-commands)
5. [Sub-skills](#sub-skills-1)
6. [Artifacts and Flow](#artifacts-and-flow)
7. [Declared Limits](#declared-limits)
8. [Usage and Tests](#usage-and-tests)

### Overview
`seo-auditor` audits public sites, local code, dev servers and single pages. The engine computes and the model explains: every finding has a stable id, severity and official citation; scores are recomputed from stored evidence without hitting the network.

**6-skill package:** master + `seo-audit`, `seo-plan`, `seo-execute`, `seo-serp`, `seo-compare`.

### Modes
| Mode | Target |
|---|---|
| `web` | Public site with respectful crawl (`--max-pages`, `--rate`) |
| `source` | Local code without starting a server |
| `local` | Loopback dev server |
| `hybrid` | Code + local server |
| `page` | Single page or URL |

### Rubric and Verdict
Weights: Technical 25 · Content 20 · Schema 15 · GEO 15 · Security 10 · Performance 15.

```
dimension_score = 100 * passed / (passed + failed)
total = weighted mean of evaluated dimensions
```

| Score | Verdict |
|---|---|
| ≥ 85 | `Leading` |
| 60–84.9 | `Competitive` |
| < 60 | `Not Ready` |

A `must` failure blocks `Leading` and degrades it to `Competitive`: a `noindex` never sits next to "Leading". `skip` items do not penalize; dimensions without checks are excluded and their weight redistributed.

### Modules and Commands
| # | Block | Command |
|---|---|---|
| 1 | Indexing + crossed directives | `index` |
| 2 | SERP + social cards | `serp` |
| 3 | Observable speed | `perf` |
| 4 | HTTP security | `headers` |
| 5 | JSON-LD + rich preview | `schema --rich-preview` |
| 6 | hreflang | `hreflang` |
| 7 | On-page | `onpage` |
| 8 | Checklist + printable HTML | `audit` → `report.html` |

11-command CLI: `audit`, `rescore`, `compare`, `serp`, `perf`, `headers`, `schema`, `hreflang`, `onpage`, `index`, `fix`.

### Sub-skills
| Sub-skill | Purpose |
|---|---|
| `seo-audit` | Full audit and diagnostic modules, rubric and offline re-score. |
| `seo-plan` | Turns `audit.json` into a prioritized `PLAN.md` and `DRAFT` files, without touching the site. |
| `seo-execute` | Applies what is safe with `--apply` and `.bak` backups; verifies with a fresh audit. |
| `seo-serp` | Google desktop/mobile, Bing and OG card simulator. |
| `seo-compare` | Audit diff (improved/worse/new/resolved) and monitoring. |

### Artifacts and Flow
Every audit produces `audit.json` (machine), `audit.md` (human) and `report.html` (printable with 🔴🟡🟢⚪ filters).

1. **Audit** → `seo-audit`.
2. **Plan** → `seo-plan` (`PLAN.md` + `robots.txt.draft`, `llms.txt.draft`, `meta-tags.html.draft`, `jsonld.json.draft`).
3. **Execute** → `seo-execute` (only `robots.txt`, `llms.txt` and `llms-full.txt` are copied; snippets are integrated by hand).
4. **Verify** → fresh audit + `seo-compare`.

### Declared Limits
- No rankings, Search Console or Analytics unless the user provides them.
- Without an external API there are no Core Web Vitals: TTFB, weight, compression and resources are measured, the rest is marked `estimate`.
- `site:` presence is indirect and does not prove indexing.
- GEO is assessed through structural signals; position in AI answers is never inferred.
- Received HTML may not include JavaScript-rendered content.
- No native PDF (zero-dependency rule): `report.html` ships **Print → Save as PDF**.

### Usage and Tests
```bash
py seo-auditor/scripts/cli.py audit https://example.com --mode web --max-pages 30 --rate 1
py seo-auditor/scripts/cli.py audit . --mode source
py seo-auditor/scripts/cli.py audit pagina.html --mode page
py seo-auditor/scripts/cli.py fix --input reports/mi-sitio/20260101-120000/audit.json --output output
py seo-auditor/scripts/cli.py compare audit-antes.json audit-despues.json

py -m unittest discover -s seo-auditor/tests -v
```
