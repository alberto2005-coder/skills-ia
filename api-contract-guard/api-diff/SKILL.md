---
name: api-diff
description: >
  Compara dos contratos OpenAPI y calcula el impacto SemVer: endpoint o tipo de respuesta
  eliminado es major, lo aditivo es minor y la documentación es patch, con detalle por ruta.
  Úsala cuando pregunten qué versión le toca a un cambio de contrato o qué campos y rutas
  desaparecen entre dos OpenAPI. English: compute the SemVer impact of a contract change with
  per-route detail.
license: MIT
metadata:
  package: api-contract-guard
  version: "1.2.1"
  author: "Alberto Ortiz"
---

# API Diff

## Objetivo

Decidir con evidencia si un cambio de contrato rompe consumidores, antes de publicarlo.

## Instrucciones de ejecución

1. Ejecuta el diff entre la versión publicada y la nueva:

```bash
py api-contract-guard/scripts/contract_diff.py --old old.json --new new.json --json
```

2. Usa `--fail-on major` en CI: el pipeline se rompe si el cambio rompe consumidores.
3. Anota en el PR el nivel y las rutas afectadas; el `major` exige versión nueva.

## Clasificación

| Cambio | Nivel |
|---|---|
| Endpoint o método eliminado | `major` |
| Tipo de respuesta modificado | `major` |
| Endpoint o método nuevo | `minor` |
| Solo cambia la descripción | `patch` |

## Límites

- Compara JSON OpenAPI, no YAML, y no resuelve `$ref` externos.
- Solo mira el primer código de respuesta (`200`/`201`): cambios en errores no se clasifican.
- No conoce a los consumidores reales: eso lo aporta `api-code-sync`.

## Gate de salida

- Nivel calculado y cambios listados con ruta y detalle.
- Cero `major` sin versión nueva o sin aprobación escrita del responsable.
- El diff queda guardado en JSON junto al PR.

## Handoff

Entrega a `api-code-sync` las rutas eliminadas o cambiadas para localizar las llamadas del frontend que hay que migrar.
