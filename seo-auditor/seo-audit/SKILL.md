---
name: seo-audit
description: Auditoría SEO completa de una web, repositorio, servidor local o página suelta — técnico, contenido, schema, GEO, seguridad y rendimiento, con rúbrica 0-100, veredicto en una línea, evidence reproducible (audit.json/audit.md/report.html) y re-score sin red. Úsala cuando el usuario pida auditar una web o un repo, diagnosticar indexación, canonical, hreflang, cabeceras, JSON-LD o on-page, o revisar el SEO de una página. English: run the full audit and check the diagnostic modules of the site — indexing, security headers, schema, hreflang, on-page and performance —, collect reproducible evidence and rescore offline.
license: MIT
metadata:
  package: seo-auditor
  version: "2.0.0"
---

# SEO Auditor · Audit

La auditoría completa: recoge evidencia, aplica el catálogo de comprobaciones y emite veredicto. **El motor calcula; el modelo explica.** Aplican las reglas duras del maestro (solo lectura, cero datos inventados, crawl respetuoso, anti-SSRF), y un fallo `must` impide el veredicto `Leading`.

Assets compartidos del paquete: `../references/`, `../scripts/`, `../templates/`, `../tests/`.

**Todos los comandos se ejecutan desde la raíz del repositorio** (`skills-ia-main/`) con el prefijo `py seo-auditor/scripts/cli.py`; las celdas de comando de las tablas son argumentos de ese CLI.

## Cuándo se usa

- «Audita example.com», «revisa el SEO de este repo», «por qué no me indexa».
- Diagnóstico puntual de un módulo: indexación, hreflang, schema, cabeceras, on-page, rendimiento.
- Antes de un plan (`seo-plan`) o después de aplicar cambios (`seo-compare`).

## Modos

| Modo | Objetivo | Comando |
|---|---|---|
| `web` | Sitio público con crawl respetuoso | `audit https://example.com --mode web --max-pages 30 --rate 1` |
| `source` | Código local (templates, metadatos, sitemap) | `audit . --mode source` |
| `local` | Servidor en desarrollo | `audit http://localhost:3000 --mode local` |
| `hybrid` | Código + ejecución local | `audit . --mode hybrid --base-url http://localhost:3000` |
| `page` | Una página o URL suelta | `audit pagina.html --mode page` |

## Módulos de diagnóstico

| Módulo | Comando | Salida |
|---|---|---|
| Indexación + directivas cruzadas | `index pagina.html --robots ./robots.txt` | robots.txt, meta robots, `X-Robots-Tag`, canonical, sitemap y conflictos |
| Presencia indirecta por motor | `index https://example.com --presence` | `site:` por motor, marcado `estimate` |
| SERP + tarjetas sociales | `serp pagina.html` | `output/serp/preview.html` (ver `seo-serp`) |
| Rendimiento observable | `perf https://example.com` | TTFB, peso, compresión, CSS/JS externos |
| Seguridad HTTP | `headers https://example.com` | score 0-100 + mixed content |
| Schema + rich preview | `schema pagina.html --rich-preview` | inventario `@type` + vista ilustrativa |
| hreflang | `hreflang pagina.html` | pares, autorreferencia, `x-default`, retorno |
| On-page | `onpage pagina.html` | ratio texto/HTML, H1-H4, `alt`, densidad |

## Método

1. Elige el modo por el objetivo real; si dudas entre `web` y `page`, empieza por `page` (una petición) y amplía.
2. Ejecuta `audit` y lee `audit.md` **antes** que `audit.json`: el veredicto y los contadores van en la cabecera.
3. Contrasta con `report.html` cuando haya que revisar visualmente.
4. Cada hallazgo tiene id estable, severidad `must/should/nice` y cita oficial. Si una comprobación no se pudo hacer, es `skip`, no un fallo.
5. Re-score sin red cuando quieras recalcular la rúbrica desde la evidencia guardada:

```bash
py seo-auditor/scripts/cli.py rescore reports/mi-sitio/20260101-120000/audit.json
```

6. Declara límites: HTML sin JS ejecutado, `site:` indirecto, CWV no medidos sin API.

## Gate de salida

- `audit.json`, `audit.md` y `report.html` generados y coherentes entre sí.
- Veredicto en una línea con puntuación y contadores 🔴🟡🟢⚪.
- Todos los `skip` explicados como límite.
- Citas presentes en cada comprobación fallida.

## Handoff

`audit.json` es la entrada de `seo-plan` (borradores y PLAN.md) y de `seo-compare` (diff entre auditorías).
