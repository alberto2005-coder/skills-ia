# DB Architect

> Auditoría de bases de datos relacionales sin motor ni conexión: esquema, riesgo de migraciones, consultas N+1 y datos de siembra deterministas.
> Relational database audit without an engine or a connection: schema, migration risk, N+1 queries and deterministic seed data.

[Español](#español) · [English](#english)

---

## Español

### Índice
1. Propósito
2. Modos
3. Arquitectura
4. Reglas
5. Herramientas
6. Instalación y uso
7. Tests
8. Límites

### Propósito
`db-architect` lee los `.sql` y el código Python de acceso a datos y responde tres preguntas antes de que lo haga producción: qué le falta al esquema, qué migración puede romper el despliegue y dónde hay un N+1. No se conecta a ninguna base: trabaja sobre ficheros y por eso es reproducible y apto para CI.

### Modos
El maestro no usa flags: el alcance de la petición fija las fases.

| Modo | Fases | Entrega |
|---|---|---|
| **Esquema** | `db-schema-audit` | Hallazgos por tabla y severidad |
| **Despliegue** | `db-schema-audit` + `db-migration-guard` | Riesgo de la migración antes de aplicarla |
| **Rendimiento** | `db-query-trace` | Consultas dentro de bucles con su ubicación |
| **Datos** | `db-seed-gen` | SQL o JSON de siembra reproducible |

Los cuatro modos comparten la misma lectura estática, así que se pueden encadenar en una sola sesión.

### Arquitectura
Un maestro y ocho sub-skills con scripts compartidos. Se instala la carpeta completa.

| Sub-skill | Qué hace |
|---|---|
| `db-architect` | Maestro: elige el modo, ordena las fases y firma el informe |
| `db-schema-audit` | Tablas sin clave primaria, claves foráneas sin índice, tipos y restricciones |
| `db-migration-guard` | `DROP TABLE`, `DROP COLUMN`, columnas obligatorias y ausencia de reversión |
| `db-expand-contract` | Plan de dos fases expand/contract y avisos de lo no divisible |
| `db-lock-audit` | Bloqueo y reescritura por operación, con su alternativa segura |
| `db-drift` | Esquema declarado frente a migraciones reproducidas |
| `db-sql-lint` | Estilo SQL: clave primaria, `SELECT *`, palabras clave y snake_case |
| `db-query-trace` | Consultas al ORM dentro de bucles (N+1) con fichero y línea |
| `db-seed-gen` | Datos de siembra deterministas desde el esquema, con semilla |

### Reglas
| Regla | Script | Severidad |
|---|---|---|
| `tabla-sin-primary-key` | `schema_audit.py` | media |
| `fk-sin-indice` | `schema_audit.py` | media |
| `drop-table`, `drop-column` | `migration_guard.py` | crítica |
| `sin-reversion` | `migration_guard.py` | aviso |
| `indice-sin-concurrently`, `rename-inseguro` | `lock_audit.py` | media |
| `reescritura-de-tipo`, `set-not-null` | `lock_audit.py` | alta |
| `deriva` (`tabla-*`, `columna-*`, `tipo-distinto`) | `drift.py` | media/alta |
| `columna-obligatoria-en-un-paso`, `rename-no-divisible`, `reescritura-no-divisible` | `expand_contract.py` | alta |
| `tabla-sin-clave`, `select-asterisco` | `sql_lint.py` | media |
| `palabra-clave-minuscula`, `identificador-no-snake`, `comparacion-distinta`, `linea-larga`, `tabulador` | `sql_lint.py` | baja |
| `consulta-en-bucle` | `query_trace.py` | media |

Cada hallazgo lleva fichero, línea, tabla o función afectada y un mensaje que explica por qué importa.

### Herramientas

```bash
py db-architect/scripts/schema_audit.py --path schema.sql --json
py db-architect/scripts/migration_guard.py --path migrations/ --fail-on critical
py db-architect/scripts/expand_contract.py --path migrations/004_cambio.sql --json
py db-architect/scripts/sql_lint.py --path migrations/ --fail-on medium
py db-architect/scripts/query_trace.py --path src/ --json
py db-architect/scripts/lock_audit.py --path migrations/ --fail-on high
py db-architect/scripts/drift.py --schema schema.sql --migrations migrations/ --json
py db-architect/scripts/seed_gen.py --schema schema.sql --rows 5 --seed 7 --format sql
```

Salida del auditor de esquema:

```json
{
  "files": 1,
  "findings": [
    {"table": "users", "rule": "tabla-sin-primary-key", "severity": "medium", "message": "la tabla users no declara PRIMARY KEY"}
  ],
  "by_severity": {"low": 0, "medium": 1, "high": 0}
}
```

Códigos de salida: `0` limpio o por debajo del umbral · `1` umbral superado · `2` ruta ilegible. Solo stdlib, sin red y sin motor de base de datos.

### Instalación y uso
Copia la carpeta `db-architect/` completa. Ejemplos de petición:
- «Revisa este esquema y dime qué le falta antes de escribir la primera migración».
- «¿Esta migración puede romper el despliegue?».
- «Busca consultas N+1 en el módulo de pedidos».
- «Genera datos de siembra reproducibles para las tablas de prueba».

### Tests

```bash
uv run python -m unittest discover -s db-architect/tests -t db-architect/tests
```

46 pruebas: esquema limpio frente a esquema con hallazgos, migración destructiva frente a reversible, N+1 detectado y no detectado, siembra determinista con la misma semilla, códigos de salida de los seis scripts, y doce sobre bloqueos (cada regla, migración segura, comentarios ignorados, umbral y `--fail-on none`) y deriva (esquema que cuadra, columnas y tablas que sobran o faltan, tipos distintos y renombrado intermedio), y dieciséis sobre el plan de dos fases (aditivo, destructivo, mezcla, columna obligatoria, cambio de tipo, `rename`, `--fail-on none` y ruta ausente) y el lint SQL (fichero limpio, palabra clave en minúscula, `SELECT *`, tabla sin clave, camelCase, `!=` con línea larga, `--fail-on none` y ruta ausente).

### Límites
El análisis es textual y heurístico: no valida el SQL contra un motor real, no conoce dialectos y no modela planes de ejecución. Un esquema generado por ORM sin `.sql` no se audita hasta exportarlo, y la detección de N+1 solo ve consultas escritas dentro del bucle, no las que dispara el ORM por carga diferida. `seed_gen` genera datos sintéticos, nunca extrae datos reales.

---

## English

### Index
1. Purpose
2. Modes
3. Architecture
4. Rules
5. Tools
6. Install and use
7. Tests
8. Limits

### Purpose
`db-architect` reads `.sql` files and Python data-access code and answers three questions before production does: what the schema is missing, which migration can break the deployment and where an N+1 lives. It never connects to a database: it works on files, which makes it reproducible and CI-friendly.

### Modes
The master takes no flags: the request's scope sets the phases.

| Mode | Phases | Deliverable |
|---|---|---|
| **Schema** | `db-schema-audit` | Findings per table and severity |
| **Deploy** | `db-schema-audit` + `db-migration-guard` | Migration risk before applying it |
| **Performance** | `db-query-trace` | Queries inside loops with their location |
| **Data** | `db-seed-gen` | Reproducible SQL or JSON seed data |

All four modes share the same static reading, so they can be chained in one session.

### Architecture
One master and eight sub-skills with shared scripts. The whole folder is installed.

| Sub-skill | What it does |
|---|---|
| `db-architect` | Master: picks the mode, orders the phases and signs the report |
| `db-schema-audit` | Tables without a primary key, foreign keys without an index, types and constraints |
| `db-migration-guard` | `DROP TABLE`, `DROP COLUMN`, mandatory columns and missing rollback |
| `db-expand-contract` | Two-phase expand/contract plan and warnings for what cannot be split |
| `db-lock-audit` | Locking and rewrite per operation, with its safe alternative |
| `db-drift` | Declared schema against replayed migrations |
| `db-sql-lint` | SQL style: primary key, `SELECT *`, keywords and snake_case |
| `db-query-trace` | ORM queries inside loops (N+1) with file and line |
| `db-seed-gen` | Deterministic seed data from the schema, with a seed |

### Rules
| Rule | Script | Severity |
|---|---|---|
| `tabla-sin-primary-key` | `schema_audit.py` | medium |
| `fk-sin-indice` | `schema_audit.py` | medium |
| `drop-table`, `drop-column` | `migration_guard.py` | critical |
| `sin-reversion` | `migration_guard.py` | warning |
| `indice-sin-concurrently`, `rename-inseguro` | `lock_audit.py` | medium |
| `reescritura-de-tipo`, `set-not-null` | `lock_audit.py` | high |
| `deriva` (`tabla-*`, `columna-*`, `tipo-distinto`) | `drift.py` | medium/high |
| `columna-obligatoria-en-un-paso`, `rename-no-divisible`, `reescritura-no-divisible` | `expand_contract.py` | high |
| `tabla-sin-clave`, `select-asterisco` | `sql_lint.py` | medium |
| `palabra-clave-minuscula`, `identificador-no-snake`, `comparacion-distinta`, `linea-larga`, `tabulador` | `sql_lint.py` | low |
| `consulta-en-bucle` | `query_trace.py` | medium |

Every finding carries file, line, affected table or function and a message explaining why it matters.

### Tools

```bash
py db-architect/scripts/schema_audit.py --path schema.sql --json
py db-architect/scripts/migration_guard.py --path migrations/ --fail-on critical
py db-architect/scripts/expand_contract.py --path migrations/004_cambio.sql --json
py db-architect/scripts/sql_lint.py --path migrations/ --fail-on medium
py db-architect/scripts/query_trace.py --path src/ --json
py db-architect/scripts/lock_audit.py --path migrations/ --fail-on high
py db-architect/scripts/drift.py --schema schema.sql --migrations migrations/ --json
py db-architect/scripts/seed_gen.py --schema schema.sql --rows 5 --seed 7 --format sql
```

Schema audit output:

```json
{
  "files": 1,
  "findings": [
    {"table": "users", "rule": "tabla-sin-primary-key", "severity": "medium", "message": "la tabla users no declara PRIMARY KEY"}
  ],
  "by_severity": {"low": 0, "medium": 1, "high": 0}
}
```

Exit codes: `0` clean or below threshold · `1` threshold exceeded · `2` unreadable path. Stdlib only, offline, no database engine.

### Install and use
Copy the whole `db-architect/` folder. Example requests:
- "Review this schema and tell me what it lacks before the first migration".
- "Can this migration break the deployment?".
- "Find N+1 queries in the orders module".
- "Generate reproducible seed data for the test tables".

### Tests

```bash
uv run python -m unittest discover -s db-architect/tests -t db-architect/tests
```

46 tests: clean schema versus schema with findings, destructive versus reversible migration, N+1 detected and not detected, deterministic seeding with the same seed, exit codes for all six scripts, and twelve covering locks (every rule, a safe migration, ignored comments, thresholds and `--fail-on none`) and drift (matching schema, extra or missing columns and tables, type mismatches and an intermediate rename), and sixteen for the two-phase plan (additive, destructive, mixed, mandatory column, type change, `rename`, `--fail-on none` and missing path) and the SQL lint (clean file, lowercase keyword, `SELECT *`, table without a key, camelCase, `!=` with a long line, `--fail-on none` and missing path).

### Limits
The analysis is textual and heuristic: it does not validate SQL against a real engine, knows no dialects and models no execution plans. An ORM-generated schema without `.sql` is not audited until exported, and N+1 detection only sees queries written inside the loop, not those triggered by lazy loading. `seed_gen` produces synthetic data and never extracts real records.
