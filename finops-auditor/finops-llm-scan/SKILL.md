---
name: finops-llm-scan
description: Revisa llamadas a APIs de LLM en el código Python: falta de max_tokens, modelos caros usados como clasificador, bucles de agente sin tope y prompts de sistema largos sin caché, con severidad y salida JSON.
license: MIT
metadata:
  package: finops-auditor
  version: "1.3.0"
---

# FinOps LLM Scan

## Objetivo

Encontrar en el código el gasto de IA que crece sin control: respuestas sin límite de tokens, modelos de gama alta haciendo trabajo de clasificador, agentes que repiten llamadas sin contador y prompts de sistema largos que se pagan en cada petición por no usar caché.

## Instrucciones de ejecución

1. Ejecuta el escáner desde la raíz del repositorio:

```bash
py finops-auditor/scripts/llm_cost_scan.py --path <ruta> --json
```

2. Lee la salida y separa lo que se arregla con una línea (un `max_tokens`) de lo que exige rediseño (un bucle de agente sin tope).
3. Si el umbral se supera, repite con `--fail-on high` para convertirlo en puerta de CI.

## Reglas

| Regla | Señal | Severidad |
|---|---|---|
| `llm-sin-limite-tokens` | Llamada sin `max_tokens`, `max_output_tokens` ni `max_completion_tokens` | alta |
| `modelo-caro` | Modelo con `opus`, `gpt-4`, `o1`, `o3` o `pro`; más grave dentro de un clasificador | alta o media |
| `bucle-sin-tope` | `while True` con llamadas al modelo y sin `break` | alta |
| `prompt-sin-cache` | Prompt de sistema de más de 1000 caracteres sin `cache_control` | media |

## Límites

- Análisis estático por AST: no ejecuta el código, no estima precios por token y no conoce el tráfico real.
- No detecta llamadas construidas de forma dinámica (`getattr`, fábricas) ni el gasto de SDKs envueltos por terceros.
- La detección de modelo caro mira el literal del argumento `model`; un alias configurado en entorno queda fuera.

## Gate de salida

- Lista de hallazgos con fichero, línea, regla y severidad, en JSON reproducible.
- Cada hallazgo tiene la corrección concreta: parámetro que falta, modelo alternativo o tope de iteraciones.
- Lo no detectable por análisis estático queda declarado, no se supone.

## Handoff

Entrega a `finops-auditor` el recuento por severidad y las rutas revisadas, y a `finops-ci-opt` los hallazgos que se puedan convertir en puerta de CI. Si no hay llamadas a modelos, dilo y cierra la fase.
