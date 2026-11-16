# 07 · Paridad

Objetivo: un número defendible de cuánto se parece tu clon al original en funciones, y dónde no.

## Entradas
`replica/features.csv`, capturas del original (`replica/screens/`) y de tu clon, `replica/flows`.

## Pasos

1. **Paridad funcional.** `python scripts/parity.py replica/features.csv --markdown --out replica/parity.md`. Must pendientes = no desplegable, sin discusión. Un `partial` cuenta medio: o se termina o se queda como gap visible.
2. **Paridad de layout.** Por pantalla: `python scripts/imgdiff.py original.png clon.png --out replica/diff/<pantalla>.png`. Ignora color a propósito: un rediseño propio no debe penalizar. Umbral orientativo 85; por debajo, mira las regiones y decide si es diferencia deliberada o pantalla sin terminar.
3. **Paridad de flujo.** Checklist manual por flujo: mismos pasos, mismo resultado, mismos casos límite cubiertos. Anota dónde tu versión hace algo distinto **a propósito**.
4. **Gaps conscientes.** Tabla: gap | motivo (fuera de alcance, decisión de producto, coste) | impacto para el usuario. Los gaps no se esconden.
5. **Veredicto.** Una frase: qué tan cerca está, para quién sirve ya y qué falta para el usuario que viene del original.

## Salida
`replica/parity.md` con score, tabla por área, gaps y veredicto; `replica/diff/*.png`.

## Checklist
- [ ] Score generado por el script, no a ojo.
- [ ] Cada must pendiente tiene plan o se declara fuera de alcance con motivo.
- [ ] Cada pantalla clave tiene diff visual revisado, no solo el número.
- [ ] Los gaps deliberados están escritos antes del lanzamiento.

## No hagas
Inflar el score marcando `done` lo que está a medias, ni llamar "mejora" a una pantalla que falta.
