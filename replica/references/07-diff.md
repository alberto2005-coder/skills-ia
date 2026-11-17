# 07 · Paridad

Objetivo: un número defendible de cuánto se parece tu clon al original en funciones, y dónde no.

## Entradas
`replica/features.csv`, capturas del original (`replica/screens/`) y de tu clon, `replica/flows`.

## Pasos

> **Formato de evidencia obligatorio.** Cada hallazgo de paridad (un `partial`, un must pendiente, una región de `imgdiff` por debajo del umbral, un gap) se registra con `templates/evidence.md`: **Fuente · Observación · Inferencia · Confianza (high/medium/low/THIN) · Límites y desconocidos**. La fuente puede ser el propio manifiesto (`features.csv` con su fila), una captura (`replica/screens/…`) o la salida del script; sin ella, el hallazgo no entra en `parity.md`.

1. **Paridad funcional.** `python scripts/parity.py replica/features.csv --markdown --out replica/parity.md`. Must pendientes = no desplegable, sin discusión. Un `partial` cuenta medio: o se termina o se queda como gap visible.
2. **Paridad de layout.** Por pantalla: `python scripts/imgdiff.py original.png clon.png --out replica/diff/<pantalla>.png`. Ignora color a propósito: un rediseño propio no debe penalizar. Umbral orientativo 85; por debajo, mira las regiones y decide si es diferencia deliberada o pantalla sin terminar. Cada pantalla evaluada deja su fila de evidencia (resultado del script = observación; "diferencia deliberada" = inferencia con su límite).
3. **Paridad de flujo.** Checklist manual por flujo: mismos pasos, mismo resultado, mismos casos límite cubiertos. Anota dónde tu versión hace algo distinto **a propósito**.
4. **Gaps conscientes.** Tabla: gap | motivo (fuera de alcance, decisión de producto, coste) | impacto para el usuario. Los gaps no se esconden; cada uno lleva su fila de evidencia con confianza y límites.
5. **Veredicto.** Una frase: qué tan cerca está, para quién sirve ya y qué falta para el usuario que viene del original.

## Salida
`replica/parity.md` con score, tabla por área, gaps, veredicto, **tabla de hallazgos con el formato de `templates/evidence.md`** y el cierre `Mapa · Límites · Desconocidos` (qué cubre la medición, hasta dónde llega, qué no se pudo comparar); `replica/diff/*.png`.

## Checklist
- [ ] Score generado por el script, no a ojo.
- [ ] Cada must pendiente tiene plan o se declara fuera de alcance con motivo.
- [ ] Cada pantalla clave tiene diff visual revisado, no solo el número.
- [ ] Cada hallazgo de paridad tiene fuente, observación e inferencia separadas, con confianza y límites (formato `templates/evidence.md`).
- [ ] Ningún `THIN` (una sola pantalla, una sola fuente) se convierte en veredicto general.
- [ ] Los gaps deliberados están escritos antes del lanzamiento.

## No hagas
Inflar el score marcando `done` lo que está a medias, ni llamar "mejora" a una pantalla que falta, ni presentar una inferencia ("seguro que es a propósito") como si fuera observación del diff.
