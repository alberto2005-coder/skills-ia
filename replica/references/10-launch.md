# 10 · Lanzamiento

Objetivo: landing, precios y listing que conviertan, sin promesas que no puedas sostener.

## Entradas
`replica/fix-plan.md` (ángulo y fixes), `replica/parity.md`, `replica/brand/`, `templates/listing.json`.

## Pasos

1. **Landing.** Hero con el ángulo en una frase, 3 beneficios ligados a los fixes reales, cómo funciona en 3 pasos, prueba (capturas propias), precios, FAQ con las objeciones que salieron de las reseñas, CTA. Sin testimonios inventados: si no tienes usuarios, no pongas logos.
2. **Precios.** Mira el pricing público del original y posiciona: más barato no es estrategia por sí solo. Modelo (plano/por uso/por asiento) alineado con la queja principal. Deja claro qué incluye y qué no.
3. **Listing.** Copia `templates/listing.json` y valida: `python scripts/listing.py replica/launch/listing.json`. Límites, claims de ranking, keywords, nombre del original, capturas.
4. **ASO básico.** Título con la categoría y el beneficio, subtítulo con la diferenciación, keywords sin repetir el título, 5-8 capturas con texto propio.
5. **Capturas y vídeo.** De tu app real, con tus datos. Ninguna captura del original, ni recortada ni recoloreada.
6. **Plan de salida.** Dónde está tu usuario (comunidades, foros, directorios), qué publicas y con qué permiso. Nada de spam masivo.

## Salida
Landing publicada o en repo, `replica/launch/listing.json` con 0 errores, `replica/launch/plan.md` (canales, mensaje, fechas).

## Checklist
- [ ] `listing.py` en 0 errores.
- [ ] Cada beneficio tiene detrás una feature que existe y pasa parity.
- [ ] Precios coherentes con lo que aplica el backend.
- [ ] Cero testimonios, métricas o logos no verificables.
- [ ] Capturas propias y legibles en móvil.
