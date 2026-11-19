# Guía rápida de uso

Todos los comandos funcionan con `py` en Windows (Python 3.9+, solo stdlib). En Linux/macOS sustituye `py` por `python3`.
Desde la raíz del repositorio:

```bash
py seo-auditor/scripts/cli.py --help
```

Desde la carpeta `seo-auditor/`:

```bash
py scripts/cli.py --help
```

## Flags comunes

| Flag | Comandos | Qué hace |
|---|---|---|
| `--allow-local` | `audit`, `index`, `serp`, `perf`, `headers`, `schema`, `hreflang`, `onpage` | Permite destinos en loopback y redes privadas (`localhost`, `127.0.0.1`, `::1`, rangos privados). Sin él se rechazan. En `--mode local` y `--mode hybrid` el destino local ya está permitido. |
| `--no-rich-preview` | `schema` | No escribe `schema/rich-preview.html`; el inventario JSON-LD y sus hallazgos se mantienen. `--rich-preview` es el comportamiento por defecto. |

## 1. Auditar código fuente local

```bash
py scripts/cli.py audit . --mode source
```

## 2. Auditar una aplicación web en desarrollo local

```bash
py scripts/cli.py audit http://localhost:3000 --mode local
```

## 3. Auditoría híbrida (código + ejecución local)

```bash
py scripts/cli.py audit . --mode hybrid --base-url http://localhost:3000
```

## 4. Auditar una web pública

```bash
py scripts/cli.py audit https://example.com --mode web --max-pages 30 --rate 1
```

El crawl respeta `robots.txt`, hace 1 petición/segundo y declara el tope de páginas en el informe.

## 5. Analizar una sola página (archivo o URL)

```bash
py scripts/cli.py audit pagina.html --mode page
py scripts/cli.py audit https://example.com/landing --mode page
```

## 6. Módulos IndexPulse → comando

| # | Módulo de IndexPulse | Comando nuestro | Qué produce | Estado |
|---|---|---|---|---|
| 1 | Diagnóstico de indexación (presencia por motor) | `index --presence` | Presencia `site:` por motor, **indirecta** y marcada `estimate` | ✅ cubierto (sin API oficial, por diseño) |
| 1b | Directivas técnicas cruzadas | `index` / `audit` | robots.txt, meta robots, `X-Robots-Tag`, canonical, sitemap + conflictos | ✅ cubierto |
| 2 | Simulador SERP + tarjetas sociales | `serp` | `output/serp/preview.html` con Google escritorio/móvil, Bing, WhatsApp/Facebook/LinkedIn/X y medidor de ancho | ✅ cubierto |
| 3 | Velocidad y Core Web Vitals | `perf` | TTFB, peso HTML, gzip/brotli, CSS/JS externos (medido); CWV solo con dato externo o `estimate` + enlace a PSI | ✅ cubierto con límite declarado |
| 4 | Auditoría de seguridad HTTP | `headers` | Score 0–100 (HSTS, CSP, XFO, XCTO, RP, PP) + mixed content | ✅ cubierto |
| 5 | Schema.org / Rich Snippets | `schema --rich-preview` | Inventario de `@type` + `schema/rich-preview.html` con lo que falta | ✅ cubierto |
| 6 | SEO internacional `hreflang` | `hreflang` | Pares, autorreferencia, `<html lang>`, `x-default`, retorno bidireccional | ✅ cubierto |
| 7 | On-page exhaustivo | `onpage` | Ratio texto/HTML, jerarquía H1–H4, imágenes sin `alt`, tabla de densidad | ✅ cubierto |
| 8 | Checklist unificada + exportación PDF | `audit` → `report.html` | Informe con filtros 🔴🟡🟢 e instrucción **Imprimir → PDF** | ✅ cubierto (HTML, no PDF nativo) |

### Comandos de módulo

```bash
py scripts/cli.py serp pagina.html --title "Título alternativo" --description "Descripción alternativa"
py scripts/cli.py perf https://example.com
py scripts/cli.py headers https://example.com
py scripts/cli.py schema pagina.html --rich-preview
py scripts/cli.py hreflang pagina.html
py scripts/cli.py onpage pagina.html
py scripts/cli.py index pagina.html --robots ./robots.txt
py scripts/cli.py index https://example.com --presence
```

## 7. Re-score sin red

Recalcula rúbrica, puntuación y veredicto desde la evidencia guardada:

```bash
py scripts/cli.py rescore reports/mi-sitio/20260101-120000/audit.json
```

Escribe `audit.rescored.json`, `audit.rescored.md` y `report.rescored.html`. No abre conexiones.

## 8. Comparar dos auditorías (compare / monitor)

```bash
py scripts/cli.py compare audit-antes.json audit-despues.json --output output/compare
```

Clasifica cada comprobación en **mejorado / empeorado / nuevo / resuelto**, con delta de puntuación y aviso de nuevos fallos `must`.

## 9. Execute con dry-run

```bash
# 1) Genera borradores DRAFT en output/
py scripts/cli.py fix --input reports/mi-sitio/20260101-120000/audit.json --output output

# 2) Revisa output/robots.txt.draft, meta-tags.html.draft, jsonld.json.draft, llms.txt.draft y PLAN.md
# 3) Aplica solo lo aplicable, con confirmación
py scripts/cli.py fix --input .../audit.json --output output --apply --dest ./mi-proyecto
```

Solo `robots.txt`, `llms.txt` y `llms-full.txt` se copian; los snippets de meta tags y JSON-LD se integran a mano. Cualquier archivo sobrescrito deja un `.bak`.

## 10. Flujo recomendado (Audit → Plan → Execute)

1. **Audit:** `audit` genera `audit.json` + `audit.md` + `report.html`.
2. **Plan:** `fix` sin `--apply` produce `PLAN.md` con acciones ordenadas por severidad y cita.
3. **Execute:** tras revisar los `TODO`, `fix --apply --dest` escribe copias y backups.
4. **Verificar:** vuelve a auditar y usa `compare` para confirmar la mejora con evidencia.

## 11. Uso con cualquier Asistente de IA

- **Activación automática:** el asistente lee `SKILL.md` y decide cuándo activar la skill.
- **Consultas modulares:** `references/` para el análisis técnico, de contenido, GEO o datos estructurados.
- **Herramientas deterministas:** el asistente ejecuta el CLI para recabar métricas sin inventar datos.
- **Informes:** las plantillas de `templates/` marcan la estructura; el motor rellena la evidencia.
