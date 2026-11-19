#!/usr/bin/env python3
import json
import argparse
import sys

def _cpu(resource):
    """CPU media del inventario, o None si falta o no es numérica."""
    value = resource.get("avg_cpu_utilization", 50)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def analyze_resources(data):
    total_cost = 0.0
    waste_cost = 0.0
    findings = []

    for resource in data.get("resources", []):
        cost = resource.get("monthly_cost", 0.0)
        total_cost += cost
        
        # Regla 1: Recursos huérfanos (volúmenes desasociados, IPs elásticas sin usar)
        if resource.get("status") == "unattached" or resource.get("utilization", 100) == 0:
            waste_cost += cost
            findings.append({
                "id": resource.get("id"),
                "type": resource.get("type"),
                "issue": "Recurso huérfano / sin uso",
                "potential_savings": cost
            })
        
        # Regla 3: subutilización moderada (10%-25%). El SKILL prometía
        # reportarla sin puntuarla; antes no se emitía ninguna señal.
        elif resource.get("type") == "compute" and _cpu(resource) is not None \
                and 10 <= _cpu(resource) < 25:
            findings.append({
                "id": resource.get("id"),
                "type": resource.get("type"),
                "issue": "Subutilización moderada (CPU 10%-25%): revisar, no puntúa",
                "potential_savings": 0.0,
                "review": True,
            })

        # Regla 2: Sobreaprovisionamiento (CPU promedio < 10% en el último mes)
        elif _cpu(resource) is not None and _cpu(resource) < 10 and resource.get("type") == "compute":
            potential_saving = cost * 0.5 # Se asume bajada de tier (50% ahorro)
            waste_cost += potential_saving
            findings.append({
                "id": resource.get("id"),
                "type": resource.get("type"),
                "issue": "Sobreaprovisionado (CPU < 10%)",
                "potential_savings": potential_saving
            })

    score = max(0, int(100 - (waste_cost / total_cost * 100))) if total_cost > 0 else 100

    return {
        "total_monthly_cost": round(total_cost, 2),
        "total_estimated_waste": round(waste_cost, 2),
        "finops_score": score,
        "findings": findings
    }

def main():
    parser = argparse.ArgumentParser(description="Analizador determinista FinOps sin dependencias externas.")
    parser.add_argument("--input", required=True, help="Ruta al fichero JSON con el inventario de recursos.")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = analyze_resources(data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()