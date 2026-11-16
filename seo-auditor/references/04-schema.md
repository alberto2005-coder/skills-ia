# Datos Estructurados y Schema.org

Audita la implementación de datos estructurados para potenciar la comprensión semántica y la elegibilidad para fragmentos enriquecidos (Rich Results).

## Reglas de Auditoría
- **Formato prioritario:** JSON-LD (`<script type="application/ld+json">`). Es el formato recomendado por Google y el más limpio de mantener.
- **Validación sintáctica:** Comprobar que el JSON sea válido y no contenga comas colgantes, comillas mal escapadas ni tipos de datos erróneos.
- **Correspondencia visual obligatoria:** Todo dato presente en Schema DEBE ser visible en la página para un usuario humano. Inventar opiniones, calificaciones ficticias o precios no mostrados infringe las directrices de los motores de búsqueda.
- **No garantizar resultados enriquecidos:** La presencia de Schema válido es un prerrequisito, no una garantía de que el buscador muestre un Rich Snippet.

## Tipos Principales y Requisitos

| Tipo Schema | Uso Típico | Propiedades Esenciales |
|---|---|---|
| `Organization` / `LocalBusiness` | Home, contacto, pie de página | `name`, `url`, `logo`, `contactPoint`, `address` (si aplica), `sameAs` |
| `Article` / `BlogPosting` | Artículos de blog, noticias | `headline`, `image`, `datePublished`, `dateModified`, `author` (tipo `Person`), `publisher` |
| `Product` | Fichas de producto e-commerce | `name`, `image`, `description`, `offers` (tipo `Offer` con `price`, `priceCurrency`, `availability`) |
| `FAQPage` | Preguntas frecuentes | `mainEntity` (lista de `Question` con `name` y `acceptedAnswer` tipo `Answer`) |
| `BreadcrumbList` | Migas de pan de navegación | `itemListElement` (elementos `ListItem` con `position`, `name` e `item` URL) |
| `SoftwareApplication` / `WebApplication` | Apps y SaaS | `name`, `operatingSystem`, `applicationCategory`, `offers` |

## Errores Frecuentes
- Propiedades requeridas ausentes según el validador oficial de Schema.org / Google.
- Esquemas duplicados o conflictivos dentro de la misma página (ej. dos bloques `Product` con datos distintos).
- URLs relativas dentro del JSON-LD en lugar de URLs absolutas canónicas.
