---
name: test-mutation
description: >
  Elige dónde merece la pena mutar el código y con qué operadores: funciones con condiciones,
  booleanos, límites y retornos donde un mutante sobreviviría a la suite actual, con presupuesto.
  Úsala cuando la cobertura sea alta pero los tests no detecten regresiones, al priorizar una
  campaña de mutación, o para justificar qué funciones quedan fuera por coste.
  English: pick mutation targets, operators and a budget from the AST — which functions a
  surviving mutant would expose, without running a single mutant.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py test-architect/scripts/mutation_targets.py *)
  - Bash(python3 test-architect/scripts/mutation_targets.py *)
license: MIT
metadata:
  package: test-architect
  version: "1.0.0"
  author: "Alberto Ortiz"
---

# Test Architect · Objetivos de mutación

La cobertura dice qué líneas se ejecutan; la mutación dice si alguien miraría el resultado. Esta sub-skill no ejecuta mutantes: lee el AST, cuenta dónde un cambio mínimo pasaría desapercibido y reparte un presupuesto entre las funciones que más lo justifican.

## Cuándo se usa

- «la cobertura es del 90 % pero se escapan bugs», «¿dónde mutamos primero?».
- Antes de una campaña de mutación, para no gastar el presupuesto en utilidades triviales.
- Al revisar un módulo nuevo: si sus condiciones no tienen test que las contradiga, el mutante sobrevive.

## Alcance y fronteras

| Comprueba | No comprueba |
|---|---|
| Condiciones, booleanos, límites y retornos mutables | Si el mutante sobrevive: eso lo mide el runner |
| Puntuación por densidad de operadores | Cobertura de líneas o de ramas |
| Presupuesto de mutantes por función | Tiempo real de la campaña |
| Funciones sin test reconocible | Contratos HTTP (`api-contract-guard`) |

El mutante se ejecuta en el proyecto, con su runner y su `--fail-on`; aquí solo se decide **dónde** y **cuántos**.

## Método

1. **Recorrer** el AST de los módulos, ignorando entorno, artefactos y tests.
2. **Contar** operadores por función: comparación, booleano, límite numérico, retorno.
3. **Puntuar** cada función por mutantes posibles, ramas y si tiene test reconocible.
4. **Repartir** el presupuesto (`--limit` funciones, `--min-mutants` por función) y dejar el resto como candidatas de segunda ronda.

## Comandos

```bash
py test-architect/scripts/mutation_targets.py --root . --json
py test-architect/scripts/mutation_targets.py --root . --limit 10 --min-mutants 4
```

`--limit` corta el número de funciones objetivo, `--min-mutants` descarta funciones con pocos operadores y `--out` escribe el JSON. Códigos de salida: `0` informe generado · `2` raíz ilegible.

## Operadores

| Operador | Qué cambia | Qué test lo mata |
|---|---|---|
| `condicional-negada` | `a > b` por `a >= b` o su negación | Caso justo en el límite |
| `booleano` | `and` por `or` | Caso donde solo una condición basta |
| `limite` | `0` o `1` por otro valor | Caso vacío y caso de un elemento |
| `retorno` | El valor devuelto | Aserción sobre el resultado, no sobre el efecto |

## Reglas

- Un mutante que nadie puede matar sin cambiar el diseño es una decisión, no un fallo.
- Se muta el dominio, no el `__str__`: la puntuación descarta lo trivial.
- El presupuesto se acuerda antes: sin tope, la campaña no termina.
- Los equivalentes se anotan en el informe; no se cuentan como supervivientes.

## Gate de salida

- Objetivos con operador y presupuesto asignado por función.
- Funciones descartadas con motivo (triviales, equivalentes o fuera de presupuesto).
- Cero objetivos `high` sin test que pueda matarlos.

## Handoff

Las funciones sin test que salgan como objetivo vuelven a `test-plan`; si el hueco está en el contrato entre módulos, a `test-contract`. La campaña real la ejecuta el proyecto y su resultado se compara contra los objetivos elegidos aquí.
