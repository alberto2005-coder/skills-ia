---
name: replica-recon
description: Fases 0-1 (y 1b) de replica — fija límites legales y alcance, hace reconocimiento de una app por funciones observables con evidencia obligatoria y produce scope.md, recon.md, features.csv y screens/. Úsala para empezar una réplica, decidir qué se puede clonar, levantar el inventario de funciones de una app o especificar software complejo (Word, Figma, suites). Palabras clave: reconocer app, alcance, inventario de funciones, qué puedo clonar, clean-room, apps complejas. English: set the legal scope and boundaries, list the features of the app you want to clone with evidence and confidence, and specify complex apps.
---

# Replica · Reconocimiento (fases 0-1)

Primera sub-skill del pipeline `replica`. Su trabajo es **decidir qué se va a reconstruir y demostrar que se puede hacer legalmente**, antes de escribir una línea de producto.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`, `../tests/`. **Comandos desde la raíz del repositorio** (`skills-ia-main/`).

## Cuándo se usa

- El usuario pide clonar, replicar o «hacer algo como X» y todavía no hay alcance escrito.
- Hay que responder «¿esto se puede copiar?» sin asesoría legal: solo señalar los checks.
- La app objetivo es un editor o suite de alta densidad interactiva (Word, Docs, Figma): entonces la fase 1b es obligatoria.

## Precondiciones

Ninguna. Si existe `replica/progreso.md`, léelo antes: una fase `aprobada` no se repite.

## Método

### Fase 0 — Límites y alcance

1. Lee `../references/00-limites.md` entero. No improvises el criterio legal.
2. Escribe `replica/scope.md` desde `../templates/scope.md`: qué funciones entran, qué queda fuera y por qué, qué fuentes están permitidas y qué se declara `THIN` desde el principio.
3. Avisa de los checks que el usuario debe resolver con su abogado (trademark, términos del original, contenido licenciado). No des asesoría legal.

### Fase 1 — Reconocimiento por función

1. Lee `../references/01-recon.md` entero, incluido el **paso 0 de foco**: una función observable y medible por iteración, no la app completa de golpe.
2. Recorre las 5 capas del método (inventario amplio → resumen → módulo → función → detalle) y detente donde el alcance lo pida.
3. Fuentes permitidas: páginas públicas, docs, help center, store listing, reseñas públicas y **tu propia cuenta**. Nunca cuenta ajena, scraping tras login ni saltarse un paywall.
4. Por cada hallazgo que sostenga una decisión, rellena una fila de `../templates/evidence.md`: **Fuente · Observación · Inferencia · Confianza (high/medium/low/THIN) · Límites y desconocidos**. Observación e inferencia nunca en la misma casilla; sin fuente, el hallazgo se descarta.
5. Salidas en `replica/`: `recon.md`, `features.csv` (desde `../templates/features.csv`, con `must`/`should`/`could` y `out_of_scope`) y `screens/` con capturas propias.
6. Cierra los documentos con **Mapa · Límites · Desconocidos**.

### Fase 1b — Apps complejas (solo si aplica)

Si el objetivo es un software de productividad o de alta densidad interactiva, lee `../references/01b-apps-complejas.md` y escribe `replica/complex-app-spec.md` desde `../templates/complex-app-spec.md`: AST del documento, modelo de selección/caret, pila de comandos con undo/redo y layout geométrico.

## Gate de salida

- `scope.md` escrito y con exclusiones explícitas.
- `features.csv` con al menos un `must` por flujo principal y sin filas sin criterio de aceptación.
- Tabla de evidencia completa en `recon.md`; ningún `THIN` usado como argumento.
- Si aplica 1b: `complex-app-spec.md` con las cuatro secciones.

Un gate rojo deja la fase `bloqueada` en `progreso.md` con el motivo escrito; no se rodea.

## Handoff

Entrega al usuario: alcance, inventario de funciones, evidencia y lo que quedó `THIN`. La siguiente sub-skill es `replica-architect` (fase 2), que consume `features.csv` y `recon.md`.
