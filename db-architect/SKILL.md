---
name: db-architect
description: Orquesta la auditoría de bases de datos: esquema, riesgo de migraciones, consultas N+1 y datos de siembra deterministas, con flujo Audit → Guard → Optimize y evidencia reproducible.
license: MIT
metadata:
  package: db-architect
  version: "1.0.0"
---

# DB Architect

## Propósito

Revisar la base de datos antes de que duela: un esquema sin claves ni índices, una migración que bloquea la tabla, una consulta que se dispara por cada fila y unos datos de prueba que nadie puede reproducir.

## Flujo obligatorio: Audit → Guard → Optimize

1. **Audit** con `db-schema-audit`: esquema real, claves primarias, claves foráneas sin índice y sintaxis.
2. **Guard** con `db-migration-guard`: cada migración antes de aplicarse, con su nivel de riesgo y su reversión.
3. **Optimize** con `db-query-trace`: consultas dentro de bucles y carga anticipada que falta.
4. **Seed** con `db-seed-gen`: datos de prueba deterministas cuando falten para verificar.

La regla dura: **ninguna migración destructiva se aplica sin aprobación humana explícita**. El paquete analiza y propone; no ejecuta SQL contra una base real.

## Sub-skills

| Sub-skill | Qué hace |
|---|---|
| `db-schema-audit` | DDL validado en SQLite en memoria, PK ausente y FK sin índice |
| `db-migration-guard` | `critical`/`warning` por operación y exigencia de `DOWN`/`downgrade()` |
| `db-query-trace` | Patrón N+1 por AST y aviso de carga anticipada ausente |
| `db-seed-gen` | Inserts deterministas en orden topológico de claves foráneas |

## Reglas

- Sin dependencias: solo stdlib y `sqlite3` en memoria; nunca se conecta a una base externa.
- Todo hallazgo lleva fichero, línea, regla y severidad; lo que no se pudo comprobar se declara.
- Los datos generados son sintéticos y llevan semilla; no se copian datos reales.

## Gate de salida

- Esquema auditado con hallazgos por severidad y sintaxis validada.
- Cada migración del alcance tiene riesgo y reversión comprobada.
- Consultas N+1 detectadas con su bucle y su corrección propuesta.
- Si se generaron datos, la semilla y el esquema usados quedan escritos.

## Handoff

Entrega a `appsec-code` cualquier consulta construida con entrada de usuario, y a `replica-test` los datos de siembra y las consultas corregidas para su verificación. Si no hay base de datos en el alcance, dilo y cierra.
