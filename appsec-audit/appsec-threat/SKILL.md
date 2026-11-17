---
name: appsec-threat
description: >
  Modelo de amenazas de un sistema real: activos, actores, flujos de datos y
  límites de confianza explícitos, casos de abuso priorizados y cada amenaza
  mapeada a OWASP Top 10 2025, a los capítulos de ASVS 5.0 y a las clases del
  catálogo de ataque. Úsala antes de auditar código, al diseñar una función
  nueva, al integrar un tercero o cuando pidan qué puede salir mal, dónde está
  la frontera de confianza y qué control lo cubre.
  English: build a threat model with trust boundaries and abuse cases, each
  threat mapped to OWASP 2025 and ASVS 5.0 chapters.
---

# AppSec · Modelo de amenazas

Un modelo de amenazas no es una lista de miedos: es el mapa de **quién puede tocar qué dato, cruzando qué frontera y con qué control**. Sin ese mapa, la auditoría revisa código sin saber qué duele si falla.

## Precondiciones

- Alcance y activos de `appsec-recon`, o un diseño que revisar antes de escribirlo.
- Una frase de negocio que diga qué se pierde si el sistema falla: dinero, datos personales, disponibilidad, reputación.
- Autorización del propietario, igual que en el resto del paquete.

## Método

1. **Activos.** Qué merece protección y con qué valor: datos personales, credenciales, claves, saldos, integridad de configuración, disponibilidad.
2. **Actores.** Anónimo, usuario autenticado, otro inquilino, soporte, insider, servicio de terceros, atacante con acceso al pipeline. Cada uno con su capacidad real, no la teórica.
3. **Límites de confianza.** Cada flecha que cruza de una zona a otra: navegador → API, API → base de datos, cola → worker, app → proveedor, CI → producción, agente → herramienta. En cada frontera se anota qué se valida y dónde.
4. **Flujos de datos.** Por activo, el recorrido concreto y las transformaciones. Un flujo que no cruza ninguna frontera no necesita control nuevo.
5. **Casos de abuso.** Por límite y actor, la acción concreta que rompe una garantía. Se escribe como historia corta, no como CWE.
6. **Prioridad.** Impacto sobre el activo por probabilidad de la ruta; lo que no tiene ruta todavía queda como hipótesis, no como riesgo aceptado.
7. **Mapeo y unidades.** Cada caso de abuso se etiqueta con categoría OWASP 2025, capítulo ASVS 5.0 y clase del catálogo, y se da de alta en el ledger.

## Mapeo

Las tablas de correspondencia viven en [`../references/threat-model.md`](../references/threat-model.md): OWASP Top 10 2025 completo, ASVS 5.0 con sus 17 capítulos y las preguntas que convierten cada límite en controles verificables.

El catálogo de clases de ataque, con CWE, OWASP y capítulo ASVS por clase, está en [`../references/attack-classes.md`](../references/attack-classes.md). La clase elegida es la que usa el ledger:

```bash
py appsec-audit/scripts/ledger.py add <dir>/.appsec-audit/coverage-ledger.json \
  --surface "POST /orders" --subsystem checkout --class access-control --owner appsec-threat
```

## Reglas duras

- Una frontera sin control declarado es un hallazgo de diseño, aunque no haya código que lo demuestre: se marca `needs_validation` con el dato que falta.
- No se inventan actores con capacidades que el sistema no concede; si no hay ruta, se dice.
- El mapeo OWASP/ASVS describe la familia, no la severidad: una amenaza en un panel interno no pesa igual que en una API pública.
- El modelo se escribe antes de auditar y se actualiza cuando aparece una superficie nueva; nunca se redacta después para justificar el informe.

## Gate de salida

- Activos, actores y límites de confianza dibujados y nombrados.
- Cada límite con su control y su pregunta de verificación.
- Cada caso de abuso con OWASP 2025, ASVS 5.0 y clase del catálogo.
- Hipótesis separadas de amenazas con ruta demostrada.
- Unidades dadas de alta en el ledger para que `gaps --strict` las exija.

## Handoff

Entrega a `appsec-code`, `appsec-infra` y `appsec-llm` los casos de abuso que caen en su superficie, y a `appsec-deps` las dependencias y terceros que cruzan una frontera. `appsec-report` recibe el mapeo para que cada hallazgo cite su amenaza; si el sistema cambia de diseño, el modelo se rehace antes de volver a auditar.
