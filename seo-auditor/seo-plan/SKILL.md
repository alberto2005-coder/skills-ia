---
name: seo-plan
description: >
  Convierte una auditoría SEO en un plan accionable ordenado por severidad (must y should) y por esfuerzo e impacto, con cita, recomendación y borradores DRAFT (robots.txt, llms.txt, meta tags, JSON-LD) sin tocar el sitio. Úsala cuando el usuario pida un plan de mejoras SEO, priorizar los fallos de una auditoría o preparar los cambios antes de aplicarlos. English: turn the audit into a prioritized SEO plan for the web, ordering must and should failures by effort and impact, with DRAFT files, without touching the site.
license: MIT
metadata:
  package: seo-auditor
  version: "3.0.0"
---

# SEO Auditor · Plan

De la evidencia al plan. **No escribe en el sitio**: genera acciones priorizadas y borradores `DRAFT`.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`.

**Todos los comandos se ejecutan desde la raíz del repositorio**  con el prefijo `py` (Windows) o `python3` (Linux/macOS) sobre `seo-auditor/scripts/cli.py`.

## Cuándo se usa

- Hay un `audit.json` y el usuario pregunta «¿por dónde empiezo?».
- Antes de aplicar cambios (`seo-execute`).
- Cuando pide un plan SEO con prioridades y esfuerzo.

## Precondiciones

- `audit.json` de una auditoría real (no inventado). Si no existe, ejecuta `seo-audit` primero.

## Método

1. Genera el plan y los borradores:

```bash
py seo-auditor/scripts/cli.py fix --input reports/mi-sitio/20260101-120000/audit.json --output output
```

2. Revisa `output/PLAN.md`: acciones ordenadas por severidad, con id de comprobación, cita y recomendación.
3. Revisa los borradores: `robots.txt.draft`, `llms.txt.draft`, `llms-full.txt.draft`, `meta-tags.html.draft`, `jsonld.json.draft`. Todos llevan marca `DRAFT` y `TODO` donde falta un dato del negocio.
4. Agrupa por esfuerzo/impacto y propone un orden de ejecución en 3 tramos: **bloqueantes** (`must`), **rápidas** (bajo esfuerzo, `should`) y **mejoras** (`nice`).
5. Marca explícitamente lo que **no** se puede resolver desde el código (contenido, enlaces externos, datos de negocio) y quién debe hacerlo.
6. Si un `TODO` depende de una decisión del usuario (marca, dominio, país, precios), pregúntala antes de rellenarlo.

## Reglas duras

- Cero cambios aplicados en esta fase. Ni un fichero del sitio se toca.
- Cada acción del plan conserva su `id` y su cita: el plan debe poder auditarse contra el informe.
- Los borradores no se presentan como definitivos: son propuestas con huecos visibles.
- Nada de recomendaciones genéricas sin comprobación detrás («mejora el contenido» no es una acción).

## Gate de salida

- `PLAN.md` con cada acción enlazada a una comprobación del `audit.json`.
- Borradores generados y con `TODO` donde falte información.
- Orden de ejecución propuesto con criterio (impacto × esfuerzo).
- Lista explícita de lo que requiere decisión humana.

## Handoff

El plan aprobado pasa a `seo-execute` para aplicar solo lo aplicable con backup.
