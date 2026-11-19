---
name: seo-execute
description: Aplica los cambios de un plan SEO de forma segura — copia robots.txt, llms.txt y llms-full.txt con backup .bak, deja los snippets de meta tags y JSON-LD para integración manual y verifica después con una nueva auditoría. Úsala cuando el usuario apruebe aplicar el plan o pida escribir los ficheros de SEO en su proyecto. English: apply the plan with --apply, write robots.txt and llms.txt, and keep .bak backups.
license: MIT
metadata:
  package: seo-auditor
  version: "3.0.0"
---

# SEO Auditor · Execute

Aplicar sin romper. Solo se escribe lo que se puede escribir con seguridad, y siempre con vuelta atrás.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`.

**Todos los comandos se ejecutan desde la raíz del repositorio**  con el prefijo `py` (Windows) o `python3` (Linux/macOS) sobre `seo-auditor/scripts/cli.py`.

## Cuándo se usa

- El usuario aprueba el plan y pide aplicarlo.
- Hay que dejar `robots.txt` o `llms.txt` en el proyecto.
- Tras aplicar, para verificar que la puntuación sube por el motivo correcto.

## Precondiciones

- `PLAN.md` revisado y aprobado explícitamente por el usuario.
- Borradores `DRAFT` de `seo-plan` sin `TODO` bloqueantes.
- Destino identificado (`--dest`), con permiso para escribir en él.

## Método

1. Confirma con el usuario **qué ficheros** se van a escribir y dónde. Sin confirmación, no se ejecuta.
2. Aplica:

```bash
py seo-auditor/scripts/cli.py fix --input reports/mi-sitio/20260101-120000/audit.json --output output --apply --dest ./mi-proyecto
```

3. Comprueba qué se escribió realmente: `robots.txt`, `llms.txt` y `llms-full.txt` se copian; los snippets de `meta-tags.html.draft` y `jsonld.json.draft` **no** se inyectan solos y hay que integrarlos a mano.
4. Verifica que cada fichero sobrescrito dejó su `.bak` y que el contenido nuevo no perdió reglas previas (en `robots.txt`, un `Disallow` existente que desaparece es un incidente).
5. Re-audita y compara:

```bash
py seo-auditor/scripts/cli.py audit . --mode source
py seo-auditor/scripts/cli.py compare antes.json despues.json
```

6. Si la puntuación baja o aparece un fallo nuevo, revierte desde el `.bak` y documenta por qué.

## Reglas duras

- Nunca se escribe sin `--apply` **y** confirmación explícita.
- Nunca se sobrescribe sin backup.
- No se tocan `.env`, credenciales ni configuración del servidor.
- Los snippets que requieren editar plantillas se entregan como instrucciones, no se aplican a ciegas.

## Gate de salida

- Ficheros aplicados verificados uno a uno, con `.bak` presente.
- Reglas previas conservadas (diff revisado, no solo exit code 0).
- Re-auditoría ejecutada y `compare` sin nuevos fallos `must`.
- Informe de qué se aplicó, qué quedó manual y qué se revirtió.

## Handoff

El resultado verificado cierra el ciclo Audit → Plan → Execute. `seo-compare` documenta la mejora con evidencia.
