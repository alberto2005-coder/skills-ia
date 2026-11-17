# Reels y Redes: {{app_nombre_propio}} (plantilla)

> Plantilla de la fase 13 (`references/13-redes.md`). 3 guiones de Reels + captions + ganchos
> para Instagram/TikTok, sin mencionar la marca original (ni su nombre, ni su dominio, ni sus
> colores de marca: `sweep.py` tiene que seguir a 0 sobre todo el copy antes de publicar).
>
> Cada guion dura 20-30 s: **hook (0-3 s) → desarrollo (3-20 s) → cierre/CTA (20-30 s)**.
> Todo claim (cifra, precio, "más rápido") necesita respaldo en la evidencia de fase 1/7/8;
> sin respaldo, el claim no va al guion (nada de métricas inventadas, nada de `THIN`).

## Guion 1 · {{ángulo: el problema que resuelve}}

- **Plataforma:** Instagram Reels + TikTok (mismo vídeo, caption adaptado)
- **Hook (0-3 s):** {{frase que para el scroll; problema concreto o pregunta directa}}
- **Desarrollo (3-20 s):**
  1. {{paso 1: muestra real de TU app, capturada por ti}}
  2. {{paso 2}}
  3. {{paso 3: el resultado en pantalla}}
- **Cierre/CTA (20-30 s):** {{qué hago yo si me interesa + dónde (link en bio / App Store)}}
- **Texto en pantalla:** {{3-4 rótulos cortos, máximo 6 palabras cada uno}}
- **Caption:** {{primera línea gancha (≤125 caracteres) → 2-3 líneas de contexto → CTA → 3-5 hashtags propios}}
- **Hashtags:** `#{{hashtag_propio_1}} #{{hashtag_propio_2}} #{{categoría_sin_marca}}`
- **Evidencia del claim:** {{qué hallazgo de `templates/evidence.md` lo respalda — fuente + confianza. Si es `THIN`: se quita el claim}}
- **Sweep:** `python scripts/sweep.py <caption.txt> --avoid "{{original}}" --avoid {{dominio_original}}` → 0

## Guion 2 · {{ángulo: demo rápida / antes-después}}

- **Plataforma:** Instagram Reels + TikTok
- **Hook (0-3 s):** {{"mira lo que hace en 10 segundos" / resultado antes-después con TU app}}
- **Desarrollo (3-20 s):**
  1. {{pantalla de tu app con tus datos}}
  2. {{acción principal en tiempo real, sin cortes que oculten nada}}
  3. {{resultado verificable en pantalla}}
- **Cierre/CTA (20-30 s):** {{invitación concreta y honesta; sin promesas que no sostengas}}
- **Texto en pantalla:** {{rótulos}}
- **Caption:** {{gancha → contexto → CTA → hashtags}}
- **Hashtags:** `#{{…}} #{{…}}`
- **Evidencia del claim:** {{…}}
- **Sweep:** → 0

## Guion 3 · {{ángulo: objeción real de las reseñas (fase 8)}}

- **Plataforma:** Instagram Reels + TikTok
- **Hook (0-3 s):** {{la queja típica de la categoría, dicha en voz alta sin nombrar a nadie}}
- **Desarrollo (3-20 s):**
  1. {{cómo lo resuelve tu versión (fix real de `fix-plan.md`)}}
  2. {{prueba en pantalla}}
  3. {{límite honesto si existe ("esto aún no lo hace")}}
- **Cierre/CTA (20-30 s):** {{…}}
- **Texto en pantalla:** {{rótulos}}
- **Caption:** {{gancha → contexto → CTA → hashtags}}
- **Hashtags:** `#{{…}} #{{…}}`
- **Evidencia del claim:** {{…}}
- **Sweep:** → 0

## Banco de ganchos (elige 1 por guion, reescrito en tu voz)

| Tipo | Ejemplo de estructura |
|---|---|
| Problema | "Sigues {{manera incómoda de hacer X}}… míralo esto" |
| Resultado | "Esto es lo que ves en 10 segundos de {{tarea}}:" |
| Pregunta | "¿Cómo hace {{X}} para {{resultado}} sin {{dolor}}?" |
| Mito | "Te han dicho que {{mito de la categoría}}. No es así:" |
| Comparativa propia | "Antes: {{dolor}} · Ahora: {{tu app}} (misma tarea, mismo dato)" |
| Objetividad | "Lo que **no** hace {{tu app}} (y por qué está bien)" |
| Cifra verificable | "{{cifra con fuente en evidencia}} — lo comprobamos aquí:" |

Prohibidos en hooks y captions: el nombre del original, su dominio, "mejor que X", "#1",
cualquier claim de ranking y cualquier métrica sin fuente.

## Tabla de control (se rellena antes de publicar)

| # | Guion | Plataforma | Claim principal | Evidencia (fase · confianza) | Sweep | Publicado (fecha) |
|---|-------|-----------|-----------------|------------------------------|-------|-------------------|
| 1 | {{…}} | IG + TikTok | {{…}} | {{…}} | 0 | |
| 2 | {{…}} | IG + TikTok | {{…}} | {{…}} | 0 | |
| 3 | {{…}} | IG + TikTok | {{…}} | {{…}} | 0 | |
