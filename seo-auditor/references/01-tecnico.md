# Diagnóstico Técnico SEO

Audita la infraestructura, rastreabilidad, indexabilidad y arquitectura técnica del sitio.

## Áreas Clave de Inspección

### 1. Rastreabilidad e Indexabilidad
- **Códigos HTTP:** 4xx, 5xx, cadenas y bucles 3xx.
- **Directivas cruzadas (módulo 1 de IndexPulse):** se comparan las cinco fuentes y se marca el conflicto, no solo la ausencia:
  - reglas de `robots.txt` (`Allow`/`Disallow`, coincidencia por prefijo más larga; `Allow` gana en empate),
  - `<meta name="robots">`,
  - cabecera `X-Robots-Tag`,
  - `<link rel="canonical">`,
  - sitemap declarado (`Sitemap:` en robots.txt o `/sitemap.xml`).
  Un `noindex` en meta con `X-Robots-Tag: index` es un **conflicto** (`IDX-CONFLICT-001`), no dos avisos sueltos.

### 2. Canónicas y Duplicidad Técnica
- URL absoluta y autorreferencial en páginas originales.
- No debe apuntar a URLs 4xx ni a redirecciones 3xx.
- Coherencia de protocolo y barra final.

### 3. Internacionalización (hreflang) — módulo 6
Checklist de pares:
1. `<html lang>` con código BCP 47 válido.
2. Cada `hreflang` usa ISO 639-1/639-2 y, si aplica, región ISO 3166-1 alfa-2.
3. **Autorreferencia**: la página se declara a sí misma.
4. **Retorno bidireccional**: cada destino declara de vuelta el origen (solo verificable con ≥ 2 páginas rastreadas).
5. **`x-default`** cuando hay más de un idioma.
6. Idioma y región mal escritos (`español!`, `en-UK` en lugar de `en-GB`).

### 4. Cabeceras HTTP de seguridad — módulo 4
Score 0–100 reproducible (pesos entre paréntesis): `Strict-Transport-Security` (20), `Content-Security-Policy` (25), `X-Frame-Options` o CSP `frame-ancestors` (15), `X-Content-Type-Options: nosniff` (15), `Referrer-Policy` (10), `Permissions-Policy` (15). Mixed content confirmado resta 20.

### 5. Renderizado y Rendimiento Observable
- Contenido esencial en el HTML inicial frente a CSR.
- Recursos que bloquean el render; fuentes y estilos.

### 6. Estructura de Enlaces Internos
- Enlaces rotos, páginas huérfanas en la muestra, profundidad de clics.

## Comprobaciones y cita oficial

| ID | Severidad | Comprobación | Documentación |
|---|---|---|---|
| `IDX-ROBOTS-001` | must | robots.txt no bloquea la URL | https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt |
| `IDX-ROBOTS-002` | should | robots.txt accesible, sin `Disallow: /` global | https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt |
| `IDX-META-001` | must | Sin `noindex` en `<meta robots>` | https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag |
| `IDX-XROBOTS-001` | must | Sin `noindex` en `X-Robots-Tag` | https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag |
| `IDX-CONFLICT-001` | must | Meta y cabecera no se contradicen | https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag |
| `IDX-CANON-001` | should | Canonical autorreferencial | https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls |
| `IDX-SITEMAP-001` | should | Sitemap declarado o detectado | https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview |
| `CRAWL-ROBOTS-001` | should | robots.txt respetado, 1 req/s, tope declarado | https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt |
| `HREF-LANG-001` | must | `<html lang>` presente | https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/lang |
| `HREF-CODE-001` | should | Códigos hreflang válidos | https://developers.google.com/search/docs/specialty/international/localized-versions |
| `HREF-SELF-001` | should | Autorreferencia hreflang | https://developers.google.com/search/docs/specialty/international/localized-versions |
| `HREF-RETURN-001` | should | Retorno bidireccional | https://developers.google.com/search/docs/specialty/international/localized-versions |
| `HREF-XDEFAULT-001` | nice | `x-default` declarado | https://developers.google.com/search/docs/specialty/international/localized-versions |
| `SEC-HSTS-001` | should | HSTS con `max-age` > 0 | https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security |
| `SEC-CSP-001` | should | CSP definida | https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy |
| `SEC-XFO-001` | should | XFO o `frame-ancestors` | https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options |
| `SEC-XCTO-001` | should | `nosniff` | https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options |
| `SEC-RP-001` | nice | Referrer-Policy | https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy |
| `SEC-PP-001` | nice | Permissions-Policy | https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy |
| `SEC-MIXED-001` | must | Sin recursos `http://` en página HTTPS | https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content |

## Salida Esperada
Ubicación, evidencia literal, severidad (`must|should|nice`), cita y recomendación reproducible.
