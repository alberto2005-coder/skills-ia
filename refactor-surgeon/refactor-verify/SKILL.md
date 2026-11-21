---
name: refactor-verify
description: >
  Verifica que el refactor no cambió la conducta comparando los casos dorados contra el snapshot
  y repitiendo los tests existentes, con veredicto limpio o discrepancia. Úsala después de
  refactorizar, para demostrar que la conducta es la misma. English: verify unchanged behaviour
  by replaying golden cases against the snapshot.
license: MIT
metadata:
  package: refactor-surgeon
  version: "1.5.1"
  author: "Alberto Ortiz"
---

# Refactor Verify

## Objetivo

Cerrar el refactor con prueba, no con opinión: mismo comportamiento y métricas mejores.

## Instrucciones de ejecución

1. Verifica los casos dorados contra el snapshot grabado:

```bash
py refactor-surgeon/scripts/golden_harness.py --cases cases.json --snapshot golden.json --verify --allow-exec
```

2. Ejecuta los tests del proyecto que cubren el módulo tocado.
3. Vuelve a medir con `code_metrics.py` y compara la nota con la del antes.

## Veredicto

| Resultado | Veredicto |
|---|---|
| Cero discrepancias y tests en verde | Refactor válido |
| Discrepancia en un caso | Se revierte el último corte |
| Métricas peores sin ganancia funcional | Se revierte el cambio |

## Límites

- Solo cubre lo que los casos declaran y los tests existentes: lo demás queda como riesgo declarado.
- No distingue una mejora de una regresión fuera de los casos.
- No arregla el código: informa de la discrepancia con la llamada, el valor dorado y el actual.

## Gate de salida

- Verificación sin discrepancias o el cambio revertido.
- Tests del módulo en verde.
- Métricas del después adjuntas junto a las del antes.

## Handoff

Entrega el veredicto y las métricas al responsable del cambio. Si aparece una discrepancia, devuelve el caso concreto a `refactor-harness` para ampliar la cobertura.
