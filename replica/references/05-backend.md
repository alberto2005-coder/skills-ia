# 05 · Backend

Objetivo: cuentas, datos, pagos e integraciones que aguantan gente real.

## Entradas

`replica/architecture.md`, `replica/features.csv`, código de la fase 4.

## Pasos

1. **Auth.** Email + verificación, o OAuth con las claves del usuario. Hash con argon2/bcrypt, sesiones con expiración y revocación, recuperación con token de un uso. Nunca inventes tu propio cifrado.
2. **Autorización por recurso.** Cada lectura/escritura comprueba pertenencia, no solo "está logueado". Escribe las reglas y pruébalas con un usuario B.
3. **Datos.** Migraciones versionadas, seeds de desarrollo, constraints de las invariantes, transacciones en operaciones de varios pasos.
4. **Pagos** (si aplica). Stripe (o equivalente) con precios propios: checkout, webhook **idempotente** con `event.id`, reconciliación de estado, gestión de impagos y cancelación. El importe y el plan se deciden en servidor.
5. **Email/notificaciones.** Proveedor transaccional, plantillas propias, reintentos y unsubscribe. Nada de emails al original.
6. **Integraciones.** Siempre API oficial y claves del usuario (Google Calendar, etc.). Scopes mínimos y desconexión limpia.
7. **Operación.** Rate limiting por endpoint sensible, backups, logs sin PII, alertas de errores, variables de entorno documentadas.

## Salida

Código backend + `replica/backend.md` con: endpoints implementados, reglas de autorización, flujos de pago, integraciones y variables de entorno necesarias.

## Checklist

- [ ] Usuario B no puede tocar recursos de A (probado).
- [ ] Webhook repetido no duplica ni pierde estado.
- [ ] Migraciones aplican desde cero en limpio.
- [ ] Secretos fuera del repo.
- [ ] Errores no filtran trazas ni datos personales.
