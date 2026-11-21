---
name: pr-findings
description: >
  Consolida los informes de varias comprobaciones o skills en un único conjunto de hallazgos,
  deduplica por fichero, línea y regla y conserva el estado real de cada check: lo no ejecutado
  queda como not_run y nunca se presenta como limpio.
  Úsala cuando haya que unir resultados de varios revisores, agentes o linters en un informe de PR.
  English: merge several checks' reports into one finding set, deduplicate by file, line and rule,
  and keep each check's real status — anything not run stays not_run, never clean.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py pr-reviewer/scripts/review_findings.py *)
  - Bash(python3 pr-reviewer/scripts/review_findings.py *)
license: MIT
metadata:
  package: pr-reviewer
  version: "1.0.0"
  author: "Alberto Ortiz"
---

# PR Reviewer · Consolidación de hallazgos

Un informe que dice «sin hallazgos» cuando tres comprobaciones no llegaron a correr es peor que no tener informe. Esta sub-skill une los resultados, elimina duplicados y deja escrito qué se ejecutó, qué no y qué falta.

## Cuándo se usa

- Varias skills o agentes devolvieron JSON y hay que entregar un solo informe.
- El pipeline se cortó y hay que distinguir «limpio» de «no ejecutado».
- Dos comprobaciones señalan el mismo fichero y la misma línea y sobra ruido.

## Alcance y fronteras

| Comprueba | No comprueba |
|---|---|
| Estado de cada check (`ran`, `not_run`, `skipped`) | Que el check esté bien diseñado |
| Duplicados por fichero, línea y regla | Si el hallazgo es un falso positivo |
| Severidad máxima por duplicado | La severidad correcta de cada origen |
| Checks exigidos que no corrieron | Que el pipeline se pueda reintentar |

La consolidación **no repara** el pipeline: si un check no corrió, el informe lo dice y, con `--require`, el comando falla. Nunca se rellena un check ausente con cero hallazgos.

## Método

1. **Cargar** cada informe: `check`, `status` y `findings`.
2. **Normalizar** el estado: un informe sin estado se trata como `not_run`, no como `ran`.
3. **Deduplicar** por `(file, line, rule)`, conservando la severidad más alta y anotando el origen.
4. **Ordenar** por severidad, fichero y línea.
5. **Comparar** contra `--require`: si un check exigido no está en `ran`, el resultado es un fallo.
6. **Escribir** el informe con `checks`, `not_run`, `findings` y totales por severidad.

## Comandos

```bash
py pr-reviewer/scripts/review_findings.py --input a.json b.json --json
py pr-reviewer/scripts/review_findings.py --input a.json b.json --require security --fail-on low
```

`--input` admite varios informes; `--require` puede repetirse; `--fail-on` decide el umbral de severidad. Códigos: `0` sin hallazgos sobre el umbral y todos los checks exigidos ejecutados, `1` umbral superado o check exigido sin ejecutar, `2` entrada ilegible.

## Formato de entrada

```json
{"check": "security", "status": "ran", "findings": [
  {"file": "src/auth.py", "line": 42, "rule": "secreto-expuesto", "severity": "high",
   "message": "clave en el código", "fix": "mover a un secreto"}
]}
```

`status` admite `ran`, `not_run` y `skipped`. Los dos últimos se copian al informe como tales.

## Reglas

- Lo ausente es `not_run`, nunca cero: el silencio no es evidencia.
- Un duplicado no se borra: se conserva una vez con el origen y el recuento.
- La severidad de origen no se rebaja al consolidar.
- Un `--require` que no corrió es un fallo del informe, no una advertencia.

## Gate de salida

- Informe con todos los checks de entrada y su estado.
- Cero checks exigidos en estado distinto de `ran`.
- Hallazgos ordenados, deduplicados y con severidad conservada.
- Totales por severidad y lista explícita de `not_run`.

## Handoff

El informe consolidado se entrega a quien aprueba el PR, y cada hallazgo conserva su origen para volver a la skill que lo produjo: seguridad a `appsec-audit`, pruebas a `test-architect`, contrato a `api-contract-guard`.
