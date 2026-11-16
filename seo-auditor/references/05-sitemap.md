# Sitemaps XML y Descubrimiento de URLs

Audita la configuración y coherencia de los sitemaps XML para asegurar un descubrimiento rápido y eficiente por parte de los motores de búsqueda.

## Principios y Buenas Prácticas
1. **Declaración en `robots.txt`:** El archivo `robots.txt` debe declarar la directiva `Sitemap: https://dominio.com/sitemap.xml` (o el sitemap index correspondiente).
2. **URLs absolutas y canónicas:** Todas las URLs listadas en el sitemap deben ser URLs absolutas con protocolo exacto (`https://`), dominio correcto y corresponder a versiones canónicas 200 OK.
3. **Exclusión de URLs no indexables:**
   - Cero URLs con redirección 3xx.
   - Cero URLs con error 4xx o 5xx.
   - Cero URLs con meta robots `noindex` o cabecera `X-Robots-Tag: noindex`.
   - Cero URLs canonicalizadas hacia otra página.
4. **Sitemap Index vs Urlset:**
   - Cuando un sitio supere las 50.000 URLs o 50 MB sin comprimir, debe dividirse mediante un archivo `sitemap_index.xml` que agrupe submódulos (ej. `/sitemap-posts.xml`, `/sitemap-pages.xml`, `/sitemap-products.xml`).
5. **Freshness / `lastmod`:**
   - La etiqueta `<lastmod>` solo debe actualizarse cuando el contenido de la página haya sufrido una modificación sustancial, no de forma artificial en cada compilación.

> **Recordatorio:** La inclusión de una URL en el sitemap facilita su descubrimiento, pero no garantiza su indexación ni su ranking.
