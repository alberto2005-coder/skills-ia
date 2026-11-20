---
name: db-architect
description: >
  Orquesta la auditoría de bases de datos: esquema, riesgo de migraciones, consultas N+1 y datos
  de siembra deterministas, con flujo Audit → Guard → Optimize y evidencia reproducible. Úsala
  cuando pidan auditar un esquema, evaluar si una migración es peligrosa o revisar las consultas
  de un ORM. English: audit a database without an engine — schema, migration risk, N+1 queries
  and deterministic seeds.
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

# DB Architect

## Propósito

Revisar la base de datos antes de que duela: un esquema sin claves ni índices, una migración que bloquea la tabla, una consulta que se dispara por cada fila y unos datos de prueba que nadie puede reproducir.

## Flujo obligatorio: Audit → Guard → Lock → Drift → Optimize

1. **Audit** con `db-schema-audit`: esquema real, claves primarias, claves foráneas sin índice y sintaxis; `db-sql-lint` revisa el estilo de las mismas sentencias.
2. **Guard** con `db-migration-guard`: cada migración antes de aplicarse, con su nivel de riesgo y su reversión.
3. **Plan** con `db-expand-contract`: qué sentencia va en la fase aditiva y cuál en la de retirada, y qué no se puede partir.
4. **Lock** con `db-lock-audit`: qué operación bloquea la tabla o la reescribe, y con qué alternativa se evita.
5. **Drift** con `db-drift`: esquema declarado frente a las migraciones reproducidas, por tabla y por columna.
6. **Optimize** con `db-query-trace`: consultas dentro de bucles y carga anticipada que falta.
7. **Seed** con `db-seed-gen`: datos de prueba deterministas cuando falten para verificar.

La regla dura: **ninguna migración destructiva se aplica sin aprobación humana explícita**. El paquete analiza y propone; no ejecuta SQL contra una base real.

## Sub-skills

| Sub-skill | Qué hace |
|---|---|
| `db-schema-audit` | DDL validado en SQLite en memoria, PK ausente y FK sin índice |
| `db-migration-guard` | `critical`/`warning` por operación y exigencia de `DOWN`/`downgrade()` |
| `db-expand-contract` | Fases expand/contract y avisos de lo no divisible |
| `db-lock-audit` | Bloqueo y reescritura por operación, con su alternativa segura |
| `db-drift` | Esquema declarado frente a migraciones reproducidas |
| `db-sql-lint` | Estilo SQL: claves, `SELECT *`, palabras clave y snake_case |
| `db-query-trace` | Patrón N+1 por AST y aviso de carga anticipada ausente |
| `db-seed-gen` | Inserts deterministas en orden topológico de claves foráneas |

## Reglas

- Sin dependencias: solo stdlib y `sqlite3` en memoria; nunca se conecta a una base externa.
- Todo hallazgo lleva fichero, línea, regla y severidad; lo que no se pudo comprobar se declara.
- Los datos generados son sintéticos y llevan semilla; no se copian datos reales.

## Gate de salida

- Esquema auditado con hallazgos por severidad y sintaxis validada.
- Cada migración del alcance tiene riesgo, reversión y bloqueo comprobados.
- Deriva entre esquema declarado y migraciones cerrada o justificada.
- Consultas N+1 detectadas con su bucle y su corrección propuesta.
- Si se generaron datos, la semilla y el esquema usados quedan escritos.

## Handoff

Entrega a `appsec-code` cualquier consulta construida con entrada de usuario, y a `replica-test` los datos de siembra y las consultas corregidas para su verificación. Si no hay base de datos en el alcance, dilo y cierra.
