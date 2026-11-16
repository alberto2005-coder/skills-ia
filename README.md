# Skills IA

> Repositorio universal de habilidades modulares para agentes y asistentes de IA.  
> Universal repository of modular skills for AI agents and assistants.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice
1. [Visión General](#visión-general)
2. [Módulos Incluidos](#módulos-incluidos)
3. [Estructura Estándar de cada Skill](#estructura-estándar-de-cada-skill)
4. [Documentación Técnica](#documentación-técnica)
5. [Requisitos y Filosofía de Cero Dependencias](#requisitos-y-filosofía-de-cero-dependencias)
6. [Licencia](#licencia)

### Visión General
**Skills IA** es una colección de habilidades modulares, deterministas e independientes diseñadas para ser integradas en cualquier asistente de Inteligencia Artificial (Claude, Gemini, ChatGPT, Antigravity, Cursor, etc.). Cada habilidad es autosuficiente y opera sin alterar paquetes globales ni requerir dependencias complejas.

### Módulos Incluidos

| Módulo | Propósito | Scripts |
| :--- | :--- | :--- |
| **[`agent-red-team`](agent-red-team/)** | Auditoría estática de seguridad, análisis AST y detección de inyecciones de prompts en paquetes de instrucciones. | `scan_skill.py`, `sanitize_unicode.py` |
| **[`humanizador-anti-ia`](humanizador-anti-ia/)** | Reescritura para eliminar patrones mecánicos de IA, mejorar el ritmo sintáctico (*burstiness*) y enriquecer la perplejidad léxica. | `audit_style.py` |
| **[`replica`](replica/)** | Reconstrucción funcional *clean-room* de aplicaciones (desde SaaS hasta editores de alta complejidad como procesadores de texto). | `parity.py`, `sweep.py`, `contrast.py`, etc. |
| **[`seo-auditor`](seo-auditor/)** | Auditoría SEO técnica, de contenido, datos estructurados (Schema.org), sitemaps y optimización para motores de IA (GEO). | `audit.py`, `cli.py` |

### Estructura Estándar de cada Skill
Cada carpeta del repositorio sigue una arquitectura estandarizada:
- `SKILL.md`: Frontmatter YAML con reglas de activación, alcance e instrucciones de ejecución.
- `references/`: Guías de conocimiento técnico, metodologías y listas de verificación.
- `scripts/`: Herramientas deterministas escritas exclusivamente con la biblioteca estándar de Python.
- `templates/`: Plantillas en Markdown, CSV o JSON para salidas estructuradas.

### Documentación Técnica
Las guías completas de cada módulo se encuentran en la carpeta [`docs/`](docs/):
- [Índice de Documentación](docs/index.md)
- [Guía de Agent Red Team](docs/agent-red-team.md)
- [Guía de Humanizador Anti-IA](docs/humanizador-anti-ia.md)
- [Guía de Replica](docs/replica.md)
- [Guía de SEO Auditor](docs/seo-auditor.md)

### Requisitos y Filosofía de Cero Dependencias
- **Python 3.8+** (utiliza únicamente la librería estándar de Python: `argparse`, `re`, `ast`, `math`, `urllib`, `html.parser`, `json`).
- No requiere `pip install` ni instalación de paquetes globales en el sistema.

### Licencia
Distribuido bajo la [Licencia MIT](LICENSE).

---

## 🇬🇧 English

### Table of Contents
1. [Overview](#overview)
2. [Included Modules](#included-modules)
3. [Standard Skill Structure](#standard-skill-structure)
4. [Technical Documentation](#technical-documentation)
5. [Requirements and Zero-Dependency Philosophy](#requirements-and-zero-dependency-philosophy)
6. [License](#license)

### Overview
**Skills IA** is a collection of modular, deterministic, and self-contained agent skills designed for integration with any AI assistant (Claude, Gemini, ChatGPT, Antigravity, Cursor, etc.). Each skill is independent and operates without modifying global packages or requiring third-party libraries.

### Included Modules

| Module | Purpose | Scripts |
| :--- | :--- | :--- |
| **[`agent-red-team`](agent-red-team/)** | Static security audit, AST code inspection, and prompt injection detection in instruction packages. | `scan_skill.py`, `sanitize_unicode.py` |
| **[`humanizador-anti-ia`](humanizador-anti-ia/)** | Stylistic rewriting to eliminate AI writing patterns, enhance sentence burstiness, and improve vocabulary entropy. | `audit_style.py` |
| **[`replica`](replica/)** | Clean-room functional specification and reverse-engineering of software (from SaaS to complex engines like word processors). | `parity.py`, `sweep.py`, `contrast.py`, etc. |
| **[`seo-auditor`](seo-auditor/)** | Technical, content, structured data (Schema.org), sitemap, and generative engine optimization (GEO) audits. | `audit.py`, `cli.py` |

### Standard Skill Structure
Each skill directory follows a unified layout:
- `SKILL.md`: YAML frontmatter with activation triggers, boundaries, and execution rules.
- `references/`: Modular technical guides, methodologies, and checklists.
- `scripts/`: Deterministic utilities built strictly with the Python standard library.
- `templates/`: Markdown, CSV, or JSON templates for consistent artifact generation.

### Technical Documentation
Comprehensive module documentation is available in the [`docs/`](docs/) directory:
- [Documentation Index](docs/index.md)
- [Agent Red Team Guide](docs/agent-red-team.md)
- [Humanizador Anti-IA Guide](docs/humanizador-anti-ia.md)
- [Replica Guide](docs/replica.md)
- [SEO Auditor Guide](docs/seo-auditor.md)

### Requirements and Zero-Dependency Philosophy
- **Python 3.8+** (uses only standard library modules: `argparse`, `re`, `ast`, `math`, `urllib`, `html.parser`, `json`).
- Zero `pip install` requirements and zero global package installations.

### License
Distributed under the [MIT License](LICENSE).
