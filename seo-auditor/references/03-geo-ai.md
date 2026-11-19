# GEO (Generative Engine Optimization) y Búsqueda con IA

Analiza la preparación del contenido para motores generativos (Google AI Overviews, Perplexity, ChatGPT Search, Gemini, Copilot) sin prometer visibilidad.

## Principios

1. **Nada de citas inventadas:** no se afirma que un sitio "aparece" o "aparecerá" en respuestas de IA sin una prueba fechada y reproducible. El motor evalúa señales, no posiciones.
2. **GEO es preparación estructural:** facilidad para extraer, comprender, verificar y citar el contenido.
3. **Separar propósitos:** permitir la búsqueda de un motor no obliga a permitir su entrenamiento. Esa distinción es explícita en toda la skill.

## 1. Allow-list de crawlers de IA por motor

| Bot | Motor | Propósito | Documentación |
|---|---|---|---|
| `OAI-SearchBot` | OpenAI (ChatGPT Search) | `search` | https://platform.openai.com/docs/bots |
| `ChatGPT-User` | OpenAI (ChatGPT) | `user-fetch` | https://platform.openai.com/docs/bots |
| `GPTBot` | OpenAI | `training` | https://platform.openai.com/docs/bots |
| `ClaudeBot` | Anthropic | `training` | https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler |
| `Claude-SearchBot` | Anthropic (búsqueda) | `search` | (misma referencia) |
| `Claude-User` | Anthropic (usuario) | `user-fetch` | (misma referencia) |
| `PerplexityBot` | Perplexity | `search` | https://docs.perplexity.ai/guides/bots |
| `Perplexity-User` | Perplexity (usuario) | `user-fetch` | https://docs.perplexity.ai/guides/bots |
| `Google-Extended` | Google (Gemini) | `training` | https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers |
| `Bingbot` | Bing / Copilot | `search` | https://www.bing.com/webmasters/help/which-crawlers-does-bing-use-8c184ec0 |

Reglas:

- Bloquear `search` o `user-fetch` reduce la probabilidad de ser citado; es una decisión de negocio, no un error técnico por sí misma.
- Bloquear solo `training` (`GPTBot`, `ClaudeBot`, `Google-Extended`) es una postura legítima y no penaliza en el motor.

Bloque recomendado (el motor lo genera en `output/robots.txt.draft`):

```text
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: GPTBot
Disallow: /
```

La comprobación `GEO-CRAWLERS-001` solo falla si hay un bot de **búsqueda** o **petición de usuario** bloqueado.

## 2. `llms.txt` y `llms-full.txt`

Estándar propuesto en https://llmstxt.org/. No es un requisito de Google; se evalúa como señal opcional (`GEO-LLMS-001`, `should`; `GEO-LLMSFULL-001`, `nice`).

Estructura (plantilla generable con `fix`):

```markdown
# Nombre del sitio

> Resumen en una frase de qué ofrece el sitio.

## Páginas

- [Guía de auditoría](https://example.com/guia)
- [Contacto](https://example.com/contacto)

## Notas

- Fuente de los datos y fecha de actualización.
```

Reglas:

- Solo enlaces reales (sitemap o páginas rastreadas). Nunca se inventan secciones.
- `llms-full.txt` añade el contenido textual completo; útil para extracción, no obligatorio.
- Si el sitio no publica `llms.txt` no es un fallo `must`: es una mejora.

## 3. E-E-A-T verificable

| Señal | Dónde se busca | Check |
|---|---|---|
| Autor | `author`/`creator` en JSON-LD, biografía visible | `GEO-EAT-001` |
| Fechas | `datePublished`/`dateModified` o fecha visible | `GEO-EAT-001` |
| Identidad | `sameAs` hacia perfiles oficiales/Wikidata | `GEO-EAT-001` |

El check pasa con al menos dos de las tres señales. No se valora "autoridad" como concepto abstracto: solo presencia y verificabilidad.

## 4. Bloque-respuesta de 134–167 palabras

Un párrafo inicial que responde la pregunta principal de forma autónoma, con datos y sin rodeos, facilita la extracción y la cita.

- Se mide el primer párrafo (`<p>`) y hasta los 5 primeros.
- Rango objetivo: **134–167 palabras**.
- Es una heurística interna: `GEO-ANSWER-001` se marca `estimate` y es `nice` (no bloquea).

Ejemplo de estructura: definición → por qué importa → cómo se comprueba → límite o matiz.

## 5. Extracción y citabilidad

- Contenido crítico en el HTML inicial (no tras acordeones JS).
- Tablas comparativas y listas ordenadas extraíbles.
- Afirmaciones con fuente primaria enlazada.
- Coherencia entre título, encabezados, JSON-LD y texto visible.

## Comprobaciones y cita oficial

| ID | Severidad | Comprobación | Documentación |
|---|---|---|---|
| `GEO-LLMS-001` | should | `/llms.txt` publicado | https://llmstxt.org/ |
| `GEO-LLMSFULL-001` | nice | `/llms-full.txt` publicado | https://llmstxt.org/ |
| `GEO-CRAWLERS-001` | should | Allow-list por propósito sin bloquear búsqueda | https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers |
| `GEO-EAT-001` | should | Autor, fechas y `sameAs` | https://static.googleusercontent.com/media/guidelines.raterhub.com/en/searchqualityevaluatorguidelines.pdf |
| `GEO-ANSWER-001` | nice | Bloque-respuesta 134–167 palabras (`estimate`) | https://developers.google.com/search/docs/fundamentals/creating-helpful-content |

## Lo que esta skill NO hace

- No consulta APIs de IA ni simula respuestas de ChatGPT/Perplexity.
- No estima "cuota de voz" ni posiciones en AI Overviews.
- No afirma indexación en motores de IA.
