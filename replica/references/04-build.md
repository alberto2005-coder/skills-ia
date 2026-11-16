# 04 · Construcción

Objetivo: pantallas funcionando, en el orden que reduce riesgo, con la matriz de features como fuente de verdad.

## Entradas
`replica/architecture.md`, `replica/design/*`, `replica/features.csv`.

## Pasos

1. **Shell.** Layout, navegación, tokens aplicados, tema, manejo de errores global, loading.
2. **Primera rebanada end-to-end.** El flujo que da la promesa de la app, completo: UI → API → datos. Nada de capas a medias.
3. **Resto por áreas**, de `must` a `could`. Una feature no se marca `done` hasta tener sus estados (vacío, error, carga, permisos) y pasar el flujo a mano.
4. **Actualiza `features.csv`** al cerrar cada una: `done`, `partial` o sigue `missing`. Sin generosidad: `partial` es honesto y `parity.py` lo cuenta como medio.
5. **Copy propio.** Reescribe todos los textos; los mensajes de error son tuyos y dicen qué hacer.
6. **Accesibilidad de serie.** Etiquetas, foco, teclado, contraste ya validado, `alt` real.
7. **Rendimiento mínimo.** Imágenes dimensionadas, lazy donde toca, sin bloqueos de render evidentes.

## Salida
Código de la app + `replica/features.csv` actualizado. Si una decisión de arquitectura cambió, se anota en `architecture.md`.

## Definición de done por pantalla
- [ ] Happy path completo contra datos reales (no mock).
- [ ] Vacío, carga, error, sin permisos.
- [ ] Teclado y foco.
- [ ] Sin restos del original (`sweep.py` en verde al final de la fase).
- [ ] `features.csv` refleja la realidad.

## No hagas
Copiar el DOM, el CSS, los textos o los assets del original. Ni "de momento" con su logo dentro.
