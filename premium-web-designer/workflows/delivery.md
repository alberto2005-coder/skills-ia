
# DELIVERY WORKFLOW

## OBJECTIVE

Deliver a complete, understandable
and maintainable project.

## GATE (OBLIGATORIO)

Este checklist es la lista de trabajo del workflow; la puerta que decide es la de
`SKILL.md` y se ejecuta antes de entregar:

```bash
py premium-web-designer/scripts/delivery_check.py <carpeta>
py premium-web-designer/scripts/delivery_check.py <carpeta> --public   # al publicar
```

Sale 0 si no falla ningún `must`, 1 si falla alguno y 2 si la carpeta no existe.
Sin `--public` se asume prototipo local; con `--public`, canonical, Open Graph con
imagen, meta description, `robots.txt`, `sitemap.xml` y el fichero de cabeceras
pasan a bloquear. Lo que la puerta no puede medir (desbordamiento, líneas del
titular, solapes, foco) lo mide `premium-qa` en el navegador: no se sustituye una
puerta por la otra.

## FINAL CHECKLIST

### DESIGN

- [ ] Approved visual direction implemented.
- [ ] Consistent design system.
- [ ] Correct typography.
- [ ] Appropriate imagery.
- [ ] Responsive layouts.

### FUNCTIONALITY

- [ ] Navigation works.
- [ ] Links work.
- [ ] Forms work.
- [ ] Interactions work.
- [ ] Required integrations verified.

### QUALITY

- [ ] Accessibility reviewed.
- [ ] SEO fundamentals implemented.
- [ ] Performance reviewed.
- [ ] Build verified.
- [ ] Critical issues resolved.

### DOCUMENTATION

- [ ] Installation instructions.
- [ ] Environment variables documented.
- [ ] Development instructions.
- [ ] Deployment requirements.
- [ ] Known limitations documented.

## FINAL REPORT

Provide:

1. Project summary.
2. Pages completed.
3. Functionality implemented.
4. Technologies used.
5. Files changed.
6. Tests performed.
7. Outstanding issues.
8. Launch instructions.

## HONESTY

Distinguish between:

- Implemented.
- Tested.
- Verified.
- Not tested.
- Not implemented.

Do not report production readiness
without checking the relevant requirements.
