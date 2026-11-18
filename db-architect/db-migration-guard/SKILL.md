---
name: db-migration-guard
description: Clasifica el riesgo de migraciones SQL y Alembic/Django: DROP, TRUNCATE y cambios de tipo como críticos, índices sin CONCURRENTLY como aviso, y exige DOWN o downgrade() para poder revertir.
license: MIT
metadata:
  package: db-architect
  version: "1.2.0"
---

# DB Migration Guard

## Objetivo

Decidir si una migración se puede aplicar en caliente o necesita ventana, y si se puede revertir. Nada se aplica desde aquí: se clasifica y se entrega el veredicto.

## Instrucciones de ejecución

1. Pasa el guardián sobre el fichero o la carpeta de migraciones:

```bash
py db-architect/scripts/migration_guard.py --path migrations --json
```

2. Con `--fail-on critical` en CI, la migración se bloquea si destruye datos o bloquea la tabla.
3. Si falta reversión, escribe el `DOWN` antes de pedir aprobación.

## Reglas

| Regla | Nivel | Por qué |
|---|---|---|
| `drop-table` | crítico | borra datos sin vuelta atrás |
| `drop-column` | crítico | rompe lectores antiguos durante el despliegue |
| `truncate` | crítico | vacía la tabla sin recuperación |
| `cambio-de-tipo` | crítico | reescribe la tabla y bloquea escrituras |
| `indice-sin-concurrently` | aviso | el índice bloquea la tabla mientras se construye |
| `columna-not-null-con-default` | aviso | reescribe la tabla en motores antiguos |
| `sin-reversion` | aviso | no hay `DOWN`/`downgrade()` |

Lo que va después del marcador de reversión (`-- DOWN`) no se clasifica como riesgo de la migración: es la vuelta atrás.

## Límites

- Reglas de texto: no interpreta SQL de forma completa ni el ORM que genera la migración.
- No mide el tamaño real de la tabla, así que un `CREATE INDEX` puede ser inocuo en una tabla pequeña.
- No aplica ni revierte nada; la ejecución queda en manos de quien tenga acceso.

## Gate de salida

- Cada migración tiene nivel, regla y línea, y su veredicto de aplicación.
- Toda migración crítica tiene plan de reversión o una razón escrita de por qué no lo necesita.
- El conjunto se ha pasado con `--fail-on critical` y el código de salida está registrado.

## Handoff

Entrega a `db-schema-audit` el esquema resultante para revalidarlo y al solicitante las migraciones críticas con su ventana propuesta. Si el proyecto no tiene migraciones, dilo.
