# Índice de Documentación / Documentation Index

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice
1. [Guías de Módulos](#guías-de-módulos)
2. [Estructura Universal de Habilidades](#estructura-universal-de-habilidades)
3. [Reglas de Seguridad y Ejecución](#reglas-de-seguridad-y-ejecución)

### Guías de Módulos
- [**Agent Red Team**](agent-red-team.md): Auditoría de seguridad estática, análisis AST de scripts Python y detección de inyecciones de prompts ocultas.
- [**Humanizador Anti-IA**](humanizador-anti-ia.md): Reescritura rítmica, entropía léxica, métrica Fernández-Huerta y purga de clichés sintéticos.
- [**Replica**](replica.md): Metodología de reconstrucción funcional limpia (*clean-room*) y protocolo de replicación para suites complejas e interactivas.
- [**SEO Auditor**](seo-auditor.md): Auditoría completa en modos web, source, local e híbrido, validación Schema.org y hoja de ruta estratégica.

### Estructura Universal de Habilidades
Cada módulo se compone de:
- `SKILL.md`: Documento maestro de instrucciones y metadatos.
- `references/`: Conocimiento de dominio especializado y referencias metodológicas.
- `scripts/`: Herramientas deterministas en Python puro sin dependencias externas.
- `templates/`: Plantillas para estructurar los resultados e informes.

### Reglas de Seguridad y Ejecución
1. Todas las herramientas funcionan en modo solo lectura por defecto.
2. No se ejecutan comandos destructivos ni llamadas de red salientes no autorizadas.
3. Compatibilidad completa con la librería estándar de Python sin requerir `pip install`.

---

## 🇬🇧 English

### Table of Contents
1. [Module Guides](#module-guides)
2. [Universal Skill Architecture](#universal-skill-architecture)
3. [Safety and Execution Guidelines](#safety-and-execution-guidelines)

### Module Guides
- [**Agent Red Team**](agent-red-team.md): Static security auditing, Python AST code inspection, and hidden prompt injection detection.
- [**Humanizador Anti-IA**](humanizador-anti-ia.md): Sentence rhythm rewriting, lexical entropy, Fernández-Huerta readability, and synthetic cliché elimination.
- [**Replica**](replica.md): Clean-room functional reverse-engineering methodology and complex engine replication protocol.
- [**SEO Auditor**](seo-auditor.md): Multi-mode SEO auditing (web, source, local, hybrid), Schema.org validation, and strategic roadmap.

### Universal Skill Architecture
Each module includes:
- `SKILL.md`: Master instruction file with execution frontmatter.
- `references/`: Domain-specific reference materials and methodologies.
- `scripts/`: Deterministic utilities written in pure standard Python.
- `templates/`: Markdown and CSV templates for consistent reporting.

### Safety and Execution Guidelines
1. All tools operate in read-only mode by default.
2. No destructive commands or unauthorized outbound network requests are performed.
3. 100% Python standard library compatibility without `pip install` requirements.
