---
name: finops-infra-scan
description: >
  Revisa Terraform y manifiestos Kubernetes: buckets sin ciclo de vida, grupos de logs sin retención, bases de datos sin autoscaling y contenedores sin límites de CPU o memoria, con salida JSON.
license: MIT
metadata:
  package: finops-auditor
  version: "1.3.0"
---

# FinOps Infra Scan

## Objetivo

Detectar el coste que la infraestructura declarada genera por omisión: almacenamiento que nunca caduca, logs que se guardan para siempre, bases de datos que se sobreaprovisionan a mano y contenedores sin límites que consumen de más.

## Instrucciones de ejecución

1. Ejecuta el escáner sobre la carpeta de infraestructura:

```bash
py finops-auditor/scripts/infra_cost_scan.py --path <ruta> --json
```

2. Cada hallazgo apunta al bloque que lo provoca; corrige el fichero y vuelve a pasarlo.
3. Para CI, usa `--fail-on high` y deja los medios como aviso.

## Reglas

| Regla | Señal | Severidad |
|---|---|---|
| `s3-sin-ciclo-de-vida` | `aws_s3_bucket` sin `lifecycle_rule` | alta |
| `logs-sin-retencion` | `aws_cloudwatch_log_group` sin `retention_in_days` | media |
| `rds-sin-autoscaling` | `aws_db_instance` sin `storage_autoscaling` | media |
| `contenedor-sin-limites` | `containers:` sin `resources.limits` | media |

## Límites

- Reglas de texto sobre `.tf` y `.yaml`: no interpreta HCL ni plantillas, así que módulos externos y `for_each` quedan fuera.
- Solo cubre AWS en Terraform y Kubernetes genérico; GCP y Azure necesitan sus propias reglas.
- No traduce precios: mide patrones de desperdicio, no facturas.

## Gate de salida

- Hallazgos con fichero, línea, regla y severidad en JSON reproducible.
- Cada hallazgo trae el atributo que falta, listo para pegar en el bloque.
- Los proveedores y módulos no cubiertos quedan declarados en el informe.

## Handoff

Entrega a `finops-rightsize` los recursos de cómputo o base de datos marcados para ajustar tamaño, y a `finops-auditor` el recuento por severidad y las rutas revisadas.
