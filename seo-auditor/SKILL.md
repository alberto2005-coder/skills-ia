---
name: seo-auditor
description: Audita y optimiza el SEO de cualquier sitio web público, código fuente local, servidor en desarrollo o modo híbrido. Cubre diagnóstico técnico (rastreabilidad, indexabilidad, canonicals, HTTP), contenido y metadatos, optimización para motores generativos de IA (GEO / AI Search), datos estructurados (Schema.org), sitemaps y estrategia accionable. Incluye motor de auditoría en Python y plantillas de informes. Úsala siempre que el usuario solicite auditar una web, revisar el código/SEO de un repositorio, preparar contenidos para IA/GEO, optimizar páginas individuales o diseñar una estrategia SEO.
---

# SEO Auditor

Sistema integral de auditoría, optimización técnica y estrategia SEO para cualquier entorno: **web pública, código fuente local, servidor en desarrollo o modo híbrido**.

## Cuándo usar esta skill

- Cuando el usuario solicite auditar un dominio web, una URL específica o un proyecto de código local.
- Para diagnosticar problemas técnicos de rastreo, indexación, canonicalización, códigos de estado HTTP o robots.
- Para evaluar la calidad on-page del contenido, arquitectura de encabezados, intención de búsqueda y metadatos.
- Para preparar contenidos frente a motores de búsqueda con IA generativa (**GEO / AI Search** en Google AI Overviews, Perplexity, ChatGPT, Gemini).
- Para auditar y validar datos estructurados (`JSON-LD` / Schema.org) y sitemaps XML.
- Para diseñar una hoja de ruta priorizada y un plan de acción SEO a 30, 60 y 90 días.

---

## Reglas duras y principios innegociables

1. **Solo lectura:** La auditoría analiza e inspecciona, nunca modifica código en producción, ni ejecuta scripts intrusivos, ni realiza mutaciones sin petición explícita del usuario.
2. **Evidencia observable antes que opinión:** Todo hallazgo debe sustentarse en evidencias verificables (código, cabeceras HTTP, extractos de contenido). Separa siempre lo **observado**, lo **inferido** y lo **no comprobado** (`unknown`).
3. **Cero datos inventados:** Prohibido alucinar rankings, volumen de tráfico, backlinks o posiciones en motores de IA. Si un dato no se puede comprobar sin herramientas externas (Search Console, Analytics), decláralo abiertamente.
4. **No etiquetar como error lo no verificado:** Un elemento no comprobable o una convención desconocida no es un fallo; se marca como hipótesis o pendiente de validación.
5. **Puntuaciones heurísticas:** La puntuación del motor es una métrica indicativa interna de salud del sitio, nunca una calificación oficial de Google.
6. **Seguridad y límites:** El rastreador web rechaza destinos privados/locales para prevenir SSRF. En modo local solo se permite loopback (`localhost`, `127.0.0.1`). Nunca se inspeccionan `.env`, certificados ni credenciales.

---

## Módulos y Pipeline de Auditoría

El sistema organiza la auditoría en 8 módulos especializados. Se puede ejecutar una auditoría integral o consultar un módulo específico según la necesidad:

| # | Módulo | Referencia | Foco / Salida |
|---|---|---|---|
| **00** | Metodología y Seguridad | `references/00-metodologia.md` | Principios, clasificación de severidad y límites |
| **01** | Diagnóstico Técnico | `references/01-tecnico.md` | Rastreo, indexabilidad, canonical, HTTP, robots |
| **02** | Contenido y On-Page | `references/02-contenido.md` | Metadatos, intención, encabezados H1-H6, utilidad |
| **03** | GEO y Búsqueda con IA | `references/03-geo-ai.md` | Preparación para LLMs (Perplexity, AI Overviews, citabilidad) |
| **04** | Schema y Datos Estructurados | `references/04-schema.md` | JSON-LD, tipos Schema.org y validación de entidades |
| **05** | Sitemap XML | `references/05-sitemap.md` | Descubrimiento de URLs, index vs urlset y canonicals |
| **06** | Estrategia y Plan de Acción | `references/06-estrategia.md` | Silos, resolución de canibalización y roadmap 30/60/90 días |
| **07** | Página Individual | `references/07-pagina-individual.md` | Diagnóstico quirúrgico de una sola URL o plantilla HTML |

> **Nota:** Al abordar un área específica, **lee su referencia correspondiente** en `references/` para asegurar el máximo rigor analítico.

---

## Herramientas deterministas (Scripts en `scripts/`)

Motor determinista en Python 3.8+ sin dependencias externas obligatorias:

```bash
# Modo 1: Web pública (rastreo HTTP controlado)
python scripts/audit.py https://example.com --mode web --max-pages 30

# Modo 2: Código fuente local (inspección de archivos estáticos/plantillas)
python scripts/audit.py . --mode source

# Modo 3: Servidor local (localhost ya en ejecución)
python scripts/audit.py http://localhost:3000 --mode local --max-pages 20

# Modo 4: Modo híbrido (código fuente + servidor local)
python scripts/audit.py . --mode hybrid --base-url http://localhost:3000
```

*Los informes generados se guardan automáticamente en `reports/<proyecto>/<timestamp>/` en formato Markdown y JSON.*

---

## Flujo de trabajo obligatorio

1. **Definir el objetivo y modo de auditoría:**
   - Si es un sitio en producción accesible: modo `web`.
   - Si es un repositorio de código o plantillas: modo `source`.
   - Si la aplicación está corriendo en desarrollo local: modo `local`.
   - Si se dispone tanto del código como del servidor local levantado: modo `hybrid`.
2. **Ejecutar el escaneo determinista:** Ejecutar el comando pertinente en `scripts/audit.py` para recopilar datos base (títulos, encabezados, canonicals, enlaces rotos, Schema, tiempos).
3. **Analizar los módulos especializados:**
   - Consultar `references/01-tecnico.md` para indexabilidad y arquitectura.
   - Consultar `references/02-contenido.md` y `references/03-geo-ai.md` para calidad semántica y citabilidad.
   - Consultar `references/04-schema.md` y `references/05-sitemap.md` para datos estructurados y sitemaps.
4. **Sintetizar y priorizar hallazgos:**
   - Agrupar los problemas por severidad (**Critical**, **High**, **Medium**, **Low**) y asignar el nivel de confianza (**High**, **Medium**, **Low**).
   - Utilizar las plantillas de `templates/audit-report.md` y `templates/action-plan.md`.
5. **Entregar informe ejecutivo y hoja de ruta:**
   - Resumen ejecutivo claro con impacto para el negocio.
   - Tabla de hallazgos con evidencia directa y recomendación técnica.
   - Plan de acción estructurado a 0-30, 30-60 y 60-90 días.
