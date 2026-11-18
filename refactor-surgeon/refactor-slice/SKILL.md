---
name: refactor-slice
description: Calcula el grafo de llamadas de un fichero y propone cortes por componentes conexas, señalando qué funciones son entradas y qué grupos no se hablan entre sí.
license: MIT
metadata:
  package: refactor-surgeon
  version: "1.0.0"
---

# Refactor Slice

## Objetivo

Partir un fichero grande por donde el código ya está separado, en lugar de inventar módulos nuevos a ojo.

## Instrucciones de ejecución

1. Analiza el fichero y lee los grupos:

```bash
py refactor-surgeon/scripts/slice_analyzer.py --path src/grande.py --json
```

2. Cada componente conexa es un candidato a módulo; las funciones que nadie llama desde dentro son puntos de entrada.
3. Corta un grupo por vez y vuelve a medir con `refactor-metrics` después de cada corte.

## Criterio de corte

| Situación | Decisión |
|---|---|
| Grupo con entrada propia y sin llamadas al resto | Módulo nuevo |
| Grupo que comparte función con otro | Se corta por la función compartida, no por el grupo |
| Función aislada | Se queda donde está hasta que aparezca su consumidor |

## Límites

- Solo ve llamadas por nombre dentro del mismo fichero: métodos, imports y llamadas dinámicas no aparecen.
- Una componente grande puede indicar acoplamiento real, no un mal corte: la herramienta sugiere, no decide.
- No reescribe código: produce el plan de cortes, el cambio lo hace la persona.

## Gate de salida

- Grupos y entradas listados antes de cortar.
- Cada corte aplicado cita el grupo y las funciones que se mueven.
- Métricas repetidas tras el corte, sin subir la complejidad total.

## Handoff

Entrega a `refactor-verify` los cortes aplicados y a `refactor-metrics` el fichero resultante para comparar la nota.
