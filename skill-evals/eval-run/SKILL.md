---
name: eval-run
description: >
  Ejecuta los casos de evaluación contra el router léxico del repositorio y
  aplica puertas de calidad: mide precisión, recall, MRR, falsos negativos y
  positivos, y detecta colisiones entre descripciones hermanas y excesos del
  presupuesto de tokens. Compara contra una corrida anterior, señala regresiones
  por id de caso y falla el comando si una métrica baja del umbral o si una
  activación se rompe.
  Úsala cuando pidan correr las evaluaciones offline, medir precisión y recall,
  comprobar colisiones o verificar que un cambio no rompe activaciones.
  English: run eval cases through the repository router — precision, recall,
  MRR, collisions, token budget, gates and per-case regressions.
license: MIT
metadata:
  package: skill-evals
  version: "1.0.0"
---

# Skill Evals · Ejecución

Aquí se cambia opinión por número. Cada caso se puntúa contra todas las skills, se ordena con el mismo desempate que usa CI y se decide si pasa con el umbral acordado.

## Precondiciones

- Fichero de casos validado por `eval-design`.
- Catálogo y `tests/phrases.json` en la raíz del repositorio.
- Línea base opcional: una corrida anterior en JSON.

## Método

1. **Cargar** el router desde `tests/trigger_router.py` (sin copiarlo ni reimplementarlo).
2. **Puntuar** cada caso: ranking completo, tres primeras posiciones y puntuación de la esperada.
3. **Decidir** el pase:
   - positiva: la esperada es primera y supera el umbral;
   - negativa: gana la esperada y la prohibida no queda primera;
   - fuera de dominio y límite: ninguna supera el umbral.
4. **Calcular** precisión, recall, MRR, falsos negativos, falsos positivos y colisiones.
5. **Presupuestar** tokens del catálogo y del cuerpo de cada `SKILL.md` (estimación `len/4`).
6. **Comparar** con la línea base: regresiones, arreglos, casos nuevos y retirados.
7. **Aplicar puertas**: `--fail-under metrica=valor`, `--fail-on-regression`.

## Comandos

```bash
py skill-evals/scripts/run.py --cases skill-evals/reports/cases.json --out skill-evals/reports/run.json --fail-under precision=0.95
py skill-evals/scripts/run.py --cases skill-evals/reports/cases.json --baseline skill-evals/reports/run-anterior.json --fail-on-regression
py skill-evals/scripts/run.py --cases skill-evals/reports/cases.json --json
```

Salida: `0` correcto · `1` puerta o regresión · `2` entrada ilegible. El JSON de corrida es el contrato que consume `eval-report`.

## Cómo leer un fallo

| Síntoma | Causa probable | Arreglo |
|---|---|---|
| Positiva con `rank > 1` y `sibling` | Descripción hermana demasiado parecida | Diferenciar vocabulario, no subir el umbral |
| Positiva con `rank > 1` sin `sibling` | Falta en la descripción el vocabulario del usuario | Añadir los términos que usa la frase |
| Fuera de dominio con puntuación alta | Descripción demasiado genérica | Acotar el alcance y quitar términos paraguas |
| Negativa que activa la prohibida | Solape de alcance entre dos skills | Repartir responsabilidades en las descripciones |
| Presupuesto excedido | Cuerpo o descripción crecidos | Mover detalle a `references/` |

## Reglas

- No se cambia el umbral para que pase un caso: se cambia la descripción o se declara la limitación.
- No se borra un caso que falla; se etiqueta y se explica.
- El baseline debe ser una corrida con el mismo conjunto de casos; casos nuevos se informan aparte.

## Gate de salida

- Corrida escrita en JSON con métricas, fallos, colisiones y presupuesto.
- Puertas solicitadas evaluadas y veredicto único (`pass`/`fail`).
- Toda regresión tiene id de caso y diagnóstico.
- El comando termina con el código correcto.

## Handoff

Entrega a `eval-report` la ruta de la corrida, la de la línea base si existe, y el veredicto. Si el veredicto es `fail`, el informe debe abrir con los fallos, no con el resumen.
