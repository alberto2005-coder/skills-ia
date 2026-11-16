# 06 · Pruebas

Objetivo: saber qué está roto y con qué gravedad, con evidencia, no con impresiones.

## Entradas
`replica/recon.md` (flujos y casos límite), `replica/features.csv`, app construida.

## Pasos

1. **Plan desde los flujos**, no desde las pantallas. Un caso por: happy path, caso límite del recon, permiso denegado, dato inválido.
2. **E2E** (Playwright/Cypress) para los flujos críticos, con datos de prueba propios y limpieza entre tests. Los que dependen de terceros, con dobles o sandbox.
3. **Casos que casi nadie prueba y aquí sí:** doble submit, dos pestañas, sesión caducada a mitad, pago rechazado, reintento de webhook, zona horaria distinta, red lenta, back del navegador, mayúsculas/acentos/emoji en inputs, ficheros gigantes.
4. **Registra bugs** con severidad S1 (pierde dinero/datos, seguridad) · S2 (flujo principal roto, sin workaround) · S3 (workaround existe) · S4 (cosmético). Cada bug: pasos, esperado, obtenido, evidencia.
5. **Criterio de salida**: 0 S1 y 0 S2 abiertos. Lo demás se puede documentar y lanzar.

## Salida
`replica/test-plan.md` (casos con ID) y `replica/bugs.md` (tabla: id | severidad | estado | pasos | esperado | obtenido). Specs e2e en el repo.

## Checklist
- [ ] El plan cubre cada flujo del recon.
- [ ] Cada bug tiene reproducción desde cero.
- [ ] Tests repetibles en CI, no solo en tu máquina.
- [ ] Ningún bug cerrado sin verificación.

## No hagas
Marcar tests en verde sin ejecutarlos, ni "arreglar" un test cambiando la expectativa. Si un S1/S2 existe, se dice aunque el usuario tenga prisa.
