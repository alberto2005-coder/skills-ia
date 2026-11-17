---
name: replica-launch
description: Fase 10 de replica — prepara el lanzamiento comercial: landing, listing de App Store/Play, precios por país (pago local, moneda, factura electrónica, WhatsApp), claims con evidencia y copy nuevo pasado por sweep. Úsala cuando la app vaya a publicarse, cuando haya que escribir el listing o cuando el usuario pregunte cómo cobrar en su país. English: write the landing and the store listing, check character limits and set per-country pricing.
---

# Replica · Lanzamiento (fase 10)

El producto está listo; falta que se pueda comprar. Landing, tiendas, precios locales y claims que se sostienen.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Todos los comandos se ejecutan desde la raíz del repositorio** (`skills-ia-main/`).

## Precondiciones

- Marca limpia (fase 9).
- Plan de mejoras (fase 8) para elegir argumentos con base real.

## Método

1. Lee `../references/10-launch.md` entero, incluida la **tabla de 10 países** (método de pago local, moneda, factura electrónica y WhatsApp).
2. Verifica cada dato de esa tabla con el proveedor de pagos y la autoridad tributaria del país antes de publicarlo: la tabla es un punto de partida, no una fuente legal.
3. **Landing**: propuesta de valor concreta, prueba visible, un solo CTA principal, estados de error y política de privacidad.
4. **Listing de tiendas** en `replica/launch/listing.json` desde `../templates/listing.json`, y valida:

```bash
py replica/scripts/listing.py replica/launch/listing.json
```

   Comprueba límites de App Store/Play, claims de ranking, keywords desperdiciadas y nombre del original en el listing.
5. **Precios locales**: moneda, impuestos y método de pago mayoritario por país; nada de conversión automática sin redondeo comercial decidido.
6. **Claims**: cada afirmación de la landing y del listing con evidencia (`features.csv`, `themes.md`, prueba propia). Sin evidencia, se reformula o se elimina.
7. **Re-sweep del copy nuevo**:

```bash
py replica/scripts/sweep.py replica/launch --avoid "App Original" --avoid apporiginal.com
```

## Gate de salida

- `listing.py` con 0 errores.
- Landing y listing sin claims sin respaldo.
- `sweep.py` en 0 sobre todo el copy nuevo.
- Precios y facturación revisados por país, con la fuente consultada anotada.

## Handoff

Con el lanzamiento preparado, `replica-deploy` (fase 11) publica, y `replica-redes` (fase 13) hace el copy social con el mismo estándar de evidencia.
