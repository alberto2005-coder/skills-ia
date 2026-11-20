---
name: db-lock-audit
description: >
  Detecta las operaciones de migración que bloquean la tabla o la reescriben: cambio de tipo,
  columna NOT NULL con DEFAULT, CREATE INDEX sin CONCURRENTLY, RENAME en un paso y VACUUM FULL.
  Úsala cuando una migración pueda dejar la tabla bloqueada o reescribirla durante minutos.
  English: flag the migration operations that lock or rewrite a table and give the safe
  alternative.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py db-architect/scripts/*)
  - Bash(python3 db-architect/scripts/*)
license: MIT
metadata:
  package: db-architect
  version: "2.1.0"
  author: "Alberto Ortiz"
---

# DB Lock Audit

## Objetivo

Separar una migración que se aplica en segundos de una que deja la tabla bloqueada cinco minutos: el guardián dice si destruye datos, este dice cuánto va a doler mientras corre.

## Instrucciones de ejecución

1. Audita la carpeta de migraciones antes de desplegar:

```bash
py db-architect/scripts/lock_audit.py --path migrations/ --json
```

2. En CI usa `--fail-on high` para bloquear las reescrituras; `--fail-on medium` añade los bloqueos de construcción de índice.
3. Cada hallazgo se corrige con la alternativa segura, no silenciándolo.

## Alternativas por hallazgo

| Regla | Alternativa |
|---|---|
| `reescritura-de-tipo` | Columna nueva con el tipo final, copia por lotes y retirada después |
| `columna-not-null-con-default` | Añadir la columna nullable, rellenar y luego `SET NOT NULL` |
| `set-not-null` | `CHECK ... NOT VALID`, validar y después `SET NOT NULL` |
| `indice-sin-concurrently` | `CREATE INDEX CONCURRENTLY` fuera de transacción |
| `rename-inseguro` | Columna nueva, doble escritura y retirada de la vieja |
| `fk-sin-not-valid` | `ADD CONSTRAINT ... NOT VALID` y `VALIDATE CONSTRAINT` |
| `vacuum-full` | `VACUUM` normal o `pg_repack` en ventana de mantenimiento |

## Límites

- Analiza SQL y migraciones en Python por patrón: no conoce la versión del motor, y lo que es reescritura en PostgreSQL 10 deja de serlo en 11.
- No mide tiempos ni tamaños de tabla: dice qué operación bloquea, no cuántos segundos.
- Los comentarios de línea se ignoran; el SQL generado dinámicamente no se ve.

## Gate de salida

- Cada operación con bloqueo tiene su alternativa escrita o su aceptación explícita.
- Cero hallazgos altos sin justificar con una ventana de mantenimiento.
- El umbral usado en la puerta queda anotado.

## Handoff

Entrega a `db-migration-guard` lo que además destruye datos y a `db-drift` el esquema resultante, para comprobar que la migración segura no cambia el modelo esperado.
