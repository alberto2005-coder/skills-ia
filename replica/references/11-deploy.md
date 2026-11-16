# 11 · Despliegue

Objetivo: publicar sin sorpresas y poder volver atrás.

## Entradas
Todo lo anterior. `replica/preflight.md` se escribe en esta fase.

## Preflight (todo o no se despliega)

```bash
python scripts/parity.py replica/features.csv      # 0 must pendientes
python scripts/sweep.py . --avoid "App Original" --avoid apporiginal.com
python scripts/contrast.py replica/design/tokens.json
python scripts/listing.py replica/launch/listing.json
```

- [ ] Tests verdes, 0 S1/S2 abiertos (`replica/bugs.md`).
- [ ] `sweep` a 0 en código de producción; exenciones solo en docs.
- [ ] `parity` sin must pendientes; gaps deliberados escritos.
- [ ] `contrast` AA; `listing` 0 errores.
- [ ] Variables de entorno definidas en el destino (no en el repo).
- [ ] Migraciones probadas desde cero y backup reciente.
- [ ] Dominio propio, DNS, HTTPS y redirects.
- [ ] Emails transaccionales con dominio verificado (SPF/DKIM).
- [ ] Pagos en modo live con claves live y webhook apuntando al dominio final.
- [ ] Plan de rollback: cómo se vuelve a la versión anterior y qué pasa con los datos.
- [ ] Monitorización: errores, uptime, y una alerta que te avise a ti.

## Pasos

1. Escribe `replica/preflight.md` con cada check, su resultado y la fecha. Un check no ejecutado se marca como no ejecutado.
2. Configura producción (hosting, base de datos, storage, secretos).
3. Migra y despliega.
4. **Smoke test** en producción: registro, flujo principal, pago de prueba real (importe mínimo), email recibido, logout.
5. Entrega los DNS que falten y verifica propagación.
6. **Pide confirmación explícita antes de publicar** (tienda o dominio público). Publicar no es un paso que se asuma.

## Salida
App live + `replica/preflight.md` completo y `replica/launch/plan.md` actualizado.

## No hagas
Desplegar con un must pendiente "porque ya casi", ni con el sweep sucio, ni publicar en tienda sin que el usuario lo haya dicho.
