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