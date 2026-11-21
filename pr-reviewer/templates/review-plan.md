# Plan de revisión · {{proyecto}}

- **PR:** {{numero o rama}}
- **Autor:** {{nombre}}
- **Fecha:** {{AAAA-MM-DD}}
- **Presupuesto:** {{N}} ficheros · {{N}} líneas

## Oleadas de lectura

| Oleada | Ficheros | Por qué primero | Revisor |
|---|---|---|---|
| 1 | {{rutas sin dependencias en el diff}} | Base de la que dependen las demás | {{nombre}} |
| 2 | {{rutas que importan a la oleada 1}} | Ya se leyó su base | {{nombre}} |
| 3 | {{ciclos y ficheros sueltos}} | Se leen juntos o aparte | {{nombre}} |

## Riesgo por fichero

| Fichero | Severidad | Señal | Acción |
|---|---|---|---|
| {{ruta}} | `high` | {{dominio sensible, secreto, dependencia}} | {{revisión dedicada / delegar}} |
| {{ruta}} | `medium` | {{tamaño, supresión}} | {{leer con lupa}} |

## Reparto

| Revisor | Ficheros | Carga | Capacidad |
|---|---|---|---|
| {{nombre}} | {{N}} | {{N}} | {{N}} |

## Sin revisar

| Check | Estado | Motivo | Responsable |
|---|---|---|---|
| {{security}} | `not_run` | {{pipeline cortado}} | {{nombre}} |

> Ningún `not_run` se presenta como limpio: si no se ejecutó, se dice.
