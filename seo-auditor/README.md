# SEO Auditor

Skill universal de auditoría, optimización técnica y estrategia SEO para cualquier asistente de IA (Claude, ChatGPT, Gemini, Antigravity, Cursor, Copilot, etc.): **web pública, proyecto local, servidor en desarrollo y modo híbrido**.

## Qué incluye

- **`SKILL.md`:** Orquestación central de auditoría y reglas duras universales.
- **8 guías modulares en `references/`:** Diagnóstico técnico, contenido, GEO (AI Search), Schema.org, sitemaps, estrategia y páginas individuales.
- **Motor Python en `scripts/`:** Comprobaciones deterministas sin dependencias externas obligatorias (stdlib de Python).
- **Plantillas en `templates/`:** Plantillas estandarizadas para informes y planes de acción priorizados.
- **Resultados en `reports/`:** Exportación en Markdown y JSON con evidencias, severidad y niveles de confianza.
- **Seguridad nativa:** Modo solo lectura, protección SSRF, límites de rastreo y exclusión de archivos sensibles.

## Requisitos

- Python 3.8+ (solo librería estándar, no requiere `pip install`).
- Compatible con cualquier agente o asistente de Inteligencia Artificial.

## Uso del motor de auditoría

Desde la carpeta `seo-auditor`:

```bash
# Auditar una web pública
python scripts/audit.py https://example.com --mode web --max-pages 30

# Auditar código fuente local (HTML, plantillas, JSX, TSX, etc.)
python scripts/audit.py . --mode source

# Auditar servidor local en ejecución (localhost)
python scripts/audit.py http://localhost:3000 --mode local --max-pages 20

# Auditoría híbrida (código local + servidor local)
python scripts/audit.py . --mode hybrid --base-url http://localhost:3000
```

Los informes se guardan automáticamente en `reports/<proyecto>/<timestamp>/` (`audit.md` y `audit.json`).

## Estructura estandarizada

```text
seo-auditor/
├── SKILL.md            # Definición e instrucciones de la skill
├── references/         # Guías metodológicas y módulos de referencia
│   ├── 00-metodologia.md
│   ├── 01-tecnico.md
│   ├── 02-contenido.md
│   ├── 03-geo-ai.md
│   ├── 04-schema.md
│   ├── 05-sitemap.md
│   ├── 06-estrategia.md
│   └── 07-pagina-individual.md
├── scripts/            # Motor determinista en Python
│   ├── audit.py        # CLI principal ejecutable directamente
│   ├── cli.py
│   ├── models.py
│   ├── report.py
│   ├── schema_audit.py
│   ├── security.py
│   ├── sitemap.py
│   ├── source_audit.py
│   └── web_audit.py
├── templates/          # Plantillas de informes y planes de acción
│   ├── action-plan.md
│   └── audit-report.md
├── reports/            # Informes generados
├── tests/              # Pruebas unitarias
└── config/             # Configuración por defecto
```

## Modos de operación

- `web`: rastrea una web pública mediante HTTP seguro con límites controlados.
- `source`: inspecciona archivos del proyecto sin arrancar la aplicación ni requerir servidor.
- `local`: rastrea una instancia local ya iniciada (`localhost`, `127.0.0.1` o `::1`).
- `hybrid`: combina análisis estático del código fuente con rastreo dinámico de una URL local indicada mediante `--base-url`.

## Licencia

MIT
