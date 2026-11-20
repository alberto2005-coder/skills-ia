---
name: replica-backend
description: >
  Fase 5 de replica — añade backend real al clon: autenticación, esquema de datos con migraciones e invariantes, permisos por recurso, pagos y trabajos en segundo plano, documentando cada decisión. Úsala cuando la app necesite cuentas, guardar datos, cobrar o ejecutar tareas asíncronas. English: add authentication, per-resource permissions, versioned migrations, payments and idempotent jobs.
license: MIT
metadata:
  package: replica
  version: "2.0.1"
  author: "Alberto Ortiz"
---

# Replica · Backend (fase 5)

La app deja de ser una maqueta: cuentas, datos que persisten, permisos y cobros que no se pueden inventar. No diseña pantallas ni maqueta: la UI llega construida de `replica-build`.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Comandos desde la raíz del repositorio**.

## Precondiciones

- Fase 4 con los flujos `must` construidos.
- Invariantes de `architecture.md` disponibles.

## Método

1. Lee `../references/05-backend.md` entero.
2. **Auth**: elige el mecanismo por requisito (sesión, tokens, OAuth). Nunca copies el flujo de autenticación del original; implementa uno estándar y documenta el modelo de sesión.
3. **Datos**: esquema con migraciones versionadas y los invariantes de la fase 2 aplicados en la base (constraints), no solo en el código.
4. **Permisos**: cada recurso con regla de propiedad explícita («quién puede leer, quién escribir»). Un endpoint sin regla es un bug de seguridad, no una decisión pendiente.
5. **Pagos**: usa el proveedor que decida el usuario; nunca simules cobros reales ni guardes datos de tarjeta. Documenta estados (pendiente, pagado, fallido, reembolsado) y qué los dispara.
6. **Jobs**: idempotencia y reintentos declarados; sin bucles infinitos ni procesos que se pisen.
7. Escribe `replica/backend.md`: decisiones, esquema, permisos por recurso, estados de pago, jobs y lo que queda fuera.

## Reglas

- Cero secretos en el repositorio: variables de entorno y `.env.example`.
- Nada de datos reales de usuarios en pruebas.
- Si el original usa un servicio privado, no se replica ese servicio: se sustituye por uno propio y se anota la diferencia.

## Gate de salida

- Auth funcionando con prueba de registro, login, logout y sesión expirada.
- Esquema aplicado desde cero en una base limpia.
- Cada recurso con regla de permisos y prueba de acceso denegado.
- Estados de pago cubiertos y probados en sandbox.
- `backend.md` sin decisiones huérfanas.

## Handoff

`backend.md` y el código pasan a `replica-test` (fase 6). Las reglas de permisos se re-verifican en `replica-deploy` (fase 11) antes de publicar.
