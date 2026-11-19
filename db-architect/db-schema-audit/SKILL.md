---
name: db-schema-audit
description: >
  Audita esquemas SQL con SQLite en memoria: claves primarias ausentes, claves foráneas sin índice y sintaxis inválida, con severidad y salida JSON para la puerta de CI.
license: MIT
metadata:
  package: db-architect
  version: "2.0.0"
---

# DB Schema Audit

## Objetivo

Validar el DDL que se va a desplegar y encontrar las dos causas estructurales de consultas lentas y migraciones caras: tablas sin clave primaria y claves foráneas sin índice.

## Instrucciones de ejecución

1. Ejecuta la auditoría sobre el esquema o la carpeta de migraciones:

```bash
py db-architect/scripts/schema_audit.py --path <ruta> --json
```

2. Corrige primero la sintaxis: un `sql-invalido` invalida el resto del informe.
3. Añade los índices que faltan y vuelve a pasarlo hasta 0 hallazgos medios.

## Reglas

| Regla | Señal | Severidad |
|---|---|---|
| `sql-invalido` | SQLite no puede ejecutar el esquema en `:memory:` | alta |
| `tabla-sin-primary-key` | `CREATE TABLE` sin `PRIMARY KEY` | media |
| `fk-sin-indice` | `FOREIGN KEY` o `REFERENCES` sin índice sobre la columna | media |

## Límites

- SQLite acepta sintaxis que PostgreSQL o MySQL rechazan: sirve para detectar lo grueso, no como validador del motor real.
- No mide cardinalidades ni planes de ejecución: un índice puede ser innecesario y aquí no se detecta.
- Los `ALTER` de migraciones quedan fuera; para eso está `db-migration-guard`.

## Gate de salida

- Hallazgos con fichero, línea, tabla, regla y severidad en JSON reproducible.
- Cada FK sin índice tiene el `CREATE INDEX` propuesto con su nombre.
- El esquema pasa SQLite en memoria antes de dar el informe por bueno.

## Handoff

Entrega a `db-migration-guard` el esquema corregido y a `db-query-trace` las tablas con más claves foráneas, que son las candidatas a bucles N+1.
