---
name: pr-reviewer
description: >
  Revisa un pull request con evidencia del diff: qué ficheros concentran el riesgo, cómo secuenciar
  su lectura, quién debe revisar cada ruta y cómo se consolidan los hallazgos de varias
  comprobaciones sin dar por limpio lo que no llegó a ejecutarse.
  Úsala cuando pidan revisar un PR, priorizar un diff grande, repartir la revisión entre personas
  o unir los resultados de varios revisores y agentes en un solo informe.
  English: review a pull request from its diff — per-file risk, reading order, reviewer routing
  and a consolidated report that keeps not-run checks explicitly not run.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py pr-reviewer/scripts/*)
  - Bash(python3 pr-reviewer/scripts/*)
license: MIT
metadata:
  package: pr-reviewer
  version: "1.0.0"
  author: "Alberto Ortiz"
---

# PR Reviewer

## Propósito

Convertir un diff en una **revisión que se puede defender**: qué se mira primero, en qué orden, quién lo mira y qué quedó sin mirar. El paquete lee el parche y el árbol; no ejecuta agentes, modelos ni la suite del proyecto, así que el resultado es el mismo en local y en CI.

## Flujo

1. **Riesgo** con `pr-risk`: rutas sensibles, tamaño, secretos añadidos y dependencias tocadas.
2. **Orden** con `pr-order`: dependencias entre los ficheros cambiados y oleadas de lectura.
3. **Reparto** con `pr-routing`: dueño por ruta, carga por revisor y rutas sin respaldo.
4. **Consolidación** con `pr-findings`: une los informes y conserva `not_run` para lo no ejecutado.
5. **Cerrar** con el informe: lo revisado, lo omitido y por qué, nunca «todo limpio» por omisión.

## Sub-skills

| Sub-skill | Qué hace |
|---|---|
| `pr-risk` | Puntúa cada fichero del diff por dominio sensible, tamaño, secretos y dependencias |
| `pr-order` | Ordena la lectura por dependencias y señala ciclos |
| `pr-routing` | Asigna revisores por glob, mide carga y detecta rutas sin dueño |
| `pr-findings` | Deduplica hallazgos y mantiene el estado real de cada comprobación |

## Fronteras

| No es de este paquete | Dónde vive |
|---|---|
| Profundidad de seguridad del código (sinks, CWE, explotación) | `appsec-audit` |
| Qué tests faltan o son inestables | `test-architect` |
| Rutas, SemVer y cobertura de autenticación de una API | `api-contract-guard` |
| Drift entre documentación y código | `docs-sync-engine` |
| Ejecutar linters, tests o agentes en vivo | El CI del proyecto auditado |

Este paquete **prioriza y consolida**; no sustituye al auditor que encuentra el fallo. Si un fichero sensible necesita análisis de seguridad, se delega y su resultado vuelve como hallazgo.

## Reglas

- Un fichero sin revisor asignado no es un fichero revisado: se nombra en el informe.
- Lo que no se ejecutó se escribe como `not_run`, jamás como cero hallazgos.
- El riesgo se explica con la señal que lo dispara, no con una nota sin motivo.
- El orden de lectura ahorra contexto: primero lo que otros ficheros importan.
- La consolidación no inventa severidades: conserva la del origen y marca los duplicados.

## Gate de salida

- Cada fichero del diff tiene severidad y motivo, o exclusión escrita.
- El orden de lectura cubre todos los ficheros, con ciclos señalados.
- Toda ruta del diff tiene dueño o aparece como `sin-dueno`.
- Informe con `checks` y su estado; ningún `not_run` presentado como limpio.

## Handoff

Si el riesgo alto es de seguridad, pasa a `appsec-audit` con fichero y línea; si es falta de pruebas, a `test-architect`; si el diff toca un contrato HTTP, a `api-contract-guard`. El informe consolidado se entrega tal cual: no se reescriben severidades ajenas.
