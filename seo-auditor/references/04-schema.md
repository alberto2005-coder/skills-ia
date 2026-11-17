# Datos Estructurados y Schema.org

Audita la implementación de datos estructurados para comprensión semántica y elegibilidad a resultados enriquecidos.

## Reglas de Auditoría
- **Formato prioritario:** JSON-LD (`<script type="application/ld+json">`).
- **Validación sintáctica:** JSON válido, sin comas colgantes ni comillas mal escapadas.
- **Correspondencia visual obligatoria:** todo dato del Schema debe ser visible para el usuario. Inventar valoraciones, precios u opiniones infringe las directrices.
- **No garantizar rich results:** el Schema válido es prerrequisito, no garantía.

## Inventario y rich preview (módulo 5)

El motor:
1. lista **todos** los `@type` presentes (incluidos los anidados: `Offer`, `AggregateRating`, `Question`, `Answer`…),
2. marca bloques con JSON inválido,
3. valida propiedades mínimas por tipo,
4. genera `schema/rich-preview.html` con lo que Google *podría* mostrar y lo que **falta** para ello.

La vista previa es ilustrativa: se etiqueta como estimación y no reproduce el render exacto del buscador.

## Tipos y propiedades requeridas

| Tipo | Uso | Propiedades mínimas | Documentación |
|---|---|---|---|
| `Organization` | Home, contacto | `name`, `url` | https://schema.org/Organization |
| `LocalBusiness` | Negocio local | `name`, `address` | https://schema.org/LocalBusiness |
| `Article` / `BlogPosting` | Blog, noticias | `headline`, `image`, `datePublished`, `author` | https://developers.google.com/search/docs/appearance/structured-data/article |
| `Product` | E-commerce | `name`, `image`, `offers` | https://developers.google.com/search/docs/appearance/structured-data/product |
| `Offer` | Precio de producto | `price`, `priceCurrency` (+ `availability`) | https://schema.org/Offer |
| `AggregateRating` | Estrellas | `ratingValue`, `ratingCount` | https://developers.google.com/search/docs/appearance/structured-data/review-snippet |
| `FAQPage` | Preguntas frecuentes | `mainEntity` con `Question.name` y `acceptedAnswer` | https://developers.google.com/search/docs/appearance/structured-data/faqpage |
| `BreadcrumbList` | Migas | `itemListElement` con `position`, `name`, `item` | https://developers.google.com/search/docs/appearance/structured-data/breadcrumb |
| `VideoObject` | Vídeo | `name`, `thumbnailUrl`, `uploadDate` | https://developers.google.com/search/docs/appearance/structured-data/video |
| `Event` | Eventos | `name`, `startDate`, `location` | https://developers.google.com/search/docs/appearance/structured-data/event |

> `Product` sin `availability` es válido en schema.org pero **no** cumple el mínimo de Google para rich result: el motor lo marca en la evidencia.

## Errores Frecuentes
- Propiedades requeridas ausentes según el validador oficial.
- Esquemas duplicados o conflictivos en la misma página (dos `Product` con datos distintos).
- URLs relativas dentro de JSON-LD en vez de absolutas canónicas.
- `AggregateRating` sin reseñas visibles (riesgo de acción manual).

## Comprobaciones y cita oficial

| ID | Severidad | Comprobación | Documentación |
|---|---|---|---|
| `SCHEMA-JSONLD-001` | should | JSON-LD presente y válido | https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data |
| `SCHEMA-PRODUCT-001` | nice | `Product` con `offers` completo | https://developers.google.com/search/docs/appearance/structured-data/product |
| `SCHEMA-RATING-001` | nice | `AggregateRating` completo | https://developers.google.com/search/docs/appearance/structured-data/review-snippet |
| `SCHEMA-FAQ-001` | nice | `FAQPage` con preguntas completas | https://developers.google.com/search/docs/appearance/structured-data/faqpage |

Validador oficial para confirmar antes de publicar: https://search.google.com/test/rich-results
