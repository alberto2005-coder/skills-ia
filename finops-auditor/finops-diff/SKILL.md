---
name: finops-diff
description: Compara el coste de dos inventarios por recurso y aplica guardrails de CI (--max-increase, --max-percent, --budget), con salida JSON y código de salida 1 cuando se supera un límite.
license: MIT
metadata:
  package: finops-auditor
  version: "1.3.0"
---

# FinOps Diff

## Objetivo

Responder en un PR «cuánto cuesta este cambio» antes de aplicarlo, y romper el pipeline cuando el aumento supera lo acordado.

## Instrucciones de ejecución

1. Compara los dos inventarios y aplica los límites:

```bash
py finops-auditor/scripts/cost_diff.py --before antes.json --after despues.json --max-increase 100 --max-percent 10 --budget 5000 --json
```

2. En CI, deja los tres guardrails declarados: el código de salida 1 es la puerta.
3. Revisa primero la lista de recursos: el total dice cuánto, los recursos dicen por qué.

## Guardrails

| Flag | Mide | Superado cuando |
|---|---|---|
| `--max-increase` | Diferencia absoluta del total | `después - antes` supera el valor |
| `--max-percent` | Diferencia porcentual | el porcentaje supera el valor; si el total anterior es 0 no aplica |
| `--budget` | Coste total nuevo | el total de `después` supera el techo |

Cada guardrail es independiente: se pueden romper los tres a la vez y el informe los lista todos con su límite y su cifra real.

## Salida

| Campo | Contenido |
|---|---|
| `before_total`, `after_total`, `delta`, `delta_percent` | Totales redondeados a dos decimales |
| `resources.added` / `removed` / `changed` | Altas, bajas y cambios de precio por `id` |
| `breaches` | Guardrail roto, límite y valor que lo superó |

`--fail-on none` deja el informe sin romper la puerta, para el primer diagnóstico.

## Límites

- Compara por `id` de recurso: si el `id` cambia entre inventarios, el recurso aparece como baja más alta y el total sigue cuadrando.
- Solo lee los precios declarados en los JSON: no consulta tarifas ni facturación.
- No valora si el aumento está justificado; mide el importe y aplica el límite que se le da.

## Gate de salida

- Totales, delta y recursos implicados escritos en el resultado.
- Cada guardrail roto con su límite y su cifra, o el «sin guardrails» declarado.
- El comando y los límites usados quedan anotados junto al diff.

## Handoff

Entrega a `finops-rightsize` los recursos que más suben para buscar ahorro compensatorio, y a `finops-llm-scan`, `finops-infra-scan` o `finops-ci-opt` el origen del aumento cuando venga de código, infraestructura o CI.
