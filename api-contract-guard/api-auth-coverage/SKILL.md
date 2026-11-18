---
name: api-auth-coverage
description: Cruza la seguridad declarada en OpenAPI con las guardas reales de las rutas del código y reporta rutas protegidas sin guarda, guardas sin `security` y operaciones sin implementar.
license: MIT
metadata:
  package: api-contract-guard
  version: "1.1.0"
---

# API Auth Coverage

## Objetivo

Que el contrato no prometa seguridad que el código no aplica: una ruta con `security` y sin guarda es un hueco abierto, y una guarda sin `security` es documentación que miente al consumidor.

## Instrucciones de ejecución

1. Cruza contrato y código antes de publicar:

```bash
py api-contract-guard/scripts/auth_coverage.py --spec openapi.json --code src/ --json
```

2. En CI usa el umbral por defecto (`medium`): `ruta-sin-guarda` es alta y rompe la puerta.
3. Cada `ruta-sin-spec` se resuelve añadiendo la operación al contrato con su seguridad, no quitando la ruta del código.

## Reglas

| Regla | Severidad | Qué señala |
|---|---|---|
| `ruta-sin-guarda` | alta | El contrato exige seguridad y la función no lleva guarda |
| `ruta-sin-spec` | media | La ruta existe en el código y no en el contrato |
| `spec-sin-security` | media | El código protege la ruta y el contrato no declara `security` |
| `spec-sin-codigo` | baja | El contrato declara la operación y no hay ruta que la implemente |

La seguridad global del documento se hereda en las operaciones que no la sobrescriben.

## Cómo se detecta una guarda

- Decoradores de ruta de FastAPI/Flask: `@app.get`, `@router.post`, `@app.route(..., methods=[...])`.
- Decoradores de guarda: cualquier decorador cuyo texto contenga `auth`, `login`, `jwt`, `permission`, `token`, `guard`, `security` o `require`.
- Rutas con parámetros: `<int:id>` se normaliza a `{id}` para comparar con OpenAPI.

## Límites

- Solo OpenAPI en JSON; no lee YAML ni resuelve `$ref` externos.
- La guarda se reconoce por el texto del decorador: una comprobación dentro del cuerpo o un middleware global no aparecen como guarda y hay que declararlos.
- Compara pares método + ruta: un prefijo montado en otro router (`include_router(prefix=…)`) puede generar `ruta-sin-spec` hasta ajustar el contrato.

## Gate de salida

- Cero `ruta-sin-guarda` o cada una con su justificación escrita.
- Operaciones del contrato y rutas del código contadas y empatadas, con las excepciones declaradas.
- El comando y el umbral usados quedan anotados junto al informe.

## Handoff

Entrega a `api-diff` las operaciones que cambian y a `api-code-sync` las rutas nuevas, para que el contrato y el frontend se actualicen en el mismo cambio.
