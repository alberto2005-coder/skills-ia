# Informe de revisión · PR {{numero}}

## Veredicto

{{aprobar / pedir cambios / bloquear}} — {{una línea con el motivo principal}}.

## Lo revisado

| Fichero | Severidad | Qué se miró | Resultado |
|---|---|---|---|
| {{ruta}} | `high` | {{corrección, seguridad, migración}} | {{ok / hallazgo}} |

## Hallazgos

| Severidad | Fichero:línea | Regla | Qué pasa | Arreglo |
|---|---|---|---|---|
| `high` | {{ruta}}:{{línea}} | {{regla}} | {{mensaje}} | {{fix}} |

## Lo no ejecutado

| Check | Estado | Motivo | Quién lo cierra |
|---|---|---|---|
| {{coverage}} | `not_run` | {{sin credenciales}} | {{nombre}} |

> Este informe no declara limpio nada que no se haya ejecutado.

## Pendiente antes de mergear

- [ ] {{hallazgo high resuelto o aceptado con motivo}}
- [ ] {{check exigido ejecutado}}
- [ ] {{cobertura de la ruta sensible}}
