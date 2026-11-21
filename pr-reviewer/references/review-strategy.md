# Estrategia de revisión de un PR

## Qué se busca en una revisión

| Dimensión | Pregunta | Señal en el diff |
|---|---|---|
| Corrección | ¿El cambio hace lo que dice? | Código nuevo, tests que lo cubren |
| Riesgo | ¿Qué se rompe si falla? | Ruta sensible, tamaño, dependencias |
| Alcance | ¿Entra algo que no toca? | Ficheros ajenos, refactors oportunistas |
| Evidencia | ¿Cómo lo sabemos? | Test, reproducción, medición |
| Reversibilidad | ¿Se puede deshacer? | Migración, cambio de contrato, flag |

Una revisión sin evidencia es una opinión. El informe debe poder responder «¿qué se miró y qué no?».

## Orden de trabajo

1. **Contexto**: leer la descripción del PR y el diff de tests antes que el de producción.
2. **Riesgo**: identificar los ficheros caros antes de leerlos en detalle.
3. **Orden**: seguir las dependencias, no el orden del diff.
4. **Reparto**: asignar por ruta con dueño claro; dos revisores en rutas sensibles.
5. **Cierre**: consolidar hallazgos y declarar lo no ejecutado.

## Presupuesto

| Tamaño del PR | Lectura | Revisores |
|---|---|---|
| Hasta 200 líneas | Una pasada completa | 1 |
| 200–400 líneas | Por oleadas, 2 sesiones | 1–2 |
| Más de 400 líneas | Partir antes de revisar | 2 |

El presupuesto no es una regla de estilo: un PR que no cabe en una sesión se aprueba por cansancio.

## Qué NO se hace

- Aprobar porque los tests pasan: los tests no cubren lo que no se escribió.
- Reescribir el PR en la revisión: se propone, no se secuestra.
- Marcar `not_run` como limpio: el silencio no es evidencia.
- Cambiar severidades ajenas al consolidar.
