# Test Architect

> Estrategia de pruebas desde el código: qué probar primero, qué estabilizar y qué contrato fijar.
> Test strategy from the source: what to test first, what to stabilise and which contract to pin.

[Español](#español) · [English](#english)

---

## Español

### Índice

1. Propósito
2. Modos
3. Arquitectura
4. Referencias
5. Herramientas
6. Instalación y uso
7. Tests
8. Límites

### Propósito

`test-architect` decide qué se prueba con evidencia del árbol, no con intuición. Cruza los módulos con los tests existentes, localiza los patrones que hacen inestable una suite, elige dónde merece la pena mutar y compara el contrato que comparten dos módulos. Todo es lectura: no ejecuta la suite ni mutantes en vivo, así que funciona en un repo que no arranca.

### Modos

El maestro no declara flags: el alcance de la petición fija la fase.

| Modo | Fase | Entrega |
|---|---|---|
| **Plan** | `test-plan` | Módulos priorizados por riesgo y ledger de exclusiones |
| **Estabilidad** | `test-flaky` | Patrones de inestabilidad con fichero y línea |
| **Mutación** | `test-mutation` | Objetivos, operadores y presupuesto de mutantes |
| **Contrato** | `test-contract` | Deriva entre fixture del proveedor y payload del consumidor |

### Arquitectura

Un maestro y cuatro sub-skills con scripts compartidos; la carpeta se instala completa. **5 skills** en total, todas en la versión 1.0.0.

| Sub-skill | Qué hace |
|---|---|
| `test-architect` | Maestro: decidir qué probar, qué estabilizar y qué fijar |
| `test-plan` | Plan por riesgo: módulos sin test y dominios sensibles |
| `test-flaky` | Inestabilidad: esperas fijas, reloj, azar y red real |
| `test-mutation` | Operadores de mutación y presupuesto sin ejecutar mutantes |
| `test-contract` | Contrato proveedor/consumidor sobre fixtures JSON |

### Referencias

| Documento | Contenido |
|---|---|
| `test-architect/references/test-strategy.md` | Matriz de riesgo, cartera de pruebas y qué no se prueba |
| `test-architect/references/flaky-patterns.md` | Catálogo de causas de inestabilidad y su arreglo |
| `test-architect/references/mutation-operators.md` | Operadores, equivalentes y reparto del presupuesto |
| `test-architect/references/contract-testing.md` | Formato del fixture y frontera con `api-contract-guard` |

Las rutas HTTP, el SemVer y la cobertura de autenticación de una API son de `api-contract-guard`; la calidad de activación de una skill, de `skill-evals`.

### Herramientas

```bash
py test-architect/scripts/plan_tests.py --root . --json
py test-architect/scripts/flaky_scan.py --root . --fail-on medium
py test-architect/scripts/mutation_targets.py --root . --limit 10 --min-mutants 4
py test-architect/scripts/contract_fixtures.py --provider p.json --consumer c.json --json
```

Salida común: `source`, `files`, `summary` con `total` y `by_severity`, y `findings` con `file`, `line`, `rule`, `severity`, `message` y `fix`. Los códigos de salida son `0` limpio o por debajo del umbral, `1` umbral superado y `2` entrada ilegible. `plan_tests.py` y `mutation_targets.py` son informativos y siempre salen `0` si la raíz existe; `flaky_scan.py` y `contract_fixtures.py` aceptan `--fail-on low|medium|high|none` con `high` por defecto.

### Instalación y uso

Copia la carpeta `test-architect/` completa. Peticiones típicas:

- «¿Por dónde empiezo a testear este repo?».
- «Este test falla solo en CI, ¿por qué es inestable?».
- «La cobertura es alta pero se escapan bugs, ¿dónde mutamos?».
- «Fija este contrato entre módulos antes de que lo rompa el refactor».

### Tests

```bash
uv run python -m unittest discover -s test-architect/tests -t test-architect/tests
```

49 tests: plan (diez, con módulo sin test en dominio sensible, cobertura por nombre, orden, presupuesto, ledger y determinismo), inestabilidad (once, con los ocho patrones, semilla fijada, `--allow-network` y umbrales), mutación (diez, con operadores por función, presupuesto y descartes), contrato (diez, con campo faltante, tipo, nulo, extra y entradas ilegibles) y estructura (ocho, con manifiesto, gate, handoff, límites del maestro y ausencia de imports de la raíz).

### Límites

La cobertura se infiere por nombre de fichero: un test agrupado o con otro nombre puede quedar sin acreditar, y por eso el proyecto puede pasar su informe real. El escáner de inestabilidad reconoce patrones sintácticos, no la causa última de un fallo. Los objetivos de mutación no predicen la tasa de supervivencia: la mide quien ejecuta los mutantes. El contrato compara fixture y payload, no documentos OpenAPI.

---

## English

### Index

1. Purpose
2. Modes
3. Architecture
4. References
5. Tools
6. Install and use
7. Tests
8. Limits

### Purpose

`test-architect` decides what gets tested from evidence in the tree, not from intuition. It crosses modules with existing tests, finds the patterns that make a suite flaky, picks where mutation is worth it and compares the contract two modules share. Everything is read-only: it runs neither the suite nor mutants, so it works on a repo that does not even start.

### Modes

The master declares no flags: the request's scope sets the phase.

| Mode | Phase | Deliverable |
|---|---|---|
| **Plan** | `test-plan` | Modules ranked by risk plus an exclusion ledger |
| **Stability** | `test-flaky` | Instability patterns with file and line |
| **Mutation** | `test-mutation` | Targets, operators and mutant budget |
| **Contract** | `test-contract` | Drift between the provider fixture and the consumer payload |

### Architecture

One master and four sub-skills with shared scripts; the folder is installed whole. **5 skills** in total, all on version 1.0.0.

| Sub-skill | What it does |
|---|---|
| `test-architect` | Master: decide what to test, what to stabilise and what to pin |
| `test-plan` | Risk plan: untested modules and sensitive domains |
| `test-flaky` | Instability: fixed sleeps, wall clock, randomness and real network |
| `test-mutation` | Mutation operators and budget without running mutants |
| `test-contract` | Provider/consumer contract over JSON fixtures |

### References

| Document | Content |
|---|---|
| `test-architect/references/test-strategy.md` | Risk matrix, test portfolio and what is not tested |
| `test-architect/references/flaky-patterns.md` | Catalogue of instability causes and their fix |
| `test-architect/references/mutation-operators.md` | Operators, equivalents and budget split |
| `test-architect/references/contract-testing.md` | Fixture format and the boundary with `api-contract-guard` |

HTTP routes, SemVer and authentication coverage of an API belong to `api-contract-guard`; a skill's activation quality belongs to `skill-evals`.

### Tools

```bash
py test-architect/scripts/plan_tests.py --root . --json
py test-architect/scripts/flaky_scan.py --root . --fail-on medium
py test-architect/scripts/mutation_targets.py --root . --limit 10 --min-mutants 4
py test-architect/scripts/contract_fixtures.py --provider p.json --consumer c.json --json
```

Shared output: `source`, `files`, `summary` with `total` and `by_severity`, and `findings` with `file`, `line`, `rule`, `severity`, `message` and `fix`. Exit codes are `0` clean or below the threshold, `1` threshold exceeded and `2` unreadable input. `plan_tests.py` and `mutation_targets.py` are informational and always exit `0` when the root exists; `flaky_scan.py` and `contract_fixtures.py` accept `--fail-on low|medium|high|none`, `high` by default.

### Install and use

Copy the whole `test-architect/` folder. Typical requests:

- "Where do I start testing this repo?".
- "This test only fails in CI, why is it flaky?".
- "Coverage is high but bugs escape, where do we mutate?".
- "Pin this contract between modules before the refactor breaks it".

### Tests

```bash
uv run python -m unittest discover -s test-architect/tests -t test-architect/tests
```

49 tests: plan (ten, with an untested module in a sensitive domain, coverage by name, ordering, budget, ledger and determinism), instability (eleven, with all eight patterns, a fixed seed, `--allow-network` and thresholds), mutation (ten, with per-function operators, budget and discards), contract (ten, with missing field, type, null, extras and unreadable inputs) and structure (eight, with manifest, gate, handoff, master limits and no imports from the root).

### Limits

Coverage is inferred from file names: a grouped test under another name may go uncredited, which is why the project can supply its real report. The instability scanner recognises syntactic patterns, not the ultimate cause of a failure. Mutation targets do not predict the survival rate: whoever runs the mutants measures it. The contract compares fixture and payload, not OpenAPI documents.
