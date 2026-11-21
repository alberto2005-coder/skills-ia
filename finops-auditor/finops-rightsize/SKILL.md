---
name: finops-rightsize
description: >
  Propone recomendaciones de cambio de tamaño (right-sizing) para instancias de cómputo y bases
  de datos basadas en métricas de rendimiento real. Úsala cuando instancias y bases de datos
  estén sobredimensionadas respecto a lo que consumen. English: propose rightsizing with
  savings, risk and a verification metric.
license: MIT
metadata:
  package: finops-auditor
  version: "1.4.1"
  author: "Alberto Ortiz"
---

# FinOps Right-Sizing

## Objetivo

Optimizar la arquitectura de costes dimensionando correctamente los recursos sobreaprovisionados, con una recomendación por recurso y el ahorro mensual que implica.

## Instrucciones de ejecución

1. Parte de los recursos marcados con baja utilización en el escaneo previo; no se recomienda cambiar el tamaño de un recurso que no aparece allí.
2. Consulta las reglas de precios estándar en [`cloud-pricing-rules.md`](../references/cloud-pricing-rules.md).
3. Propón el cambio de tier (por ejemplo de `t3.xlarge` a `t3.medium`) y calcula el ahorro porcentual exacto sobre el coste declarado.
4. Ordena el plan por ahorro mensual descendente y separa lo que requiere ventana de mantenimiento de lo que se aplica en caliente.

## Formato de cada recomendación

| Campo | Contenido |
|---|---|
| `recurso` | Identificador del inventario |
| `actual` | Tier o clase actual |
| `propuesto` | Tier o clase destino |
| `ahorro_mensual` | Coste actual menos coste propuesto |
| `riesgo` | `bajo`, `medio` o `alto`, con la razón |
| `verificación` | Métrica y ventana que hay que vigilar tras el cambio |

## Límites

- No aplica cambios: propone y deja la ejecución a quien tenga acceso al proveedor.
- No recomienda bajar de tier recursos con CPU media por encima del 25 % ni sin métricas de al menos 14 días.
- Los precios salen del inventario o de la tabla de referencia; si falta el precio destino, la recomendación se marca como incompleta.

## Gate de salida

- Cada recomendación enlaza un recurso real del inventario y una regla de la referencia.
- Toda recomendación tiene ahorro calculado, riesgo y métrica de verificación.
- Los recursos que no se recomienda tocar aparecen con su motivo.
- El plan está ordenado por ahorro y no incluye cambios sin respaldo en métricas.

## Handoff

Entrega al maestro el plan de redimensionado, el ahorro total mensual y los recursos descartados con su razón, para que el informe ejecutivo separe ahorro confirmado de ahorro potencial.
