---
name: skill-evals
description: >
  Evalúa de principio a fin un catálogo de skills de agente y deja evidencia
  reproducible: orquesta el diseño de casos, la ejecución con el motor léxico
  del repositorio, las puertas de calidad y el veredicto final. Sirve para
  decidir si una skill o una versión nueva merece publicarse, comparar dos
  corridas y montar el flujo de evaluación en CI. Úsala cuando pidan una
  evaluación completa del catálogo de skills, auditar el conjunto antes de
  publicarlo o montar el flujo de evaluación en integración continua. Cubre el
  ciclo de las herramientas de la competencia (skill-creator, skill-reach,
  SkillEvaluator) sin modelo ni API.
  English: end-to-end offline evaluation of an agent skill catalog — cases,
  routing, quality gates and a reproducible verdict.
license: MIT
metadata:
  package: skill-evals
  version: "1.1.0"
  author: "Alberto Ortiz"
---

# Skill Evals

Evaluar una skill no es leerla: es medir si se activa cuando debe, si deja de activarse cuando no debe, cuánto contexto cuesta y si una versión nueva rompe lo que la anterior hacía bien. Todo con el mismo router léxico que usa la suite del repositorio, así que un número de esta skill y un test de CI no pueden contradecirse.

## Regla cero: medir, no opinar

- **Sin red y sin modelo**: no hay llamadas a APIs, ni jueces LLM, ni sandbox. Si un dato no sale de un fichero del repositorio, no entra en el informe.
- **Sin tocar el catálogo**: la evaluación lee `SKILL.md`, `skills.json` y `tests/phrases.json`; nunca edita descripciones ni frases por su cuenta.
- **Determinista**: mismo conjunto de casos y mismo catálogo producen el mismo JSON, el mismo informe y el mismo veredicto.
- **Reproducible**: cada caso tiene id estable, split por hash y puntuación redondeada; nada depende del reloj ni del orden del sistema de ficheros.
- **Sin inflar**: el router léxico aproxima el routing, no lo sustituye. Un 1.000 de precisión aquí no demuestra que un modelo real active la skill; demuestra que la descripción contiene el vocabulario de sus casos.

## Sub-skills

| Sub-skill | Qué hace |
|---|---|
| `eval-design` | Convierte `phrases.json` en casos versionables, añade límites, reparte train/test y comprueba cobertura |
| `eval-run` | Ejecuta los casos contra el router, calcula precisión/recall/MRR, colisiones y presupuesto, y aplica puertas |
| `eval-report` | Renderiza la corrida en Markdown o HTML autónomo, con tabla de fallos, colisiones y diff contra la línea base |
| `eval-ab` | Compara dos corridas grabadas: eficacia, cumplimiento, coste, latencia y variabilidad |

Comparten `scripts/`, `references/` y `templates/` de esta carpeta. Se instala el paquete completo.

## Flujo

1. **Diseñar** los casos desde las frases del repositorio (`--check` valida sin escribir):

```bash
py skill-evals/scripts/design.py --from-phrases tests/phrases.json --out skill-evals/reports/cases.json
```

2. **Ejecutar** con puerta de precisión y guardar la corrida:

```bash
py skill-evals/scripts/run.py --cases skill-evals/reports/cases.json --out skill-evals/reports/run.json --fail-under precision=0.95
```

3. **Comparar** contra la corrida anterior y fallar si hay regresiones:

```bash
py skill-evals/scripts/run.py --cases skill-evals/reports/cases.json --baseline skill-evals/reports/run-anterior.json --fail-on-regression --json
```

4. **Optimizar** una descripción que pierde sus positivas: candidatos desde los fallos de train, filtro en train, elección por test y diff sin escribir por defecto:

```bash
py skill-evals/scripts/optimize.py --skill appsec-recon --cases skill-evals/reports/cases.json
```

5. **Informar** en Markdown o HTML:

```bash
py skill-evals/scripts/report.py --run skill-evals/reports/run.json --out skill-evals/reports/informe.md
py skill-evals/scripts/report.py --run skill-evals/reports/run.json --baseline skill-evals/reports/run-anterior.json --format html --out skill-evals/reports/informe.html
```

## Qué se mide

| Métrica | Definición | Puerta sugerida |
|---|---|---|
| Precisión | Casos correctos / casos totales (positivas, negativas, límites y fuera de dominio) | ≥ 0,95 |
| Recall | Positivas que quedan en primera posición / positivas | ≥ 0,98 |
| MRR | Media de 1/rango de la skill esperada en las positivas | ≥ 0,98 |
| Colisiones | Pares de descripciones con Jaccard ≥ 0,50 | 0 |
| Falsos positivos | Fuera de dominio que superan el umbral | 0 |
| Presupuesto | Tokens estimados del catálogo y del cuerpo de cada SKILL.md | catálogo ≤ 8.000; cuerpo ≤ 5.000 |

Definiciones, límites y sesgos en [`references/metrics.md`](references/metrics.md).

## Cobertura de la competencia

El mapeo función a función —qué hace cada herramienta del mercado, qué se cubre aquí, qué se mejora y qué se añade— está en [`references/competitors.md`](references/competitors.md). Resumen: se cubren validación estática, detección de solapamiento, métricas de trigger, baseline con/sin skill, split train/test, optimización de descripción y dos formatos de informe; se mejora con offline puro, puertas de CI y diff por caso; se añade presupuesto de contexto, límites sintéticos y veredicto único reproducible.

## Reglas duras

- **No se evalúa con frases inventadas**: los casos salen de `tests/phrases.json` o de un fichero de casos explícito.
- **No se maquilla un fallo**: un caso que falla aparece en el informe con su puntuación y su hermana; no se sube el umbral para taparlo.
- **No se sube el split de test al de train**: la selección de una descripción candidata se hace por test, nunca por train.
- **No se edita `SKILL.md` desde esta skill**: propone el cambio y lo aplica quien lo pida.
- **Sin dependencias**: solo stdlib y el router del repositorio.

## Limitaciones declaradas

- El router es léxico (TF-IDF + bigramas): no entiende sinónimos que no compartan raíz ni intención conversacional.
- No mide calidad de la salida de la skill, solo activación, solapamiento y coste. Para eso hace falta un agente real, que esta skill no arranca.
- El presupuesto de tokens es una estimación por caracteres (`len/4`), no un conteo de tokenizador.
