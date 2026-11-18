# FinOps Auditor

> Auditoría de costes cloud sobre un inventario JSON: recursos huérfanos, cómputo sobreaprovisionado, derechosizing y ahorro mensual con scripts deterministas y sin red.
> Cloud cost audit over a JSON inventory: orphaned resources, overprovisioned compute, rightsizing and monthly savings with deterministic, offline scripts.

[Español](#español) · [English](#english)

---

## Español

### Índice
1. Propósito
2. Modos
3. Arquitectura
4. Rúbrica
5. Herramientas
6. Instalación y uso
7. Tests
8. Límites

### Propósito
`finops-auditor` convierte un inventario de recursos cloud —con su coste mensual, su estado y su utilización— en tres cosas: el desperdicio estimado, una recomendación de redimensionado por recurso y un informe ejecutivo con la puntuación FinOps. No consulta la factura del proveedor ni métricas en vivo: mide lo que el inventario declara y separa lo medido de lo supuesto.

### Modos
El maestro no usa flags: el modo lo fija el alcance de la petición.

| Modo | Fases que ejecuta | Entrega |
|---|---|---|
| **Escaneo** | Fase 1 con `finops-scan` | JSON del analizador con coste total, desperdicio y hallazgos |
| **Informe** | Fases 1-3: escaneo, derechosizing y plantilla | Informe Markdown con ahorro, riesgos y recursos descartados |

El modo Escaneo sirve para responder «cuánto estamos tirando» en una sola pasada. El modo Informe es el que se entrega a dirección: añade el plan de redimensionado y separa ahorro confirmado de ahorro potencial.

### Arquitectura
Un maestro y seis sub-skills con assets compartidos (`references/`, `scripts/`, `templates/`). Se instala la carpeta completa.

| Sub-skill | Qué hace |
|---|---|
| `finops-auditor` | Maestro: elige el modo, ordena las fases y firma el informe |
| `finops-scan` | Inventario, recursos ociosos, subutilización y anomalías de coste |
| `finops-rightsize` | Redimensionado por recurso con ahorro, riesgo y métrica de verificación |
| `finops-llm-scan` | Coste de llamadas a LLM: `max_tokens`, modelo caro como clasificador y bucles sin tope |
| `finops-infra-scan` | Terraform y Kubernetes: buckets sin ciclo de vida, logs sin retención y contenedores sin límites |
| `finops-ci-opt` | GitHub Actions: caché de dependencias y ejecución duplicada de push y pull_request |
| `finops-diff` | Coste entre dos inventarios con guardrails `--max-increase`, `--max-percent` y `--budget` |

`finops-scan` entrega el JSON de hallazgos a `finops-rightsize`; el maestro recibe ambos y el informe. Los umbrales viven en [`cloud-pricing-rules.md`](../finops-auditor/references/cloud-pricing-rules.md) y la plantilla en [`report-template.md`](../finops-auditor/templates/report-template.md).

### Rúbrica
La puntuación es determinista: `finops_score = max(0, 100 − desperdicio / coste total × 100)`, redondeada hacia abajo. Sin coste inventariado la puntuación es 100 y no se inventan ahorros.

| Regla | Señal en el inventario | Desperdicio que suma |
|---|---|---|
| Recurso huérfano | `status: unattached` o `utilization: 0` | 100 % de su coste mensual |
| Cómputo subutilizado | `type: compute` con `avg_cpu_utilization` < 10 | 50 % de su coste mensual |
| Subutilización moderada | CPU media entre 10 % y 25 % | No puntúa: se reporta para revisión |

El 50 % de la segunda regla es una convención declarada —bajar de tier a la mitad—, no una medición del proveedor. Cada hallazgo lleva recurso, regla y ahorro potencial, para que el número se pueda recalcular a mano.

### Herramientas

```bash
py finops-auditor/scripts/finops_analyzer.py --input inventory.json
py finops-auditor/scripts/llm_cost_scan.py --path src/ --fail-on medium
py finops-auditor/scripts/infra_cost_scan.py --path infra/ --json
py finops-auditor/scripts/ci_cost_scan.py --path .github/workflows/ --json
py finops-auditor/scripts/cost_diff.py --before antes.json --after despues.json --max-increase 100 --budget 5000 --json
```

Salida JSON con `total_monthly_cost`, `total_estimated_waste`, `finops_score` y la lista de `findings`:

```json
{
  "total_monthly_cost": 360.0,
  "total_estimated_waste": 110.0,
  "finops_score": 69,
  "findings": [
    {"id": "eip-dead", "type": "network", "issue": "Recurso huérfano / sin uso", "potential_savings": 10.0}
  ]
}
```

Códigos de salida: `0` análisis correcto · `1` entrada ilegible o JSON inválido, con `{"error": "..."}`. Solo stdlib, sin dependencias y sin llamadas de red.

### Instalación y uso
Copia la carpeta `finops-auditor/` completa. Ejemplos de petición:
- «Audita los costes de esta infraestructura y dime cuánto desperdiciamos».
- «Detecta volúmenes desasociados e IPs elásticas sin usar».
- «Propón derechosizing para las instancias con CPU por debajo del 10 %».
- «Prepara el informe mensual de ahorro para dirección».

### Tests

```bash
uv run python -m unittest discover -s finops-auditor/tests -t finops-auditor/tests
```

Dos pruebas propias sobre el analizador (y 26 en el paquete, con las de los escáneres y el diff): una infraestructura limpia puntúa 100 sin desperdicio y una con un recurso huérfano y una instancia al 3 % detecta los dos hallazgos y baja la nota.

### Límites
Solo analiza el inventario que se le entrega: no consulta facturación ni métricas en vivo, no aplica cambios y no convierte monedas. La estimación de subutilización asume una bajada de tier del 50 %, y un recurso sin precio o sin métricas se declara ausente en lugar de estimarse. No sustituye a la herramienta de costes del proveedor; la complementa con una segunda lectura reproducible.

---

## English

### Index
1. Purpose
2. Modes
3. Architecture
4. Rubric
5. Tools
6. Install and use
7. Tests
8. Limits

### Purpose
`finops-auditor` turns a cloud resource inventory —monthly cost, status and utilisation— into three things: estimated waste, a rightsizing recommendation per resource and an executive report with the FinOps score. It never queries the provider's bill or live metrics: it measures what the inventory states and separates measured from assumed.

### Modes
The master uses no flags: the request's scope sets the mode.

| Mode | Phases it runs | Deliverable |
|---|---|---|
| **Scan** | Phase 1 with `finops-scan` | Analyzer JSON with total cost, waste and findings |
| **Report** | Phases 1-3: scan, rightsizing and template | Markdown report with savings, risks and discarded resources |

Scan mode answers "how much are we wasting" in one pass. Report mode is the one you hand to leadership: it adds the rightsizing plan and separates confirmed from potential savings.

### Architecture
One master and six sub-skills sharing assets (`references/`, `scripts/`, `templates/`). The whole folder is installed.

| Sub-skill | What it does |
|---|---|
| `finops-auditor` | Master: picks the mode, orders the phases and signs the report |
| `finops-scan` | Inventory, idle resources, underutilisation and cost anomalies |
| `finops-rightsize` | Per-resource rightsizing with savings, risk and a verification metric |
| `finops-llm-scan` | LLM call cost: `max_tokens`, expensive model as classifier and unbounded loops |
| `finops-infra-scan` | Terraform and Kubernetes: buckets without lifecycle, logs without retention and containers without limits |
| `finops-ci-opt` | GitHub Actions: dependency cache and duplicated push and pull_request runs |
| `finops-diff` | Cost between two inventories with `--max-increase`, `--max-percent` and `--budget` guardrails |

`finops-scan` hands the findings JSON to `finops-rightsize`; the master receives both plus the report. Thresholds live in [`cloud-pricing-rules.md`](../finops-auditor/references/cloud-pricing-rules.md) and the template in [`report-template.md`](../finops-auditor/templates/report-template.md).

### Rubric
The score is deterministic: `finops_score = max(0, 100 − waste / total cost × 100)`, rounded down. With no inventoried cost the score is 100 and no savings are invented.

| Rule | Signal in the inventory | Waste it adds |
|---|---|---|
| Orphaned resource | `status: unattached` or `utilization: 0` | 100 % of its monthly cost |
| Underutilised compute | `type: compute` with `avg_cpu_utilization` < 10 | 50 % of its monthly cost |
| Moderate underutilisation | Average CPU between 10 % and 25 % | Not scored: reported for review |

The 50 % in the second rule is a declared convention —a one-tier drop— not a provider measurement. Every finding carries resource, rule and potential savings so the number can be recomputed by hand.

### Tools

```bash
py finops-auditor/scripts/finops_analyzer.py --input inventory.json
py finops-auditor/scripts/llm_cost_scan.py --path src/ --fail-on medium
py finops-auditor/scripts/infra_cost_scan.py --path infra/ --json
py finops-auditor/scripts/ci_cost_scan.py --path .github/workflows/ --json
py finops-auditor/scripts/cost_diff.py --before antes.json --after despues.json --max-increase 100 --budget 5000 --json
```

JSON output with `total_monthly_cost`, `total_estimated_waste`, `finops_score` and the `findings` list:

```json
{
  "total_monthly_cost": 360.0,
  "total_estimated_waste": 110.0,
  "finops_score": 69,
  "findings": [
    {"id": "eip-dead", "type": "network", "issue": "Orphaned / unused resource", "potential_savings": 10.0}
  ]
}
```

Exit codes: `0` analysis ok · `1` unreadable input or invalid JSON, with `{"error": "..."}`. Stdlib only, no dependencies, no network calls.

### Install and use
Copy the whole `finops-auditor/` folder. Example requests:
- "Audit the cost of this infrastructure and tell me how much we waste".
- "Find unattached volumes and unused elastic IPs".
- "Propose rightsizing for instances under 10 % CPU".
- "Prepare the monthly savings report for leadership".

### Tests

```bash
uv run python -m unittest discover -s finops-auditor/tests -t finops-auditor/tests
```

Two tests over the analyzer (26 in the package, including the scanners and the diff): a clean infrastructure scores 100 with zero waste, and one with an orphaned resource plus an instance at 3 % finds both findings and lowers the score.

### Limits
It only reads the inventory it is given: no billing or live metrics, it applies no changes and converts no currencies. The underutilisation estimate assumes a 50 % tier drop, and a resource without price or metrics is reported as missing instead of estimated. It does not replace the provider's cost tool; it complements it with a reproducible second reading.
