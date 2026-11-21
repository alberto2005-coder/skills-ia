# PR Reviewer

> Revisión de pull requests desde el diff: riesgo por fichero, orden de lectura, reparto entre revisores y consolidación que conserva lo no ejecutado.
> Pull request review from the diff: per-file risk, reading order, reviewer routing and a consolidation that keeps what did not run.

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

`pr-reviewer` convierte un diff en una revisión defendible. Lee el parche y el árbol para decir qué ficheros concentran el riesgo, en qué secuencia conviene leerlos, quién debe revisar cada ruta y qué quedó sin ejecutar. No arranca agentes, modelos ni la suite del proyecto: el mismo parche produce el mismo informe en local y en CI.

### Modos

El maestro no declara flags: el alcance de la petición fija la fase.

| Modo | Fase | Entrega |
|---|---|---|
| **Riesgo** | `pr-risk` | Severidad por fichero con la señal que la dispara |
| **Orden** | `pr-order` | Oleadas de lectura por imports, con ciclos señalados |
| **Reparto** | `pr-routing` | Dueño por ruta, carga por revisor y rutas sin respaldo |
| **Consolidación** | `pr-findings` | Informe único con el estado real de cada check |

### Arquitectura

Un maestro y cuatro sub-skills con scripts compartidos; la carpeta se instala completa. **5 skills** en total, todas en la versión 1.0.0.

| Sub-skill | Qué hace |
|---|---|
| `pr-reviewer` | Maestro: priorizar el PR, ordenar la lectura y consolidar lo revisado |
| `pr-risk` | Riesgo por fichero: dominio sensible, tamaño, claves expuestas y supresiones |
| `pr-order` | Orden de lectura por dependencias locales y ciclos |
| `pr-routing` | Reparto tipo CODEOWNERS con carga y respaldo |
| `pr-findings` | Consolidación con `not_run` explícito y deduplicación |

### Referencias

| Documento | Contenido |
|---|---|
| `pr-reviewer/references/review-strategy.md` | Dimensiones de una revisión, orden de trabajo y presupuesto |
| `pr-reviewer/references/risk-signals.md` | Dominios sensibles, señales textuales y falsos positivos |
| `pr-reviewer/references/findings-contract.md` | Estados del check, forma del hallazgo y deduplicación |
| `pr-reviewer/references/routing-and-ownership.md` | Patrones de ruta, carga y rutas sensibles |

La profundidad de seguridad es de `appsec-audit`; la estrategia de pruebas, de `test-architect`; el contrato HTTP, de `api-contract-guard`.

### Herramientas

```bash
py pr-reviewer/scripts/review_risk.py --diff cambios.patch --fail-on high
py pr-reviewer/scripts/review_order.py --diff cambios.patch --root .
py pr-reviewer/scripts/review_routing.py --diff cambios.patch --owners owners.json
py pr-reviewer/scripts/review_findings.py --input security.json tests.json --require security
```

Salida común: `source`, `summary` con `total` y `by_severity`, y `findings` con `file`, `line`, `rule`, `severity`, `message` y `fix`. Los códigos de salida son `0` limpio o por debajo del umbral, `1` umbral superado y `2` entrada ilegible. `review_risk.py`, `review_routing.py` y `review_findings.py` aceptan `--fail-on low|medium|high|none` con `high` por defecto; `review_order.py` es informativo y siempre sale `0` si el parche se puede leer.

`review_findings.py` nunca rellena un check ausente: un informe sin `status` se trata como `not_run`, y con `--require` un check que no corrió hace fallar el comando.

### Instalación y uso

Copia la carpeta `pr-reviewer/` completa. Peticiones típicas:

- «Revisa este PR y dime por dónde empiezo».
- «¿En qué orden leo estos ficheros?».
- «¿Quién debería revisar cada ruta?».
- «Une los informes de seguridad y pruebas sin marcar como limpio lo que no se ejecutó».

### Tests

```bash
uv run python -m unittest discover -s pr-reviewer/tests -t pr-reviewer/tests
```

51 tests: riesgo (diez, con dominio sensible, secreto, dependencia, supresión, presupuesto y determinismo), orden (diez, con oleadas, ciclo, sin grafo, huérfano y raíz ilegible), reparto (diez, con regla específica, sin dueño, carga y respaldo) y consolidación (doce, con `not_run`, estado ausente, duplicados, checks exigidos y entradas ilegibles), más estructura (nueve, con manifiesto, gates, límites del maestro y ausencia de imports de la raíz).

### Límites

El riesgo se puntúa por ruta y por texto: una ruta sensible puede no serlo en un proyecto concreto y un secreto detectado puede ser un ejemplo. El orden solo entiende imports de Python; el resto de lenguajes se marca `sin-grafo`. El reparto aplica las reglas declaradas, no consulta permisos reales ni disponibilidad. La consolidación no juzga si un hallazgo es un falso positivo.

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

`pr-reviewer` turns a diff into a defensible review. It reads the patch and the tree to say which files carry the risk, in what sequence to read them, who should review each path and what was left unrun. It starts no agents, models or project suite: the same patch produces the same report locally and in CI.

### Modes

The master declares no flags: the request's scope sets the phase.

| Mode | Phase | Deliverable |
|---|---|---|
| **Risk** | `pr-risk` | Per-file severity with the signal that triggered it |
| **Order** | `pr-order` | Reading waves by imports, with cycles flagged |
| **Routing** | `pr-routing` | Owner per path, reviewer load and paths without backup |
| **Consolidation** | `pr-findings` | One report with each check's real status |

### Architecture

One master and four sub-skills with shared scripts; the folder is installed whole. **5 skills** in total, all on version 1.0.0.

| Sub-skill | What it does |
|---|---|
| `pr-reviewer` | Master: prioritise the PR, order the reading and consolidate what was reviewed |
| `pr-risk` | Per-file risk: sensitive domain, size, leaked keys and suppressions |
| `pr-order` | Reading order by local dependencies and cycles |
| `pr-routing` | CODEOWNERS-style routing with load and backup |
| `pr-findings` | Consolidation with an explicit `not_run` and deduplication |

### References

| Document | Content |
|---|---|
| `pr-reviewer/references/review-strategy.md` | Review dimensions, working order and budget |
| `pr-reviewer/references/risk-signals.md` | Sensitive domains, textual signals and false positives |
| `pr-reviewer/references/findings-contract.md` | Check states, finding shape and deduplication |
| `pr-reviewer/references/routing-and-ownership.md` | Path patterns, load and sensitive paths |

Security depth belongs to `appsec-audit`; test strategy to `test-architect`; the HTTP contract to `api-contract-guard`.

### Tools

```bash
py pr-reviewer/scripts/review_risk.py --diff cambios.patch --fail-on high
py pr-reviewer/scripts/review_order.py --diff cambios.patch --root .
py pr-reviewer/scripts/review_routing.py --diff cambios.patch --owners owners.json
py pr-reviewer/scripts/review_findings.py --input security.json tests.json --require security
```

Shared output: `source`, `summary` with `total` and `by_severity`, and `findings` with `file`, `line`, `rule`, `severity`, `message` and `fix`. Exit codes are `0` clean or below the threshold, `1` threshold exceeded and `2` unreadable input. `review_risk.py`, `review_routing.py` and `review_findings.py` accept `--fail-on low|medium|high|none`, `high` by default; `review_order.py` is informational and always exits `0` when the patch can be read.

`review_findings.py` never fills in a missing check: a report without `status` is treated as `not_run`, and with `--require` a check that did not run fails the command.

### Install and use

Copy the whole `pr-reviewer/` folder. Typical requests:

- "Review this PR and tell me where to start".
- "In what order do I read these files?".
- "Who should review each path?".
- "Merge the security and test reports without calling unrun checks clean".

### Tests

```bash
uv run python -m unittest discover -s pr-reviewer/tests -t pr-reviewer/tests
```

51 tests: risk (ten, with sensitive domain, secret, dependency, suppression, budget and determinism), order (ten, with waves, cycle, no graph, orphan and unreadable root), routing (ten, with a specific rule, unowned files, load and backup) and consolidation (twelve, with `not_run`, missing status, duplicates, required checks and unreadable inputs), plus structure (nine, with manifest, gates, master limits and no imports from the root).

### Limits

Risk is scored by path and text: a sensitive path may not be sensitive in a given project and a detected secret may be a sample. Order only understands Python imports; other languages are marked `sin-grafo`. Routing applies the declared rules and does not query real permissions or availability. Consolidation does not judge whether a finding is a false positive.
