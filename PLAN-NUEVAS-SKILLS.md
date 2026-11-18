# Plan de revisión: documentar lo añadido y construir las 5 IAs nuevas

> Estado: **propuesta para leer, nada implementado**. Revisa las decisiones del §6 antes de que empiece.
> Base revisada: `plan_maestro_de_implementaci_n_de_nuevas_skills.md` (247 líneas) y el árbol real del repo a 2026-11-18.

---

## 1. Lo que ya está en el repo (verificado)

**8 paquetes, 44 skills, 490 tests en verde.**

| Paquete | Skills |
|---|---:|
| `replica` | 14 |
| `appsec-audit` | 11 |
| `seo-auditor` | 6 |
| `skill-evals` | 4 |
| `agent-red-team` | 3 |
| `humanizador-anti-ia` | 3 |
| `premium-web-designer` | 2 |
| `finops-auditor` | 1 |

`finops-auditor` es el intento nuevo al que te refieres. Lo he integrado en el índice y en la documentación general, pero **a medias**:

- Hecho: `finops-auditor/skills.json`, entrada en `skills.json` raíz (`skills_total` 44, versión 2.8.0), `license`/`metadata`, 3 frases positivas + 1 negativa en `tests/phrases.json`, fila en la tabla de `README.md` (ES/EN), fila y recuentos en `docs/index.md`, y `# noqa: E402` en su test.
- Pendiente: no tiene guía `docs/finops-auditor.md`, no aparece en las subtablas de paquete del README, sus dos "sub-skills" son ficheros sueltos en `sub-skills/*.md` en vez de carpetas con `SKILL.md`, el maestro no tiene `## Gate de salida` ni `## Handoff`, y su script único `finops_analyzer.py` (59 líneas) resuelve solo dos reglas de desperdicio.

## 2. Correcciones al plan maestro

| # | El plan dice | La realidad / riesgo |
|---|---|---|
| 1 | 7 paquetes, 43 skills → 12 y 65 | Ya son **8 y 44**. Con 22 skills nuevas serían **13 paquetes y 66 skills** (44 + 22) |
| 2 | `finops-auditor` = 4 skills desde cero | Ya existe con 1 skill y 2 sub-skills en `.md`; hay que **reconstruirlo**, no crearlo |
| 3 | `scripts/__init__.py` obligatorio | Ningún paquete lo usa (los tests hacen `sys.path.insert`). Añadirlo rompe la convención |
| 4 | CLI uniforme `--path` / `--json` / `--fail-on` | Los scripts existentes usan flags de dominio (`--cases`, `--check`, `--apply`) y códigos 0/1/2. Propongo mantener 0/1/2 y usar `--path` solo en los escáneres nuevos |
| 5 | §4.2: "añadir aserciones" sobre frontmatter y manifiestos | Ya existen en `tests/lint_frontmatter.py`. Lo que falta de verdad: **enlaces relativos vivos** y **coherencia `skills.json` ↔ `SKILL.md`** en todo el repo (44 skills actuales incluidas) |
| 6 | `uv run ruff format --check .` | El repo **no está formateado con ruff format**; aplicarlo reformatea todo el árbol. Hay que decidir cobertura |
| 7 | Auditoría AST con `sys.stdlib_module_names` | Ese atributo es de **Python 3.10**; el repo declara `>=3.9`. Necesita guarda por versión o lista propia |
| 8 | ≥5 positivas + ≥5 negativas por skill | La suite exige 2 y 1; el router léxico con umbral 0,3 no aguanta bien 5 frases artificiales por skill (empates y falsos positivos). Recomiendo 3 + 2 |
| 9 | `docs-changelog` con `git log` | Salida dependiente del reloj y del historial: hay que permitir `--since/--until` y usar un repo efímero en los tests |
| 10 | `golden_harness` importa y ejecuta el código del proyecto | Choca con la regla cero del repo (no ejecutar código no confiable sin autorización explícita) |
| 11 | `code_sync` con `ast` para frontend | `ast` no parsea JavaScript; ahí solo hay `re` y heurísticas, y hay que declararlo como límite |
| 12 | `seed_gen` con `random`, `uuid`, `datetime` | Determinismo solo si se usa `random.Random(seed)`, `UUID(int=...)` y fechas fijas; nunca `uuid4()` ni `now()` |

## 3. Fase 0 — Cerrar la documentación de `finops-auditor`

Objetivo: que el paquete esté documentado como los demás y que su estructura sea la del repo. Sin ampliar todavía a 4 skills.

1. `docs/finops-auditor.md` bilingüe con el formato de `docs/appsec-audit.md`: propósito, arquitectura, modos Quick/Full, tabla de sub-skills, reglas, CLI, rúbrica, tests y límites. Enlace en las dos listas de guías de `docs/index.md`.
2. Subtabla del paquete en `README.md` (ES y EN), después de la de `skill-evals`.
3. Normalizar estructura: `finops-scan/SKILL.md` y `finops-rightsize/SKILL.md` (con `license`/`metadata`), `references/` y `templates/` como hasta ahora, y borrar `sub-skills/`.
4. Añadir al maestro `## Gate de salida` (qué debe cumplirse para dar el informe por cerrado) y `## Handoff`.
5. Ampliar `phrases.json` a 3 positivas + 2 negativas por skill resultante y subir el manifiesto a las 3 skills.
6. Aceptación: `run_tests.py` verde, `lint_frontmatter` OK con 46 `SKILL.md`, gate `skill-evals` con 0 fallos y `docs/index.md` sin enlaces rotos.

## 4. Fases 1-5 — Los cinco paquetes del plan

Orden y alcance ajustados a las correcciones del §2. Cada fase termina con suite, lint, gate y guía bilingüe.

### Fase 1 · `finops-auditor` 2.0 — 4 skills (1 maestro + `finops-llm-scan`, `finops-infra-scan`, `finops-ci-opt`)
- Scripts: `llm_cost_scan.py` (AST: `max_tokens`, caching, modelo caro en clasificador, bucle sin tope), `infra_cost_scan.py` (S3 sin lifecycle, logs sin retención, pods sin `limits`), `ci_cost_scan.py` (sin caché, `push`+`pull_request` sin `concurrency`), `finops_score.py` (agrega y puntúa 0-100).
- Reutiliza `finops_analyzer.py` como base de `finops_score.py`; se retira el script genérico.
- Tests: 4 módulos + fixtures `.py`, `.tf`, `.yaml`; determinismo del score.
- Esfuerzo orientativo: 1 sesión.

### Fase 2 · `db-architect` — 5 skills (maestro + `db-schema-audit`, `db-migration-guard`, `db-query-trace`, `db-seed-gen`)
- `schema_audit.py` con `sqlite3 :memory:` (sin tocar bases reales), `migration_guard.py` con niveles `CRITICAL`/`WARNING` y verificación de `downgrade()`, `query_trace.py` (AST: ORM dentro de bucles), `seed_gen.py` (orden topológico + `--seed` fijo).
- Tests: 4 módulos; el de migraciones comprueba exit 1 con `--fail-on critical`.
- Esfuerzo orientativo: 1-2 sesiones (es el más denso por SQL).

### Fase 3 · `api-contract-guard` — 4 skills (maestro + `api-diff`, `api-code-sync`, `api-mock-server`)
- `contract_diff.py` (SemVer MAJOR/MINOR/PATCH estable), `code_sync.py` (rutas de backend por decoradores + frontend por `re`; límite declarado para JS), `mock_server.py` (`http.server` en `127.0.0.1:0`, cierre garantizado, sin red externa).
- Tests: 3 módulos, incluido servidor efímero con `urllib` en el mismo proceso.
- Esfuerzo orientativo: 1 sesión.

### Fase 4 · `refactor-surgeon` — 5 skills (maestro + `refactor-metrics`, `refactor-harness`, `refactor-slice`, `refactor-verify`)
- `code_metrics.py` (complejidad McCabe por AST, anidamiento, parámetros, mantenibilidad 0-100), `golden_harness.py` (**solo con `--allow-exec`**, jamás por defecto), `slice_analyzer.py` (grafo de llamadas y componentes conexas), `verify_gate.py` (compara contra `golden_snapshot.json`).
- Tests: 3 módulos; el harness se prueba con una función propia del fixture, no con código del usuario.
- Esfuerzo orientativo: 1-2 sesiones.

### Fase 5 · `docs-sync-engine` — 4 skills (maestro + `docs-drift-check`, `docs-arch-gen`, `docs-changelog`)
- `drift_check.py` (env vars `os.environ`/`process.env` vs `.env.example` y README, enlaces Markdown vivos, flags documentados vs `argparse`), `arch_mermaid.py` (imports internos → `graph TD`), `changelog_gen.py` (`git log` con `--since/--until`, agrupado por prefijo), `docs_score.py`.
- Tests: 3 módulos con repo Git efímero en `tempfile`.
- Esfuerzo orientativo: 1 sesión.

## 5. Fase 6 — Cierre transversal

1. `run_tests.py`: cinco entradas de suite nuevas.
2. `tests/phrases.json`: 3 positivas + 2 negativas por skill nueva (66 skills al final), con contraste explícito contra `appsec-infra`, `appsec-code`, `replica-build` y `seo-audit` como pide el plan.
3. `tests/lint_frontmatter.py`: nuevas comprobaciones de enlaces relativos y coherencia índice ↔ `SKILL.md` (se aplican también a las 44 actuales).
4. `.github/workflows/tests.yml`: ya ejecuta toda la suite y el gate de `skill-evals`; no requiere cambios salvo timeout si las suites crecen.
5. `skills.json` raíz: 13 paquetes, 66 skills, versión 3.0.0.
6. `README.md` y `docs/index.md` (ES/EN): recuentos, 5 filas y 5 subtablas, enlaces a las 5 guías.
7. `CHANGELOG.md` bilingüe: una entrada por paquete o una por fase, con tests y cifras.

## 6. Decisiones que necesito de ti

| # | Decisión | Recomendación |
|---|---|---|
| A | ¿Reconstruir `finops-auditor` a 4 skills como dice el plan, o dejar la de 1 skill documentada y ampliarla después? | Reconstruir en la fase 1 |
| B | ¿Formatear todo el repo con `ruff format` o limitar el gate a los paquetes nuevos? | Solo paquetes nuevos |
| C | ¿3 positivas + 2 negativas por skill o las 5 + 5 del plan? | 3 + 2, medidas con `skill-evals` |
| D | ¿`golden_harness` puede ejecutar código con `--allow-exec` explícito? | Sí, nunca por defecto |
| E | ¿Renombro `plan_maestro_de_implementaci_n_de_nuevas_skills.md` a `PLAN-NUEVAS-SKILLS.md` y borro este borrador, o los dejo los dos? | Dejar tu plan como histórico y este como ejecutable |

## 7. Criterio de "terminado" por paquete

```bash
uv run --locked python run_tests.py
uv run --locked python tests/lint_frontmatter.py
uv run --locked ruff check .
uv run --locked python skill-evals/scripts/design.py --from-phrases tests/phrases.json --out skill-evals/reports/cases.json
uv run --locked python skill-evals/scripts/run.py --cases skill-evals/reports/cases.json --fail-under precision=0.95 --fail-under recall=0.98 --fail-under mrr=0.98
```

Verde en los cinco, guía bilingüe enlazada en `docs/index.md`, fila y subtabla en `README.md`, entrada en `CHANGELOG.md` y commit propio por paquete (sin atribución de IA).
