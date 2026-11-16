# GEO (Generative Engine Optimization) y Búsqueda con IA

Analiza la preparación de los contenidos para sistemas de respuesta y motores de búsqueda generativa (Google AI Overviews, Perplexity, ChatGPT Search, Gemini, Claude).

## Principios de GEO
1. **No inventar citas ni prometer visibilidad garantizada:** No afirmar que un sitio "ya aparece" o "aparecerá" en respuestas generadas por IA sin una prueba fechada y reproducible.
2. **Tratar GEO como preparación y diagnóstico estructural:** Evaluar la facilidad con la que un modelo de lenguaje o scraper de IA puede extraer, comprender, verificar y citar el contenido.

## Dimensiones de Análisis

### 1. Disponibilidad y Accesibilidad Textual
- El contenido crítico debe estar disponible en texto plano accesible en el HTML, sin requerir clics en acordeones cerrados por JS o llamadas de red secundarias.
- Comprobación de políticas en `robots.txt` para bots de IA (ej. `GPTBot`, `PerplexityBot`, `ClaudeBot`, `Google-Extended`). Si están bloqueados, señalarlo como decisión voluntaria u obstáculo de rastreo según los objetivos del proyecto.

### 2. Capacidad de Extracción y Citabilidad
- **Definiciones directas y claras:** Introducciones concisas que responden a preguntas tipo "¿Qué es X?" o "¿Cómo funciona Y?" en los primeros 1–2 párrafos.
- **Datos factuales y fuentes primarias:** Afirmaciones sustentadas en datos concretos, estadísticas con fuente citada y testimonios reales.
- **Formato estructurado:** Tablas comparativas claras (`<table>` o markdown) y listas ordenadas que facilitan la extracción y resumen por LLMs.

### 3. Claridad de Entidades y Autoridad
- Consistencia en el nombre de marcas, productos, conceptos clave y autores en todo el sitio.
- Asociación con entidades reconocidas mediante datos estructurados (`sameAs` en Schema apuntando a Wikidata, perfiles oficiales o fuentes de referencia).
- Biografías de autor verificables y páginas "Sobre nosotros" detalladas.

### 4. Coherencia Semántica
- Consistencia estricta entre el título de la página, los encabezados, el Schema.org (`JSON-LD`) y el texto visible. Las contradicciones confunden a los analizadores semánticos.

## Recomendaciones Accionables
- Añadir resúmenes ejecutivos ("Key Takeaways") al inicio de artículos técnicos extensos.
- Incorporar tablas de especificaciones o respuestas directas a preguntas frecuentes estructuradas con `FAQPage`.
- Citar siempre fuentes originales con enlaces salientes respetados.
