---
name: eval-report
description: >
  Renderiza una corrida de evaluación en Markdown o en un HTML autónomo con
  estilos embebidos: resumen de métricas, tabla de fallos con esperado, ganador
  y hermana, colisiones, presupuesto de contexto y cambios contra la línea base.
  Incluye el veredicto del gate y explica cada regresión por id de caso.
  Úsala cuando pidan el informe de evaluación, la tabla de fallos y el veredicto,
  un HTML para adjuntar o comparar dos corridas en un documento legible.
  English: turn an eval run into a deterministic Markdown or standalone HTML
  report with failures, collisions, context budget and baseline changes.
license: MIT
metadata:
  package: skill-evals
  version: "1.1.0"
  author: "Alberto Ortiz"
---

# Skill Evals · Informe

El informe no descubre nada: ordena lo que la corrida ya demostró. Su valor está en que un fallo se lea en diez segundos y en que dos corridas se puedan comparar sin abrir JSON.

## Precondiciones

- Corrida JSON de `eval-run` con `format: skill-evals-run`.
- Línea base opcional para la sección de cambios.
- Destino: stdout, `.md` o `.html`.

## Estructura

1. **Veredicto y umbral** en la primera línea: `PASS` o `FAIL`, sin ambigüedad.
2. **Resumen**: casos, aprobados, precisión, recall, MRR, falsos negativos/positivos, colisiones, tokens de catálogo y skills fuera de presupuesto.
3. **Por tipo y split**: positivas, negativas, límites, fuera de dominio; train y test por separado.
4. **Fallos**: id, esperado, ganador, puntuación y hermana. Si no hay, se dice explícitamente.
5. **Colisiones**: pares con Jaccard y su valor.
6. **Presupuesto**: las cinco skills más pesadas y el total del catálogo.
7. **Cambios contra la línea base**: regresiones, arreglos, nuevos y retirados, con ids.

## Comandos

```bash
py skill-evals/scripts/report.py --run skill-evals/reports/run.json --out skill-evals/reports/informe.md
py skill-evals/scripts/report.py --run skill-evals/reports/run.json --baseline skill-evals/reports/run-anterior.json --format html --out skill-evals/reports/informe.html
py skill-evals/scripts/report.py --run skill-evals/reports/run.json --format md
```

Sin `--out` escribe en stdout. El HTML es un único fichero, sin CDN ni JavaScript, con el contenido escapado.

## Reglas

- **Determinista**: mismo JSON de entrada, mismo informe byte a byte. Sin fecha ni hora.
- **Sin HTML crudo**: todo texto de un caso se escapa; una descripción con `<script>` no se ejecuta.
- **Un veredicto**: si el gate falló, el informe no puede titular «correcto».
- **Fallos primero**: con veredicto `fail`, la sección de fallos va antes que el presupuesto.
- **Sin métricas inventadas**: solo se muestran las que están en el JSON de corrida.

## Gate de salida

- Informe generado en el formato pedido, con veredicto visible.
- Todos los fallos y regresiones de la corrida aparecen con id.
- Colisiones y presupuesto incluidos aunque estén vacíos.
- HTML válido como documento único y sin recursos externos.

## Handoff

Entrega la ruta del informe y el veredicto a quien tomó la decisión de publicar el catálogo. Si el veredicto es `fail`, adjunta la lista de ids y la corrección propuesta en la descripción; no se publica hasta que la corrida pase.
