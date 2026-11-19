---
name: docs-drift-check
description: >
  Detecta referencias rotas en la documentación comparando las rutas entre backticks y los
  enlaces relativos contra el árbol real del repositorio. Úsala cuando haya que comprobar que
  los enlaces y las rutas citadas en la documentación siguen existiendo. English: find broken
  references by comparing backtick paths and relative links with the tree.
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
  version: "1.2.0"
---

# Docs Drift Check

## Objetivo

Encontrar la documentación que cita ficheros que ya no existen, antes de que lo haga un lector.

## Instrucciones de ejecución

1. Comprueba la carpeta de documentación:

```bash
py docs-sync-engine/scripts/docs_drift.py --docs docs/ --root . --json
```

2. En CI usa `--fail-on high`: una referencia rota rompe el pipeline.
3. Excluye con `--exclude` las guías históricas que citan rutas antiguas a propósito.

## Qué revisa

| Origen | Ejemplo |
|---|---|
| Rutas entre backticks | `` `pkg/scripts/x.py` `` |
| Enlaces relativos | `[guía](../SKILL.md)` |
| Enlaces externos | Se ignoran |

## Límites

- Comprueba existencia, no contenido: un comando dentro del fichero puede estar obsoleto y seguir pasando.
- No resuelve anclas (`#seccion`) ni rutas absolutas de sistema.
- No corrige la documentación: señala fichero y línea para que se arregle.

## Gate de salida

- Cero referencias rotas o lista con su justificación.
- Los ficheros históricos excluidos quedan nombrados.
- La comprobación se puede repetir con el mismo comando.

## Handoff

Entrega a `docs-arch-gen` las rutas que cambiaron de sitio y a `docs-changelog` la nota de la corrección documental.
