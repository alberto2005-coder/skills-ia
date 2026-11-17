# Defectos observados y cómo se detectan

Casos medidos en una revisión real de una web construida con este sistema. No son hipótesis: cada uno trae la medida antes y después, la causa y la comprobación que lo caza.

## 1. Titular en la columna estrecha de una rejilla

- **Síntoma:** en escritorio el `h1` se parte en cinco líneas y empuja el hero 416 px.
- **Medida:** 1440 px → `402×416`, 5 líneas. Después → `640×250`, 3 líneas.
- **Causa:** auto-placement de la rejilla. El `eyebrow` ocupaba la columna ancha y el titular caía en la de 402 px con cuerpo de 80 px.
- **Arreglo:** áreas explícitas (`grid-template-areas: "eyebrow eyebrow" / "title title" / "lead meta"`) en lugar de confiar en el orden del documento.
- **Lo detecta:** gate de tres líneas del titular y el snippet de `qa-metrics.md`.

## 2. Punto de ruptura que llega antes de tiempo

- **Síntoma:** tres pasos en fila a 768 px, cada uno de 214 px: texto apretado y líneas de dos palabras.
- **Medida:** 768 px → columnas de `213.9px`; después → una columna de 690 px; a 1024 px → tres de 292 px.
- **Causa:** el `@media (min-width: 48rem)` metía tres columnas donde aún no caben.
- **Arreglo:** mover el cambio de columnas a `64rem` y apilar por debajo.
- **Lo detecta:** gate de ancho útil por componente (ninguna columna de texto por debajo de ~250 px).

## 3. Objetivos táctiles pequeños

- **Síntoma:** botones cómodos con ratón e incómodos con dedo.
- **Medida:** «Añadir» `139×39`, filtro `64×34`, «Cesta» `92×38`; después los tres a 44 px de alto. Dentro de la cesta, los botones de cantidad estaban en 28 px y el de cerrar en 36; ahora 44.
- **Causa:** relleno vertical como única fuente de altura.
- **Arreglo:** `min-height: 2.75rem` en controles, sin depender del contenido.
- **Lo detecta:** gate de 44 px en `premium-qa` y `CSS-004` en la puerta estática.

## 4. Ancla que aterriza debajo de la cabecera fija

- **Síntoma:** al pulsar «Catálogo» el título queda tapado por la cabecera.
- **Medida:** objetivo a 65 px con la cabecera terminando en 74; después a 148 px.
- **Causa:** cabecera `position: sticky` sin compensación de desplazamiento.
- **Arreglo:** `html { scroll-padding-top: 6rem }` (alto de cabecera más aire).
- **Lo detecta:** `CSS-003` en la puerta estática y la comprobación de anclas de `qa-metrics.md`.

## 5. Estilos viejos servidos desde caché

- **Síntoma:** se edita el CSS y las medidas no cambian; parece que el arreglo no funciona.
- **Medida:** dos mediciones idénticas tras un cambio real de la hoja.
- **Causa:** el navegador reutiliza `styles.css` sin revalidar.
- **Arreglo:** versión en la URL (`styles.css?v=3`) y recarga antes de volver a medir.
- **Lo detecta:** `HTML-015` en la puerta estática.

## 6. Metadatos incompletos para publicar

- **Síntoma:** el sitio se ve bien y pierde presentación social e indexación.
- **Medida:** auditoría externa con 8 avisos: sin `robots.txt` con `Sitemap:`, sin `sitemap.xml`, sin `llms.txt`, sin señales de autoría, sin cabeceras de seguridad; y en la puerta propia, sin `canonical`, sin `og:image` y sin `twitter:card`.
- **Causa:** el mínimo SEO se daba por supuesto y nadie lo verificaba.
- **Arreglo:** lista cerrada en `performance-seo.md` y comprobaciones `HTML-007/008/009` y `FILE-001..004`.
- **Lo detecta:** la puerta estática antes de publicar y `seo-auditor` después.

## Cómo usar este catálogo

Antes de medir, recórrelo: si el sitio repite uno de estos patrones, compruébalo primero y evita reabrir el mismo diagnóstico. Si aparece un defecto nuevo, añádelo aquí con su medida, su causa y la comprobación que lo detecta; un defecto sin medida no entra.
