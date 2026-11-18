---
name: refactor-metrics
description: Mide complejidad ciclomática, anidamiento, líneas y parámetros por función, con nota de mantenibilidad 0-100, para decidir qué se refactoriza y comparar el después.
license: MIT
metadata:
  package: refactor-surgeon
  version: "1.3.0"
---

# Refactor Metrics

## Objetivo

Elegir el objetivo del refactor con números: la función con `V(G)` alto y anidamiento profundo va primero.

## Instrucciones de ejecución

1. Mide el módulo o la carpeta completa:

```bash
py refactor-surgeon/scripts/code_metrics.py --path src/ --json
```

2. Usa `--fail-on medium` en CI para impedir que entre código nuevo por encima del límite.
3. Guarda el JSON antes y después: la comparación es la prueba del refactor.

## Límites por defecto

| Métrica | Límite |
|---|---|
| Complejidad `V(G)` | 10 |
| Anidamiento | 4 |
| Parámetros | 6 |
| Líneas por función | 60 |

## Límites de la herramienta

- Analiza la sintaxis, no ejecuta el código: un módulo con imports rotos se mide igual.
- No mide acoplamiento entre módulos ni cobertura de tests.
- La nota de mantenibilidad es una heurística propia: sirve para comparar el mismo módulo, no entre proyectos.

## Gate de salida

- Métricas del antes guardadas en JSON.
- La función objetivo está identificada con su métrica y su límite.
- El límite que se va a mejorar queda escrito y es medible.

## Handoff

Entrega a `refactor-harness` el módulo objetivo para grabar sus casos antes de tocar el código.
