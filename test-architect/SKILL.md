---
name: test-architect
description: >
  Diseña la estrategia de pruebas de un repositorio a partir de su código: qué probar primero,
  qué tests son inestables, dónde merece la pena mutar y qué contratos hay que fijar.
  Úsala cuando pidan un plan de pruebas, revisar tests inestables o flaky, elegir objetivos de
  mutación, o fijar los contratos entre módulos antes de refactorizar.
  English: decide what to test first, hunt flaky tests, pick mutation targets and pin the
  contracts between modules — all from the source tree, without running any suite.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py test-architect/scripts/*)
  - Bash(python3 test-architect/scripts/*)
license: MIT
metadata:
  package: test-architect
  version: "1.0.0"
  author: "Alberto Ortiz"
---

# Test Architect

## Propósito

Decidir **qué se prueba, qué se estabiliza y qué se congela** con evidencia del árbol, no con intuición. El paquete lee código y tests y devuelve planes y hallazgos; no lanza la suite ni mutantes en vivo, así que se puede usar en un repo que no compila.

## Flujo

1. **Plan** con `test-plan`: módulos por riesgo (autenticación, dinero, permisos) y cobertura real por nombre de test.
2. **Estabilidad** con `test-flaky`: esperas fijas, reloj de pared, azar sin semilla, red real y estado compartido.
3. **Mutación** con `test-mutation`: funciones donde una mutación sobreviviría y presupuesto de mutantes.
4. **Contratos** con `test-contract`: campos, tipos y obligatoriedad entre fixture proveedor y consumidor.
5. **Cerrar** con el ledger de cobertura: lo que se decide no probar se anota con motivo, no se olvida.

## Sub-skills

| Sub-skill | Qué hace |
|---|---|
| `test-plan` | Plan priorizado: riesgo del módulo frente a la cobertura que declaran los tests |
| `test-flaky` | Patrones de inestabilidad en los ficheros de test, con fichero y línea |
| `test-mutation` | Objetivos de mutación y operadores por función, sin ejecutar nada |
| `test-contract` | Deriva entre el contrato declarado y el payload de los fixtures |

## Fronteras

| No es de este paquete | Dónde vive |
|---|---|
| Rutas, OpenAPI y SemVer del contrato HTTP | `api-contract-guard` (`api-diff`, `api-auth-coverage`) |
| Calidad de activación de una skill y su presupuesto | `skill-evals` |
| Ejecutar la suite, mutantes o runners reales | El proyecto auditado y su CI |
| Corrección de seguridad del código | `appsec-audit` |

Un contrato aquí es el **payload entre módulos o fixtures**, no el documento OpenAPI: si el problema es una ruta que desaparece o un cambio major, la skill es `api-diff`.

## Reglas

- Se lee antes de escribir: un plan sin cobertura declarada es una lista de deseos.
- El riesgo manda sobre el número: una función de cobro sin test pesa más que veinte utilidades cubiertas.
- Un test inestable se arregla en su causa (reloj, azar, red, orden), no con un reintento.
- La mutación elige dónde duele; el mutante lo ejecuta el proyecto, con su runner y su presupuesto.
- Todo lo que se decide no probar queda escrito en el ledger con el motivo.

## Gate de salida

- Plan con prioridades y cada módulo de riesgo alto con test asignado o exclusión motivada.
- Cero patrones de inestabilidad `high` sin explicar.
- Objetivos de mutación dentro del presupuesto acordado.
- Contratos sin campos obligatorios ausentes ni tipos divergentes.

## Handoff

Si el hueco es de contrato HTTP, pasa a `api-contract-guard`; si es de cobertura de seguridad, a `appsec-audit`; si el plan detecta que la suite no arranca, se entrega el diagnóstico y no se promete cobertura.
