# SEO Auditor

> Sistema integral de auditoría SEO técnica, semántica y estructural.  
> Comprehensive technical, content, structured data, and structural SEO audit engine.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice
1. [Visión General](#visión-general)
2. [Modos de Operación](#modos-de-operación)
3. [Módulos de Referencia](#módulos-de-referencia)
4. [Herramientas del Motor](#herramientas-del-motor)
5. [Ejemplos de Ejecución](#ejemplos-de-ejecución)
6. [Plantillas de Informe](#plantillas-de-informe)

### Visión General
`seo-auditor` evalúa sitios web públicos, código fuente local, instancias de desarrollo en localhost y entornos híbridos. Genera informes deterministas con evidencias, niveles de severidad y confianza, respetando límites de seguridad (SSRF) y modo solo lectura.

### Modos de Operación
- **`web`**: Rastreo HTTP controlado sobre dominios públicos autorizados.
- **`source`**: Inspección estática de código fuente, plantillas y archivos HTML/JSX sin levantar servidor.
- **`local`**: Rastreo de una aplicación en ejecución en loopback (`localhost`, `127.0.0.1`).
- **`hybrid`**: Combina el análisis del código fuente con la inspección en vivo del servidor local.

### Módulos de Referencia
Ubicados en `seo-auditor/references/`:
- `00-metodologia.md`: Principios de evidencia, severidad (Critical/High/Med/Low) y límites seguros.
- `01-tecnico.md`: Códigos HTTP, robots.txt, canonicals, hreflang y renderizado.
- `02-contenido.md`: Títulos, meta descriptions, jerarquía H1–H6 y cobertura temática.
- `03-geo-ai.md`: Preparación para motores generativos (AI Overviews, Perplexity, citabilidad).
- `04-schema.md`: Datos estructurados JSON-LD y validación de tipos Schema.org.
- `05-sitemap.md`: Coherencia de sitemaps XML, índices y concordancia canónica.
- `06-estrategia.md`: Resolución de canibalización, clusters temáticos y roadmap 30/60/90 días.
- `07-pagina-individual.md`: Análisis quirúrgico sobre una URL o archivo específico.

### Herramientas del Motor
- `scripts/audit.py`: Punto de entrada directo compatible con terminales y agentes.
- `scripts/cli.py`: Módulo de argumentos y orquestación.
- `scripts/source_audit.py`: Analizador estático de HTML y plantillas.
- `scripts/web_audit.py`: Rastreador HTTP seguro con protección SSRF.
- `scripts/report.py`: Generador de informes Markdown y JSON con puntuación heurística.

### Ejemplos de Ejecución
```bash
# Auditar web pública
python seo-auditor/scripts/audit.py https://example.com --mode web --max-pages 30

# Auditar repositorio de código local
python seo-auditor/scripts/audit.py ./mi-proyecto --mode source

# Auditar servidor en localhost
python seo-auditor/scripts/audit.py http://localhost:3000 --mode local

# Auditoría híbrida (código local + servidor)
python seo-auditor/scripts/audit.py ./mi-proyecto --mode hybrid --base-url http://localhost:3000
```

### Plantillas de Informe
Ubicadas en `seo-auditor/templates/`:
- `audit-report.md`: Estructura para el informe de hallazgos por área técnica.
- `action-plan.md`: Matriz priorizada de acciones P1/P2/P3 con responsables y esfuerzo.

---

## 🇬🇧 English

### Table of Contents
1. [Overview](#overview)
2. [Operating Modes](#operating-modes)
3. [Reference Modules](#reference-modules)
4. [Engine Tools](#engine-tools)
5. [Execution Examples](#execution-examples)
6. [Reporting Templates](#reporting-templates)

### Overview
`seo-auditor` analyzes public websites, local source code repositories, development servers on localhost, and hybrid configurations. It outputs deterministic reports with verifiable evidence, severity levels, and confidence scores under safe SSRF boundaries and read-only mode.

### Operating Modes
- **`web`**: Controlled HTTP crawl against authorized public domains.
- **`source`**: Static inspection of source code, templates, and HTML/JSX files without running a server.
- **`local`**: Crawl of an active development server on loopback (`localhost`, `127.0.0.1`).
- **`hybrid`**: Combines source code static analysis with dynamic live verification on localhost.

### Reference Modules
Located in `seo-auditor/references/`:
- `00-metodologia.md`: Evidence principles, severity tiers, and safe boundaries.
- `01-tecnico.md`: HTTP status codes, robots.txt, canonicals, hreflang, and rendering.
- `02-contenido.md`: Title tags, meta descriptions, H1–H6 hierarchy, and search intent.
- `03-geo-ai.md`: Generative Engine Optimization (AI Overviews, Perplexity, citability).
- `04-schema.md`: JSON-LD structured data and Schema.org entity validation.
- `05-sitemap.md`: XML sitemap structure, index files, and canonical alignment.
- `06-estrategia.md`: Cannibalization resolution, topic clusters, and 30/60/90-day roadmaps.
- `07-pagina-individual.md`: Deep-dive audit for a single page or template.

### Engine Tools
- `scripts/audit.py`: Direct execution entrypoint for terminals and agents.
- `scripts/cli.py`: CLI arguments and workflow orchestration.
- `scripts/source_audit.py`: HTML and template static analyzer.
- `scripts/web_audit.py`: Safe HTTP crawler with SSRF protection.
- `scripts/report.py`: Generates Markdown and JSON reports with heuristic scoring.

### Execution Examples
```bash
# Audit a public website
python seo-auditor/scripts/audit.py https://example.com --mode web --max-pages 30

# Audit local source code repository
python seo-auditor/scripts/audit.py ./my-project --mode source

# Audit localhost development server
python seo-auditor/scripts/audit.py http://localhost:3000 --mode local

# Hybrid audit (local code + live server)
python seo-auditor/scripts/audit.py ./my-project --mode hybrid --base-url http://localhost:3000
```

### Reporting Templates
Located in `seo-auditor/templates/`:
- `audit-report.md`: Structure for categorized technical findings.
- `action-plan.md`: Prioritized action matrix (P1/P2/P3) with effort and validation criteria.
