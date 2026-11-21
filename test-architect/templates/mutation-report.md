# Informe de mutación · {{proyecto}}

- **Fecha:** YYYY-MM-DD
- **Runner:** <mutmut | cosmic-ray | stryker | otro>
- **Objetivos elegidos con:** `py test-architect/scripts/mutation_targets.py --limit 10 --min-mutants 4`

## Presupuesto

| Concepto | Valor |
|---|---|
| Funciones objetivo | |
| Mutantes previstos | |
| Mutantes ejecutados | |
| Equivalentes documentados | |

## Objetivos

| Función | Fichero:línea | Mutantes | Operadores | Test que los mata |
|---|---|---|---|---|
| | | | condicional-negada, booleano | |

## Resultado

| Métrica | Valor |
|---|---|
| Mutantes muertos | |
| Supervivientes | |
| Tasa de supervivencia | |

## Supervivientes

| Función | Mutante | Lectura | Acción |
|---|---|---|---|
| | `>` por `>=` | Falta el caso del límite | Añadir test del límite |

Un superviviente en dominio sensible es `high` aunque la tasa global sea buena.

## Descartados

| Función | Motivo |
|---|---|
| | Equivalente: comportamiento idéntico por contrato |
| | Fuera de presupuesto: segunda ronda |

## Gate

- [ ] Cada objetivo tiene operador y presupuesto.
- [ ] Equivalentes anotados y restados.
- [ ] Cero supervivientes en dominio sensible sin acción.
