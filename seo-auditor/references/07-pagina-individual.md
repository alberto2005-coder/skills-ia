# Auditoría de Página Individual

Guía paso a paso para auditar a fondo una URL pública específica o un archivo HTML/plantilla local.

## Procedimiento de Análisis

1. **Objetivo de la página:** Identificar la función principal (landing de conversión, post de blog, ficha de producto, página de precios, contacto).
2. **Inspección técnica on-page:**
   - Código de estado HTTP y tiempo de respuesta inicial.
   - Presencia y validez de la etiqueta `<link rel="canonical">`.
   - Directivas en `<meta name="robots">`.
3. **Optimización de metadatos y encabezados:**
   - `<title>`: Relevancia, longitud y adecuación a la intención de búsqueda.
   - `<meta name="description">`: Mensaje de valor y llamada a la acción.
   - `<h1>`: Unicidad y coherencia con el título.
   - Subencabezados (`<h2>`, `<h3>`): Estructura semántica clara.
4. **Calidad de contenido:**
   - ¿Resuelve directamente la duda o necesidad del usuario?
   - ¿Hay párrafos de respuesta directa o definiciones útiles para citabilidad de IA (GEO)?
   - ¿El contenido principal está disponible sin requerir interacción compleja por JavaScript?
5. **Enlaces e imágenes:**
   - Enlaces internos y externos con textos ancla contextuales.
   - Imágenes con atributos `alt` informativos.
6. **Datos estructurados (Schema.org):**
   - Bloques JSON-LD presentes y coherencia con la información visible en la página.

## Estructura del Informe de Página
1. **Ficha técnica:** URL/archivo, tipo de página, código HTTP.
2. **Diagnóstico y hallazgos:** Puntos críticos, advertencias y oportunidades ordenadas por impacto.
3. **Evidencias literales:** Fragmentos de código o texto evaluados.
4. **Plan de optimización recomendado:** Acciones paso a paso listas para aplicar.
