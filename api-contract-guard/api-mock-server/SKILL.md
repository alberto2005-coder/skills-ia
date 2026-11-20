---
name: api-mock-server
description: >
  Levanta un servidor HTTP mock en 127.0.0.1 desde un contrato OpenAPI, responde los ejemplos
  declarados y no sale nunca a la red ni toca el backend real. Úsala cuando haya que probar el
  frontend sin backend, tener respuestas de ejemplo del contrato o un servidor local aislado.
  English: serve a local mock from the OpenAPI examples without touching the real backend.
license: MIT
metadata:
  package: api-contract-guard
  version: "1.2.0"
  author: "Alberto Ortiz"
---

# API Mock Server

## Objetivo

Probar el cliente contra el contrato sin desplegar el backend: respuestas de ejemplo, rutas inexistentes con 404 y nada de tráfico externo.

## Instrucciones de ejecución

1. Levanta el mock desde la raíz del repositorio:

```bash
py api-contract-guard/scripts/mock_server.py --spec api.json --port 8080
```

2. Apunta el cliente a `http://127.0.0.1:8080` y prueba los casos del contrato.
3. Para tests, importa `serve(spec)` y usa el puerto efímero que devuelve; cierra con `shutdown()`.

## Comportamiento

| Petición | Respuesta |
|---|---|
| Ruta y método declarados | `200` con el `example` del contrato |
| Ruta declarada sin ejemplo | `200` con `{"mock": ruta, "method": MÉTODO}` |
| Ruta o método no declarados | `404` con el motivo |

## Límites

- Solo sirve `GET` y `POST` y solo escucha en `127.0.0.1`.
- No valida el cuerpo de la petición ni aplica reglas de negocio: es un mock, no un emulador.
- No resuelve `$ref` externos ni genera datos aleatorios: devuelve lo que el contrato declara.

## Gate de salida

- Puerto y contrato usados quedan escritos junto al resultado de la prueba.
- Toda ruta probada que devolvió 404 está declarada como hueco del contrato.
- El mock se ha cerrado y no queda ningún proceso escuchando.

## Handoff

Entrega a `api-code-sync` las rutas que el cliente llamó y el mock no declaraba, y a `api-diff` cualquier ejemplo que ya no case con el contrato.
