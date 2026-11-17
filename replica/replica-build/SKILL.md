---
name: replica-build
description: Fase 4 de replica — construye la app por incrementos que cierran flujos must de features.csv, usando los tokens y contratos ya aprobados, y actualiza el estado de cada función al terminarla. Úsala para implementar pantallas y flujos de un clon, para continuar la construcción tras la arquitectura o para saber qué falta para cerrar la paridad. English: implement incrementally the must flows from features.csv with the approved tokens.
license: MIT
metadata:
  package: replica
  version: "2.0.0"
---

# Replica · Construcción (fase 4)

Escribe la app. Cada incremento cierra un flujo `must`, se prueba solo y actualiza `features.csv`. Esta fase no incluye auth, datos persistentes, pagos ni jobs: eso es `replica-backend` (fase 5).

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Comandos desde la raíz del repositorio** (`skills-ia-main/`).

## Precondiciones

- `architecture.md` con contratos e invariantes.
- `design/tokens.json` y `design/components.md`.
- `features.csv` con criterios de aceptación por fila.

## Método

1. Lee `../references/04-build.md` entero.
2. Ordena el trabajo por incrementos de `architecture.md`; dentro de cada uno, primero el camino feliz y después vacío/error/carga.
3. Implementa contra los contratos: si necesitas cambiar uno, actualiza `architecture.md` en el mismo paso y anótalo.
4. Usa solo `design/tokens.json`; ningún color o tamaño hardcodeado fuera de tokens.
5. Al cerrar una función, actualiza su fila en `features.csv`: `todo` → `partial` → `done`, con la prueba que lo demuestra. Sin prueba, no es `done`.
6. Nada de código, nombres internos, textos ni assets del original: clean-room también aquí.
7. Si el alcance crece, para y vuelve a `replica-recon`; no añadas funciones `could` por iniciativa propia.

## Gate de salida

- Todos los flujos `must` del incremento en `done` con prueba ejecutada.
- Estados vacío, error y carga implementados en cada pantalla de datos.
- Cero dependencias nuevas fuera de las aprobadas en `architecture.md`.
- `features.csv` coherente con el código (una fila `done` sin prueba es un gate rojo).

## Handoff

El código construido pasa a `replica-backend` (fase 5) para auth, datos y pagos, y a `replica-test` (fase 6) para el plan de pruebas.
