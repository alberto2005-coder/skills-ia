---
name: db-query-trace
description: Detecta consultas ORM dentro de bucles (N+1) en código Python con AST, sin ejecutarlo, y avisa cuando falta carga anticipada como selectinload o joinedload.
license: MIT
metadata:
  package: db-architect
  version: "1.2.0"
---

# DB Query Trace

## Objetivo

Encontrar el patrón que multiplica consultas sin que se note en los tests: un bucle que consulta el ORM por cada fila en lugar de traer todo con una sola consulta.

## Instrucciones de ejecución

1. Ejecuta el trazador sobre el código:

```bash
py db-architect/scripts/query_trace.py --path <ruta> --json
```

2. Para cada hallazgo, sustituye la consulta del bucle por carga anticipada (`selectinload`, `joinedload`, `prefetch_related`) o por una consulta con `IN` fuera del bucle.
3. Vuelve a pasarlo: el objetivo es 0 hallazgos.

## Reglas

| Regla | Señal | Severidad |
|---|---|---|
| `consulta-en-bucle` | `for`/`async for` con `.get`, `.filter`, `.filter_by`, `.execute`, `.query`, `.all`, `.first`, `.one` o `.fetchall` y sin carga anticipada | media |

Un bucle que solo recorre relaciones ya cargadas no se marca: es el caso correcto.

## Límites

- Análisis estático: no sabe si la colección tiene 10 filas o 100.000, así que el impacto real se mide aparte.
- No sigue el ORM a través de funciones auxiliares ni de repositorios que envuelven la consulta.
- No detecta N+1 en SQL a mano ni en otros lenguajes.

## Gate de salida

- Hallazgos con fichero, línea, colección iterada y regla, en JSON reproducible.
- Cada hallazgo tiene la consulta corregida propuesta.
- Los bucles descartados por tener carga anticipada quedan fuera del informe, sin ruido.

## Handoff

Entrega a `db-schema-audit` las tablas implicadas por si falta un índice, y al solicitante la lista de bucles con su corrección. Si el proyecto no usa ORM, dilo.
