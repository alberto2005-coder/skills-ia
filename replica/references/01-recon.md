# 01 · Reconocimiento

Objetivo: un mapa funcional de la app que sirva para construir sin volver a mirarla, y un tamaño honesto del trabajo.

## Entradas

Nada de `replica/` (es la primera fase). Sí: URL, store listing, tu cuenta.

## Paso 0 · Foco (obligatorio antes de mirar nada)

**Elige una función observable, no la app entera.** Reconstruir "toda la app" de golpe produce mapas gigantes, superficiales y sin criterio de parada. El foco se estrecha en cascada, de mayor a menor:

1. **Análisis completo** → solo inventario de superficies: qué pantallas existen y qué flujo es el corazón (1 sesión corta, sin profundizar).
2. **Resumen** → 1 página: el promesa-usuario en una frase, el flujo principal y los 2-3 flujos secundarios.
3. **Módulo** → eliges **un módulo** (p. ej. "alta + primer uso", "carrito y pago", "buscador y ficha").
4. **Función** → dentro del módulo, **una función observable y medible por iteración**: un flujo que se puede ver empezar y terminar, con estados vacío/error/success visibles.

Reglas del foco:

- La función elegida se escribe arriba del todo en `recon.md`: *"Foco de esta iteración: <función observable>"*.
- Iteración = una función. Al terminarla, la siguiente función se añade **refinando** el recon, nunca rehaciéndolo.
- Si el usuario pide "la app completa", se responde con el plan de iteraciones (función → función) y se empieza por la primera; no se abre el análisis completo de todas a la vez.
- Una función deja de ser foco cuando está mapeada con sus estados, sus casos límite y su fila en `features.csv`.

## Caché de análisis (no repitas análisis ya guardado)

- Si `replica/recon.md` **ya existe**, el análisis **se refina, no se rehace**. Primero se lee lo guardado; después solo se añade, corrige o profundiza lo que falte.
- Prohibido rehacer el inventario completo, volver a capturar pantallas ya capturadas o re-leer fuentes ya citadas salvo que el usuario lo pida o la app haya cambiado (si cambia, se anota fecha y qué cambió, sin borrar lo anterior).
- Cada pasada nueva deja constancia en `recon.md` con fecha: `## Revisión YYYY-MM-DD — qué se añadió y por qué`.
- Si `features.csv` existe, se actualizan filas concretas (`status`, `notes`); no se genera un manifiesto paralelo.
- El caché vale también para fuentes: las URLs ya citadas con su fecha no se re-verifican en cada pasada; se re-verifican solo los hallazgos que vayan a usarse como `high` en una decisión.

## Pasos

> **Formato de evidencia obligatorio.** Cada hallazgo de esta fase (pantalla, flujo, invariantes, precios, límites) se registra con la plantilla `templates/evidence.md`: **Fuente · Observación · Inferencia · Confianza (high/medium/low/THIN) · Límites y desconocidos**. Un hallazgo sin fuente (URL o fichero + fecha) se descarta; observación e inferencia nunca van en la misma casilla.

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
## Foco de esta iteración   (función observable elegida en el Paso 0)
## Superficies
## Pantallas        (tabla: pantalla | propósito | estados | notas)
## Flujos           (uno por sección, con casos límite)
## Modelo de datos  (entidades, relaciones, invariantes)
## Evidencia        (tabla con el formato de templates/evidence.md: Fuente · Observación · Inferencia · Confianza · Límites)
## Mapa · Límites · Desconocidos   (qué cubre esta evidencia, hasta dónde llega, qué falta)
## Fuera de alcance (qué y por qué)
## Tamaño           (flujo | talla | riesgo)
## Fuentes          (URLs públicas usadas y fecha)
## Revisiones       (fechas en las que se refinó este recon, sin borrar lo anterior)
```

`replica/features.csv` y `replica/screens/` con tus capturas.

## Checklist

- [ ] Arriba del todo está la función observable de esta iteración (Paso 0).
- [ ] Si `recon.md` ya existía, se ha refinado: no se ha rehecho ni se han duplicado hallazgos.
- [ ] Cada hallazgo clave tiene fila en la tabla de evidencia con las 5 columnas (fuente, observación, inferencia, confianza, límites).
- [ ] Ningún hallazgo `THIN` se usa como argumento; ninguno con confianza `high` tiene "Límites" vacío.
- [ ] Cada flujo tiene al menos 3 casos límite.
- [ ] Cada pantalla tiene estados de vacío y error definidos.
- [ ] Invariantes escritas como frases verificables.
- [ ] `out_of_scope` justificado, no escondido.
- [ ] Capturas propias o públicas, ninguna de pago.
- [ ] Textos de UI descritos con tus palabras, no copiados.

## No hagas

Rellenar features que no has visto funcionar, ni asumir que "seguro que tiene X". Si no lo has visto, no está. Tampoco rehacer desde cero un recon ya guardado, ni mezclar observación e inferencia en la misma casilla, ni borrar desconocidos porque molesten.
