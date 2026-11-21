# Operadores de mutación y presupuesto

La mutación comprueba si un test **mira** el resultado. `mutation_targets.py` no ejecuta mutantes: cuenta dónde se pueden aplicar y reparte el presupuesto.

## Operadores

| Operador | Ejemplo original | Mutante | Test que lo mata |
|---|---|---|---|
| `condicional-negada` | `if total > limite:` | `if total >= limite:` | Caso con `total == limite` |
| `booleano` | `if activo and verificado:` | `if activo or verificado:` | Caso con uno solo verdadero |
| `limite` | `if len(items) > 0:` | `if len(items) > 1:` | Lista vacía y lista de un elemento |
| `retorno` | `return balance - amount` | `return balance` | Aserción sobre el saldo devuelto |

Cada operador vale uno; la puntuación de la función es la suma de los cuatro más las ramas. Un `__str__` con dos retornos puntúa, pero se descarta por trivial en el plan.

## Equivalentes

Un mutante equivalente se comporta igual que el original en todo caso posible: no se puede matar y no es un fallo de la suite. Se documenta en el informe y se resta del presupuesto.

Ejemplos típicos:

- `x * 1` mutado a `x / 1`.
- Una condición que ya era siempre verdadera por contrato.
- Un `return` en la última línea de una función sin más salidas.

## Presupuesto

| Parámetro | Efecto |
|---|---|
| `--limit` | Funciones objetivo de la campaña |
| `--min-mutants` | Descarta funciones con pocos puntos de mutación |
| `planned_mutants` | Suma de mutantes del informe: es el coste acordado |

Sin tope, la campaña no termina. Se empieza por las funciones del plan de riesgo y se amplía solo si la tasa de supervivencia baja.

## Lectura del resultado

| Tasa de supervivencia | Lectura |
|---|---|
| < 10 % | La suite mira el resultado; se puede ampliar el alcance |
| 10–30 % | Hay aserciones débiles en las ramas mutadas |
| > 30 % | La cobertura era nominal: faltan casos de contrato, no de línea |

Un superviviente en un dominio sensible (cobro, permisos) es un hallazgo `high` aunque la tasa global sea buena.

## Frontera

La campaña la ejecuta el proyecto con su runner (`mutmut`, `cosmic-ray`, `stryker`). Este paquete elige objetivos, operadores y presupuesto, y no promete una tasa: la mide quien ejecuta.
