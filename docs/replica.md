# Replica

> Reconstrucción funcional clean-room de software, por fases y con evidencia.  
> Clean-room functional reconstruction of software, phase by phase, with evidence.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice

1. [Filosofía Clean-Room](#filosofía-clean-room)
2. [Pipeline de 14 Fases (0–13)](#pipeline-de-14-fases-013)
3. [Sub-skills](#sub-skills)
4. [Comando Maestro y Estado](#comando-maestro-y-estado)
5. [Evidencia Obligatoria](#evidencia-obligatoria)
6. [Herramientas Deterministas](#herramientas-deterministas)
7. [Plantillas](#plantillas)
8. [Uso y Tests](#uso-y-tests)

### Filosofía Clean-Room

`replica` reconstruye **lo que una aplicación hace**, no lo que posee. Solo fuentes públicas, documentación, help center, store listing, reseñas públicas y **tu propia cuenta**. Nunca código, assets, textos ni bases de datos del original. Si sus términos prohíben un competidor, se dice y se limita a fuentes públicas; la decisión legal es del usuario.

**Paquete de 14 skills:** maestro + 13 sub-skills, una por bloque de fases.

### Pipeline de 14 Fases (0–13)

| # | Fase | Sub-skill | Salida en `replica/` |
|---|---|---|---|
| 0 | Límites y alcance | `replica-recon` | `scope.md` |
| 1 | Reconocimiento por función | `replica-recon` | `recon.md`, `features.csv`, `screens/` |
| 1b | Apps complejas (Word, Figma, suites) | `replica-recon` | `complex-app-spec.md` |
| 2 | Arquitectura | `replica-architect` | `architecture.md` |
| 3 | Sistema de diseño | `replica-design` | `design/tokens.json`, `design/components.md` |
| 4 | Construcción | `replica-build` | código + `features.csv` actualizado |
| 5 | Backend (auth, datos, pagos) | `replica-backend` | `backend.md` |
| 6 | Pruebas | `replica-test` | `test-plan.md`, `bugs.md` |
| 7 | Paridad | `replica-diff` | `parity.md`, `diff/*.png` |
| 8 | Voz del usuario | `replica-entrepreneur` | `reviews.csv`, `themes.md`, `fix-plan.md` |
| 9 | Marca (rebrand) | `replica-brand` | `brand/*` + código limpio |
| 10 | Lanzamiento | `replica-launch` | landing, `launch/listing.json`, `launch/paises.md` |
| 11 | Despliegue | `replica-deploy` | `preflight.md`, app live |
| 12 | Análisis estático (**opt-in**) | `replica-static` | `static/static-report.md`, `static/hallazgos-*.json` |
| 13 | Redes (**opt-in**) | `replica-redes` | `launch/redes.md` |

La fase 12 exige petición explícita, artefacto propio o autorizado y herramientas ya instaladas (nunca DRM, logins ajenos ni paywalls). La 13 va siempre después de la marca (9) y el lanzamiento (10). Cualquier fase puede ejecutarse suelta.

### Sub-skills

| Sub-skill | Fases | Qué hace |
|---|---|---|
| `replica-recon` | 0, 1, 1b | Límites legales, alcance, inventario de funciones con evidencia y especificación de apps complejas. |
| `replica-architect` | 2 | Stack, módulos, modelo de datos con invariantes y contratos entre capas. |
| `replica-design` | 3 | Tokens, componentes y estados con identidad propia, validados con contraste WCAG. |
| `replica-build` | 4 | Construcción por incrementos que cierran flujos `must`. |
| `replica-backend` | 5 | Auth, esquema con migraciones, permisos por recurso, pagos y jobs. |
| `replica-test` | 6 | Plan y ejecución de pruebas, invariantes y bugs S1/S2/S3. |
| `replica-diff` | 7 | Paridad funcional (`parity.py`) y visual (`imgdiff.py`). |
| `replica-entrepreneur` | 8 | Reseñas reales con cita y URL, temas y plan de mejoras. |
| `replica-brand` | 9 | Rebrand completo y `sweep.py` a 0. |
| `replica-launch` | 10 | Landing, listing de tiendas y precios por país. |
| `replica-deploy` | 11 | Preflight, backups y publicación verificada. |
| `replica-static` | 12 | Análisis estático autorizado, con límites declarados. |
| `replica-redes` | 13 | 3 guiones de Reels, captions y banco de ganchos. |

### Comando Maestro y Estado

El maestro (`replica/SKILL.md`) arranca o retoma el pipeline: lee `replica/progreso.md`, recorre las fases en orden, **para al final de cada una** y pide aprobación explícita. Guarda fase, estado (`pendiente` · `en curso` · `aprobada` · `bloqueada` · `n/a`), decisiones, bloqueos y bitácora. Un gate rojo deja la fase `bloqueada`; no se rodea.

### Evidencia Obligatoria

En recon (1), paridad (7) y análisis estático (12) todo hallazgo que sostenga una decisión usa `templates/evidence.md`: **Fuente · Observación · Inferencia · Confianza (high/medium/low/THIN) · Límites y desconocidos**. Sin fuente, el hallazgo se descarta; `THIN` (<3 muestras o una sola fuente) no se usa como argumento.

### Herramientas Deterministas

- `parity.py`: paridad funcional ponderada (must 3 / should 2 / could 1), falla si queda un `must`.
- `sweep.py`: nombre, dominio, colores e identificadores del original; exit 1 si hay restos.
- `contrast.py`: WCAG AA/AAA sobre los tokens.
- `imgdiff.py`: diff de layout por regiones, sin penalizar el color.
- `reviews.py`: temas y citas literales con URL; descarta filas sin enlace.
- `listing.py`: límites de App Store/Play, claims y nombre del original.

### Plantillas

`scope.md`, `architecture.md`, `complex-app-spec.md`, `test-plan.md`, `preflight.md`, `evidence.md`, `progreso.md`, `reels.md`, `features.csv`, `tokens.json`, `reviews.csv`, `themes.json`, `listing.json`.

### Uso y Tests

```bash
# Paridad funcional
py replica/scripts/parity.py replica/features.csv --markdown --out replica/parity.md

# Sweep de marca
py replica/scripts/sweep.py . --avoid "App Original" --avoid apporiginal.com

# Tests del paquete
py -m unittest discover -s replica/tests -v
```

---

## 🇬🇧 English

### Table of Contents

1. [Clean-Room Philosophy](#clean-room-philosophy)
2. [14-Phase Pipeline (0–13)](#14-phase-pipeline-013)
3. [Sub-skills](#sub-skills-1)
4. [Master Command and State](#master-command-and-state)
5. [Mandatory Evidence](#mandatory-evidence)
6. [Deterministic Tools](#deterministic-tools)
7. [Templates](#templates)
8. [Usage and Tests](#usage-and-tests)

### Clean-Room Philosophy

`replica` reconstructs **what an application does**, not what it owns. Only public sources, docs, help center, store listing, public reviews and **your own account**. Never the original's code, assets, copy or databases. If its terms forbid a competitor, say so and stay on public sources; the legal call belongs to the user.

**14-skill package:** master + 13 sub-skills, one per phase block.

### 14-Phase Pipeline (0–13)

| # | Phase | Sub-skill | Output in `replica/` |
|---|---|---|---|
| 0 | Boundaries and scope | `replica-recon` | `scope.md` |
| 1 | Feature-based reconnaissance | `replica-recon` | `recon.md`, `features.csv`, `screens/` |
| 1b | Complex apps (Word, Figma, suites) | `replica-recon` | `complex-app-spec.md` |
| 2 | Architecture | `replica-architect` | `architecture.md` |
| 3 | Design system | `replica-design` | `design/tokens.json`, `design/components.md` |
| 4 | Build | `replica-build` | code + updated `features.csv` |
| 5 | Backend (auth, data, payments) | `replica-backend` | `backend.md` |
| 6 | Tests | `replica-test` | `test-plan.md`, `bugs.md` |
| 7 | Parity | `replica-diff` | `parity.md`, `diff/*.png` |
| 8 | User voice | `replica-entrepreneur` | `reviews.csv`, `themes.md`, `fix-plan.md` |
| 9 | Brand (rebrand) | `replica-brand` | `brand/*` + clean code |
| 10 | Launch | `replica-launch` | landing, `launch/listing.json`, `launch/paises.md` |
| 11 | Deployment | `replica-deploy` | `preflight.md`, live app |
| 12 | Static analysis (**opt-in**) | `replica-static` | `static/static-report.md`, `static/hallazgos-*.json` |
| 13 | Social (**opt-in**) | `replica-redes` | `launch/redes.md` |

Phase 12 requires an explicit request, an owned or authorized artifact and already-installed tools (never DRM, third-party logins or paywalls). Phase 13 always runs after brand (9) and launch (10). Any phase can be run standalone.

### Sub-skills

| Sub-skill | Phases | Purpose |
|---|---|---|
| `replica-recon` | 0, 1, 1b | Legal boundaries, scope, evidence-backed feature inventory and complex-app spec. |
| `replica-architect` | 2 | Stack, modules, data model with invariants and layer contracts. |
| `replica-design` | 3 | Own tokens, components and states, validated with WCAG contrast. |
| `replica-build` | 4 | Incremental build closing `must` flows. |
| `replica-backend` | 5 | Auth, schema with migrations, per-resource permissions, payments and jobs. |
| `replica-test` | 6 | Test plan and execution, invariants, S1/S2/S3 bugs. |
| `replica-diff` | 7 | Functional (`parity.py`) and visual (`imgdiff.py`) parity. |
| `replica-entrepreneur` | 8 | Real reviews with quote and URL, themes and fix plan. |
| `replica-brand` | 9 | Full rebrand and `sweep.py` at 0. |
| `replica-launch` | 10 | Landing, store listing and per-country pricing. |
| `replica-deploy` | 11 | Preflight, backups and verified deployment. |
| `replica-static` | 12 | Authorized static analysis, with declared limits. |
| `replica-redes` | 13 | 3 Reels scripts, captions and hook bank. |

### Master Command and State

The master (`replica/SKILL.md`) starts or resumes the pipeline: reads `replica/progreso.md`, walks phases in order, **stops after each one** and asks for explicit approval. It records phase, state (`pending` · `in progress` · `approved` · `blocked` · `n/a`), decisions, blockers and log. A red gate leaves the phase `blocked`; it is never bypassed.

### Mandatory Evidence

In recon (1), parity (7) and static analysis (12), every finding backing a decision uses `templates/evidence.md`: **Source · Observation · Inference · Confidence (high/medium/low/THIN) · Limits and unknowns**. No source, no finding; `THIN` (<3 samples or a single source) is not used as an argument.

### Deterministic Tools

- `parity.py`: weighted functional parity (must 3 / should 2 / could 1); fails on any pending `must`.
- `sweep.py`: original name, domain, colors and identifiers; exit 1 on leftovers.
- `contrast.py`: WCAG AA/AAA over design tokens.
- `imgdiff.py`: layout diff by regions, color-agnostic.
- `reviews.py`: themes and literal quotes with URL; drops rows without a link.
- `listing.py`: App Store/Play limits, claims and original name in the listing.

### Templates

`scope.md`, `architecture.md`, `complex-app-spec.md`, `test-plan.md`, `preflight.md`, `evidence.md`, `progreso.md`, `reels.md`, `features.csv`, `tokens.json`, `reviews.csv`, `themes.json`, `listing.json`.

### Usage and Tests

```bash
# Functional parity
py replica/scripts/parity.py replica/features.csv --markdown --out replica/parity.md

# Brand sweep
py replica/scripts/sweep.py . --avoid "OriginalApp" --avoid originalapp.com

# Package tests
py -m unittest discover -s replica/tests -v
```
