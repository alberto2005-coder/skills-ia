---
name: replica-test
description: >
  Fase 6 de replica — plan de pruebas y ejecución real: flujo principal end-to-end, estados vacío/error, invariantes de datos, permisos, regresión y bugs con severidad. Úsala antes de medir paridad, cuando haya que probar un clon, escribir el plan de pruebas o decidir si algo está listo para lanzar. English: write the test plan, run end-to-end cases and log bugs by S1 S2 S3 severity.
license: MIT
metadata:
  package: replica
  version: "2.0.0"
---

# Replica · Pruebas (fase 6)

Un clon sin pruebas no está listo: está sin terminar. Esta fase convierte `features.csv` e invariantes en pruebas ejecutables. Mide corrección propia, no parecido con el original: la paridad es `replica-diff` (fase 7).

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Comandos desde la raíz del repositorio**.

## Precondiciones

- Fases 4 y 5 con código funcional.
- `features.csv` con criterios de aceptación.
- Invariantes de `architecture.md` y reglas de permisos de `backend.md`.

## Método

1. Lee `../references/06-test.md` entero.
2. Escribe `replica/test-plan.md` desde `../templates/test-plan.md`: por cada flujo `must`, camino feliz + al menos un caso de error + un caso límite.
3. Prueba los **invariantes** directamente (no a través de la UI): un invariante que solo se comprueba visualmente no está probado.
4. Prueba permisos en negativo: usuario sin sesión, usuario ajeno, recurso inexistente.
5. Ejecuta de verdad. Un plan sin ejecución no es un gate.
6. Registra cada fallo en `replica/bugs.md` con severidad **S1** (bloquea uso o pierde datos), **S2** (flujo principal degradado), **S3** (cosmético). Un S1/S2 abierto bloquea el lanzamiento.
7. Repite la suite completa antes de declarar la fase cerrada.

## Gate de salida

- Flujo principal end-to-end verde.
- Estados vacío, error y carga probados.
- Invariantes cubiertos por prueba.
- Permisos probados en negativo.
- 0 bugs S1/S2 abiertos.
- `test-plan.md` y `bugs.md` actualizados con el resultado real de la última ejecución.

## Handoff

Con la suite verde, `replica-diff` (fase 7) mide paridad funcional contra el original.
