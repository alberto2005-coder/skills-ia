---
name: seo-compare
description: Compara dos auditorías SEO y clasifica cada comprobación en mejorado, empeorado, nuevo o resuelto, con delta de puntuación y aviso de nuevos fallos must. Úsala para medir el efecto de un deploy, monitorizar una web en el tiempo o demostrar que un cambio mejoró de verdad. English: diff two audits and classify improved, worse, new and resolved checks.
---

# SEO Auditor · Compare y monitorización

¿Mejoró? Con evidencia, no con impresión.

Assets compartidos: `../references/`, `../scripts/`.

**Todos los comandos se ejecutan desde la raíz del repositorio** (`skills-ia-main/`) con el prefijo `py seo-auditor/scripts/cli.py`.

## Cuándo se usa

- Después de aplicar un plan (`seo-execute`), para medir el efecto real.
- Monitorización periódica: dos `audit.json` de fechas distintas.
- Cuando el usuario pregunta «¿esto ha servido de algo?».

## Precondiciones

- Dos auditorías comparables: mismo modo y mismo alcance. Comparar `web` con `source` no mide nada.
- Si solo hay un `audit.json`, pide el re-score a `seo-audit` antes de comparar.

## Método

1. Ejecuta:

```bash
py seo-auditor/scripts/cli.py compare audit-antes.json audit-despues.json --output output/compare
```

2. Lee el resultado: cada comprobación queda en **mejorado / empeorado / nuevo / resuelto**, con delta de puntuación por dimensión y aviso de nuevos fallos `must`.
3. Distingue lo que cambió por el trabajo de lo que cambió por el entorno (contenido nuevo, páginas distintas, crawl distinto). Si los alcances no coinciden, dilo antes de dar un delta.
4. Un `must` nuevo degrada el veredicto aunque la media suba: no se compensa con aprobados.
5. Documenta el resultado con la fecha, los dos ficheros comparados y la conclusión en una línea.

## Reglas duras

- No se compara lo incomparable: modos, topes de páginas y URLs deben coincidir.
- El delta no se presenta como «mejora SEO» si el cambio fue de contenido o de alcance.

## Gate de salida

- `compare.md` generado con las cuatro categorías y el delta.
- Ningún `must` nuevo sin explicar.
- Alcances declarados y comparables.
- Conclusión en una línea con evidencia.

## Handoff

Si hay regresiones, vuelve a `seo-plan` con el `audit.json` nuevo. Si todo mejora, guarda el par de auditorías como línea base del próximo ciclo.
