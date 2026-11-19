# Skill Evals

> Evaluación offline de skills: casos desde frases reales, routing léxico determinista, puertas de precisión/recall/MRR, informe reproducible y optimización de descripciones.
> Offline skill evaluation: cases from real phrases, deterministic lexical routing, precision/recall/MRR gates, a reproducible report and description optimisation.

[Español](#español) · [English](#english)

---

## Español

### Índice

1. Propósito
2. Modos
3. Arquitectura
4. Métricas y puertas
5. Herramientas
6. Instalación y uso
7. Tests
8. Límites

### Propósito

`skill-evals` responde a una pregunta que ningún `SKILL.md` puede contestar solo: cuando alguien escribe «revisa el seo de esta web», ¿se activa la skill correcta y ninguna de sus hermanas? Lo mide sin modelo ni red: un router léxico puntúa la frase contra las descripciones del catálogo, se compara con la verdad declarada en `tests/phrases.json` y el resultado se contrasta con puertas numéricas que rompen CI.

### Modos

El maestro no usa flags: el alcance de la petición fija las fases.

| Modo | Fases | Entrega |
|---|---|---|
| **Diseño** | `eval-design` | JSON de casos con tipo y split train/test |
| **Ejecución** | `eval-run` | Precisión, recall, MRR, colisiones y presupuesto de contexto |
| **Informe** | `eval-report` | Markdown o HTML autónomo, con diff contra la línea base |
| **Optimización** | `eval-run` + `eval-design` | Descripción propuesta, sin aplicarla salvo `--apply` |

### Arquitectura

Un maestro y tres sub-skills con scripts compartidos. Se instala la carpeta completa.

| Sub-skill | Qué hace |
|---|---|
| `skill-evals` | Maestro: diseña, ejecuta, compara e informa |
| `eval-design` | Casos desde `phrases.json`, casos límite, cobertura y split train/test |
| `eval-run` | Métricas, colisiones entre hermanas, presupuesto de contexto, regresiones y puertas |
| `eval-report` | Informe Markdown o HTML con tabla de fallos y diff contra la línea base |

La librería común es [`evalkit.py`](../skill-evals/scripts/evalkit.py): rutas de casos, carga del router, métricas y formato de la corrida. Las referencias viven en [`metrics.md`](../skill-evals/references/metrics.md) y [`competitors.md`](../skill-evals/references/competitors.md), y las plantillas en [`eval-cases.json`](../skill-evals/templates/eval-cases.json) y [`report.md`](../skill-evals/templates/report.md).

### Métricas y puertas

Cada caso declara su tipo (`positive`, `negative`, `boundary`, `out_of_domain`) y su split (`train`, `test`). Sobre esa verdad se calculan tres métricas y tres topes:

| Concepto | Valor por defecto |
|---|---|
| Acierto de activación | Score mínimo `0.3` y top-1 |
| Precisión | Puerta `0.95` |
| Recall | Puerta `0.98` |
| MRR | Puerta `0.98` |
| Colisión entre hermanas | Jaccard `0.50` |
| Catálogo | `8.000` tokens |
| Cuerpo de un `SKILL.md` | `5.000` tokens y 500 líneas |
| Vecinos considerados | top-3 |

Una skill que no gana su propia frase, o que empata con una hermana, es un fallo aunque la media salga bien: el informe lista los casos, no solo el porcentaje.

### Herramientas

```bash
py skill-evals/scripts/design.py --from-phrases tests/phrases.json --out skill-evals/reports/cases.json
py skill-evals/scripts/run.py --cases skill-evals/reports/cases.json --out skill-evals/reports/run.json --fail-under precision=0.95 --fail-under recall=0.98 --fail-under mrr=0.98
py skill-evals/scripts/report.py --run skill-evals/reports/run.json --format md --out skill-evals/reports/informe.md
py skill-evals/scripts/optimize.py --skill seo-audit --cases skill-evals/reports/cases.json --json
```

Salida resumida de `design.py`:

```text
por tipo: positive=238, negative=133, boundary=2, out_of_domain=6
escrito: skill-evals/reports/cases.json
```

`run.py` añade `--baseline` para comparar con una corrida anterior y `--fail-on-regression` para romper la puerta cuando empeora. `optimize.py` propone una descripción nueva a partir de los fallos de *train*, elige el candidato con *test* y solo escribe en el `SKILL.md` con `--apply`.

Códigos de salida: `0` correcto o por encima de las puertas · `1` puerta superada o regresión · `2` fichero ilegible.

### Instalación y uso

Copia la carpeta `skill-evals/` completa. Ejemplos de petición:

- «Diseña los casos de evaluación del catálogo de skills».
- «Mide precisión, recall y MRR y dime qué skills fallan».
- «Genera el informe de evaluación en HTML».
- «Propón una descripción mejor para las skills que fallan sus frases».

### Tests

```bash
uv run python -m unittest discover -s skill-evals/tests -t skill-evals/tests
```

42 pruebas: diseño de casos desde `phrases.json` y validación con `--check`, métricas y puertas de `run.py`, comparación con línea base y regresiones, colisiones y presupuesto de contexto, informe Markdown y HTML byte a byte, optimizador sin escritura y con `--apply`, y estructura del paquete (frontmatter, manifiesto, gates y handoff).

### Límites

El router es léxico: mide solapamiento de vocabulario con la descripción, no comprensión semántica, así que una paráfrasis muy alejada del texto puede fallar sin que la skill esté mal escrita. La calidad depende de `tests/phrases.json`: frases sesgadas producen métricas optimistas, y las frases se escribieron después de ver las descripciones, no a ciegas. No evalúa la calidad de la respuesta de la skill, solo su activación. Todo es offline y determinista: sin modelo, sin red y sin reloj, de modo que dos corridas con los mismos datos coinciden byte a byte.

---

## English

### Index

1. Purpose
2. Modes
3. Architecture
4. Metrics and gates
5. Tools
6. Install and use
7. Tests
8. Limits

### Purpose

`skill-evals` answers a question no `SKILL.md` can answer on its own: when someone types "audit the SEO of this site", does the right skill activate and none of its siblings? It measures that with no model and no network: a lexical router scores the phrase against the catalog descriptions, the result is compared with the truth declared in `tests/phrases.json`, and the outcome is checked against numeric gates that fail CI.

### Modes

The master takes no flags: the request's scope sets the phases.

| Mode | Phases | Deliverable |
|---|---|---|
| **Design** | `eval-design` | Cases JSON with kind and train/test split |
| **Run** | `eval-run` | Precision, recall, MRR, collisions and context budget |
| **Report** | `eval-report` | Standalone Markdown or HTML, with a diff against the baseline |
| **Optimisation** | `eval-run` + `eval-design` | Proposed description, not written unless `--apply` |

### Architecture

One master and three sub-skills with shared scripts. The whole folder is installed.

| Sub-skill | What it does |
|---|---|
| `skill-evals` | Master: designs, runs, compares and reports |
| `eval-design` | Cases from `phrases.json`, boundary cases, coverage and train/test split |
| `eval-run` | Metrics, sibling collisions, context budget, regressions and gates |
| `eval-report` | Markdown or HTML report with a failure table and baseline diff |

The shared library is [`evalkit.py`](../skill-evals/scripts/evalkit.py): case paths, router loading, metrics and run format. References live in [`metrics.md`](../skill-evals/references/metrics.md) and [`competitors.md`](../skill-evals/references/competitors.md), templates in [`eval-cases.json`](../skill-evals/templates/eval-cases.json) and [`report.md`](../skill-evals/templates/report.md).

### Metrics and gates

Every case declares its kind (`positive`, `negative`, `boundary`, `out_of_domain`) and its split (`train`, `test`). Three metrics and three caps are computed over that truth:

| Concept | Default value |
|---|---|
| Activation match | Minimum score `0.3` and top-1 |
| Precision | Gate `0.95` |
| Recall | Gate `0.98` |
| MRR | Gate `0.98` |
| Sibling collision | Jaccard `0.50` |
| Catalog | `8,000` tokens |
| `SKILL.md` body | `5,000` tokens and 500 lines |
| Neighbours considered | top-3 |

A skill that does not win its own phrase, or that ties with a sibling, is a failure even when the average looks fine: the report lists the cases, not just the percentage.

### Tools

```bash
py skill-evals/scripts/design.py --from-phrases tests/phrases.json --out skill-evals/reports/cases.json
py skill-evals/scripts/run.py --cases skill-evals/reports/cases.json --out skill-evals/reports/run.json --fail-under precision=0.95 --fail-under recall=0.98 --fail-under mrr=0.98
py skill-evals/scripts/report.py --run skill-evals/reports/run.json --format md --out skill-evals/reports/informe.md
py skill-evals/scripts/optimize.py --skill seo-audit --cases skill-evals/reports/cases.json --json
```

Condensed `design.py` output:

```text
por tipo: positive=238, negative=133, boundary=2, out_of_domain=6
escrito: skill-evals/reports/cases.json
```

`run.py` adds `--baseline` to compare with a previous run and `--fail-on-regression` to fail the gate when it gets worse. `optimize.py` proposes a new description from *train* failures, picks the candidate on *test* and only writes to the `SKILL.md` with `--apply`.

Exit codes: `0` correct or above the gates · `1` gate failed or regression · `2` unreadable file.

### Install and use

Copy the whole `skill-evals/` folder. Example requests:

- "Design the evaluation cases for the skill catalog".
- "Measure precision, recall and MRR and tell me which skills fail".
- "Generate the evaluation report as HTML".
- "Propose a better description for the skills that fail their phrases".

### Tests

```bash
uv run python -m unittest discover -s skill-evals/tests -t skill-evals/tests
```

42 tests: case design from `phrases.json` and `--check` validation, `run.py` metrics and gates, baseline comparison and regressions, collisions and context budget, byte-identical Markdown and HTML reports, the optimiser with and without `--apply`, and package structure (frontmatter, manifest, gates and handoff).

### Limits

The router is lexical: it measures vocabulary overlap with the description, not semantic understanding, so a paraphrase far from the text can fail without the skill being wrong. Quality depends on `tests/phrases.json`: biased phrases produce optimistic metrics, and the phrases were written after seeing the descriptions, not blind. It does not evaluate the quality of a skill's answer, only its activation. Everything is offline and deterministic: no model, no network and no clock, so two runs over the same data match byte for byte.
