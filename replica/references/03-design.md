# 03 · Sistema de diseño

Objetivo: un sistema propio que se sienta del mismo oficio que el original, sin copiar su expresión.

## Entradas

`replica/screens/`, `replica/recon.md`, `templates/tokens.json`.

## Pasos

1. **Mide estructura, no pixels de marca.** De las capturas saca: escala tipográfica, densidad, ritmo de espaciado (4/8px), radios, alturas de control, jerarquía. No muestrees sus colores exactos ni su logo.
2. **Tokens propios.** Copia `templates/tokens.json` y define roles: `background`, `surface`, `text`, `muted`, `primary`, `on_primary`, estados (`success`, `warning`, `danger`). Nombra por rol, no por color.
3. **Contraste.** `python scripts/contrast.py replica/design/tokens.json` hasta AA en todos los pares de texto.
4. **Tipografía e iconos.** Fuente abierta (OFL/Apache) y set de iconos abierto; anota licencia en `components.md`.
5. **Componentes.** Por componente: anatomía, variantes, tamaños, estados (hover/focus/active/disabled/loading/error), teclado y foco visible. Incluye lo específico del dominio (selector de fecha, botón de hueco, tarjeta de plan).
6. **Movimiento.** Duraciones y curvas coherentes; respeta `prefers-reduced-motion`.
7. **Modo claro/oscuro** solo si la app lo tiene; si no, no lo inventes.

## Salida

`replica/design/tokens.json`, `replica/design/components.md` con la tabla de componentes, estados y licencias.

## Checklist

- [ ] AA en todos los pares texto/fondo, foco visible.
- [ ] Objetivos táctiles ≥44px.
- [ ] Nada de logos, ilustraciones, iconos ni fuentes del original.
- [ ] Un solo sistema de espaciado, sin números mágicos.
- [ ] Estados vacío/error/carga diseñados, no improvisados.

## No hagas

"Recrear pixel a pixel" la pantalla del original: eso es copiar expresión y además produce un clon peor. Reconstruye la estructura y dale tu propia piel.
