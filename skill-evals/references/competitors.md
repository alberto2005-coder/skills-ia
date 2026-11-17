# Qué hace la competencia y qué cubre este paquete

Investigación de noviembre de 2026 sobre las herramientas y skills de evaluación
de agentes más citadas. La columna «Aquí» dice qué script o sub-skill lo cubre;
«Mejora» y «Nuevo» separan lo que se hace mejor de lo que no existía.

## Herramientas revisadas

| Herramienta | Qué aporta | Fuente |
|---|---|---|
| Anthropic `skill-creator` | Genera casos, ejecuta con/sin skill, juez LLM, estadísticas (media/desviación), optimización de descripción con split 60/40 train/test y 3 repeticiones por consulta | github.com/anthropics/skills (skills/skill-creator) |
| Claude Code `plugin eval` | Casos con graders, 3 runs por caso, umbral por caso, baseline sin plugin (`W/OUT`), delta `Δ` | code.claude.com/docs/en/plugin-evals |
| Google `skill-reach` | `reach lint`, `reach overlap` (colisiones y rival más cercano), `reach eval --agent keyword` offline, `reach optimize` con hill climbing, informe HTML, evaluación de trayectorias multi-paso | github.com/google/skill-reach |
| NVIDIA `SkillEvaluator` | Tres niveles: validación estática (esquema, seguridad, PII, licencia), deduplicación semántica, evaluación en vivo con sandbox; Skill Lift, pass@k y cinco dimensiones | github.com/NVIDIA/SkillEvaluator · docs.nvidia.com/skills/skillevaluator |
| `agentskills.io` | Guía de evals: 2–3 casos, variar el fraseo, un caso límite, baseline con/sin skill, `iteration-N/` | agentskills.io/skill-creation/evaluating-skills |
| `addyosmani/agent-skills` evals | Tres niveles: estructural, trigger/routing con TF-IDF léxico y umbral `--min-rank1 95`, comportamiento con agente | github.com/addyosmani/agent-skills (evals/README.md) |

## Cobertura función a función

| Función de la competencia | Aquí | Mejora | Nuevo |
|---|---|---|---|
| Validación de frontmatter, nombres y esquema | `tests/lint_frontmatter.py` del repo + `design.py --check` | Reglas del estándar (nombre ≤64, descripción 20–1024, cuerpo <500) ya en CI | — |
| Cobertura del catálogo (skills sin casos) | `design.py` bloquea si falta una positiva | Falla antes de ejecutar, no después | Detección temprana por catálogo |
| Casos positivos y negativos con ganadora | `design.py` desde `tests/phrases.json` | Los casos son los mismos que usa CI: no hay dos verdades | `forbid` explícito por negativa |
| Casos límite | `design.py` añade frase genérica y vacía | Límites sintéticos deterministas | — |
| Split train/test 60/40 | `evalkit.split_for` por SHA-1 | Estable entre máquinas y ejecuciones, sin depender de un modelo | Split reproducible por id |
| Evaluación offline sin API | `run.py` sobre `trigger_router.py` | Mismo router que CI, cero coste, cero sandbox | — |
| Precisión/recall de activación | `run.py` (`precision`, `recall`, `mrr`) | Métricas por tipo y por split, no solo un agregado | MRR por caso |
| Baseline con/sin skill y `Δ` | `run.py --baseline` + `diff_runs` | Diff por id de caso: regresión, arreglo, nuevo, retirado | Regresión bloqueante (`--fail-on-regression`) |
| Detección de solapamiento entre descripciones | `evalkit._collisions` (Jaccard) | Sin embeddings ni modelo: umbral explícito y pares ordenados | Lista de pares con valor |
| Presupuesto de contexto | `evalkit._budget` | Tokens de catálogo y cuerpo, top 5 y lista fuera de presupuesto | Límite de catálogo y de cuerpo |
| Optimización de descripción | `optimize.py`: candidatos desde los términos ausentes en fallos de train, filtro por train, elección por test y diff con métricas antes/después | Sin modelo ni hill climbing opaco: candidatos deterministas, guarda de colisiones y `--apply` explícito | Optimización reproducible con diff auditable y selección held-out |
| Informe HTML/Markdown | `report.py` | HTML autónomo, escapado, sin CDN ni JS, byte a byte reproducible | Dos formatos desde el mismo JSON |
| Veredicto único y puertas de CI | `run.py --fail-under`, `--fail-on-regression` | Código de salida 0/1/2 y veredicto en el JSON | Puerta combinada métrica + regresión |
| Evaluación multi-paso / trayectorias | Fuera de alcance: el repo mide activación, no ejecución encadenada | — | Declarado como limitación |
| Calidad de la respuesta (juez LLM) | Fuera de alcance: exige modelo y red | — | Declarado como limitación |

## Decisiones de diseño

1. **Un solo router.** Reimplementar el scoring habría permitido números más
   bonitos y desconectados de CI. Se importa `tests/trigger_router.py` tal cual.
2. **Sin modelo.** Un juez LLM añade coste, no determinismo y una dependencia de
   red que el repositorio no acepta. La evaluación léxica detecta los dos fallos
   que dominan el routing real: vocabulario ausente (falso negativo) y
   descripción demasiado ancha (falso positivo).
3. **Casos, no prompts sueltos.** Un caso sin `expect` no distingue «no debe
   activarse» de «no se activa nada»; de ahí `expect: null` y `forbid`.
4. **El informe no decide.** El veredicto lo pone `run.py`; `report.py` solo lo
   presenta. Así el HTML no puede contradecir al código de salida.

## Lo que la competencia hace y aquí no

- Sandbox con Docker y agente real (SkillEvaluator, plugin evals): requiere
  modelo, red y ejecución de código; este repositorio es de solo lectura.
- Embeddings para deduplicación semántica: exige modelo; aquí Jaccard léxico.
- pass@k y repeticiones: sin modelo no hay varianza que medir; el router es
  determinista por diseño.
- Optimización automática con hill climbing multi-ronda: se sustituye por
  diagnóstico + propuesta + verificación, que deja el cambio auditable en diff.
