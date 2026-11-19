# Sitemaps XML y Descubrimiento de URLs

Audita configuración y coherencia de los sitemaps para un descubrimiento eficiente.

## Principios y Buenas Prácticas

1. **Declaración en `robots.txt`:** `Sitemap: https://dominio.com/sitemap.xml` (o el índice correspondiente).
2. **URLs absolutas y canónicas:** protocolo exacto y versión canónica que responde 200.
3. **Exclusión de URLs no indexables:** sin 3xx, 4xx, 5xx, `noindex` ni canonicalizadas hacia otra página.
4. **Sitemap Index vs Urlset:** a partir de 50.000 URLs o 50 MB sin comprimir, dividir con `sitemap_index.xml`.
5. **`lastmod` honesto:** solo cuando el contenido cambió de forma sustancial.

> La inclusión en el sitemap facilita el descubrimiento; no garantiza indexación ni ranking.

## Comprobaciones y cita oficial

| ID | Severidad | Comprobación | Documentación |
|---|---|---|---|
| `IDX-SITEMAP-001` | should | Sitemap declarado en robots.txt o detectado en `/sitemap.xml` | https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview |
| `IDX-ROBOTS-002` | should | robots.txt accesible y sin bloqueo global | https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt |

## Cómo lo mide el motor

- `sitemap.py` parsea `urlset`/`sitemapindex` (XML local o remoto) y cuenta `<loc>`.
- En modo `web`, si `robots.txt` no declara sitemap se prueba `/sitemap.xml` (una única petición).
- En modo `source`, se detecta `sitemap.xml`, `sitemap_index.xml` y `sitemap-index.xml` en la raíz del proyecto.
- El informe declara cuántas URLs se listaron y si el sitemap se pudo verificar (`data.sitemap`).
