---
name: api-contract-guard
description: Orquesta la defensa de un contrato de API: diff SemVer entre versiones, cruce de rutas backend/frontend y servidor mock local, con veredicto major/minor/patch y evidencia reproducible.
license: MIT
metadata:
  package: api-contract-guard
  version: "1.0.0"
---

# API Contract Guard

## Propósito

Evitar que un cambio de API rompa a quien la consume: decidir si el impacto es `major`, `minor` o `patch`, encontrar las llamadas del frontend que ya no existen y levantar un mock local para probar sin backend.

## Flujo

1. **Diff** con `api-diff`: compara la versión publicada con la nueva y calcula el impacto SemVer.
2. **Cruce** con `api-code-sync`: verifica que cada llamada del frontend tenga su endpoint y cada endpoint su consumidor.
3. **Mock** con `api-mock-server`: sirve los ejemplos del contrato en `127.0.0.1` para probar el cliente sin desplegar nada.
4. **Veredicto**: un `major` exige versión nueva de la API y plan de migración; un `minor` solo requiere anuncio.

## Sub-skills

| Sub-skill | Qué hace |
|---|---|
| `api-diff` | Diff OpenAPI → `major`/`minor`/`patch` con detalle por ruta |
| `api-code-sync` | Rutas backend vs llamadas frontend: `dead-call` y `sin-consumidor` |
| `api-mock-server` | Servidor HTTP local con los ejemplos del contrato |

## Reglas

- Sin red: el diff y el cruce son estáticos y el mock solo escucha en loopback.
- Un `major` no se negocia con un umbral: se publica una versión nueva.
- Todo hallazgo lleva ruta, método y evidencia; lo que no se pudo analizar se declara.

## Gate de salida

- Diff calculado con su nivel y la lista de cambios por ruta.
- Cruce cerrado: cero `dead-call` o cada una justificada.
- Si se levantó el mock, el contrato y el puerto usados quedan escritos.

## Handoff

Entrega a `api-diff` la versión anterior y a `api-code-sync` las rutas afectadas. Si el frontend no está en el alcance, dilo y limita el veredicto al contrato.
