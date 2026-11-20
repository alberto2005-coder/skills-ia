---
name: refactor-surgeon
description: >
  Refactoriza con red: mide complejidad y anidamiento, graba casos dorados, propone cortes por
  grafo de llamadas y verifica que la conducta no cambió. Úsala cuando haya que refactorizar sin
  tests o demostrar que la conducta sigue igual. English: refactor with a safety net — metrics,
  golden cases, call-graph cuts and behaviour verification.
license: MIT
metadata:
  package: refactor-surgeon
  version: "1.5.0"
  author: "Alberto Ortiz"
---

# Refactor Surgeon

## Propósito

Cambiar la forma del código sin cambiar lo que hace: primero medir, luego congelar la conducta con casos dorados, después cortar y al final verificar que nada se movió.

## Flujo

1. **Medir** con `refactor-metrics`: complejidad ciclomática, anidamiento y nota de mantenibilidad por función.
2. **Priorizar** con `refactor-hotspots`: churn × complejidad desde un `--since` explícito.
3. **Congelar** con `refactor-harness`: graba los casos dorados antes de tocar nada.
4. **Purgar** con `refactor-deadcode`: imports y definiciones privadas que ya nadie usa.
5. **Deduplicar** con `refactor-clones`: los bloques que solo cambian de nombre se unifican antes de cortar.
6. **Desenredar** con `refactor-cycles`: los módulos que se importan en círculo no se cortan todavía.
7. **Cortar** con `refactor-slice`: el grafo de llamadas dice qué funciones forman un módulo.
8. **Verificar** con `refactor-verify`: los mismos casos deben dar el mismo resultado.

## Sub-skills

| Sub-skill | Qué hace |
|---|---|
| `refactor-metrics` | Complejidad, anidamiento y mantenibilidad por función |
| `refactor-hotspots` | Churn × complejidad desde git log, con degradación explícita |
| `refactor-harness` | Graba casos dorados antes del cambio |
| `refactor-deadcode` | Imports y definiciones privadas sin uso |
| `refactor-clones` | Duplicación por shingles normalizados del AST |
| `refactor-cycles` | Ciclos de imports entre módulos |
| `refactor-slice` | Componentes conexas del grafo de llamadas |
| `refactor-verify` | Compara la conducta contra los casos grabados |

## Reglas

- Sin casos dorados no se refactoriza: primero se congela la conducta.
- Un refactor no cambia comportamiento; si cambia algo, se convierte en otro cambio.
- Cada corte se justifica con métricas de antes y después, no con impresiones.
- Lo que se borra por muerto se confirma contra los casos dorados, no por intuición.

## Gate de salida

- Métricas antes y después, y la nota de mantenibilidad.
- Casos dorados grabados y verificados sin discrepancias.
- Los cortes aplicados quedan listados con su grupo de funciones.

## Handoff

Entrega a `refactor-verify` el snapshot y el comando de verificación. Si aparece una discrepancia, el cambio se revierte antes de seguir cortando.
