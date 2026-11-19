# Premium Web Designer

> Sistema de diseño y desarrollo de sitios web con dirección de arte, UX/UI y QA independiente medible.
> Website design and development system with art direction, UX/UI and measurable independent QA.

[Español](#español) · [English](#english)

---

## Español

### Índice

1. Propósito
2. Tipos de proyecto
3. Arquitectura
4. Flujo y gates
5. QA y puerta de entrega
6. SEO mínimo
7. Instalación y uso
8. Dependencias y compatibilidad
9. Tests

### Propósito

`premium-web-designer` coordina un flujo de agencia digital para crear, rediseñar, desarrollar y auditar sitios web. Desde la versión 2.1 es un paquete con **maestro + `premium-qa`**: el maestro construye y decide, la sub-skill audita lo ya construido.

### Tipos de proyecto

- Sitios corporativos y landing pages.
- Ecommerce.
- Sitios creativos y portafolios.
- Plataformas SaaS y aplicaciones web.

### Arquitectura

Coordina un orquestador y especialistas de dirección de arte, UX/UI, frontend, backend y QA visual. Usa subagentes nativos cuando la plataforma los ofrece; si no, simula el trabajo de forma secuencial y lo declara.

### Flujo y gates

Discovery → Creative Direction → UX Architecture → Technical Planning → Development → Quality Assurance → Delivery, con gates 1–8. El gate 7 es la auditoría visual independiente y se ejecuta con `premium-qa`.

Los gates medibles no se negocian con impresiones: desbordamiento 0 px, titular de tres líneas como máximo, controles primarios de 44 px, anclas visibles bajo la cabecera fija, versión en los assets locales y foco atrapado en los overlays.

### QA y puerta de entrega

`premium-qa` mide en 360, 390, 768, 1024 y 1440 px, recorre teclado y overlays, comprueba contraste y devuelve un informe con severidad y arreglo propuesto.

La parte estática se comprueba antes, sin navegador:

```bash
py premium-web-designer/scripts/delivery_check.py <carpeta-del-sitio>
```

Revisa `lang`, título, descripción, canonical, Open Graph, un solo `h1`, orden de encabezados, `alt`, JSON-LD, `:focus-visible`, `prefers-reduced-motion`, compensación de cabecera pegajosa, versión en CSS/JS, `robots.txt`, `sitemap.xml` y `llms.txt`. Sale con código 1 si falla una comprobación `must`. En el JSON, `severity` es la escala de riesgo (`high`/`medium`/`low`) y `gate` conserva el nivel de puerta (`must`/`should`/`nice`). Añade `--public` cuando la carpeta vaya a publicarse: entonces canonical, Open Graph con imagen, `robots.txt` y `sitemap.xml` pasan a `must` y bloquean la entrega, y se revisan las cabeceras del hosting (`_headers`, `netlify.toml`, `vercel.json`) para avisar si falta CSP o HSTS.

### SEO mínimo

Cada página pública entrega `lang`, título único de 15–65 caracteres, descripción de 70–165, canonical, Open Graph con imagen, Twitter card, un `h1`, JSON-LD que coincide con lo visible, `robots.txt` con `Sitemap:`, `sitemap.xml` y `llms.txt` cuando el sitio responde a superficies de IA. Las cabeceras de seguridad y la compresión se configuran en el despliegue (CSP, HSTS, `nosniff`, brotli/gzip). La auditoría SEO profunda sigue perteneciendo a `seo-auditor`.

### Instalación y uso

Instala la carpeta completa en una ubicación de descubrimiento compatible: el maestro y `premium-qa` comparten `references/`, `scripts/` y `templates/`.

Ejemplos de peticiones:

- «Crea un sitio corporativo premium para mi empresa».
- «Crea una tienda ecommerce con carrito y checkout verificado».
- «Audita el diseño de mi web en los cinco anchos y dime qué se rompe».

### Dependencias y compatibilidad

La skill no exige lenguaje ni framework. El descubrimiento y la delegación dependen de la plataforma anfitriona: la portabilidad de las instrucciones no garantiza ejecución nativa en todos los agentes. El script de la puerta usa solo la librería estándar de Python 3.9+.

### Tests

```powershell
uv run python premium-web-designer/tests/run_tests.py
```

Nunca afirmes que una prueba se completó si no se ejecutó.

---

## English

### Table of Contents

1. Purpose
2. Project Types
3. Architecture
4. Workflow and Gates
5. QA and Delivery Gate
6. SEO Minimum
7. Installation and Usage
8. Dependencies and Compatibility
9. Tests

### Purpose

`premium-web-designer` coordinates a digital-agency workflow for creating, redesigning, developing and auditing websites. Since 2.1 it is a **master + `premium-qa`** package: the master builds and decides, the sub-skill audits what already exists.

### Project Types

- Corporate websites and landing pages.
- Ecommerce stores.
- Creative websites and portfolios.
- SaaS platforms and web applications.

### Architecture

It coordinates an orchestrator plus art direction, UX/UI, frontend, backend and visual QA specialists. It uses native subagents where available and otherwise simulates the work sequentially and says so.

### Workflow and Gates

Discovery → Creative Direction → UX Architecture → Technical Planning → Development → Quality Assurance → Delivery, with gates 1–8. Gate 7 is the independent visual audit, run through `premium-qa`.

Measurable gates are not settled by impressions: 0 px overflow, a headline of at most three lines, 44 px primary controls, anchors clear of sticky headers, versioned local assets and focus trapped inside overlays.

### QA and Delivery Gate

`premium-qa` measures at 360, 390, 768, 1024 and 1440 px, walks the keyboard and overlay paths, checks contrast and returns a report with severity and a proposed fix.

The static half is checked before that, without a browser:

```bash
py premium-web-designer/scripts/delivery_check.py <site-folder>
```

It covers `lang`, title, description, canonical, Open Graph, a single `h1`, heading order, `alt`, JSON-LD, `:focus-visible`, `prefers-reduced-motion`, sticky-header offset, CSS/JS versioning, `robots.txt`, `sitemap.xml` and `llms.txt`, and exits 1 when any `must` check fails. In the JSON, `severity` is the risk scale (`high`/`medium`/`low`) and `gate` keeps the delivery gate (`must`/`should`/`nice`). Pass `--public` when the folder is going live: canonical, Open Graph with image, `robots.txt` and `sitemap.xml` become `must` and block delivery, and the hosting headers (`_headers`, `netlify.toml`, `vercel.json`) are inspected to warn about a missing CSP or HSTS.

### SEO Minimum

Every public page ships `lang`, a unique 15–65 character title, a 70–165 description, canonical, Open Graph with image, Twitter card, one `h1`, JSON-LD matching visible content, `robots.txt` with `Sitemap:`, `sitemap.xml` and `llms.txt` when the site answers AI surfaces. Security headers and compression belong to the deployment (CSP, HSTS, `nosniff`, brotli/gzip). Deep SEO audits stay in `seo-auditor`.

### Installation and Usage

Install the whole folder in an agent-supported discovery location: the master and `premium-qa` share `references/`, `scripts/` and `templates/`.

Example requests:

- “Create a premium corporate website for my company.”
- “Create an ecommerce experience with a cart and verified checkout.”
- “Audit my site's layout at five widths and tell me what breaks.”

### Dependencies and Compatibility

The skill requires no particular language or framework. Discovery and delegation depend on the host platform: portable instructions do not guarantee native execution on every agent. The gate script uses only the Python 3.9+ standard library.

### Tests

```powershell
uv run python premium-web-designer/tests/run_tests.py
```

Never claim a test was completed unless it was actually performed.
