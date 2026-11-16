# Guía rápida de uso

## 1. Auditar código fuente local

```bash
python scripts/audit.py . --mode source
```

## 2. Auditar una aplicación web en desarrollo local

Inicia tu servidor en otra terminal y luego:

```bash
python scripts/audit.py http://localhost:3000 --mode local
```

## 3. Auditoría híbrida (código + ejecución local)

```bash
python scripts/audit.py . --mode hybrid --base-url http://localhost:3000
```

## 4. Auditar una web pública

```bash
python scripts/audit.py https://example.com --mode web --max-pages 30
```

## 5. Uso con cualquier Asistente de IA

Esta skill está estructurada con el estándar universal de skills para IA (compatible con Claude, Gemini, ChatGPT, Antigravity, Cursor, etc.):

- **Activación automática:** El asistente lee `SKILL.md` e identifica cuándo activar la skill según el contexto de la conversación.
- **Consultas modulares:** El asistente consulta las guías en `references/` para el análisis técnico, de contenido, GEO o de datos estructurados.
- **Herramientas deterministas:** El asistente (o el usuario) ejecuta `scripts/audit.py` para recabar métricas y hallazgos objetivos sin inventar datos.
- **Generación de informes:** El asistente formatea las conclusiones siguiendo las plantillas de `templates/audit-report.md` y `templates/action-plan.md`.
