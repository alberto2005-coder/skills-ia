---
name: eval-ab
description: >
  Compara dos corridas de evaluación ya grabadas en JSON y decide si la variante B mejora a la A:
  eficacia, cumplimiento de los casos obligatorios, coste, latencia y variabilidad entre repeticiones.
  Úsala cuando haya que elegir entre dos versiones de una skill o de un prompt con datos ya medidos,
  sin volver a ejecutar agentes ni modelos.
  English: compare two recorded evaluation runs in JSON — effectiveness, compliance, cost, latency
  and run-to-run variability — without executing any agent or model again.
license: MIT
metadata:
  package: skill-evals
  version: "1.1.0"
  author: "Alberto Ortiz"
---

# Skill Evals · Comparativa A/B

Elegir variante mirando la media es cómo se publica una regresión. Esta sub-skill compara dos corridas grabadas y separa lo que mejora de lo que empeora: acierto, cumplimiento de lo obligatorio, coste, latencia y estabilidad entre repeticiones.

## Cuándo se usa

- Hay dos versiones de una descripción o de un prompt y sus corridas ya están guardadas.
- Una variante sube el acierto pero también el coste, y hay que decidir con el número delante.
- Se sospecha que una variante es inestable: acierta a veces y falla otras con el mismo caso.

## Alcance y fronteras

| Comprueba | No comprueba |
|---|---|
| Eficacia: proporción de muestras correctas | Que el caso esté bien diseñado (`eval-design`) |
| Cumplimiento: acierto en casos obligatorios o negativos | Si el router es el adecuado |
| Coste y latencia medios por muestra | El coste real de un proveedor |
| Variabilidad: desviación de la puntuación por caso | La causa de la variabilidad |
| Diferencia por caso entre A y B | Significancia estadística con muestras pequeñas |

No ejecuta nada: lee dos JSON ya producidos por `eval-run` o por el arnés del proyecto. Comparar no es volver a correr.

## Método

1. **Normalizar** cada corrida: casos con sus muestras (`passed`, `score`, `latency_ms`, `cost_usd`).
2. **Calcular** por corrida: eficacia, cumplimiento, coste medio, latencia media y variabilidad.
3. **Emparejar** por id de caso y calcular la diferencia de eficacia de cada uno.
4. **Comparar** B contra A: puntos porcentuales en eficacia y cumplimiento, porcentaje en coste y latencia.
5. **Aplicar** las puertas pedidas y emitir un veredicto único.

## Comandos

```bash
py skill-evals/scripts/ab_compare.py --a control.json --b variante.json --json
py skill-evals/scripts/ab_compare.py --a control.json --b variante.json --max-cost-increase 20 --max-latency-increase 15
```

Códigos: `0` sin puerta superada, `1` alguna puerta superada, `2` corrida ilegible.

## Formato de una corrida

```json
{
  "label": "control",
  "cases": [
    {"id": "positiva-auth", "kind": "positive", "samples": [
      {"passed": true, "score": 0.91, "latency_ms": 120, "cost_usd": 0.002}
    ]},
    {"id": "negativa-deploy", "kind": "negative", "samples": [
      {"passed": true, "score": 0.80, "latency_ms": 110, "cost_usd": 0.0015}
    ]}
  ]
}
```

Una lista plana de muestras con el mismo `id` se agrupa igual: cada muestra es una repetición.

## Cómo leer el resultado

| Campo | Significado | Decisión |
|---|---|---|
| `effectiveness` | Muestras correctas / total | Sube o no sube |
| `compliance` | Acierto en casos `negative` u obligatorios | No puede bajar |
| `cost` | Coste medio por muestra | Comparar con el presupuesto |
| `latency` | Latencia media por muestra | Comparar con el SLA |
| `variability` | Desviación media de la puntuación por caso | Menos es más estable |
| `cases[].delta` | Diferencia de eficacia por caso | Explica la media |

## Reglas

- B no gana por media si pierde cumplimiento: lo obligatorio no se negocia.
- Una mejora de eficacia con coste disparado se declara empate con su motivo.
- La variabilidad se mide con repeticiones; sin ellas se informa como `null`, no como cero.
- No se comparan corridas con conjuntos de casos distintos sin declararlo.

## Gate de salida

- Comparativa escrita con métricas de A, de B y su diferencia.
- Puertas solicitadas evaluadas y veredicto único.
- Casos donde B pierde, identificados por id.
- Coste y latencia expresados por muestra, no como total agregado.

## Handoff

Si B mejora y pasa las puertas, `eval-report` redacta el informe con la comparativa como evidencia; si empeora el cumplimiento, vuelve a `eval-design` para revisar los casos obligatorios antes de cambiar nada.
