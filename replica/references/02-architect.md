# 02 · Arquitectura

Objetivo: decidir stack, datos y API antes de escribir pantallas, y ordenar el trabajo por rebanadas verticales.

## Entradas
`replica/recon.md`, `replica/features.csv`.

## Pasos

1. **Stack.** Elige por el equipo que lo va a mantener, no por moda. Justifica en una línea por decisión: framework, base de datos, auth, pagos, email, hosting, almacenamiento. Si hay requisito de mobil nativo, dilo y separa.
2. **Esquema.** DDL real, no diagrama de cajas. Incluye:
   - claves y relaciones con `on delete`;
   - **constraints de las invariantes del recon** (unique parcial, check, exclusion);
   - índices por las consultas que ya sabes que vas a hacer;
   - `created_at/updated_at`, soft delete solo si hace falta;
   - multi-tenant (`tenant_id` en todo lo que lo necesite) o single-tenant explícito.
3. **API.** Tabla de endpoints: método, ruta, auth requerida, entrada, salida, errores. Recursos anidados con permisos por recurso, no solo por rol.
4. **Rebanadas verticales.** Orden de construcción: primero el flujo que da la promesa de la app (reservar, publicar, comprar) de punta a punta; luego el resto.
5. **Riesgos técnicos.** Webhooks duplicados, idempotencia, zona horaria, límites de terceros, colas y reintentos, datos que crecen.
6. **No funcionales mínimos.** Rate limiting, backups, logs sin datos personales, secretos en entorno.

## Salida

`replica/architecture.md`:

```markdown
# Arquitectura: <nombre propio>
## Decisiones       (tabla: decisión | alternativa descartada | por qué)
## Esquema          (SQL)
## API              (tabla de endpoints)
## Orden de build   (rebanadas, con la primera end-to-end)
## Riesgos
## Entornos y secretos
```

## Checklist
- [ ] Cada invariante del recon tiene constraint o transacción que la protege.
- [ ] Ningún endpoint sin regla de autorización escrita.
- [ ] La primera rebanada es un flujo completo, no "el login y ya".
- [ ] Pagos: webhook idempotente y estado reconciliable.
- [ ] Fechas en UTC en almacenamiento, zona del usuario en presentación.
