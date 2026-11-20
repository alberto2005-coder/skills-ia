---
name: docs-terms
description: >
  Revisa la terminología de la documentación con glosarios accept/reject, sugiere el reemplazo
  de cada término prohibido y avisa de grafías que no son la canónica. Úsala cuando haya que
  unificar terminología y grafías entre documentos. English: enforce canonical glossary terms
  and flag banned spellings.
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
  author: "Alberto Ortiz"
---

# Docs Terms

## Objetivo

Que el mismo concepto se llame igual en toda la documentación: un glosario versionado decide qué término vale y con qué grafía, y el resto se corrige.

## Instrucciones de ejecución

1. Pasa el glosario sobre la documentación publicada:

```bash
py docs-sync-engine/scripts/terms_check.py --path docs/ --accept accept.txt --reject reject.txt --json
```

2. `reject.txt` admite `malo => bueno`, así el hallazgo ya trae el reemplazo.
3. En CI usa `--fail-on medium`: los términos prohibidos rompen y las grafías menores se revisan aparte.

## Reglas

| Regla | Severidad | Qué señala |
|---|---|---|
| `termino-rechazado` | media | El término está en `reject.txt` |
| `grafia-no-canonica` | baja | El término de `accept.txt` aparece con otra grafía |

El texto dentro de bloques de código y de `código en línea` se ignora: solo se revisa prosa.

## Límites

- Coincidencia por palabra completa: no detecta variantes morfológicas (`endpoints`) salvo que estén en el glosario.
- No entiende contexto: un término legítimo en una cita textual se marca igual y se excluye del glosario o se acepta la excepción.
- El glosario vive en el repositorio; aquí no se inventan términos ni se traducen.

## Gate de salida

- Cero términos rechazados o cada uno con su reemplazo aplicado.
- Glosarios usados y número de documentos revisados anotados.
- Los términos nuevos se añaden al glosario en el mismo cambio que la documentación.

## Handoff

Entrega a `docs-drift-check` los documentos corregidos y a `docs-arch-gen` el glosario, para que el borrador generado use la misma grafía.
