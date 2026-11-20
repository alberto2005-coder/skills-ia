---
name: replica-deploy
description: >
  Fase 11 de replica — preflight y publicación: variables de entorno, migraciones, permisos, backups, dominio, monitorización básica y confirmación explícita del usuario antes de desplegar. Úsala cuando el clon vaya a producción, cuando haya que revisar qué falta antes de publicar o para desplegar con seguridad. English: run preflight checks with backups and rollback, then verify the deployment is live.
license: MIT
metadata:
  package: replica
  version: "2.0.1"
  author: "Alberto Ortiz"
---

# Replica · Despliegue (fase 11)

El último gate. Aquí se comprueba que publicar no rompe datos, no filtra secretos y no deja la app sin vuelta atrás.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Comandos desde la raíz del repositorio**.

## Precondiciones

- Fases 9 y 10 cerradas (`sweep` limpio, listing validado).
- Suite de pruebas verde y 0 bugs S1/S2.

## Método

1. Lee `../references/11-deploy.md` entero.
2. Rellena `replica/preflight.md` desde `../templates/preflight.md`. No es decorativo: cada casilla tiene comando o evidencia.
3. Comprueba:
   - variables de entorno y secretos fuera del repositorio;
   - migraciones aplicadas en una copia limpia y plan de rollback;
   - backups configurados y **probado un restore**;
   - dominio, TLS y redirecciones canónicas;
   - permisos de producción distintos de los de desarrollo;
   - monitorización mínima (errores y disponibilidad) y alerta a alguien.
4. Re-ejecuta el sweep sobre el artefacto que se va a desplegar, no sobre el árbol de desarrollo.
5. Pide **confirmación explícita** al usuario con el resumen de lo que va a pasar. Sin un «sí», no se despliega.
6. Despliega y verifica en producción: flujo principal, login, una escritura y una lectura reales.
7. Si algo falla, rollback documentado y fase `bloqueada` con el motivo.

## Gate de salida

- `preflight.md` completo, sin casillas en blanco.
- Restore de backup probado, no solo configurado.
- Sweep del artefacto en 0.
- Confirmación del usuario registrada en `replica/progreso.md`.
- Verificación post-deploy con evidencia.

## Handoff

Con la app en producción, `replica-redes` (fase 13) puede publicar contenido social apuntando a la URL real.
