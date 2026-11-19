---
name: finops-auditor
description: >
  Auditoría integral de costes Cloud, detección de recursos huérfanos, instancias
  sobreaprovisionadas y recomendaciones de optimización FinOps con scripts deterministas. Úsala
  cuando la factura cloud haya subido o cuando haya que justificar el gasto antes de aprobarlo.
  English: audit cloud spend, orphaned resources and overprovisioned instances with
  deterministic scripts.
license: MIT
metadata:
  package: finops-auditor
  version: "1.4.0"
---

# FinOps Auditor Master

Orquesta el análisis de costes, uso de recursos y eficiencia financiera en infraestructuras cloud (AWS, GCP, Azure, Kubernetes) sin dependencias externas.

## Protocolo de Ejecución

1. **Fase 1 (Escaneo)**: `finops-scan` inventaría los recursos del JSON, detecta ociosos y calcula el desperdicio.
2. **Fase 2a (Código con IA)**: `finops-llm-scan` revisa llamadas al modelo sin tope de tokens, modelos caros y prompts sin caché.
3. **Fase 2b (Infraestructura)**: `finops-infra-scan` revisa Terraform y manifiestos Kubernetes: buckets sin ciclo de vida, logs sin retención y contenedores sin límites.
4. **Fase 2c (CI)**: `finops-ci-opt` revisa los workflows de GitHub Actions: falta de caché y doble ejecución de `push` y `pull_request`.
5. **Fase 3 (Derechizado)**: `finops-rightsize` propone instancias óptimas y planes de ahorro (Reserved Instances / Savings Plans).
6. **Fase 3b (Diff)**: `finops-diff` compara dos inventarios y rompe el pipeline si el aumento supera los guardrails acordados.
7. **Fase 4 (Informe)**: valida con el motor de reglas y genera el informe ejecutivo en Markdown con `templates/report-template.md`.

El modo lo fija el alcance: si solo se pide el inventario, basta `finops-scan`; si se pide revisar un repositorio, entran las tres fases 2; el informe completo exige todas.

## Sub-skills

| Sub-skill | Qué aporta |
|---|---|
| `finops-scan` | Inventario, huérfanos, subutilización y anomalías de coste |
| `finops-llm-scan` | Coste de IA: tokens sin límite, modelos caros, bucles y prompts sin caché |
| `finops-infra-scan` | Coste de Terraform y Kubernetes |
| `finops-ci-opt` | Coste de CI: caché y concurrencia |
| `finops-rightsize` | Redimensionado con ahorro, riesgo y verificación |
| `finops-diff` | Coste entre dos inventarios con guardrails de CI |

## Reglas

- Toda cifra sale de un fichero o de la salida de un script del paquete; lo que no se pudo medir se declara.
- Los escáneres son estáticos: no ejecutan el proyecto, no instalan dependencias y no salen a la red.
- El ahorro se separa en confirmado (medido) y potencial (convención de bajada de tier).

## Gate de salida

- Inventario o hallazgos recibidos por escrito, con la ruta del JSON y el coste total mensual.
- Puntuación FinOps calculada con la rúbrica del paquete y cada hallazgo con recurso, regla y ahorro.
- Ahorro confirmado separado del potencial, y recursos sin métricas o sin precio declarados como no medidos.
- Informe en Markdown con la plantilla del paquete y sin cifras que no salgan de los JSON.

## Handoff

Entrega el informe y las rutas de los JSON al solicitante. Si solo se pidió el escaneo, cierra con el JSON de `finops-scan` y di que el derechosizing queda pendiente. Si el inventario no trae precios, el informe abre con ese vacío en lugar de estimar costes.
