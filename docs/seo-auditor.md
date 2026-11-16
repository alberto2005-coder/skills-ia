# Documentación: SEO Auditor

## Descripción
Sistema de diagnóstico SEO integral capaz de auditar webs públicas por HTTP, repositorios de código local, instancias en desarrollo y combinaciones híbridas.

## Módulos de referencia
- `00-metodologia.md`: Principios, umbrales de severidad (Critical/High/Med/Low) y límites de seguridad SSRF.
- `01-tecnico.md`: Indexabilidad, códigos HTTP, redirecciones, canonicals y directivas robots.
- `02-contenido.md`: Metadatos, jerarquía H1-H6, intención de búsqueda y accesibilidad.
- `03-geo-ai.md`: Optimización para motores de respuesta generativa y citabilidad estructurada.
- `04-schema.md`: Validación de datos estructurados JSON-LD y Schema.org.
- `05-sitemap.md`: Diagnóstico de sitemaps XML e indexabilidad.
- `06-estrategia.md`: Resolución de canibalización, clusters temáticos y plan a 30/60/90 días.
- `07-pagina-individual.md`: Análisis quirúrgico sobre una URL o archivo único.

## Motor de auditoría (`scripts/`)
- `audit.py`: Punto de entrada directo para todas las comprobaciones.

## Modos de ejecución
```bash
# Modo Web
python seo-auditor/scripts/audit.py https://example.com --mode web

# Modo Código Fuente (Source)
python seo-auditor/scripts/audit.py ./mi-proyecto --mode source

# Modo Servidor Local
python seo-auditor/scripts/audit.py http://localhost:3000 --mode local

# Modo Híbrido
python seo-auditor/scripts/audit.py ./mi-proyecto --mode hybrid --base-url http://localhost:3000
```
