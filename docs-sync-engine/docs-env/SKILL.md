---
name: docs-env
description: >
  Cruza las variables de entorno que lee el código con .env.example y la documentación, y
  reporta las que faltan en cada lado y las declaradas que nadie usa. Úsala cuando alguien clone
  el repositorio y no sepa qué variables necesita, o cuando sobren variables en .env.example.
  English: cross-check env vars read in code against .env.example and the docs.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py docs-sync-engine/scripts/*)
  - Bash(python3 docs-sync-engine/scripts/*)
  - Bash(git log *)
license: MIT
metadata:
  package: docs-sync-engine
  version: "1.3.0"
  author: "Alberto Ortiz"
---

# Docs Env

## Objetivo

Que quien clona el repositorio sepa qué variables necesita antes de ejecutarlo: si el código lee una variable que no está en `.env.example`, el arranque falla en la primera máquina nueva.

## Instrucciones de ejecución

1. Cruza código, ejemplo y documentación:

```bash
py docs-sync-engine/scripts/env_check.py --path src/ --env-example .env.example --docs README.md --json
```

2. Añade a `.env.example` cada `env-sin-ejemplo` con un valor de mentira, nunca el real.
3. Cada `env-sin-documentar` se nombra en el README o en la guía de despliegue, con su formato y su efecto.

## Reglas

| Regla | Severidad | Qué señala |
|---|---|---|
| `env-sin-ejemplo` | media | El código la lee y no está en `.env.example` |
| `env-sin-documentar` | media | El código la lee y no aparece en la documentación |
| `ejemplo-sin-uso` | baja | Está en `.env.example` y ningún fichero la lee |

Reconoce `os.environ[...]`, `os.environ.get`, `os.getenv`, `process.env.X` e `import.meta.env.X`, y en `.env.example` acepta tanto `CLAVE=` como `export CLAVE=`.

## Límites

- Solo estático: una variable construida por concatenación o leída desde configuración externa no se ve.
- La documentación se reconoce por el nombre en mayúsculas dentro de los ficheros indicados; un README que la describe sin nombrarla cuenta como no documentada.
- No valida valores ni formato: comprueba presencia, no corrección.

## Gate de salida

- Cero variables usadas sin ejemplo ni documentación, o cada excepción justificada.
- `.env.example` sin secretos reales y con las variables nuevas.
- Número de variables usadas, declaradas y documentadas anotado junto al informe.

## Handoff

Entrega a `docs-drift-check` las rutas de los documentos tocados y a `docs-changelog` las variables nuevas de la versión, para que la nota de release las nombre.
