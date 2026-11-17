---
name: replica-architect
description: Fase 2 de replica — convierte el inventario de funciones en arquitectura: stack, módulos, modelo de datos con invariantes, contratos entre capas y plan de construcción por incrementos. Úsala tras el reconocimiento, cuando haya que decidir stack y estructura antes de programar, o cuando el usuario pida el diseño técnico de un clon.
---

# Replica · Arquitectura (fase 2)

Convierte «qué hace la app» en «cómo se construye sin copiar nada».

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Comandos desde la raíz del repositorio** (`skills-ia-main/`).

## Precondiciones

- `replica/scope.md`, `replica/recon.md` y `replica/features.csv` existen y su gate pasó.
- Si falta `features.csv`, vuelve a `replica-recon`; no lo inventes.

## Método

1. Lee `../references/02-architect.md` entero antes de decidir nada.
2. Elige el stack por los requisitos del alcance, no por moda; si el usuario ya tiene stack, respétalo y justifica solo lo que cambie.
3. Define módulos y sus límites: qué responsabilidad tiene cada uno y qué **no** hace.
4. Modelo de datos con **invariantes explícitas** (lo que nunca puede ser cierto, p. ej. «un pedido pagado siempre tiene importe y moneda»). Cada invariante debe poder testearse.
5. Contratos entre capas: entradas, salidas y errores de cada frontera (API, repositorio, UI). Sin contratos, la fase 4 inventa.
6. Plan de incrementos: cada incremento cierra un flujo `must` de `features.csv` y se puede probar solo.
7. Escribe `replica/architecture.md` desde `../templates/architecture.md`.

## Reglas

- Clean-room: la arquitectura se deriva del comportamiento observado en `recon.md`, nunca de código, esquemas o nombres internos del original.
- Si una decisión depende de un hallazgo, cita su fila de evidencia (`../templates/evidence.md`).
- Si dos opciones son válidas, elige una y anota el motivo y el coste de cambiarla después.

## Gate de salida

- Stack elegido con motivo y alternativa descartada.
- Modelo de datos con invariantes testeables.
- Contratos definidos en cada frontera.
- Cada `must` de `features.csv` asignado a un incremento.
- Sin decisiones huérfanas: toda elección relevante cita evidencia o se marca como supuesto.

## Handoff

`architecture.md` alimenta `replica-design` (fase 3) y `replica-build` (fase 4). Los invariantes pasan a `replica-test` (fase 6).
