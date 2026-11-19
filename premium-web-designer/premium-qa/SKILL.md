---
name: premium-qa
description: >
  Independent QA and visual audit for an existing website or web application.
  Use when the user asks to review, audit, test or compare a built site, measure
  overflow at five widths (360, 390, 768, 1024 and 1440 px), count the headline
  lines, check responsive layout, verify tap targets, contrast and sticky header
  anchor offset, inspect accessibility, validate a delivery before publishing or
  explain why a page breaks on one screen size. Produces measured findings with
  numbers, not impressions, and a delivery report with severity per defect.
  También responde a peticiones en español: auditar una web ya construida,
  revisar el diseño en móvil y escritorio, medir desbordamiento, líneas del
  titular y objetivos táctiles en cada ancho, comprobar accesibilidad y cabecera
  fija antes de publicar.
license: MIT
metadata:
  package: premium-web-designer
  version: "3.0.0"
---

# Premium QA — auditoría medible de una web

QA independiente del rol que construyó: mide, no opina. Cada hallazgo lleva número, ancho de pantalla y severidad.

Assets compartidos del paquete: `../references/`, `../scripts/`, `../templates/`, `../agents/`. **Comandos desde la raíz del repositorio**.

## Cuándo se usa

- «Revisa esta web», «audítala antes de publicar», «¿por qué se rompe en móvil?».
- Comparar el resultado con el diseño aprobado.
- Verificar los gates medibles del maestro en un sitio ya construido.

Si el encargo es **crear o rediseñar**, manda el maestro; esta sub-skill solo audita.

Antes de medir, recorre `../references/known-defects.md`: seis defectos ya medidos, con su causa y la comprobación que los caza. Si el sitio repite uno de esos patrones, empieza por ahí.

## Protocolo

### 1. Inventario antes de medir

Enumera páginas, plantillas, estados (vacío, error, carga) y componentes interactivos. Una página no visitada no es una página revisada: declara el alcance y lo que queda fuera.

### 2. Puerta estática

```bash
py premium-web-designer/scripts/delivery_check.py <carpeta-del-sitio>
```

Cubre `lang`, título, descripción, canonical, Open Graph, un solo `h1`, orden de encabezados, `alt`, JSON-LD, `:focus-visible`, `prefers-reduced-motion`, compensación de cabecera pegajosa, versión en CSS/JS locales, `robots.txt`, `sitemap.xml` y `llms.txt`. Sale 1 si falla algún `must`.

**`--public` cuando la carpeta va a publicarse.** Sin esa bandera la puerta asume prototipo local y deja en aviso canonical, Open Graph con imagen, `robots.txt` y `sitemap.xml`. Con ella, esos cuatro son `must` y bloquean la entrega: úsala en el gate de salida de una web real, no en un borrador sin dominio.

`--public` revisa además las cabeceras del hosting: busca `_headers`, `netlify.toml` o `vercel.json` y avisa si no declaran `Content-Security-Policy` o `Strict-Transport-Security` con `max-age`.

### 3. Medición en navegador

Para cada ancho (360, 390, 768, 1024, 1440) ejecuta el snippet de `../references/qa-metrics.md` y anota: desbordamiento, líneas del `h1`, tamaño de los controles, posición de las anclas bajo la cabecera y elementos que se solapan.

### 4. Recorrido funcional

Teclado completo (Tab, Escape, foco devuelto), formularios con error y éxito, estados vacíos, cesta o carrito si existe, enlaces y navegación. En cada overlay comprueba que el foco entra, queda atrapado y vuelve al abridor.

### 5. Accesibilidad y contraste

Contraste de texto y de estados (hover, focus, disabled), nombres accesibles, jerarquía de encabezados, `alt` útil, orden de tabulación y respeto a `prefers-reduced-motion`.

### 6. Informe

Rellena `../templates/qa-report.md` con una fila por hallazgo: qué, dónde, en qué ancho, medida observada, severidad (`bloqueante` · `mayor` · `menor`) y arreglo propuesto. Separa lo medido de lo estimado y lista lo que no se pudo comprobar.

## Gates numéricos

| Comprobación | Umbral |
|---|---|
| Desbordamiento horizontal | 0 px en los cinco anchos |
| Líneas del `h1` | ≤ 3 en cada ancho |
| Ancho útil de un componente | ≥ 250 px por columna de texto; si no, apilar |
| Control primario | ≥ 44×44 px |
| Control secundario | ≥ 24×24 px |
| Ancla bajo cabecera fija | título visible, sin solape |
| Contraste de texto | ≥ 4.5:1 (≥ 3:1 en texto grande) |
| Contraste de estados | ≥ 3:1 frente al fondo |
| Foco en overlays | entra, se atrapa y vuelve |

Un umbral incumplido no se negocia con una impresión: se mide otra vez y, si no se puede medir, se declara como límite.

## Gate de salida

- Puerta estática ejecutada, con su código de salida anotado.
- Los cinco anchos medidos y cada hallazgo con su número.
- Recorrido de teclado y de overlays documentado.
- Informe con severidad, arreglo propuesto y límites declarados.
- Cero afirmaciones del tipo «se ve bien» sin medida detrás.

## Handoff

Devuelve el informe al maestro o a quien construyó. Los `bloqueante` reabren la fase de desarrollo antes de cualquier entrega; los `menor` se agrupan en una iteración posterior. Si el encargo era solo SEO, entrega a `seo-auditor`.
