---
name: refactor-hotspots
description: >
  Ordena los ficheros por churn de git log desde una fecha obligatoria multiplicado por su
  complejidad, y declara «no medido» sin fecha, sin repositorio o en un clon shallow. Úsala para
  decidir por dónde empezar el refactor con datos de churn y complejidad. English: rank files by
  git churn times complexity, and say "not measured" when it cannot be measured.
license: MIT
metadata:
  package: refactor-surgeon
  version: "1.5.1"
  author: "Alberto Ortiz"
---

# Refactor Hotspots

## Objetivo

Decidir por dónde empezar con evidencia, no con la impresión de que un módulo «está fatal»: el fichero que más cambia y más complejo es el que más devuelve por hora de refactor.

## Instrucciones de ejecución

1. Mide con una fecha explícita y completa:

```bash
py refactor-surgeon/scripts/hotspots.py --path . --since 2026-01-01T00:00:00 --top 10 --json
```

2. Empieza por el primero que además tenga casos dorados posibles (`refactor-harness`).
3. Repite la medición después del corte con el mismo `--since`: el churn ya no es comparable si cambia la ventana.

## Cómo se calcula

| Pieza | Fuente |
|---|---|
| Churn | Líneas añadidas + borradas por fichero en `git log --numstat` desde `--since` |
| Complejidad | Suma de `V(G)` de las funciones del fichero; los que no son Python cuentan 1 |
| Score | Churn × complejidad, ordenado de mayor a menor |

Cada fila del informe lleva ruta, churn, complejidad y score, para poder discutir el número y no la intuición. Los ficheros que ya no existen se cuentan aparte (`skipped`) y no entran en el ranking: recomendar refactorizar un fichero borrado no sirve de nada.

## No medido

| Situación | Resultado |
|---|---|
| Falta `--since` | `measured: false`, salida 2 |
| La ruta no es un repositorio git | `measured: false`, salida 2 |
| Clon shallow (historia truncada) | `measured: false`, salida 2 |
| `--since` con solo fecha | Se normaliza a `AAAA-MM-DDT00:00:00` antes de llamar a git |

La degradación es explícita a propósito: un churn calculado sobre historia truncada parece un dato y no lo es.

## Límites

- Es el único script del paquete que lee historia: el resultado depende del repositorio y de la ventana elegida, no solo del código.
- Solo ve ficheros rastreados por git; el código generado o ignorado por `.gitignore` queda fuera.
- El score pondera igual una línea añadida que una borrada y no mide riesgo de cambio: ordena, no decide.

## Gate de salida

- Ventana (`--since`), commits leídos y ficheros ordenados por escrito.
- Si no se pudo medir, el motivo escrito y el análisis continúa con `refactor-metrics`.
- El fichero elegido tiene su grupo de casos dorados antes de tocarlo.

## Handoff

Entrega a `refactor-harness` el fichero prioritario para congelar su conducta y a `refactor-slice` su grafo de llamadas, ya con el orden de ataque decidido.
