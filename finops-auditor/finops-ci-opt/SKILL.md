---
name: finops-ci-opt
description: Revisa workflows de GitHub Actions: falta de caché de dependencias y ejecución duplicada de push y pull_request sin concurrencia, con salida JSON y umbral de fallo para la puerta de CI.
license: MIT
metadata:
  package: finops-auditor
  version: "1.2.0"
---

# FinOps CI Opt

## Objetivo

Cortar el gasto de integración continua que se paga dos veces: suites que corren por `push` y por `pull_request` sin cancelar la anterior, y workflows que reinstalan dependencias en cada ejecución por no tener caché.

## Instrucciones de ejecución

1. Ejecuta el escáner sobre los workflows:

```bash
py finops-auditor/scripts/ci_cost_scan.py --path .github/workflows --json
```

2. Aplica primero `concurrency` con `cancel-in-progress: true`, que es el ahorro grande; después añade caché de dependencias.
3. Cierra con `--fail-on high` en el propio workflow para que la regla no vuelva a romperse.

## Reglas

| Regla | Señal | Severidad |
|---|---|---|
| `ci-doble-ejecucion` | `push` y `pull_request` sin `concurrency` con `cancel-in-progress` | alta |
| `ci-sin-cache` | Workflow sin `actions/cache`, `setup-uv` con caché ni `cache:` | media |

## Límites

- Reglas de texto: no valida la sintaxis YAML ni sigue workflows reutilizables (`uses: ./.github/workflows/...`).
- No mide minutos ni dinero: mide patrones que multiplican ejecuciones.
- Un workflow sin caché puede ser correcto si sus pasos son triviales; se reporta como aviso, no como fallo.

## Gate de salida

- Hallazgos con fichero, regla y severidad en JSON reproducible.
- Cada hallazgo trae el bloque YAML que lo cierra (`concurrency` o `cache`).
- Los workflows reutilizables y los no cubiertos quedan declarados.

## Handoff

Entrega a `finops-auditor` el recuento por severidad y los workflows revisados. Si el repositorio no tiene CI, dilo y no inventes ahorro.
