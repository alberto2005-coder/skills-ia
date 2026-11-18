---
name: finops-scan
description: Escanea y recopila el inventario completo de recursos cloud (instancias, bases de datos, almacenamiento, IPs) y detecta desperdicios y anomalías de coste.
license: MIT
metadata:
  package: finops-auditor
  version: "1.3.0"
---

# FinOps Scan

## Objetivo

Identificar recursos ociosos, volúmenes de almacenamiento sin adjuntar, direcciones IP elásticas sin asociar e instancias con una utilización de CPU inferior al 10 % durante periodos prolongados, con el coste mensual de cada uno.

## Instrucciones de ejecución

1. Recibe un JSON con el inventario de recursos, sus costes mensuales, su estado y su utilización media.
2. Ejecuta el analizador determinista desde la raíz del repositorio:

```bash
py finops-auditor/scripts/finops_analyzer.py --input <ruta>/resources.json
```

3. Contrasta cada hallazgo con los umbrales de [`cloud-pricing-rules.md`](../references/cloud-pricing-rules.md): huérfano al 100 % de su coste y subutilización de cómputo con CPU media por debajo del 10 %.
4. Guarda la salida tal cual: es la entrada de `finops-rightsize` y la base del informe del maestro.

## Qué se cuenta como desperdicio

| Regla | Señal en el inventario | Desperdicio estimado |
|---|---|---|
| Recurso huérfano | `status: unattached` o `utilization: 0` | 100 % del coste mensual |
| Cómputo subutilizado | `type: compute` con `avg_cpu_utilization` < 10 | 50 % del coste mensual |
| Subutilización moderada | CPU media entre 10 % y 25 % | No se punúa: se reporta para revisión |

## Límites

- Solo analiza el JSON que se le entrega: no consulta APIs de facturación ni métricas en vivo.
- Un recurso sin `monthly_cost` se reporta como dato ausente, nunca se estima su precio.
- La estimación de ahorro de cómputo asume bajar de tier un 50 %; es una convención declarada, no una medición del proveedor.

## Gate de salida

- Inventario normalizado con `id`, `type`, `monthly_cost`, `status` y `utilization` cuando existan.
- Cada hallazgo tiene recurso, regla disparada y ahorro potencial en la moneda del inventario.
- La salida del analizador está guardada y es reproducible byte a byte con el mismo JSON.
- Los recursos sin métricas quedan declarados como no medidos, no se suponen sanos.

## Handoff

Entrega a `finops-rightsize` el JSON de hallazgos y el inventario completo, y al maestro la ruta de ambos y el coste total mensual inventariado. Si no hay ningún hallazgo, el handoff lo dice explícitamente para que el informe no invente ahorros.
