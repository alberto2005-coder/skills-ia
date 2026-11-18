---
name: finops-auditor
description: Auditoría integral de costes Cloud, detección de recursos huérfanos, instancias sobreaprovisionadas y recomendaciones de optimización FinOps con scripts deterministas.
license: MIT
metadata:
  package: finops-auditor
  version: "1.1.0"
---

# FinOps Auditor Master

Orquesta el análisis de costes, uso de recursos y eficiencia financiera en infraestructuras cloud (AWS, GCP, Azure, Kubernetes) sin dependencias externas.

## Protocolo de Ejecución
1. **Fase 1 (Escaneo)**: Ejecuta `finops-scan` para inventariar recursos, detectar anomalías y calcular el desperdicio estimado.
2. **Fase 2 (Derechizado / Right-sizing)**: Ejecuta `finops-rightsize` para proponer instancias óptimas y planes de ahorro (Reserved Instances / Savings Plans).
3. **Fase 3 (Generación de Informe)**: Valida con el motor de reglas y genera el informe ejecutivo en Markdown utilizando las plantillas de `templates/`.

## Gate de salida
- Inventario o hallazgos recibidos por escrito, con la ruta del JSON y el coste total mensual.
- Puntuación FinOps calculada con la rúbrica del paquete y cada hallazgo con recurso, regla y ahorro.
- Ahorro confirmado separado del potencial, y recursos sin métricas o sin precio declarados como no medidos.
- Informe en Markdown con la plantilla del paquete y sin cifras que no salgan del inventario.

## Handoff
Entrega el informe y las rutas de los JSON al solicitante. Si solo se pidió el escaneo, cierra con el JSON de `finops-scan` y di que el derechosizing queda pendiente. Si el inventario no trae precios, el informe abre con ese vacío en lugar de estimar costes.
