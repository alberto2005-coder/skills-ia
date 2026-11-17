---
name: appsec-recon
description: >
  Primera fase de una auditoría de seguridad: fija alcance y autorización,
  inventaría activos, mapea la superficie de ataque y recoge la evidencia base.
  Incluye revisión de cabeceras y configuración expuesta, inventario de
  dependencias y SBOM, y barrido de secretos en el árbol de trabajo.
  Úsala cuando pidan empezar una auditoría, definir el alcance de un pentest,
  revisar la superficie de un repo antes del análisis profundo o comprobar
  configuraciones y dependencias vulnerables.
  English: scope and authorize a security audit, inventory assets and attack
  surface, and collect the evidence baseline before deep analysis.
---

# AppSec · Reconocimiento

Sin alcance no hay auditoría: solo una lista de miedos. Esta fase produce el inventario y la evidencia sobre la que trabajan las demás.

## Precondiciones

- Propietario del sistema identificado y **autorización** para revisarlo (texto, ticket o correo).
- Ruta del repositorio, URL o artefacto a auditar.
- Declaración de lo que queda fuera: entornos productivos, datos de clientes, servicios de terceros.

Si falta la autorización, se detiene aquí y se pide por escrito. Sin ella no se toca nada.

## Método

1. **Alcance.** Activos, límites, ventana temporal y qué se puede tocar. Se escribe antes de mirar código.
2. **Inventario.** Lenguajes, frameworks, puntos de entrada (rutas, colas, cron, webhooks), almacenes de datos, integraciones y secretos necesarios.
3. **Superficie.** Todo lo que un atacante puede alcanzar: endpoints públicos, paneles, uploads, redirects, APIs internas expuestas, puertos y buckets.
4. **Dependencias.** Manifiestos y lockfiles, versiones fijadas, dependencias sin mantenimiento, scripts de instalación y procedencia de paquetes.
5. **Secretos.** Claves, tokens, contraseñas y certificados en el árbol, en el historial y en la configuración de CI.
6. **Perímetro.** Cabeceras de seguridad, CORS, cookies, TLS, exposición de metadatos y ficheros de descubrimiento.

## Evidencia

Cada dato lleva origen y fecha: `ruta:línea`, comando ejecutado y salida literal, o URL y cabecera observada. Sin esa tríada, el hallazgo no pasa de hipótesis y así se etiqueta.

## Cobertura mínima

- Mapa de puntos de entrada con método, autenticación requerida y datos que acepta.
- Lista de dependencias con versión y motivo de sospecha, si lo hay.
- Secretos encontrados, redactados, con ubicación y si están activos o caducados.
- Cabeceras y configuración de perímetro observadas, no supuestas.
- Inventario de infraestructura declarada (Docker, IaC, cloud) para `appsec-infra`.

## Herramientas del paquete

```bash
py appsec-audit/scripts/scan_secrets.py <ruta> --json
```

Barrido determinista de secretos con redacción. No sustituye a un escáner de historial: si el repo tiene historial largo, se declara lo revisado y lo que no.

## Gate de salida

- Alcance y autorización escritos, con exclusiones explícitas.
- Inventario de activos y superficie completo para el tamaño del proyecto.
- Dependencias y secretos revisados con evidencia por ítem.
- Hipótesis separadas de hechos observados.

## Handoff

Entrega a `appsec-code` los puntos de entrada y las rutas con datos de usuario, a `appsec-infra` la infraestructura declarada y a `appsec-llm` cualquier componente de IA. Si el proyecto no tiene código propio (solo configuración), salta directo a `appsec-infra`.
