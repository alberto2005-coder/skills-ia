# 08 · Voz del usuario

Objetivo: convertir quejas reales en un plan de producto y un ángulo, sin inventar ni una cita.

## Entradas

Reseñas públicas: App Store/Play, G2, Capterra, Trustpilot, Reddit, foros del sector, hilos públicos. `templates/reviews.csv`, `templates/themes.json`.

## Pasos

1. **Recolecta a mano o con export público.** Una fila por reseña: `source,url,rating,text,date`. La URL es obligatoria; sin enlace, la fila no vale.
2. **Temas.** Copia `templates/themes.json` y define temas con palabras clave (tolera plurales y sufijos). Añade los que aparezcan en los datos, no los que te gustaría oír.
3. **Analiza.** `python scripts/reviews.py replica/reviews.csv --themes replica/themes.json --out replica/themes.md`. El script descarta filas sin URL y marca `THIN` todo tema con <3 reseñas o una sola fuente.
4. **Prioriza.** Solo temas sólidos entran al plan: frecuencia × dolor (rating bajo) × coste de arreglarlo. Un tema `THIN` se investiga, no se usa como argumento comercial.
5. **Plan de fixes.** Cada fix: qué cambia en el producto, en qué pantalla, y cómo se mide que funcionó.
6. **Ángulo.** Una frase de posicionamiento construida sobre los temas sólidos: "X para quien odia Y". Si no hay temas sólidos, el ángulo no está listo.

## Salida

`replica/reviews.csv`, `replica/themes.md`, `replica/fix-plan.md` (tabla: tema | evidencia (n, fuentes) | fix | métrica) y el ángulo en una línea.

## Checklist

- [ ] 100% de las citas con URL y literales.
- [ ] Sample size declarado en cada afirmación.
- [ ] Temas `THIN` marcados como tales, no promocionados.
- [ ] Cada fix tiene una pantalla y una métrica.

## No hagas

Escribir reseñas de ejemplo como si fueran reales, redondear "unas cuantas quejas" a "la mayoría", ni atribuir a usuarios lo que dice un blog.
