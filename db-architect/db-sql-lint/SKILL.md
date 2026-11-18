---
name: db-sql-lint
description: Lint de estilo sobre ficheros SQL con reglas acotadas: palabras clave, SELECT *, tablas sin clave primaria, snake_case, líneas largas, tabuladores y != en lugar de <>.
license: MIT
metadata:
  package: db-architect
  version: "1.2.0"
---

# DB SQL Lint

## Objetivo

Que las migraciones y consultas se lean igual entre autores: el estilo no cambia el resultado, pero una tabla sin clave primaria o un `SELECT *` sí acaban costando.

## Instrucciones de ejecución

1. Pasa el lint sobre las migraciones antes del guardián de riesgo:

```bash
py db-architect/scripts/sql_lint.py --path migrations/ --json --fail-on medium
```

2. Corrige primero lo de severidad media (clave primaria y `SELECT *`); el estilo bajo se arregla en la misma pasada.
3. En CI usa `--fail-on medium` para no bloquear por espacios mientras el resto se estabiliza.

## Reglas

| Regla | Severidad | Qué señala |
|---|---|---|
| `tabla-sin-clave` | media | `CREATE TABLE` sin `PRIMARY KEY` |
| `select-asterisco` | media | `SELECT *` acopla la consulta al orden de columnas |
| `palabra-clave-minuscula` | baja | Palabras clave en minúsculas |
| `identificador-no-snake` | baja | Identificador en camelCase |
| `comparacion-distinta` | baja | `!=` en lugar de `<>` |
| `linea-larga` | baja | Más de 120 caracteres |
| `tabulador` | baja | Tabuladores en el fichero |

## Límites

- Texto, no dialecto: no distingue PostgreSQL de MySQL y puede marcar sintaxis válida de uno como rara.
- No formatea ni reescribe: solo señala con fichero, línea y regla.
- Es un subconjunto pequeño: no cubre las 79 reglas de sqlfluff ni sus reglas de indentación.

## Gate de salida

- Cero hallazgos medios o cada uno con su justificación escrita.
- Ficheros analizados y umbral usados anotados junto al resultado.
- El estilo no se arregla dentro de una migración ya aplicada: se corrige en la siguiente.

## Handoff

Entrega a `db-migration-guard` la migración ya limpia y a `db-expand-contract` el plan de las que cambian estructura, para que el estilo no oculte un cambio de riesgo.
