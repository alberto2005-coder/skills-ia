# 09 · Marca

Objetivo: que el resultado sea tuyo, no un clon con otro logo pegado.

## Entradas
App construida, `replica/fix-plan.md` (ángulo), `replica/design/`.

## Pasos

1. **Nombre.** 3-5 candidatos; comprueba: dominio disponible, handles, búsqueda en App Store/Play, y **registro de marca** (OEPM/EUIPO/USPTO, búsqueda por clase). Comprueba antes de enamorarte.
2. **Identidad.** Paleta nueva (no la del original ni un giro de tono del mismo hex), tipografía, logo (brief a diseñador o generado por ti), voz: 3 adjetivos y 3 ejemplos de cómo suena.
3. **Aplicación.** Nombre y colores en app, metadatos, emails, icono, splash. Tokens actualizados y `contrast.py` en verde otra vez.
4. **Sweep.** `python scripts/sweep.py . --avoid "App Original" --avoid apporiginal.com --color "#<hex original>"`. Incluye identificadores (`OriginalAppEmbed`), nombres de fichero, rutas, dominios, textos y metadatos. Renombra, no comentes "esto venía del original".
5. **Exenciones honestas.** Los documentos de recon pueden nombrar el original: usa `sweep:ignore-file` solo en esos ficheros, nunca en código de producción.
6. **Metadatos.** Revisa `package.json`, `Info.plist`/manifest, copyright, autor, bundle id, nombres de proyecto.

## Salida
`replica/brand/brand.md` (nombre, checks hechos y pendientes, paleta, voz, logo brief) y código limpio con `sweep.py` a 0.

## Checklist
- [ ] Búsqueda de marca hecha y anotada con fecha y fuentes.
- [ ] `sweep.py` a 0 en el código de producción.
- [ ] Paleta con AA tras el cambio.
- [ ] Nada de su logo, icono, tipografía ni ilustraciones.
- [ ] Bundle id, dominio y emails propios.
