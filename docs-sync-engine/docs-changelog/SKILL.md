---
name: docs-changelog
description: >
  Arma el borrador del CHANGELOG agrupando commits convencionales por tipo y versión, con
  sección Otros para lo que no sigue la convención. Úsala al preparar una release o cuando el
  CHANGELOG no refleje los commits. English: build a CHANGELOG draft from conventional commits,
  with an Other section.
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

# Docs Changelog

## Objetivo

Escribir la entrega desde los commits reales: qué se añadió, qué se corrigió y qué se quedó fuera de la convención.

## Instrucciones de ejecución

1. Genera el borrador desde el rango de la release:

```bash
py docs-sync-engine/scripts/changelog_gen.py --range v3.1.0..HEAD --version 3.2.0 --out CHANGELOG.md
```

2. Revisa que cada entrada se entienda sin abrir el commit; reescribe las que no.
3. Los commits que no siguen `tipo(ámbito): resumen` caen en `Otros`: si aparecen, faltó convención en el equipo.

## Secciones

| Tipo | Sección |
|---|---|
| `feat` | Nuevo |
| `fix` | Correcciones |
| `perf`, `refactor` | Rendimiento, Refactor |
| `docs`, `test`, `build`, `ci`, `chore` | Documentación, Pruebas, Construcción, CI, Mantenimiento |
| Sin convención | Otros |

## Límites

- Lee `git log` local o un fichero de commits: no consulta el remoto ni PRs.
- No decide la versión: la recibe por parámetro y no calcula SemVer.
- Agrupa y ordena; no reescribe el texto de los commits.

## Gate de salida

- Borrador generado con la versión y el rango escritos.
- Entradas de `Otros` revisadas o justificadas.
- El CHANGELOG se escribe en el idioma del proyecto y se commitea con la release.

## Handoff

Entrega el borrador al responsable de la release y, si cambió la estructura, avisa a `docs-arch-gen` para regenerar la arquitectura.
