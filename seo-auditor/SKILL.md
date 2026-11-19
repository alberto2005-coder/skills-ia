---
name: seo-auditor
description: >
  Audita y optimiza el SEO de cualquier sitio web público, código fuente local, servidor en desarrollo o modo híbrido. Cubre diagnóstico técnico (rastreabilidad, indexación, canonicals, hreflang, cabeceras de seguridad), contenido y on-page, optimización para motores generativos (GEO / AI Search), datos estructurados con rich preview, sitemaps, simulador de SERP y rendimiento. Motor Python stdlib con rúbrica 0–100 por dimensiones, veredicto en una línea, evidencia reproducible (audit.json), re-score sin red, comparación entre auditorías y modo Execute con dry-run. Úsala siempre que el usuario pida auditar una web, revisar el SEO de un repositorio, preparar contenidos para IA/GEO, optimizar una página individual o diseñar una estrategia SEO. English: choose the audit mode and follow the audit plan execute flow, with the rubric and the one-line verdict.
license: MIT
metadata:
  package: seo-auditor
  version: "3.0.0"
---

# SEO Auditor 2.0

Auditoría y optimización SEO para **web pública, código fuente, servidor local o modo híbrido**, con motor determinista en Python stdlib y evidencia reproducible.

## Cuándo usar esta skill

- Auditar un dominio, una URL o un proyecto local.
- Diagnosticar rastreo, indexación, canonicalización, hreflang o cabeceras HTTP.
- Evaluar calidad on-page, jerarquía de encabezados, imágenes y metadatos.
- Preparar contenidos para GEO / AI Search (AI Overviews, Perplexity, ChatGPT, Gemini).
- Validar JSON-LD y simular resultados enriquecidos.
- Medir velocidad observable (TTFB, peso, compresión, recursos) sin inventar CWV.
- Priorizar un plan y aplicarlo con seguridad (dry-run).

## Reglas duras

1. **Solo lectura por defecto.** Nada se escribe en el sitio sin `--apply` + confirmación explícita. Los borradores viven en `output/` marcados `DRAFT`.
2. **Evidencia antes que opinión.** Todo hallazgo tiene id, evidencia literal y cita oficial. Lo inferido se marca `estimate`; lo no medible, `skip`.
3. **Cero datos inventados.** No se inventan rankings, tráfico, backlinks, Core Web Vitals ni presencia en motores de IA. Sin API oficial, `site:` es indirecto (`estimate`).
4. **No etiquetar como error lo no verificado.** Un elemento no comprobable es `skip`, no un fallo.
5. **Puntuación heurística.** La rúbrica es interna y reproducible; no es una nota oficial de Google.
6. **Crawl respetuoso.** robots.txt se consulta y se respeta; 1 petición/segundo por defecto; tope de páginas y profundidad declarados en el informe.
7. **Seguridad.** El rastreador bloquea destinos privados (SSRF), también en **cada salto** de una redirección; en local solo loopback. Nunca se inspeccionan `.env`, claves ni credenciales.

## Rúbrica 0–100 y veredicto

| Dimensión | Peso |
|---|---:|
| Técnico | 25 |
| Contenido | 20 |
| Schema | 15 |
| GEO | 15 |
| Seguridad | 10 |
| Rendimiento | 15 |

```text
score_dimensión = 100 * aprobados / (aprobados + fallidos)
total = media ponderada de las dimensiones evaluadas
```

Las dimensiones sin comprobaciones (p. ej. Seguridad en modo `source`) se excluyen y su peso se redistribuye. Los `skip` no penalizan.

| Puntuación | Veredicto |
|---|---|
| ≥ 85 | `Leading` |
| 60–84.9 | `Competitive` |
| < 60 | `Not Ready` |

El **veredicto en una línea** encabeza siempre el informe, seguido de la puntuación y los contadores 🔴🟡🟢⚪.

**Regla de bloqueo:** con al menos un fallo `must`, el veredicto no puede ser `Leading` (se degrada a `Competitive`). La fórmula no cambia; se evita que un `noindex` conviva con un "Leading".

## Cada comprobación: id + severidad + cita

- **id estable** (p. ej. `IDX-CONFLICT-001`, `ONP-ALT-001`): sirve para informes, `compare` y tests.
- **severidad** `must` → 🔴 crítico · `should` → 🟡 aviso · `nice` → 🟢 mejora opcional.
- **cita** al documento oficial (Google Search Central, schema.org, MDN, ogp.me, llmstxt.org).

El catálogo vive en `scripts/checks.py`; las referencias lo explican en tablas en `references/00..05`.

## Sub-skills

El paquete se instala como una unidad: las sub-skills comparten `references/`, `scripts/`, `templates/` y `tests/` de esta carpeta (sin duplicar).

| Sub-skill | Qué hace |
|---|---|
| `seo-audit` | Auditoría completa y módulos de diagnóstico, rúbrica y `rescore` |
| `seo-plan` | Convierte `audit.json` en `PLAN.md` y borradores `DRAFT` sin tocar el sitio |
| `seo-execute` | Aplica lo aplicable con backup y verifica con una nueva auditoría |
| `seo-serp` | Simulador de SERP y tarjetas sociales (`output/serp/preview.html`) |
| `seo-compare` | Diff entre auditorías (mejorado/empeorado/nuevo/resuelto) y monitorización |

Esta skill es el **maestro**: decide el flujo Audit → Plan → Execute y los límites. Las sub-skills se activan solas cuando el usuario pide solo una parte.

## Comandos

Todos se ejecutan desde la **raíz del repositorio**, con la ruta del paquete:

```bash
py seo-auditor/scripts/cli.py audit <url|ruta|fichero> --mode <web|source|local|hybrid|page>
```

Catálogo completo de los 11 comandos, modos, módulos y flags en [`USAGE.md`](USAGE.md) y en `seo-audit`. Cada auditoría produce `audit.json` (máquina), `audit.md` (persona) y `report.html` (imprimible con filtros) bajo `--output` (por defecto `reports/` en el directorio desde el que ejecutas; se crea solo).

## Flujo Audit → Plan → Execute

1. **Audit.** Ejecuta `audit` con el modo adecuado. Lee `audit.md` y `report.html`; el veredicto y la rúbrica salen de `checks`, no de una impresión.
2. **Plan.** Ejecuta `fix` **sin** `--apply`: genera `PLAN.md` con acciones ordenadas por severidad, cita y recomendación, más los borradores `DRAFT`.
3. **Execute.** Revisa cada `TODO`. Solo `robots.txt`, `llms.txt` y `llms-full.txt` se aplican con `--apply --dest`; los snippets de meta tags y JSON-LD se integran a mano. Se crea un `.bak` de lo sobrescrito.
4. **Verificar.** Vuelve a auditar y usa `compare` para confirmar mejorado/empeorado/nuevo/resuelto. `rescore` recalcula la rúbrica desde `checks` sin abrir conexiones.

## Qué se mide, qué se estima y qué no se inventa

| Medido (sin red tras la captura) | `estimate` | No se inventa |
|---|---|---|
| Títulos, metadatos, canonical, hreflang | Ancho de título en px | Posiciones o rankings |
| Reglas robots.txt, meta, `X-Robots-Tag` | Ratio texto/HTML | Tráfico o conversiones |
| JSON-LD, tipos y propiedades | Bloque-respuesta 134–167 palabras | LCP/CLS/TBT/Speed Index sin dato externo |
| Cabeceras HTTP y mixed content | Presencia `site:` | Indexación confirmada sin Search Console |
| TTFB, peso HTML, compresión, CSS/JS externos | TBT a partir de bytes de JS | Backlinks o autoridad de dominio |

Además: no se consultan rankings, Search Console ni Analytics salvo que el usuario los aporte; el HTML recibido puede no incluir contenido generado por JavaScript; GEO se evalúa por señales estructurales y editoriales, sin inferir posición en respuestas de IA; y no hay PDF nativo (rompería cero dependencias): `report.html` incluye **Imprimir → Guardar como PDF**.

## Estructura

```text
seo-auditor/
├── SKILL.md + <sub-skill>/SKILL.md   # maestro + 5 sub-skills
├── USAGE.md                          # 11 comandos, modos y flags
├── references/                       # 00..07 (metodología, técnico, contenido, GEO, schema, sitemap, estrategia, página)
├── scripts/                          # cli.py, page.py, analyze.py, checks.py, report.py, compare.py, execute.py, source_audit.py, web_audit.py, sitemap.py + módulos
├── templates/
├── tests/                            # unittest, fixtures sintéticos, sin red
└── output/                           # borradores DRAFT (se crean solos)
```
