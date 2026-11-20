---
name: replica-redes
description: >
  Fase 13 de replica — escribe el contenido social del lanzamiento (3 guiones de Reels, captions por red y banco de ganchos) con claims respaldados por evidencia y sin marca original, y lo pasa por sweep. Úsala cuando el usuario pida guiones, captions o contenido para redes de un clon ya lanzado. English: write three Reels scripts, captions and a hook bank for social networks.
license: MIT
metadata:
  package: replica
  version: "2.0.1"
  author: "Alberto Ortiz"
---

# Replica · Redes (fase 13)

Contenido social que se puede grabar hoy y defender mañana. Tres guiones, captions por red y ganchos reutilizables.

Assets compartidos: `../references/`, `../templates/`, `../scripts/`. **Todos los comandos se ejecutan desde la raíz del repositorio**.

## Precondiciones

- Marca (fase 9) y lanzamiento (fase 10) cerrados.
- App publicada o con URL de espera operativa.
- Evidencia disponible en `features.csv`, `parity.md` y `themes.md`.

## Método

1. Lee `../references/13-redes.md` entero y usa `../templates/reels.md`.
2. **3 guiones** de 20-40 s con la misma estructura: gancho (0-3 s), problema concreto, demostración en pantalla, cierre con una sola acción. Cada guion ataca un tema distinto.
3. **Captions por red** (Instagram, TikTok, LinkedIn, X) con la longitud y el tono de cada una; sin hashtags de relleno ni frases de «descubre el futuro».
4. **Banco de ganchos**: 10-15 aperturas probables, cada una apoyada en un tema con evidencia.
5. **Sweep 0 del copy nuevo**:

```bash
py replica/scripts/sweep.py replica/launch/redes.md --avoid "App Original" --avoid apporiginal.com
```

6. Cada claim del guion o caption cita su evidencia. Si no hay muestra suficiente (`THIN`), se cambia el ángulo: no se maquilla la cifra.

## Gate de salida

- 3 guiones completos y grabables, con duración y planos.
- Captions por red, todas con CTA único.
- Banco de ganchos con ≥10 entradas.
- 0 claims sin respaldo y 0 restos de marca original (`sweep.py` en 0).

## Handoff

`replica/launch/redes.md` queda listo para producción. Cualquier cambio posterior de copy reabre esta fase y repite el sweep.
