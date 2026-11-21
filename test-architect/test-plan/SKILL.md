---
name: test-plan
description: >
  Convierte el árbol y los tests existentes en un plan priorizado: qué módulos no tienen prueba,
  cuáles tocan autenticación, dinero o permisos, y qué se cubre primero con el presupuesto que hay.
  Úsala cuando pidan un plan de pruebas, decidan por dónde empezar a testear un repo heredado, o
  quieran justificar qué queda fuera de la cobertura.
  English: turn the tree into a prioritised test plan — untested modules, risky domains and a
  coverage ledger that records what is left out and why.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py test-architect/scripts/plan_tests.py *)
  - Bash(python3 test-architect/scripts/plan_tests.py *)
license: MIT
metadata:
  package: test-architect
  version: "1.0.2"
  author: "Alberto Ortiz"
---

# Test Architect · Plan de pruebas

Un plan útil no es la lista de ficheros sin test: es el cruce entre lo que puede romperse caro y lo que hoy nadie comprueba. Esta sub-skill lee el árbol y los nombres de los tests, y devuelve prioridades con la razón escrita.

## Cuándo se usa

- «¿por dónde empiezo a testear este repo?», «hazme un plan de pruebas».
- Un módulo nuevo entra en un dominio sensible (cobro, sesión, permisos) y hay que decidir qué se prueba antes de mergear.
- Antes de una release, para saber qué zonas quedan sin red.

## Alcance y fronteras

| Comprueba | No comprueba |
|---|---|
| Módulos sin test por nombre y dominio | Calidad interna de los tests que existen |
| Dominios de riesgo por ruta, nombre y símbolos | Cobertura de líneas real (no ejecuta la suite) |
| Tamaño y superficie pública del módulo | Que el test existente pase |
| Exclusiones motivadas del ledger | Rutas ni contratos HTTP (`api-contract-guard`) |

El plan se apoya en señales estáticas: nombres de fichero, funciones públicas, clases y palabras del dominio. Si el proyecto ya publica un informe de cobertura, se usa como entrada y manda sobre la heurística.

## Método

1. **Inventariar** los módulos del árbol, excluyendo entorno, artefactos y `tests/`.
2. **Cruzar** cada módulo con los ficheros de test por nombre (`test_<módulo>.py`, `<módulo>_test.py` o carpeta homónima).
3. **Puntuar** el riesgo: dominio sensible, superficie pública, longitud y manejo de excepciones.
4. **Ordenar** por puntuación y cortar por `--limit`, dejando el resto fuera del plan pero dentro del ledger.
5. **Escribir** el ledger con el motivo de cada exclusión.

## Comandos

```bash
py test-architect/scripts/plan_tests.py --root . --json
py test-architect/scripts/plan_tests.py --root . --limit 20 --min-score 8 --out plan.json
```

`--root` fija el árbol (por defecto, el directorio actual), `--limit` el número de módulos del plan, `--min-score` el corte de riesgo y `--out` escribe el JSON en vez de imprimirlo. Códigos de salida: `0` plan generado · `2` raíz ilegible.

## Cómo leer un hallazgo

| Regla | Significado | Arreglo |
|---|---|---|
| `modulo-sin-tests` | El módulo no tiene test reconocible por nombre | Añadir test o anotar la exclusión |
| `dominio-riesgoso` | Ruta o símbolos de cobro, sesión o permisos | Probar el caso feliz y el de error antes que nada |
| `superficie-grande` | Muchas funciones públicas sin red | Partir el módulo o empezar por las de entrada |

## Reglas

- El plan se ordena por coste del fallo, no por número de líneas.
- Un módulo sin test en dominio sensible es `high`; el resto, como mucho `medium`.
- Una exclusión sin motivo escrito no existe: el ledger es parte del entregable.
- No se promete cobertura: se promete orden y justificación.

## Gate de salida

- Cada módulo `high` del plan tiene test asignado o exclusión motivada.
- Ledger generado con el corte aplicado y la fecha.
- El plan cabe en el presupuesto acordado (`--limit`).

## Handoff

Los módulos que fallan por inestabilidad, no por falta de test, pasan a `test-flaky`; los que necesitan congelar un contrato entre módulos, a `test-contract`. Si el proyecto pide cobertura real, se ejecuta su runner fuera de esta skill.
