# Contrato de hallazgos y estado de los checks

## Por qué un estado explícito

Un informe con cero hallazgos puede significar dos cosas opuestas: «se revisó y está limpio» o «no se llegó a revisar». Si no se distinguen, el PR se aprueba por omisión. Por eso cada comprobación lleva su estado.

| Estado | Significado | Efecto en el informe |
|---|---|---|
| `ran` | Se ejecutó y estos son sus hallazgos | Cuenta como revisado |
| `not_run` | No se ejecutó (sin tiempo, sin credenciales, pipeline cortado) | Aparece en `not_run`, nunca como limpio |
| `skipped` | Se decidió no ejecutarla | Aparece en `not_run` con su motivo |

Un informe de entrada sin `status` se normaliza a `not_run`: la ausencia de dato no es evidencia de limpieza.

## Forma del hallazgo

| Campo | Tipo | Obligatorio |
|---|---|---|
| `file` | ruta relativa | sí |
| `line` | entero ≥ 1 | sí |
| `rule` | identificador estable | sí |
| `severity` | `low`, `medium`, `high` | sí |
| `message` | qué pasa, en una línea | sí |
| `fix` | qué hacer | sí |

La consolidación añade `checks` (orígenes) y `duplicates` (cuántas veces apareció) sin tocar la severidad de origen.

## Deduplicación

Clave `(file, line, rule)`. Al repetirse:

1. se conserva la severidad **más alta**;
2. se suman los orígenes;
3. se incrementa `duplicates`;
4. se mantiene el primer mensaje, que suele ser el más específico.

## Checks exigidos

`--require security` convierte «no ejecutado» en fallo del informe con la regla `check-no-ejecutado` y salida `1`. Es la forma de impedir que un PR se apruebe porque la comprobación importante no llegó a correr.

## Frontera con el contrato del repositorio

`contracts/findings/` normaliza la salida nativa de los auditores. `pr-findings` no reetiqueta esos hallazgos como propios: los conserva con su origen para que la trazabilidad no se pierda.
