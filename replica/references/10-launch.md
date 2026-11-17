# 10 · Lanzamiento

Objetivo: landing, precios y listing que conviertan, sin promesas que no puedas sostener.

## Entradas
`replica/fix-plan.md` (ángulo y fixes), `replica/parity.md`, `replica/brand/`, `templates/listing.json`.

## Pasos

1. **Landing.** Hero con el ángulo en una frase, 3 beneficios ligados a los fixes reales, cómo funciona en 3 pasos, prueba (capturas propias), precios, FAQ con las objeciones que salieron de las reseñas, CTA. Sin testimonios inventados: si no tienes usuarios, no pongas logos.
2. **Precios.** Mira el pricing público del original y posiciona: más barato no es estrategia por sí solo. Modelo (plano/por uso/por asiento) alineado con la queja principal. Deja claro qué incluye y qué no.
3. **Listing.** Copia `templates/listing.json` y valida: `python scripts/listing.py replica/launch/listing.json`. Límites, claims de ranking, keywords, nombre del original, capturas.
4. **ASO básico.** Título con la categoría y el beneficio, subtítulo con la diferenciación, keywords sin repetir el título, 5-8 capturas con texto propio.
5. **Capturas y vídeo.** De tu app real, con tus datos. Ninguna captura del original, ni recortada ni recoloreada.
6. **Plan de salida.** Dónde está tu usuario (comunidades, foros, directorios), qué publicas y con qué permiso. Nada de spam masivo.

## Países (`paises.md`-style)

Si vas a vender en más de un país, copia esta tabla a `replica/launch/paises.md` y complétala por mercado. Es **orientativa y está fechada**: métodos de pago y fiscalidad cambian; **verifica siempre con tu proveedor de pagos y con la autoridad tributaria** de cada país (y con tu asesor fiscal) antes de prometer algo en la landing.

| País | Moneda | Métodos de pago locales (habitual) | Factura electrónica (orientativo) | Atención por WhatsApp |
|---|---|---|---|---|
| España | EUR € | Tarjeta (Redsys), Bizum, transferencia SEPA, PayPal | Verifactu / factura electrónica con Hacienda (AEAT) | Muy usado; WhatsApp Business habitual |
| México | MXN $ | Tarjeta, SPEI, OXXO en efectivo, CoDi | CFDI 4.0 ante el SAT (obligatorio) | Masivo; canal principal de soporte |
| Argentina | ARS $ | Mercado Pago, tarjeta, transferencia/ débito | Comprobante electrónico con CAE (AFIP/ARCA) | Muy usado |
| Colombia | COP $ | PSE (banco), tarjeta, Nequi, Daviplata, efecty | Factura electrónica ante la DIAN | Muy usado |
| Chile | CLP $ | Tarjeta (Webpay), Servipag, transferencia | Boleta/factura electrónica ante el SII | Habitual |
| Perú | PEN S/ | Yape, Plin, PagoEfectivo, tarjeta (Niubiz), transferencia | Comprobante electrónico ante la SUNAT | Muy usado |
| Brasil | BRL R$ | **Pix**, boleto bancario, tarjeta | Nota fiscal (NF-e/NFS-e), obligatoria según actividad | Muy usado (WhatsApp Business API) |
| Ecuador | USD $ | Tarjeta, transferencia bancaria, pago en efectivo | Comprobante electrónico ante el SII/SRI | Habitual |
| Uruguay | UYU $ | RedPagos, ahorro, tarjeta | e-Factura ante la DGI | Habitual |
| Estados Unidos | USD $ | Tarjeta (Stripe), Apple/Google Pay, ACH | Sales tax por estado (sin factura nacional); W-9/W-8 según contraparte | Menos habitual (predomina email/SMS) |

Notas de uso:

- **Pagos:** confirma con tu PSP (Stripe, Mercado Pago, local) qué método está disponible *para tu tipo de empresa* y qué comisión tiene; no todos los métodos de la tabla se ofrecen en todos los países desde el primer día.
- **Impuestos:** IVA/IVA equivalente, retenciones y umbrales de venta transfronteriza los define la autoridad tributaria de cada país; esta tabla **no** es asesoría fiscal (regla dura 7).
- **WhatsApp:** usa WhatsApp Business (API o app oficial), con opt-in del usuario y opción de baja; sin spam masivo, y respetando las políticas de Meta.
- **Landing:** muestra el precio en la moneda local si puedes; si no, declara la moneda y el tipo de cambio y no finjas que es "lo mismo" en todas partes.

## Salida
Landing publicada o en repo, `replica/launch/listing.json` con 0 errores, `replica/launch/plan.md` (canales, mensaje, fechas) y, si aplica, `replica/launch/paises.md`.

## Checklist
- [ ] `listing.py` en 0 errores.
- [ ] Cada beneficio tiene detrás una feature que existe y pasa parity.
- [ ] Precios coherentes con lo que aplica el backend.
- [ ] Cero testimonios, métricas o logos no verificables.
- [ ] Capturas propias y legibles en móvil.
- [ ] Pagos, moneda y facturación por país verificados con el proveedor y la autoridad tributaria (no con la tabla orientativa).
