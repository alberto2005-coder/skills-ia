---
name: db-drift
description: >
  Compara el esquema declarado con el que resulta de reproducir las migraciones en orden y
  reporta tablas, columnas y tipos que solo están en un lado, con la deriva por nombre. Úsala
  cuando sospeche que el esquema desplegado y las migraciones no cuentan la misma historia.
  English: compare the declared schema with the one replayed migrations produce.
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
---

# DB Drift

## Objetivo

Detectar la base de datos que no coincide con su código: el `.sql` declarado dice una cosa y la cadena de migraciones construye otra.

## Instrucciones de ejecución

1. Compara las dos fuentes en una sola pasada:

```bash
py db-architect/scripts/drift.py --schema schema.sql --migrations migrations/ --json
```

2. En CI, `--fail-on drift` (por defecto) rompe la puerta en cuanto hay diferencias.
3. Cada diferencia se arregla con una migración nueva; no se edita el histórico aplicado.

## Qué compara

| Hallazgo | Significado |
|---|---|
| `tabla-solo-en-esquema` | Declarada y ninguna migración la crea |
| `tabla-solo-en-migraciones` | Creada por una migración y ausente del esquema |
| `columna-solo-en-esquema` | El esquema la pide y las migraciones no la añaden |
| `columna-solo-en-migraciones` | Nace en una migración y el esquema no la documenta |
| `tipo-distinto` | El tipo no coincide entre las dos fuentes |

También aplica `RENAME`, `DROP`, `ADD COLUMN` y `ALTER COLUMN TYPE` en el orden alfabético de las migraciones, así que un renombrado intermedio no genera un falso positivo.

## Límites

- Modelo textual: no ejecuta SQL ni entiende dialectos, `$ref` ni procedimientos almacenados.
- Compara nombres y tipos normalizados, no restricciones, índices ni valores por defecto.
- Requiere que el esquema declarado sea SQL; un esquema gestionado solo por ORM no se compara hasta exportarlo.

## Gate de salida

- Cero diferencias o cada una con su migración de corrección propuesta.
- Tablas comparadas y número de migraciones reproducidas anotados.
- El comando y el umbral usados quedan escritos junto al resultado.

## Handoff

Entrega a `db-lock-audit` la migración de corrección para revisar su bloqueo y a `db-schema-audit` el esquema resultante para validar claves e índices.
