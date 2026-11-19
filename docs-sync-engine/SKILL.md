---
name: docs-sync-engine
description: >
  Mantiene la documentación pegada al código: detecta referencias rotas, genera el borrador de
  arquitectura y arma el CHANGELOG desde los commits, de forma reproducible. Úsala cuando la
  documentación haya quedado atrás del código o antes de publicar una release. English: keep
  docs glued to the code — broken references, architecture draft and CHANGELOG.
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

# Docs Sync Engine

## Propósito

Que la documentación no mienta: toda ruta citada existe, la arquitectura se regenera desde el árbol y el CHANGELOG sale de los commits, no de la memoria.

## Flujo

1. **Verificar** con `docs-drift-check`: cada ruta citada en la doc debe existir en el repositorio.
2. **Terminología** con `docs-terms`: glosario aceptado/rechazado y grafía canónica de cada término.
3. **Entorno** con `docs-env`: cada variable que lee el código aparece en `.env.example` y en la guía.
4. **Regenerar** con `docs-arch-gen`: la tabla de módulos y responsabilidades sale de los AST.
5. **Cerrar** con `docs-changelog`: agrupa los commits convencionales por versión.
6. **Comparar**: el borrador regenerado se revisa contra el documento vigente y solo se commitea lo que cambió de verdad.

## Sub-skills

| Sub-skill | Qué hace |
|---|---|
| `docs-drift-check` | Referencias de la doc frente al árbol: enlaces y rutas entre backticks |
| `docs-terms` | Glosario: términos rechazados y grafías canónicas |
| `docs-env` | Variables de entorno frente a `.env.example` y los docs |
| `docs-terms` | Glosario: términos rechazados y grafías canónicas |
| `docs-env` | Variables de entorno frente a `.env.example` y los docs |
| `docs-arch-gen` | Borrador de arquitectura desde docstrings y entradas |
| `docs-changelog` | CHANGELOG agrupado desde commits convencionales |

## Reglas

- La documentación se regenera, no se reescribe a mano: si el borrador difiere, manda el código.
- Un enlace roto es un fallo del repositorio, no una nota al pie.
- Todo documento generado lleva escrito el comando que lo regenera.
- Un término prohibido o una variable sin documentar es documentación rota, igual que un enlace.
- Un término prohibido o una variable sin documentar es documentación rota, igual que un enlace.

## Gate de salida

- Cero referencias rotas o cada una justificada.
- Documento de arquitectura regenerado y diff revisado.
- CHANGELOG de la versión generado desde los commits incluidos.

## Handoff

Entrega a `docs-drift-check` las rutas nuevas y a `docs-changelog` la versión publicada. Si un documento no se puede regenerar, se declara como manual y se anota el motivo.
