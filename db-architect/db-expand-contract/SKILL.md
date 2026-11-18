---
name: db-expand-contract
description: Divide una migración en el plan de dos fases expand y contract, separa lo aditivo de lo destructivo y avisa de lo que no se puede partir sin reescribir la tabla.
license: MIT
metadata:
  package: db-architect
  version: "1.2.0"
---

# DB Expand Contract

## Objetivo

Desplegar un cambio de esquema sin ventana de mantenimiento: primero se añade lo nuevo y se escribe en los dos lados, después se retira lo viejo. Una migración que mezcla las dos cosas obliga a parar la aplicación.

## Instrucciones de ejecución

1. Genera el plan antes de aplicar nada:

```bash
py db-architect/scripts/expand_contract.py --path migrations/004_cambio.sql --json
```

2. Aplica la fase `expand`, despliega el código que escribe en el formato nuevo y solo entonces la fase `contract`.
3. Cada aviso se resuelve con su alternativa, no posponiéndolo.

## Fases

| Fase | Sentencias | Cuándo se aplica |
|---|---|---|
| `expand` | `CREATE TABLE`, `ADD COLUMN`, `CREATE INDEX [CONCURRENTLY]`, `ADD CONSTRAINT … NOT VALID`, `VALIDATE CONSTRAINT` | Antes del despliegue del código |
| `contract` | `DROP TABLE`, `DROP COLUMN`, `DROP CONSTRAINT`, `RENAME`, `SET NOT NULL`, `ALTER … TYPE` | Después de que el código nuevo esté estable |
| `unknown` | Cualquier sentencia que el analizador no reconoce (`DROP INDEX`, `INSERT`, …) | Nunca: se revisa a mano |

`deployable_together` es `false` cuando la migración mezcla las dos fases o trae alguna desconocida: entonces necesita dos despliegues, no uno más largo.

## Avisos

| Regla | Por qué |
|---|---|
| `columna-obligatoria-en-un-paso` | `ADD COLUMN … NOT NULL` no se puede repartir: columna nullable, relleno y apriete |
| `rename-no-divisible` | Un `RENAME` rompe el código viejo: columna nueva, doble escritura y retirada |
| `reescritura-no-divisible` | `ALTER … TYPE` reescribe la tabla: columna nueva con el tipo final y copia por lotes |
| `sentencia-desconocida` | No se puede colocar en una fase sin saber si añade o retira |

## Límites

- Lee SQL textual: no conoce el estado real de la base ni qué código está desplegado.
- No genera el relleno de datos ni la doble escritura; marca dónde van.
- Un cambio de tipo que PostgreSQL resuelve sin reescribir (por ejemplo, ampliar `varchar`) se avisa igual: el análisis no distingue versiones del motor.

## Gate de salida

- Plan con las dos fases por escrito y el número de despliegues que necesita.
- Cada aviso con su alternativa aplicada o su aceptación explícita.
- La migración aplicada queda enganchada a `db-lock-audit` para revisar el bloqueo de cada fase.

## Handoff

Entrega a `db-lock-audit` cada fase para medir su bloqueo, a `db-migration-guard` la reversión de las dos y a `db-drift` el esquema que debería quedar tras el contrato.
