---
name: seo-serp
description: Simula cómo se verá una página en Google escritorio y móvil, Bing, y en las tarjetas sociales de WhatsApp, Facebook, LinkedIn y X, con medidor de ancho de título/descripción y aviso de truncamiento. Úsala cuando el usuario quiera previsualizar un título, meta descripción o tarjeta OG, o iterar copy antes de publicarlo. English: preview the title and description in Google desktop and mobile, Bing and the social cards.
---

# SEO Auditor · SERP y tarjetas

Ver antes de publicar. Genera un `preview.html` autocontenido con las vistas que verá el usuario final.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`.

**Todos los comandos se ejecutan desde la raíz del repositorio** (`skills-ia-main/`) con el prefijo `py seo-auditor/scripts/cli.py`.

## Cuándo se usa

- «¿Cómo se ve este título en Google?», «¿me lo corta?».
- Revisar Open Graph / Twitter Card antes de compartir.
- Iterar copy con dos variantes sin tocar la web.

## Método

1. Genera la vista:

```bash
py seo-auditor/scripts/cli.py serp pagina.html
py seo-auditor/scripts/cli.py serp pagina.html --title "Título alternativo" --description "Descripción alternativa"
```

2. Abre `output/serp/preview.html`: Google escritorio y móvil, Bing, y tarjetas de WhatsApp, Facebook, LinkedIn y X.
3. Lee el medidor de ancho: título ~580 px en escritorio, descripción truncada por caracteres según plataforma. El ancho en píxeles es **`estimate`** (métrica de fuente aproximada), no una medición del navegador.
4. Corrige en este orden: título (intención + marca), descripción (beneficio concreto, sin relleno), OG (`og:title`, `og:description`, `og:image` con proporción correcta).
5. Si falta `og:image` o no tiene las dimensiones recomendadas, es un hallazgo, no un detalle estético.

## Reglas duras

- El truncamiento es estimado: se indica como tal y no se presenta como captura real de Google.
- No se prometen posiciones ni rich results desde esta vista.
- Nada de títulos con claims sin respaldo (aplica la regla de evidencia del paquete).
- No se modifica la página: solo se previsualiza con `--title`/`--description`.

## Gate de salida

- `preview.html` generado con todas las vistas.
- Título y descripción sin truncamiento en la vista principal, o truncamiento asumido y explicado.
- `og:*` y Twitter Card completos, con imagen válida.
- Variantes comparadas cuando el usuario pedía elegir.

## Handoff

El copy aprobado se aplica en la web con `seo-execute` (snippets manuales) y se verifica con una nueva auditoría.
