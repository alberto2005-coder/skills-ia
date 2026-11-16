# 01 · Reconocimiento

Objetivo: un mapa funcional de la app que sirva para construir sin volver a mirarla, y un tamaño honesto del trabajo.

## Entradas
Nada de `replica/` (es la primera fase). Sí: URL, store listing, tu cuenta.

## Pasos

1. **Inventario de superficies.** Web, iOS, Android, API pública, emails transaccionales que recibas, onboarding. Anota qué cubre cada una y las diferencias entre plataformas.
2. **Pantallas.** Por cada una: propósito, cómo se llega, acciones posibles, datos que muestra, estados (vacío, carga, error, éxito, sin permisos, límite alcanzado), y qué pasa al volver atrás.
3. **Flujos.** Disparador → pasos → resultado. Con casos límite por flujo: doble submit, pago rechazado, sesión caducada, dos usuarios a la vez, zona horaria, cancelación a mitad, reintento.
4. **Modelo de datos inferido.** Entidades, campos visibles, relaciones, y sobre todo **invariantes** (qué no puede ocurrir: dos reservas del mismo hueco, un pago sin pedido, un miembro sin invitación). Esas invariantes se convertirán en constraints.
5. **Matriz de features.** Copia `templates/features.csv` y rellena: `id,area,priority,feature,status,notes`. Prioridad `must` solo para lo que sin ello la app no cumple su promesa. `status` empieza en `missing`; lo que sea red, contenido licenciado o mercado va `out_of_scope` y se explica en `notes`.
6. **Tamaño y riesgos.** S/M/L por flujo, dependencia de terceros (pagos, mapas, calendarios) y lo que podría tumbar el proyecto.

## Salida

`replica/recon.md`:

```markdown
# Recon: <App>
## Superficies
## Pantallas        (tabla: pantalla | propósito | estados | notas)
## Flujos           (uno por sección, con casos límite)
## Modelo de datos  (entidades, relaciones, invariantes)
## Fuera de alcance (qué y por qué)
## Tamaño           (flujo | talla | riesgo)
## Fuentes          (URLs públicas usadas y fecha)
```

`replica/features.csv` y `replica/screens/` con tus capturas.

## Checklist
- [ ] Cada flujo tiene al menos 3 casos límite.
- [ ] Cada pantalla tiene estados de vacío y error definidos.
- [ ] Invariantes escritas como frases verificables.
- [ ] `out_of_scope` justificado, no escondido.
- [ ] Capturas propias o públicas, ninguna de pago.
- [ ] Textos de UI descritos con tus palabras, no copiados.

## No hagas
Rellenar features que no has visto funcionar, ni asumir que "seguro que tiene X". Si no lo has visto, no está.
