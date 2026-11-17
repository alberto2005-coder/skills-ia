# Premium Web Designer

> Sistema de diseño y desarrollo de sitios web con dirección de arte, UX/UI y QA independiente.  
> Website design and development system with art direction, UX/UI and independent QA.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice
1. [Propósito](#propósito)
2. [Tipos de proyecto](#tipos-de-proyecto)
3. [Arquitectura](#arquitectura)
4. [Diseño y flujo](#diseño-y-flujo)
5. [Instalación y uso](#instalación-y-uso)
6. [Dependencias y compatibilidad](#dependencias-y-compatibilidad)
7. [Tests](#tests)

### Propósito
`premium-web-designer` coordina un flujo de agencia digital para crear, rediseñar, desarrollar y auditar sitios web. Es una skill independiente: no tiene sub-skills.

### Tipos de proyecto
- Sitios corporativos y landing pages.
- Ecommerce.
- Sitios creativos y portafolios.
- Plataformas SaaS y aplicaciones web.

### Arquitectura
Coordina un orquestador de proyecto y especialistas de dirección de arte, UX/UI, frontend, backend y QA visual. Usa subagentes nativos cuando la plataforma los ofrece; si no, simula el trabajo de forma secuencial.

### Diseño y flujo
Cada proyecto recibe una dirección creativa propia. El sistema prioriza identidad visual original, tipografía profesional, composición intencional, diseño responsive, interacciones útiles, accesibilidad, rendimiento y código mantenible.

Flujo: **Discovery → Creative Direction → UX Architecture → Technical Planning → Development → Quality Assurance → Delivery**.

Las instrucciones internas están en inglés; la skill entiende peticiones multilingües y se comunica en el idioma preferido por el usuario. El contenido del sitio se genera en el idioma solicitado.

### Instalación y uso
Instala la carpeta completa en una ubicación de descubrimiento de skills compatible con el agente. Algunas plataformas requieren una ruta o configuración propia.

Ejemplos de peticiones:
- «Crea un sitio corporativo premium para mi empresa».
- «Rediseña este proyecto con Premium Web Designer».
- «Crea una tienda ecommerce con descubrimiento de productos, carrito y checkout verificado».
- «Haz una auditoría visual y técnica completa».

La personalización específica de cada proyecto pertenece a `project-brief.md`, `design-system.md` y `AGENTS.md`; el núcleo universal no debe acoplarse a preferencias de un único proyecto.

### Dependencias y compatibilidad
La skill no exige un lenguaje ni framework concreto. Cada proyecto puede necesitar Node.js, un gestor de paquetes, un framework frontend, herramientas de pruebas de navegador, herramientas de diseño o servicios backend; instala únicamente lo que requiera el proyecto.

Las instrucciones se basan en Markdown y frontmatter YAML. La disponibilidad de descubrimiento nativo y delegación depende de la plataforma: la portabilidad de instrucciones no garantiza ejecución nativa en todos los agentes.

### Tests
Ejecuta la suite desde la raíz del repositorio:

```powershell
uv run python premium-web-designer/tests/run_tests.py
```

La skill no debe afirmar que una prueba se completó si no se ejecutó realmente.

---

## 🇬🇧 English

### Table of Contents
1. [Purpose](#purpose)
2. [Project Types](#project-types)
3. [Architecture](#architecture)
4. [Design and Workflow](#design-and-workflow)
5. [Installation and Usage](#installation-and-usage)
6. [Dependencies and Compatibility](#dependencies-and-compatibility)
7. [Tests](#tests-1)

### Purpose
`premium-web-designer` coordinates a digital-agency workflow for creating, redesigning, developing and auditing websites. It is a standalone skill with no sub-skills.

### Project Types
- Corporate websites and landing pages.
- Ecommerce stores.
- Creative websites and portfolios.
- SaaS platforms and web applications.

### Architecture
It coordinates a project orchestrator and specialists for art direction, UX/UI, frontend, backend and visual QA. It uses native subagents where available and otherwise simulates the specialist workflow sequentially.

### Design and Workflow
Every project gets a distinctive creative direction. The system prioritizes original visual identities, professional typography, intentional composition, responsive design, meaningful interactions, accessibility, performance and maintainable code.

Workflow: **Discovery → Creative Direction → UX Architecture → Technical Planning → Development → Quality Assurance → Delivery**.

Internal instructions are written in English. The skill understands multilingual requests and communicates in the user's preferred language; website content is generated in the requested language.

### Installation and Usage
Install the complete folder in an agent-supported skill discovery location. Some platforms require their own native path or configuration.

Example requests:
- “Create a premium corporate website for my company.”
- “Redesign this project using Premium Web Designer.”
- “Create an ecommerce experience with product discovery, a cart and verified checkout.”
- “Perform a complete visual and technical audit.”

Project-specific customization belongs in `project-brief.md`, `design-system.md` and `AGENTS.md`; keep the universal core independent from individual project preferences.

### Dependencies and Compatibility
The skill does not require a particular programming language or framework. Individual projects may need Node.js, a package manager, a frontend framework, browser testing tools, design tools or backend services; install only what the project requires.

The core instructions use Markdown and YAML frontmatter. Native agent discovery and delegation depend on the host platform: portable instructions do not guarantee native execution on every agent.

### Tests
Run the suite from the repository root:

```powershell
uv run python premium-web-designer/tests/run_tests.py
```

Never claim a test was completed unless it was actually performed.
