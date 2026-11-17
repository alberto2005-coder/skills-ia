# Auditoría de Contenido y On-Page

Evalúa calidad, intención, metadatos, estructura semántica y valor para el usuario.

## Criterios de Evaluación

### 1. Metadatos Principales
- **`<title>`:** claro, relevante y único. Referencia orientativa 45–65 caracteres; el límite real es de píxeles (~580 px en escritorio), por eso el motor calcula ambos y etiqueta el ancho como `estimate`.
- **`<meta name="description">`:** resumen con valor diferencial, única por página. Orientativo 120–160 caracteres; el motor avisa del truncamiento.

### 2. Jerarquía de Encabezados (H1–H4) — módulo 7
- Exactamente **un** `<h1>` (ausente o duplicado = `ONP-H1-001`).
- Sin saltos arbitrarios (`h1 → h3` sin `h2`).
- Encabezados por semántica, no por tamaño visual.

### 3. On-Page medible
| Métrica | Cómo se obtiene | Etiqueta |
|---|---|---|
| Ratio texto/HTML | caracteres de texto visible / caracteres de HTML | `estimate` (umbral orientativo 15 %) |
| Recuento de palabras | tokenización del texto visible | medido |
| Imágenes sin `alt` | lista de rutas (sin render) | medido |
| Jerarquía H1–H4 | recuento y saltos | medido |
| Densidad de términos | frecuencia sobre términos no vacíos | **informativa** |

> **Aviso:** la densidad de palabras clave **no** es una métrica de calidad ni un objetivo SEO. Se muestra como tabla informativa (`ONP-KW-001`) para detectar desequilibrios evidentes, nunca como meta a alcanzar.

### 4. Intención de Búsqueda y Utilidad
Adecuación informativa / transaccional / comercial / navegacional; profundidad suficiente; formato escaneable (párrafos, tablas, listas).

### 5. Duplicidad y Thin Content
Solo se clasifica como duplicado o escaso con evidencia textual comparada entre dos o más páginas. No se penalizan páginas utilitarias legítimas.

### 6. Autoría y E-E-A-T
Autor u organización identificable, fuentes primarias y fechas visibles de publicación y actualización.

### 7. Accesibilidad y Multimedia
`alt` descriptivo en imágenes informativas y `alt=""` en decorativas; texto ancla descriptivo (evitar "clic aquí").

## Comprobaciones y cita oficial

| ID | Severidad | Comprobación | Documentación |
|---|---|---|---|
| `SRC-TITLE-001` | must | Existe `<title>` | https://developers.google.com/search/docs/appearance/title-link |
| `SERP-TITLE-001` | should | Ancho del título dentro de ~580 px (`estimate`) | https://developers.google.com/search/docs/appearance/title-link |
| `SRC-META-001` | should | Existe meta description | https://developers.google.com/search/docs/appearance/snippet |
| `SERP-DESC-001` | should | Descripción ≤ 160 caracteres | https://developers.google.com/search/docs/appearance/snippet |
| `ONP-H1-001` | must | Un único H1 | https://developer.mozilla.org/en-US/docs/Web/HTML/Element/Heading_Elements |
| `ONP-ALT-001` | should | Imágenes con `alt` | https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img |
| `ONP-RATIO-001` | nice | Ratio texto/HTML ≥ 15 % (`estimate`) | https://developers.google.com/search/docs/fundamentals/seo-starter-guide |
| `ONP-KW-001` | nice | Tabla de densidad (informativa) | https://developers.google.com/search/docs/fundamentals/seo-starter-guide |
| `SERP-OG-001` | nice | Open Graph completo | https://ogp.me/ |
| `SERP-TW-001` | nice | Twitter Card declarada | https://developer.x.com/en/docs/twitter-for-websites/cards/overview/abouts-cards |
