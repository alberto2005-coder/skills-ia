---
name: api-code-sync
description: Cruza rutas del backend con llamadas del frontend con expresiones regulares: detecta dead calls, métodos que no coinciden y endpoints sin consumidor, con salida JSON.
license: MIT
metadata:
  package: api-contract-guard
  version: "1.1.0"
---

# API Code Sync

## Objetivo

Comprobar que el cliente y el servidor hablan del mismo contrato antes de desplegar: ni llamadas a rutas inexistentes ni endpoints que nadie usa.

## Instrucciones de ejecución

1. Cruza las rutas declaradas con las llamadas reales:

```bash
py api-contract-guard/scripts/code_sync.py --backend api.py --frontend app.js --json
```

2. Un `dead-call` bloquea el despliegue; un `sin-consumidor` se revisa para decidir si se retira.
3. Vuelve a pasarlo tras corregir: el objetivo es cero `dead-call`.

## Reglas

| Regla | Señal | Severidad |
|---|---|---|
| `dead-call` | El frontend llama a una ruta que el backend no declara | alta |
| `metodo-distinto` | La ruta existe con otro método HTTP | media |
| `sin-consumidor` | El backend declara una ruta sin ninguna llamada | baja |

## Límites

- El backend se lee de decoradores (`@app.get`, `@router.post`) y el frontend por expresiones regulares: `fetch`, `axios` y `XMLHttpRequest`.
- Las rutas se comparan normalizadas (sin query y sin barra final); un parámetro de ruta (`/users/{id}`) no se resuelve contra valores concretos.
- No sigue imports ni plantillas: una ruta construida dinámicamente aparece como `dead-call` y hay que declararla.

## Gate de salida

- Cero `dead-call` o cada una justificada por construcción dinámica.
- Los `metodo-distinto` corregidos en cliente o servidor.
- El informe con rutas, llamadas y hallazgos queda adjunto.

## Handoff

Entrega a `api-diff` las rutas que han cambiado y a `api-mock-server` la lista de rutas sin backend para probar el cliente contra el contrato.
