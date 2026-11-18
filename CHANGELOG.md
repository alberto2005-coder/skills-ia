# Changelog / Registro de Cambios

*[Español](#español) · [English](#english)*

---

## Español

Todas las modificaciones notables de este proyecto están documentadas en este archivo.

### - 2026-11-18 · `refactor-surgeon` 1.4 — `refactor-hotspots`

#### Añadido
- **Sub-skill `refactor-hotspots`:** ordena los ficheros por churn de `git log` desde una fecha obligatoria multiplicado por su complejidad, para empezar el refactor por lo que más devuelve por hora.
- **`scripts/hotspots.py`:** churn desde `--since` (una fecha sin hora se normaliza a `T00:00:00`, porque git la redondearía a la hora de la consulta), `V(G)` del fichero con las comprensiones contadas por sus `if`, y score = churn × complejidad; `--top`, `--json`, `--fail-on hotspot` con `--min-score`. Sin fecha, fuera de un repositorio o en un clon shallow devuelve `measured: false` y salida 2 en lugar de un número falso; los ficheros borrados se cuentan en `skipped` y no entran en el ranking.
- **8 pruebas** en `refactor-surgeon/tests/test_hotspots.py` contra repositorios git temporales: sin `--since`, sin repositorio, churn y complejidad medidos, fecha sin hora normalizada a medianoche, ventana que filtra, orden y `--top`, `--fail-on hotspot` y clon shallow.
- **Frases de activación:** 3 positivas y 2 negativas en `tests/phrases.json`, verificadas contra el router antes de escribirlas.

#### Cambiado
- **Índice raíz `skills.json`:** de **78 a 79 skills**, versión 4.1.0; `refactor-surgeon` pasa a 1.4.0 con 9 skills.
- **`docs/refactor-surgeon.md` y `README.md`:** modo Priorización, comando, fila nueva y 42 pruebas por paquete.

### - 2026-11-18 · `docs-sync-engine` 1.1 — `docs-terms` y `docs-env`

#### Añadido
- **Sub-skill `docs-terms`:** glosario versionado con `accept.txt` (grafía canónica) y `reject.txt` (términos prohibidos, con `malo => bueno` para sugerir el reemplazo).
- **`scripts/terms_check.py`:** reglas `termino-rechazado` (media) y `grafia-no-canonica` (baja), que muestra la variante encontrada en el texto (`found`) y no repite la canónica; bloques de código y `código en línea` se ignoran conservando los números de línea, y `--fail-on` acepta `low|medium|high|none`.
- **Sub-skill `docs-env`:** cada variable que lee el código debe estar en `.env.example` y en la documentación, y lo declarado que nadie usa se reporta.
- **`scripts/env_check.py`:** reconoce `os.environ[...]`, `os.environ.get`, `os.getenv`, `process.env.X` e `import.meta.env.X`, y en el ejemplo acepta `CLAVE=` y `export CLAVE=`; reglas `env-sin-ejemplo`, `env-sin-documentar` (media) y `ejemplo-sin-uso` (baja).
- **16 pruebas** repartidas entre `docs-sync-engine/tests/test_terms_check.py` y `test_env_check.py` (8 cada uno): glosario limpio, rechazado con reemplazo, grafía no canónica con la variante real, fences sin desplazar líneas, `export`, `process.env`, `import.meta.env`, `--fail-on none` y rutas o glosarios ausentes.

#### Cambiado
- **Índice raíz `skills.json`:** de **76 a 78 skills**, versión 4.0.0; `docs-sync-engine` pasa a 1.1.0 con 6 skills.
- **Maestro y `docs/docs-sync-engine.md`:** fases Terminología y Entorno, filas y comandos nuevos, y 27 pruebas por paquete.

### - 2026-11-18 · `api-contract-guard` 1.1 — `api-auth-coverage`

#### Añadido
- **Sub-skill `api-auth-coverage`:** cruza el `security` del contrato con las guardas reales de las rutas, para que un endpoint que se documenta como protegido no quede abierto.
- **`scripts/auth_coverage.py`:** hereda el `security` global, normaliza `<int:id>` a `{id}`, reconoce rutas de FastAPI y Flask y guardas por nombre de decorador; reglas `ruta-sin-guarda` (alta), `ruta-sin-spec`, `spec-sin-security` (media) y `spec-sin-codigo` (baja), con `--json` y `--fail-on medium`.
- **9 pruebas** en `api-contract-guard/tests/test_auth_coverage.py`: rutas con guarda, contrato sin guarda, guarda sin `security`, ruta fuera del contrato, operación sin código, seguridad global heredada, Flask con parámetros normalizados, `--fail-on none` y contrato ausente.

#### Cambiado
- **Índice raíz `skills.json`:** de **75 a 76 skills**, versión 3.9.0; `api-contract-guard` pasa a 1.1.0 con 5 skills.
- **Maestro y `docs/api-contract-guard.md`:** fase Cobertura, fila, comando y 20 pruebas por paquete.

### - 2026-11-18 · `db-architect` 1.2 — `db-expand-contract` y `db-sql-lint`

#### Añadido
- **Sub-skill `db-expand-contract`:** parte una migración en fase aditiva (`expand`) y de retirada (`contract`) para desplegar sin ventana de mantenimiento.
- **`scripts/expand_contract.py`:** clasifica cada sentencia y avisa de lo que no se puede repartir (`columna-obligatoria-en-un-paso`, `rename-no-divisible`, `reescritura-no-divisible`); lo que no reconoce (`DROP INDEX`, `INSERT`, …) va a `phases.unknown` con aviso `sentencia-desconocida` y nunca a `expand`, y el separador de sentencias respeta cadenas y cuerpos `$$` de funciones. `--json` y `--fail-on unsafe|none`.
- **Sub-skill `db-sql-lint`:** estilo SQL antes del guardián de riesgo, con reglas acotadas.
- **`scripts/sql_lint.py`:** `tabla-sin-clave`, `select-asterisco` (media), `palabra-clave-minuscula`, `identificador-no-snake`, `comparacion-distinta`, `linea-larga`, `tabulador` (baja); los comentarios de línea no cuentan para identificadores ni comparaciones, y un `CREATE TABLE` sin `;` final también se revisa.
- **18 pruebas** repartidas entre `db-architect/tests/test_expand_contract.py` y `test_sql_lint.py` (10 y 8): aditivo, destructivo con `DROP CONSTRAINT`, mezcla, columna obligatoria, cambio de tipo, `rename`, cuerpo de función con `;`, sentencia desconocida, fichero limpio, cada regla de estilo, `--fail-on none` y rutas ausentes.

#### Cambiado
- **Índice raíz `skills.json`:** de **73 a 75 skills**, versión 3.8.0; `db-architect` pasa a 1.2.0 con 9 skills.
- **Maestro y `docs/db-architect.md`:** fase Plan, `db-sql-lint` en Audit, filas, comandos y 48 pruebas por paquete.

### - 2026-11-18 · `finops-auditor` 1.3 — `finops-diff`

#### Añadido
- **Sub-skill `finops-diff`:** responde «cuánto cuesta este cambio» comparando dos inventarios por `id` de recurso y rompe el pipeline cuando el aumento supera lo acordado.
- **`scripts/cost_diff.py`:** totales `before_total`/`after_total` con su delta absoluto y porcentual, altas, bajas y cambios de precio por recurso, y guardrails independientes `--max-increase`, `--max-percent` y `--budget`; `--json`, `--fail-on guardrail|none` y códigos de salida 0/1/2 para CI.
- **8 pruebas** en `finops-auditor/tests/test_cost_diff.py`: inventarios idénticos sin hallazgos, crecimiento con altas y cambios, cada guardrail rompiendo la puerta con su cifra, los tres a la vez, `--fail-on none`, e inventario inexistente devolviendo 2.
- **Frases de activación:** 3 positivas y 2 negativas en `tests/phrases.json` (ganan `db-lock-audit` y `appsec-infra`), verificadas contra el router antes de escribirlas.

#### Cambiado
- **Índice raíz `skills.json`:** de **70 a 71 skills**, versión 3.5.0; `finops-auditor` pasa a 1.3.0 con 7 skills.
- **Maestro del paquete:** fase **3b (Diff)** en el protocolo y fila nueva en la tabla de sub-skills.
- **`docs/finops-auditor.md`, `README.md` y `docs/index.md`:** «seis sub-skills», comando `cost_diff.py` en los dos bloques, recuentos actualizados y 26 pruebas descritas por paquete.

### - 2026-11-18 · `db-architect` 1.1 — `db-lock-audit` y `db-drift`

#### Añadido
- **Sub-skill `db-lock-audit`:** detecta la migración que bloquea la tabla o la reescribe, separando el riesgo de datos (del guardián) del tiempo de bloqueo (de este auditor).
- **`scripts/lock_audit.py`:** reglas `reescritura-de-tipo`, `columna-not-null-con-default`, `set-not-null`, `indice-sin-concurrently`, `rename-inseguro`, `fk-sin-not-valid`, `check-sin-not-valid`, `vacuum-full` y `delete-sin-where`, con `--path`, `--json` y `--fail-on low|medium|high|none` (por defecto `high`); cada hallazgo sale con fichero, línea, tabla, regla y alternativa segura. Códigos 0/1/2, sin motor ni conexión.
- **Sub-skill `db-drift`:** compara el esquema declarado con el que resulta de reproducir las migraciones en orden alfabético, por tabla, por columna y por tipo.
- **`scripts/drift.py`:** reglas `tabla-solo-en-esquema`, `tabla-solo-en-migraciones`, `columna-solo-en-esquema`, `columna-solo-en-migraciones` y `tipo-distinto`, aplicando `CREATE TABLE`, `ADD`/`DROP COLUMN`, `ALTER TYPE`, `RENAME COLUMN`, `RENAME TO` y `DROP TABLE`; flags `--schema`, `--migrations`, `--json` y `--fail-on drift|none`.
- **12 pruebas** repartidas entre `db-architect/tests/test_lock_audit.py` y `db-architect/tests/test_drift.py` (6 cada uno): cada regla de bloqueo, migración segura, comentarios ignorados, umbrales y `--fail-on none`; y esquema que cuadra, columnas y tablas que sobran o faltan, tipos distintos, renombrado intermedio y `DROP` de una tabla declarada.
- **Frases de activación:** 2 positivas y 2 negativas para `db-lock-audit` (ganan `db-schema-audit` y `replica-diff`) y 3 + 2 para `db-drift` (ganan `db-seed-gen` y `eval-run`), verificadas contra el router antes de escribirlas.

#### Cambiado
- **Índice raíz `skills.json`:** de **68 a 70 skills**, versión 3.4.0; `db-architect` pasa a 1.1.0 con 7 skills.
- **Maestro del paquete:** el flujo pasa a **Audit → Guard → Lock → Drift → Optimize**, con las dos sub-skills en la tabla y los gates ampliados.
- **`docs/db-architect.md`, `README.md` y `docs/index.md`:** filas y comandos nuevos, recuentos actualizados y 30 pruebas descritas por paquete.

### - 2026-11-18 · `refactor-surgeon` 1.1 — `refactor-clones`

#### Añadido
- **Sub-skill `refactor-clones`:** detección de duplicación por shingles normalizados sobre el AST. Los identificadores se sustituyen por su tipo (`Name`, `arg`, `Attribute`, `Constant:tipo`), así que un renombrado cuenta como clon exacto en lugar de pasar desapercibido.
- **`scripts/clone_detect.py`:** ventanas de tokens con Jaccard entre funciones, `--shingle` (8), `--min-tokens` (20), `--threshold` (0.8), `--json` y `--fail-on clone|none`; cada par sale con `clon-exacto`/`clon-cercano`, similitud y las dos ubicaciones. Códigos de salida 0/1/2, sin ejecutar el código analizado.
- **7 pruebas** en `refactor-surgeon/tests/test_clone_detect.py`: renombrado detectado como clon exacto, funciones distintas sin hallazgos, funciones diminutas ignoradas, umbral que filtra el par, `--fail-on none`, ruta ausente y estructura del JSON.
- **Frases de activación:** 3 positivas y 2 negativas en `tests/phrases.json`, verificadas contra el router antes de escribirlas.

#### Cambiado
- **Índice raíz `skills.json`:** de **67 a 68 skills**, versión 3.3.0; `refactor-surgeon` pasa a 1.1.0 con 6 skills.
- **Maestro del paquete:** `refactor-clones` entra en el flujo (medir → congelar → deduplicar → cortar → verificar) y en la tabla de sub-skills.
- **`docs/refactor-surgeon.md`, `README.md` y `docs/index.md`:** fila y comando nuevos, recuentos actualizados y 19 pruebas descritas por paquete.

### - 2026-11-18 · `finops-auditor` 2.0, `db-architect`, `api-contract-guard`, `refactor-surgeon` y `docs-sync-engine`

#### Añadido
- **`finops-auditor` 2.0 (6 skills):** `finops-scan` y `finops-rightsize` más `finops-llm-scan` (coste de llamadas a LLM), `finops-infra-scan` (Terraform y Kubernetes) y `finops-ci-opt` (GitHub Actions), con `llm_cost_scan.py`, `infra_cost_scan.py` y `ci_cost_scan.py`, 18 pruebas y guía bilingüe.
- **`db-architect` (5 skills):** maestro + `db-schema-audit`, `db-migration-guard`, `db-query-trace` y `db-seed-gen`, con `schema_audit.py`, `migration_guard.py`, `query_trace.py` y `seed_gen.py`, 18 pruebas y guía bilingüe.
- **`api-contract-guard` (4 skills):** maestro + `api-diff`, `api-code-sync` y `api-mock-server`, con `contract_diff.py` (impacto SemVer), `code_sync.py` (rutas backend/frontend) y `mock_server.py` (loopback), 11 pruebas y guía bilingüe.
- **`refactor-surgeon` (5 skills):** maestro + `refactor-metrics`, `refactor-harness`, `refactor-slice` y `refactor-verify`, con `code_metrics.py`, `golden_harness.py` y `slice_analyzer.py`, 12 pruebas y guía bilingüe.
- **`docs-sync-engine` (4 skills):** maestro + `docs-drift-check`, `docs-arch-gen` y `docs-changelog`, con `docs_drift.py`, `arch_gen.py` y `changelog_gen.py`, 11 pruebas y guía bilingüe.
- **Lint ampliado:** `tests/lint_frontmatter.py` comprueba además los enlaces relativos de todos los Markdown y que el índice raíz cuadre con el disco (`skills_total`, skills por paquete y cobertura de cada `SKILL.md`), con 7 pruebas nuevas en `tests/test_lint_links.py`.

#### Cambiado
- **`run_tests.py`:** las cinco suites nuevas (`api-contract-guard`, `db-architect`, `docs-sync-engine`, `finops-auditor`, `refactor-surgeon`) se ejecutan con el resto: 13 suites y 567 pruebas.
- **Índice raíz `skills.json`:** 12 paquetes y **67 skills**, versión 3.2.0.
- **`README.md` y `docs/index.md`:** recuentos, filas de los cinco paquetes, tablas de sub-skills y enlaces a las guías nuevas, en español e inglés.
- **`tests/phrases.json`:** frases de activación para las 13 skills nuevas, verificadas contra el router antes de escribirlas.

### - 2026-11-18 · `skill-evals` 1.0 y puertas de calidad en CI

#### Añadido
- **Paquete `skill-evals` (4 skills):** maestro + `eval-design`, `eval-run` y `eval-report`, con `scripts/evalkit.py` (casos, métricas, colisiones, presupuesto y diff), `design.py`, `run.py`, `report.py` y `optimize.py`, más `references/competitors.md`, `references/metrics.md`, `templates/` y 42 pruebas. Cierra el ciclo de skill-creator, skill-reach y SkillEvaluator sin modelo ni red.
- **Optimizador de descripciones:** candidatos solo desde fallos de *train*, filtro en *train*, selección final en *test*, diff y `--apply` explícito; nunca reescribe un `SKILL.md` por su cuenta.
- **Informe reproducible:** Markdown o HTML autónomo con tabla de fallos, colisiones, presupuesto de contexto y diff contra la línea base.
- **Paquete `finops-auditor` (3 skills):** se incorpora al catálogo la auditoría de costes cloud con recursos huérfanos, sobreaprovisionamiento y derechosizing. `finops-scan` y `finops-rightsize` pasan de ficheros sueltos en `sub-skills/` a carpetas con su `SKILL.md`, `## Gate de salida` y `## Handoff`, con manifiesto, `license`/`metadata`, frases de activación y el arreglo del import en sus tests.
- **Gate en CI:** el job de lint ejecuta `design.py --from-phrases tests/phrases.json --out skill-evals/reports/cases.json` y `run.py --fail-under precision=0.95 --fail-under recall=0.98 --fail-under mrr=0.98`, así que una descripción que rompa el routing falla el workflow.

#### Cambiado
- **Lint de frontmatter más estricto:** `name` en minúsculas de 64 caracteres como máximo, descripción de 20 a 1024 y cuerpo por debajo de 500 líneas; los 44 `SKILL.md` llevan `license: MIT` y `metadata.package`/`metadata.version` mantenidos por `tests/sync_skill_metadata.py --check`.
- **Workflow de CI:** además de `push` corre en `pull_request`, con `permissions: contents: read`, `timeout-minutes`, cancelación por concurrencia y `ruff` (E4/E7/E9/F) junto a la suite.
- **Suite de pruebas:** 490 pruebas; los recuentos y las listas de skills se derivan de `skills.json` y del sistema de ficheros, así que una skill nueva no obliga a editar constantes.

### - 2026-11-17 · `appsec-audit` 1.4 — CI, remediación y escala

#### Añadido
- **`appsec-ci`:** `detect_tools.py` detecta herramientas por PATH y metadatos sin instalarlas ni ejecutarlas, y audita el workflow (`pull_request_target` con token de escritura, checkout del head, acciones sin pin, inyección por interpolación, secretos). `normalize_sarif.py` convierte SARIF externo en `needs_validation`, comprueba compatibilidad con `upload-sarif` y aplica `--fail-on`. Con `references/agent-hardening.md` y `templates/pr-comment.md`.
- **`appsec-fix`:** `apply_patch.py` con dry-run por defecto, escritura solo con `--apply --yes`, copia `.orig` y verificación que exige `--sandbox` declarado; política de sandbox, reversión y análisis de variantes en `references/remediation.md`.
- **`appsec-scale`:** `scale_report.py` consolida varios repos, dibuja la topología repo → tercero y estima horas y coste por fase según perfil y tarifa, con `references/scale.md`.
- **Tests:** 27 pruebas nuevas (122 en el paquete) y tres sub-skills más (11 en total, 39 en el repositorio).

### - 2026-11-17 · `appsec-audit` 1.3 — Threat model y dependencias

#### Añadido
- **`appsec-threat`:** activos, actores, límites de confianza, casos de abuso y mapeo de cada amenaza a OWASP Top 10 2025, ASVS 5.0 y la clase del ledger, con `templates/threat-model.md` y `references/threat-model.md`.
- **`appsec-deps`:** `scripts/sbom.py` genera el SBOM CycloneDX 1.5 desde `package.json`, `requirements.txt`, `pyproject.toml` y `go.mod`, cruza avisos por versión y ecosistema y decide alcanzabilidad por imports (`reachable`, `test-only`, `not-imported`, `unknown`), con puerta para altas y críticas alcanzables.
- **Catálogo ampliado:** de 14 a 24 clases de ataque en `references/attack-classes.md`, el ledger y su esquema, cada una con CWE, OWASP 2025 y capítulo ASVS.
- **Tests:** 23 pruebas nuevas (95 en el paquete), incluida la coherencia entre catálogo y clases aceptadas por el ledger.

### - 2026-11-17 · `appsec-audit` 1.2 — Fase 1

#### Añadido
- **Verificador independiente:** `templates/verification.md` entrega al revisor solo ubicación, CWE, patrón y propósito declarado, sin evidencia ni veredicto, y mapea cada veredicto a los campos que exige `findings.json`.
- **`scripts/export_sarif.py`:** SARIF 2.1.0 con una regla por CWE, `critica`/`alta` como `error`, `media` como `warning`, `baja` como `note`, solo `confirmed`, `needs_validation` como `note` con `--include-pending` y huella en `partialFingerprints`.
- **`scripts/diff_scope.py`:** modo diff/PR; convierte un parche o `git diff --base` en rangos de líneas añadidas y separa los hallazgos que caen dentro del cambio.
- **`scripts/diff_reports.py`:** baseline por fingerprint con `new`, `fixed`, `changed` y `persisting`, y `--fail-on new` como puerta de PR sobre los `confirmed` nuevos.
- **Tests:** 26 pruebas nuevas (72 en el paquete) y documentación bilingüe de los cuatro mecanismos.

### - 2026-11-17 · CI, SARIF y trazabilidad

#### Añadido
- **`agent-red-team/scripts/export_sarif.py`:** exporta el informe a SARIF 2.1.0 con una regla por categoría, mapeo `critical/high → error`, `medium → warning`, `low → note`, REJECT siempre `error` y `needs_validation` como `note` solo con `--include-pending`. Los `rejected` no se exportan. 12 tests nuevos (50 en el paquete).
- **`tests/lint_frontmatter.py`:** lint de frontmatter (delimitadores, `name` igual a la carpeta, `description` útil) y de los manifiestos de paquete, con 6 tests propios.
- **CI real:** `.github/workflows/tests.yml` pasa a dos jobs — lint en Ubuntu y la suite completa en **matriz Ubuntu / macOS / Windows** con Python 3.13.

#### Cambiado
- **`PLAN-MEJORA.md` se retira:** todas sus fases están implementadas y su contenido vive ahora en el CHANGELOG y en la guía de cada paquete.

### - 2026-11-17 · `appsec-audit` 1.1 — Fase 0

#### Añadido
- **Artefactos verificables:** `init_audit.py` crea `<target>/.appsec-audit/` con `findings.json`, `coverage-ledger.json` y `architecture.md` válidos desde el primer minuto, sin sobrescribir sin `--force`.
- **`schemas/findings.schema.json` y `schemas/coverage-ledger.schema.json`:** contrato cerrado de ambos artefactos, con campos permitidos y enums.
- **`validate_findings.py`:** validador determinista que exige severidad solo en `confirmed`, confianza ≥ 7, dos pasos de explotación, parche, `unresolved` en `needs_validation`, `reason` en `rejected`, huella recalculada y `source_unit` existente en el ledger.
- **`ledger.py`:** alta de unidades superficie × subsistema × clase de ataque, actualización de estado y `gaps --strict` como puerta de cierre.
- **Fingerprint estable:** `sha256(cwe|fichero|causa raíz)[:32]`, independiente del número de línea, para deduplicar y re-ejecutar.
- **`references/artifacts.md`** y guía bilingüe: veredictos, huellas y estados del ledger.
- **Tests:** 25 pruebas nuevas de init, validador y ledger (46 en el paquete).

### - 2026-11-17 · `appsec-audit` 1.0

#### Añadido
- **Paquete `appsec-audit` (6 skills):** maestro + `appsec-recon`, `appsec-code`, `appsec-infra`, `appsec-llm` y `appsec-report`. Cubre web, APIs, repositorios, Docker, IaC, cloud/IAM, binarios y sistemas con LLM, agentes y MCP, con arquitectura de dos fases (descubrimiento y trazado Sources → Sinks, más tribunal de validación) y assets compartidos.
- **Regla cero:** todo fichero, comentario, README o cadena se trata como dato hostil; el revisor no ejecuta código del proyecto, no instala dependencias, no sale a la red sin autorización y redacta todo secreto. Un intento de inyección indirecta se reporta como hallazgo.
- **Tribunal con umbral:** cada candidato responde cinco preguntas (alcanzable, mitigado, aplica en producción, quién lo explota, evidencia) y recibe confianza 1–10; **por debajo de 7 se descarta** con el motivo registrado.
- **`scripts/scan_secrets.py`:** patrones conocidos (AWS, GitHub, Slack, Stripe, Google, JWT, claves privadas) más entropía de Shannon en asignaciones genéricas, con redacción y `--strict` para CI.
- **`scripts/map_flows.py`:** índice heurístico de candidatos fuente → sumidero en nueve familias de lenguaje, con la fuente cercana y salida `--json`.
- **`scripts/grade.py`:** nota A–F determinista desde los hallazgos validados (25 por crítico, 10 por alto, 3 por medio, 1 por bajo, suelo en 0); los descartados no puntúan.
- **`references/`:** `benchmark.md` (tabla comparativa de las siete referencias con la mejora aplicada), `sources-sinks.md`, `owasp-cwe.md`, `cloud-iac.md`, `llm-agents-mcp.md` y `prompt-injection-defense.md`.
- **`templates/`:** informe completo, ficha de hallazgo y hoja del tribunal.
- **Tests:** 21 pruebas propias (estructura, frontmatter, gates y handoff, manifiesto, secretos con fixtures, trazado y códigos de salida de los tres scripts).
- **`docs/appsec-audit.md`:** guía bilingüe con la tabla comparativa de mecánicas heredadas y mejoras.

#### Cambiado
- **Índice raíz `skills.json`:** 6 paquetes, **34 skills**.
- **`run_tests.py`:** la suite `appsec-audit` se ejecuta con el resto (329 tests en total).
- **`tests/phrases.json`:** 21 frases positivas y 12 negativas nuevas, sin colisión con `agent-red-team` ni `seo-audit`.
- **`README.md` y `docs/index.md`:** recuentos, tabla del paquete y enlace a la guía, en español e inglés.
- **`tests/test_triggers.py`:** la cobertura del dataset pasa de 28 a 34 skills.

### - 2026-11-17 · `premium-web-designer` 2.1

#### Añadido
- **Sub-skill `premium-qa`:** auditoría independiente de una web ya construida, con protocolo de medición en 360/390/768/1024/1440 px, gates numéricos (desbordamiento 0, titular de 3 líneas como máximo, controles de 44 px, anclas libres de la cabecera fija, foco en overlays) e informe por severidad.
- **`scripts/delivery_check.py`:** puerta estática en stdlib sobre `lang`, título, descripción, canonical, Open Graph, jerarquía de encabezados, `alt`, JSON-LD, `:focus-visible`, `prefers-reduced-motion`, cabecera pegajosa sin `scroll-padding-top`, versión en CSS/JS, `robots.txt`, `sitemap.xml` y `llms.txt`. Sale con código 1 si falla un `must`.
- **`references/qa-metrics.md`:** snippet de medición en consola con lecturas esperadas, comprobación de anclas y diagnóstico de CSS cacheado.
- **Modo `--public` en la puerta:** canonical, Open Graph con imagen, `robots.txt` y `sitemap.xml` pasan de aviso a `must` cuando la carpeta va a publicarse, con fixture y cinco tests que fijan el cambio de severidad y el código de salida.
- **Cabeceras del hosting:** la puerta detecta `_headers`, `netlify.toml` y `vercel.json`, y en `--public` avisa si no declaran CSP o HSTS con `max-age` (`HDR-001..003`), con fixture `site_public` y tests para los tres formatos.
- **`references/known-defects.md`:** catálogo de los seis defectos medidos en una revisión real (titular en columna estrecha, ruptura temprana, controles diminutos, ancla bajo cabecera, CSS cacheado y metadatos incompletos), con síntoma, medida antes/después, causa, arreglo y la comprobación que los detecta.
- **Tests:** seis pruebas de la puerta con fixtures de sitio correcto y defectuoso (43 en el paquete).
- **`references/performance-seo.md`:** mínimo SEO por página (canonical, Open Graph con imagen, jerarquía de encabezados, sitemap declarado, `llms.txt`) y cabeceras de seguridad para el despliegue.

#### Corregido (detectado al revisar una demo real)
- El maestro no daba criterios medibles: la demo entregó un `h1` de cinco líneas por auto-placement de la rejilla, pasos de 214 px a 768, controles de 34–39 px, anclas tapadas por la cabecera fija y CSS servido desde caché. Ahora son gates explícitos en el maestro y en `premium-qa`.
- El maestro pasa de 440 a 111 líneas: el detalle vive en `agents/`, `workflows/`, `references/` y la sub-skill.

### - 2026-11-17

#### Cambiado
- **Arquitectura multi-skill:** cada paquete pasa de una skill monolítica a **maestro + sub-skills** con cortes de uso real. Los assets (`references/`, `scripts/`, `templates/`, `tests/`) siguen compartidos en la raíz del paquete: no se duplica nada.
- **Índice raíz `skills.json`:** 5 paquetes, **27 skills** en total, incluido `premium-web-designer` como skill independiente.
- **`README.md`:** tablas de módulos y sub-skills en español e inglés, y estructura estándar de paquete.
- **Desacoplamiento de firmas en `agent-red-team`:** las reglas y patrones de detección se extraen de `scripts/scan_skill.py` a `scripts/rules.json` (con soporte CLI mediante `--rules`) para eliminar falsos positivos heurísticos en motores antivirus locales.

#### Añadido
- **`replica` (14 skills):** maestro + `replica-recon` (0-1b), `replica-architect` (2), `replica-design` (3), `replica-build` (4), `replica-backend` (5), `replica-test` (6), `replica-diff` (7), `replica-entrepreneur` (8), `replica-brand` (9), `replica-launch` (10), `replica-deploy` (11), `replica-static` (12, opt-in) y `replica-redes` (13). Cada sub-skill declara precondiciones, método, gate de salida y handoff.
- **`seo-auditor` (6 skills):** maestro + `seo-audit`, `seo-plan`, `seo-execute`, `seo-serp` y `seo-compare`, con los 11 comandos del CLI repartidos sin duplicar la tabla módulo→comando.
- **`agent-red-team` (3 skills):** maestro + `red-scan` (guidance, sin ficheros) y `red-audit` (auditoría completa con verificación independiente y ledger).
- **`humanizador-anti-ia` (3 skills):** maestro + `humanizar` (reescritura) y `detector-ia` (solo medición, sin tocar el texto).
- **Índice de sub-skills en cada `SKILL.md` maestro**, con la nota de instalación conjunta y las rutas relativas al paquete.
- **Tests de coherencia maestro/sub-skill** en `tests/test_coherence.py` (11 tests): ninguna sub-skill repite prosa de su maestro (los comandos CLI sí pueden repetirse, con tope), todas tienen `## Gate de salida` y `## Handoff`, cada maestro indexa sus sub-skills, no reaparecen las contradicciones corregidas (`dos condiciones`, `Quick en detalle`, tabla de módulos, `rescore` duplicado), los comandos son ejecutables desde la raíz y los maestros no vuelven a crecer sin control.
- **Tests de activación (trigger)** para las 27 skills en `tests/`: router léxico determinista sin red (`trigger_router.py`), dataset de 112 frases (58 positivas y 54 negativas) y 13 tests que comprueban top-1 global, victoria dentro del paquete, ausencia de solapamiento entre hermanas, frases de otro dominio y determinismo.

#### Documentación
- **Fuente única:** `seo-auditor/` deja de duplicar `README.md`, `CHANGELOG.md` y `LICENSE`. La documentación vive en la raíz y en [`docs/seo-auditor.md`](docs/seo-auditor.md); la licencia del repo pasa a ser la única. `USAGE.md` se mantiene porque es el catálogo de comandos que referencia el maestro.
- **`docs/` alineado con la estructura real:** índice con los 5 paquetes y sus 27 skills, estructura de paquete y comandos de test.
- **`docs/agent-red-team.md`:** corregido el protocolo de «4 fases» al real de **6 fases (0–5)**, con modos guidance/auditoría, sub-skills, nivel RECHAZO, code fences, ledger, esquema JSON y códigos de salida.
- **`docs/replica.md`:** de 11 a **14 fases (0–13)**, tabla fase→sub-skill, comando maestro con `progreso.md` y formato de evidencia.
- **`docs/seo-auditor.md`:** modo `page`, rúbrica y veredicto, 11 comandos, 8 módulos, sub-skills, artefactos y límites.
- **`docs/humanizador-anti-ia.md`:** eliminadas métricas obsoletas (Fernández-Huerta, TTR, burstiness CV); documenta modos, score de 4 señales, 40 patrones y sub-skills.

#### Revisado
- **Maestro de `seo-auditor` recortado de 195 a 121 líneas:** fuera el bloque de 17 comandos (viven en `USAGE.md` y en `seo-audit`), la tabla de módulos y el árbol script a script; quedan como referencia de una línea más el comando de entrada. Sin perder ninguna instrucción ni límite (reglas, rúbrica, severidades, flujo, tabla medido/estimado/no inventado y límites).
- **Coherencia maestro/sub-skill:** se eliminaron las reglas y procedimientos duplicados (protocolo de red team, flujo y modos del humanizador, tabla de módulos y re-score del SEO, detalle del escáner), se corrigió la contradicción de la fase 12 («dos condiciones» frente a las tres reales) y cada sub-skill declara ahora qué **no** hace cuando el límite con una hermana era ambiguo (build/backend, test/diff, brand/design).

#### Corregido (detectado por los tests de activación)
- `replica` no declaraba que orquesta el pipeline ni el estado en `progreso.md`; `replica-diff` no mencionaba «original y clon»; `replica-backend` no listaba esquema ni migraciones; `humanizar` no declaraba la calibración de voz y `detector-ia` no mencionaba puntuar. Las cinco descripciones se completaron para que el enrutado real elija la sub-skill correcta.

#### Fases de mejora cerradas en esta versión
- **Fase 1 (`replica`):** evidencia obligatoria por hallazgo, foco por función, caché de análisis, comando maestro `/replica` con `progreso.md`, fase 13 de redes, análisis estático opt-in, tabla de 10 países y 72 tests.
- **Fase 2 (`agent-red-team`):** modos guidance/auditoría, verificación independiente `confirmed/needs_validation/rejected`, ledger, esquema JSON, 6 combinaciones REJECT, excepción de code fences, catálogo de 15 ataques, reglas externas en `rules.json` y 36 tests.
- **Fase 3 (`humanizador-anti-ia`):** catálogo de 40 patrones, pack español, score 0-100 de 4 señales, modos Quick/Full/Voice, registro, honestidad factual, protección de código y 16 tests.
- **Fase 4 (`seo-auditor`):** rúbrica cableada, 10 scripts nuevos, CLI de 11 comandos, 8 bloques IndexPulse, `report.html`, `compare`, `rescore`, `fix` con dry-run y 104 tests.

#### Notas
- Compatibilidad declarada con **Python 3.8+**; la verificación se ejecutó sobre Python 3.13 (no había 3.8 disponible en el entorno).
- Las 5 suites de paquete suman **267 tests**; las suites transversales añaden **24** más (291 en total).

### - 2026-11-16

#### Añadido
- **`agent-red-team`:** Motor de escaneo estático contra caracteres Unicode invisibles, análisis sintáctico de Python (AST) y plantilla de reporte de riesgos.
- **`humanizador-anti-ia`:** Auditor estilístico de variación rítmica (coeficiente de variación), índice de legibilidad en español, lista de sustituciones naturales y plantilla de informe.
- **`replica`:** Protocolo integral de especificación de aplicaciones, protocolo de motores complejos interactivos (AST de documento, historial de comandos, layout geométrico) y plantillas de alcance, arquitectura, pruebas y preflight.
- **`seo-auditor`:** Unificación del motor de auditoría en modos web, source, local e híbrido, modularización de referencias de SEO técnico, semántico, datos estructurados y hoja de ruta estratégica.
- **`docs/`:** Documentación técnica individualizada para cada componente.

---

## English

All notable changes to this project are documented in this file.

### - 2026-11-18 · `refactor-surgeon` 1.4 — `refactor-hotspots`

#### Added
- **`refactor-hotspots` sub-skill:** ranks files by `git log` churn since a mandatory date times their complexity, so a refactor starts where it pays back most.
- **`scripts/hotspots.py`:** churn from `--since` (a bare date is normalised to `T00:00:00`, because git would round it to the time of the query), per-file `V(G)` with comprehensions counted by their `if`, and score = churn × complexity; `--top`, `--json`, `--fail-on hotspot` with `--min-score`. Without a date, outside a repository or in a shallow clone it returns `measured: false` and exit 2 instead of a false number; deleted files are counted in `skipped` and stay out of the ranking.
- **8 tests** in `refactor-surgeon/tests/test_hotspots.py` against temporary git repositories: no `--since`, not a repository, churn and complexity measured, bare date normalised to midnight, filtering window, ordering and `--top`, `--fail-on hotspot` and a shallow clone.
- **Activation phrases:** 3 positives and 2 negatives in `tests/phrases.json`, verified against the router before being written.

#### Changed
- **Root index `skills.json`:** from **78 to 79 skills**, version 4.1.0; `refactor-surgeon` moves to 1.4.0 with 9 skills.
- **`docs/refactor-surgeon.md` and `README.md`:** Prioritisation mode, command, new row and 42 tests per package.

### - 2026-11-18 · `docs-sync-engine` 1.1 — `docs-terms` and `docs-env`

#### Added
- **`docs-terms` sub-skill:** versioned glossary with `accept.txt` (canonical spelling) and `reject.txt` (banned terms, with `bad => good` to suggest the replacement).
- **`scripts/terms_check.py`:** rules `termino-rechazado` (medium) and `grafia-no-canonica` (low), which reports the variant found in the text (`found`) instead of repeating the canonical one; code blocks and inline code are ignored while keeping line numbers, and `--fail-on` accepts `low|medium|high|none`.
- **`docs-env` sub-skill:** every variable the code reads must be in `.env.example` and in the docs, and declared ones nothing reads are reported.
- **`scripts/env_check.py`:** recognises `os.environ[...]`, `os.environ.get`, `os.getenv`, `process.env.X` and `import.meta.env.X`, and accepts both `KEY=` and `export KEY=` in the example; rules `env-sin-ejemplo`, `env-sin-documentar` (medium) and `ejemplo-sin-uso` (low).
- **16 tests** split between `docs-sync-engine/tests/test_terms_check.py` and `test_env_check.py` (8 each): clean glossary, rejected term with replacement, non-canonical spelling with the real variant, fences without shifting lines, `export`, `process.env`, `import.meta.env`, `--fail-on none` and missing paths or glossaries.

#### Changed
- **Root index `skills.json`:** from **76 to 78 skills**, version 4.0.0; `docs-sync-engine` moves to 1.1.0 with 6 skills.
- **Master and `docs/docs-sync-engine.md`:** Terminology and Environment phases, new rows and commands, and 27 tests per package.

### - 2026-11-18 · `api-contract-guard` 1.1 — `api-auth-coverage`

#### Added
- **`api-auth-coverage` sub-skill:** crosses the contract's `security` with the real guards on the routes, so an endpoint documented as protected does not stay open.
- **`scripts/auth_coverage.py`:** inherits global `security`, normalises `<int:id>` to `{id}`, recognises FastAPI and Flask routes and guard decorators; rules `ruta-sin-guarda` (high), `ruta-sin-spec`, `spec-sin-security` (medium) and `spec-sin-codigo` (low), with `--json` and `--fail-on medium`.
- **9 tests** in `api-contract-guard/tests/test_auth_coverage.py`: guarded routes, contract without a guard, guard without `security`, route outside the contract, operation without code, inherited global security, Flask with normalised parameters, `--fail-on none` and missing contract.

#### Changed
- **Root index `skills.json`:** from **75 to 76 skills**, version 3.9.0; `api-contract-guard` moves to 1.1.0 with 5 skills.
- **Master and `docs/api-contract-guard.md`:** Coverage phase, row, command and 20 tests per package.

### - 2026-11-18 · `db-architect` 1.2 — `db-expand-contract` and `db-sql-lint`

#### Added
- **`db-expand-contract` sub-skill:** splits a migration into an additive phase (`expand`) and a removal phase (`contract`) so it can ship without a maintenance window.
- **`scripts/expand_contract.py`:** classifies every statement and warns about what cannot be staged (`columna-obligatoria-en-un-paso`, `rename-no-divisible`, `reescritura-no-divisible`); anything it does not recognise (`DROP INDEX`, `INSERT`, …) goes to `phases.unknown` with a `sentencia-desconocida` warning and never to `expand`, and the statement splitter respects strings and `$$` function bodies. `--json` and `--fail-on unsafe|none`.
- **`db-sql-lint` sub-skill:** SQL style before the risk guard, with a bounded rule set.
- **`scripts/sql_lint.py`:** `tabla-sin-clave`, `select-asterisco` (medium), `palabra-clave-minuscula`, `identificador-no-snake`, `comparacion-distinta`, `linea-larga`, `tabulador` (low); line comments do not count for identifiers or comparisons, and a `CREATE TABLE` without a trailing `;` is still checked.
- **18 tests** split between `db-architect/tests/test_expand_contract.py` and `test_sql_lint.py` (10 and 8): additive, destructive with `DROP CONSTRAINT`, mixed, mandatory column, type change, `rename`, function body with `;`, unknown statement, clean file, every style rule, `--fail-on none` and missing paths.

#### Changed
- **Root index `skills.json`:** from **73 to 75 skills**, version 3.8.0; `db-architect` moves to 1.2.0 with 9 skills.
- **Master and `docs/db-architect.md`:** Plan phase, `db-sql-lint` in Audit, rows, commands and 48 tests per package.

### - 2026-11-18 · `finops-auditor` 1.3 — `finops-diff`

#### Added
- **`finops-diff` sub-skill:** answers "what does this change cost" by comparing two inventories per resource `id`, and fails the pipeline when the increase goes past what was agreed.
- **`scripts/cost_diff.py`:** `before_total`/`after_total` with their absolute and percentage delta, added, removed and repriced resources, and independent `--max-increase`, `--max-percent` and `--budget` guardrails; `--json`, `--fail-on guardrail|none` and exit codes 0/1/2 for CI.
- **8 tests** in `finops-auditor/tests/test_cost_diff.py`: identical inventories clean, growth with additions and changes, each guardrail breaking the gate with its figure, all three at once, `--fail-on none`, and a missing inventory returning 2.
- **Activation phrases:** 3 positives and 2 negatives in `tests/phrases.json` (`db-lock-audit` and `appsec-infra` win), verified against the router before being written.

#### Changed
- **Root index `skills.json`:** from **70 to 71 skills**, version 3.5.0; `finops-auditor` moves to 1.3.0 with 7 skills.
- **Package master:** **3b (Diff)** phase in the protocol and a new row in the sub-skill table.
- **`docs/finops-auditor.md`, `README.md` and `docs/index.md`:** "six sub-skills", `cost_diff.py` command in both blocks, updated counts and 26 tests described per package.

### - 2026-11-18 · `db-architect` 1.1 — `db-lock-audit` and `db-drift`

#### Added
- **`db-lock-audit` sub-skill:** flags the migration that locks the table or rewrites it, keeping data risk (the guard's job) apart from lock time (this auditor's).
- **`scripts/lock_audit.py`:** rules `reescritura-de-tipo`, `columna-not-null-con-default`, `set-not-null`, `indice-sin-concurrently`, `rename-inseguro`, `fk-sin-not-valid`, `check-sin-not-valid`, `vacuum-full` and `delete-sin-where`, with `--path`, `--json` and `--fail-on low|medium|high|none` (`high` by default); every finding carries the file, line, table, rule and safe alternative. Exit codes 0/1/2, without an engine or a connection.
- **`db-drift` sub-skill:** compares the declared schema with the one produced by replaying the migrations in alphabetical order, per table, per column and per type.
- **`scripts/drift.py`:** rules `tabla-solo-en-esquema`, `tabla-solo-en-migraciones`, `columna-solo-en-esquema`, `columna-solo-en-migraciones` and `tipo-distinto`, applying `CREATE TABLE`, `ADD`/`DROP COLUMN`, `ALTER TYPE`, `RENAME COLUMN`, `RENAME TO` and `DROP TABLE`; flags `--schema`, `--migrations`, `--json` and `--fail-on drift|none`.
- **12 tests** split between `db-architect/tests/test_lock_audit.py` and `db-architect/tests/test_drift.py` (6 each): every lock rule, a safe migration, ignored comments, thresholds and `--fail-on none`; and a matching schema, extra or missing columns and tables, type mismatches, an intermediate rename and a `DROP` of a declared table.
- **Activation phrases:** 2 positives and 2 negatives for `db-lock-audit` (`db-schema-audit` and `replica-diff` win) and 3 + 2 for `db-drift` (`db-seed-gen` and `eval-run` win), verified against the router before being written.

#### Changed
- **Root index `skills.json`:** from **68 to 70 skills**, version 3.4.0; `db-architect` moves to 1.1.0 with 7 skills.
- **Package master:** the flow becomes **Audit → Guard → Lock → Drift → Optimize**, with both sub-skills in the table and wider gates.
- **`docs/db-architect.md`, `README.md` and `docs/index.md`:** new rows and commands, updated counts and 30 tests described per package.

### - 2026-11-18 · `refactor-surgeon` 1.1 — `refactor-clones`

#### Added
- **`refactor-clones` sub-skill:** duplication detection through normalised AST shingles. Identifiers are replaced by their kind (`Name`, `arg`, `Attribute`, `Constant:type`), so a rename shows up as an exact clone instead of slipping through.
- **`scripts/clone_detect.py`:** token windows with Jaccard across functions, `--shingle` (8), `--min-tokens` (20), `--threshold` (0.8), `--json` and `--fail-on clone|none`; every pair carries `clon-exacto`/`clon-cercano`, its similarity and both locations. Exit codes 0/1/2, without running the analysed code.
- **7 tests** in `refactor-surgeon/tests/test_clone_detect.py`: rename detected as an exact clone, distinct functions clean, tiny functions ignored, threshold filtering the pair, `--fail-on none`, missing path and JSON shape.
- **Activation phrases:** 3 positives and 2 negatives in `tests/phrases.json`, verified against the router before being written.

#### Changed
- **Root index `skills.json`:** from **67 to 68 skills**, version 3.3.0; `refactor-surgeon` moves to 1.1.0 with 6 skills.
- **Package master:** `refactor-clones` joins the flow (measure → freeze → deduplicate → cut → verify) and the sub-skill table.
- **`docs/refactor-surgeon.md`, `README.md` and `docs/index.md`:** new row and command, updated counts and 19 tests described per package.

### - 2026-11-18 · `finops-auditor` 2.0, `db-architect`, `api-contract-guard`, `refactor-surgeon` and `docs-sync-engine`

#### Added
- **`finops-auditor` 2.0 (6 skills):** `finops-scan` and `finops-rightsize` plus `finops-llm-scan` (LLM call cost), `finops-infra-scan` (Terraform and Kubernetes) and `finops-ci-opt` (GitHub Actions), with `llm_cost_scan.py`, `infra_cost_scan.py` and `ci_cost_scan.py`, 18 tests and a bilingual guide.
- **`db-architect` (5 skills):** master + `db-schema-audit`, `db-migration-guard`, `db-query-trace` and `db-seed-gen`, with `schema_audit.py`, `migration_guard.py`, `query_trace.py` and `seed_gen.py`, 18 tests and a bilingual guide.
- **`api-contract-guard` (4 skills):** master + `api-diff`, `api-code-sync` and `api-mock-server`, with `contract_diff.py` (SemVer impact), `code_sync.py` (backend/frontend routes) and `mock_server.py` (loopback), 11 tests and a bilingual guide.
- **`refactor-surgeon` (5 skills):** master + `refactor-metrics`, `refactor-harness`, `refactor-slice` and `refactor-verify`, with `code_metrics.py`, `golden_harness.py` and `slice_analyzer.py`, 12 tests and a bilingual guide.
- **`docs-sync-engine` (4 skills):** master + `docs-drift-check`, `docs-arch-gen` and `docs-changelog`, with `docs_drift.py`, `arch_gen.py` and `changelog_gen.py`, 11 tests and a bilingual guide.
- **Wider lint:** `tests/lint_frontmatter.py` now also checks every relative link in every Markdown file and that the root index matches the disk (`skills_total`, skills per package and coverage of every `SKILL.md`), with 7 new tests in `tests/test_lint_links.py`.

#### Changed
- **`run_tests.py`:** the five new suites (`api-contract-guard`, `db-architect`, `docs-sync-engine`, `finops-auditor`, `refactor-surgeon`) run with the rest: 13 suites and 567 tests.
- **Root index `skills.json`:** 12 packages and **67 skills**, version 3.2.0.
- **`README.md` and `docs/index.md`:** counts, rows for the five packages, sub-skill tables and links to the new guides, in Spanish and English.
- **`tests/phrases.json`:** activation phrases for the 13 new skills, verified against the router before being written.

### - 2026-11-18 · `skill-evals` 1.0 and quality gates in CI

#### Added
- **`skill-evals` package (4 skills):** master + `eval-design`, `eval-run` and `eval-report`, with `scripts/evalkit.py` (cases, metrics, collisions, budget and diff), `design.py`, `run.py`, `report.py` and `optimize.py`, plus `references/competitors.md`, `references/metrics.md`, `templates/` and 42 tests. It closes the skill-creator, skill-reach and SkillEvaluator loop without a model or a network.
- **Description optimizer:** candidates only from *train* failures, filtered on *train*, picked on *test*, with a diff and an explicit `--apply`; it never rewrites a `SKILL.md` on its own.
- **Reproducible report:** Markdown or standalone HTML with the failure table, collisions, context budget and a diff against the baseline.
- **`finops-auditor` package (3 skills):** the cloud cost audit for orphaned resources, overprovisioning and rightsizing joins the catalogue. `finops-scan` and `finops-rightsize` move from loose files in `sub-skills/` to their own `SKILL.md` folders with `## Gate de salida` and `## Handoff`, plus manifest, `license`/`metadata`, trigger phrases and the import fix in their tests.
- **CI gate:** the lint job runs `design.py --from-phrases tests/phrases.json --out skill-evals/reports/cases.json` and `run.py --fail-under precision=0.95 --fail-under recall=0.98 --fail-under mrr=0.98`, so a description that breaks routing fails the workflow.

#### Changed
- **Stricter frontmatter lint:** lowercase `name` of at most 64 characters, description between 20 and 1024 characters and body under 500 lines; all 44 `SKILL.md` files carry `license: MIT` plus `metadata.package`/`metadata.version`, kept in sync by `tests/sync_skill_metadata.py --check`.
- **CI workflow:** runs on `pull_request` as well as `push`, with `permissions: contents: read`, `timeout-minutes`, concurrency cancellation and `ruff` (E4/E7/E9/F) next to the suite.
- **Test suite:** 490 tests; counts and skill lists derive from `skills.json` and the filesystem, so a new skill needs no constant edits.

### - 2026-11-17 · `appsec-audit` 1.4 — CI, remediation and scale

#### Added
- **`appsec-ci`:** `detect_tools.py` finds tools through PATH and metadata without installing or running them, and audits the workflow (`pull_request_target` with a write token, PR head checkout, unpinned actions, interpolation injection, exposed secrets). `normalize_sarif.py` turns external SARIF into `needs_validation`, checks `upload-sarif` compatibility and applies `--fail-on`. Ships `references/agent-hardening.md` and `templates/pr-comment.md`.
- **`appsec-fix`:** `apply_patch.py` defaults to dry-run, writes only with `--apply --yes`, keeps a `.orig` copy and requires a declared `--sandbox` for verification; sandbox, rollback and variant analysis policy in `references/remediation.md`.
- **`appsec-scale`:** `scale_report.py` consolidates several repos, draws the repo → vendor topology and estimates hours and cost per phase from profile and rate, documented in `references/scale.md`.
- **Tests:** 27 new tests (122 in the package) and three more sub-skills (11 total, 39 across the repository).

### - 2026-11-17 · `appsec-audit` 1.3 — Threat model and dependencies

#### Added
- **`appsec-threat`:** assets, actors, trust boundaries and abuse cases, with every threat mapped to OWASP Top 10 2025, ASVS 5.0 and its ledger class, plus `templates/threat-model.md` and `references/threat-model.md`.
- **`appsec-deps`:** `scripts/sbom.py` builds a CycloneDX 1.5 SBOM from `package.json`, `requirements.txt`, `pyproject.toml` and `go.mod`, matches advisories by version and ecosystem and decides reachability from imports (`reachable`, `test-only`, `not-imported`, `unknown`), gating on reachable high and critical findings.
- **Expanded catalog:** 14 to 24 attack classes in `references/attack-classes.md`, the ledger and its schema, each with CWE, OWASP 2025 and ASVS chapter.
- **Tests:** 23 new tests (95 in the package), including catalogue-versus-ledger class consistency.

### - 2026-11-17 · `appsec-audit` 1.2 — Phase 1

#### Added
- **Independent verifier:** `templates/verification.md` hands the reviewer only location, CWE, pattern and declared purpose, with no evidence or verdict, and maps each verdict to the fields `findings.json` requires.
- **`scripts/export_sarif.py`:** SARIF 2.1.0 with one rule per CWE, `critica`/`alta` as `error`, `media` as `warning`, `baja` as `note`, `confirmed` only, `needs_validation` as `note` with `--include-pending`, and the fingerprint in `partialFingerprints`.
- **`scripts/diff_scope.py`:** diff/PR mode; turns a patch or `git diff --base` into added-line ranges and separates findings that fall inside the change.
- **`scripts/diff_reports.py`:** fingerprint baseline with `new`, `fixed`, `changed` and `persisting`, plus `--fail-on new` as a PR gate on new `confirmed` findings.
- **Tests:** 26 new tests (72 in the package) and bilingual documentation for all four mechanics.

### - 2026-11-17 · CI, SARIF and traceability

#### Added
- **`agent-red-team/scripts/export_sarif.py`:** exports the report to SARIF 2.1.0 with one rule per category, `critical/high → error`, `medium → warning`, `low → note`, REJECT always `error` and `needs_validation` as `note` only with `--include-pending`. `rejected` findings are never exported. 12 new tests (50 in the package).
- **`tests/lint_frontmatter.py`:** frontmatter lint (delimiters, `name` matching the folder, meaningful `description`) plus package manifest checks, with 6 tests of its own.
- **Real CI:** `.github/workflows/tests.yml` now has two jobs — lint on Ubuntu and the full suite on a **Ubuntu / macOS / Windows matrix** with Python 3.13.

#### Changed
- **`PLAN-MEJORA.md` is retired:** every phase is implemented and its content now lives in the CHANGELOG and each package's guide.

### - 2026-11-17 · `appsec-audit` 1.1 — Phase 0

#### Added
- **Verifiable artifacts:** `init_audit.py` creates `<target>/.appsec-audit/` with `findings.json`, `coverage-ledger.json` and `architecture.md`, valid from the start and never overwritten without `--force`.
- **`schemas/findings.schema.json` and `schemas/coverage-ledger.schema.json`:** closed contract for both artifacts, with allowed fields and enums.
- **`validate_findings.py`:** deterministic validator requiring severity only on `confirmed`, confidence ≥ 7, two exploit steps, a patch, `unresolved` on `needs_validation`, `reason` on `rejected`, a recomputed fingerprint and a `source_unit` that exists in the ledger.
- **`ledger.py`:** creates surface × subsystem × attack-class units, updates their state and exposes `gaps --strict` as the closing gate.
- **Stable fingerprint:** `sha256(cwe|file|root cause)[:32]`, independent of line numbers, for deduplication and re-runs.
- **`references/artifacts.md`** and bilingual guide: verdicts, fingerprints and ledger states.
- **Tests:** 25 new tests for init, validator and ledger (46 in the package).

### - 2026-11-17 · `appsec-audit` 1.0

#### Added
- **`appsec-audit` package (6 skills):** master + `appsec-recon`, `appsec-code`, `appsec-infra`, `appsec-llm` and `appsec-report`. Covers web, APIs, repositories, Docker, IaC, cloud/IAM, binaries and LLM/agent/MCP systems, with a two-phase design (discovery and Sources → Sinks tracing, plus a validation tribunal) and shared assets.
- **Zero rule:** every file, comment, README or string is treated as hostile data; the reviewer runs no project code, installs nothing, makes no unauthorized outbound call and redacts every secret. An indirect injection attempt is reported as a finding.
- **Threshold tribunal:** each candidate answers five questions (reachable, mitigated, applies in production, who exploits it, evidence) and gets 1–10 confidence; **below 7 it is discarded** with the reason logged.
- **`scripts/scan_secrets.py`:** known shapes (AWS, GitHub, Slack, Stripe, Google, JWT, private keys) plus Shannon entropy on generic assignments, with redaction and `--strict` for CI.
- **`scripts/map_flows.py`:** heuristic source → sink candidate index across nine language families, with the nearby source and `--json` output.
- **`scripts/grade.py`:** deterministic A–F grade from validated findings (25 per critical, 10 per high, 3 per medium, 1 per low, floored at 0); discarded findings score nothing.
- **`references/`:** `benchmark.md` (the seven references compared with the improvement applied), `sources-sinks.md`, `owasp-cwe.md`, `cloud-iac.md`, `llm-agents-mcp.md` and `prompt-injection-defense.md`.
- **`templates/`:** full report, single finding sheet and tribunal worksheet.
- **Tests:** 21 of its own (structure, frontmatter, gates and handoff, manifest, secrets with fixtures, tracing and the three scripts' exit codes).
- **`docs/appsec-audit.md`:** bilingual guide including the inherited-mechanic comparison table.

#### Changed
- **Root index `skills.json`:** 6 packages, **34 skills**.
- **`run_tests.py`:** the `appsec-audit` suite runs with the rest (329 tests in total).
- **`tests/phrases.json`:** 21 new positive and 12 new negative phrases, with no collision against `agent-red-team` or `seo-audit`.
- **`README.md` and `docs/index.md`:** counts, package table and guide link in Spanish and English.
- **`tests/test_triggers.py`:** dataset coverage moves from 28 to 34 skills.

### - 2026-11-17 · `premium-web-designer` 2.1

#### Added
- **`premium-qa` sub-skill:** independent audit of an existing site with a measurement protocol at 360/390/768/1024/1440 px, numeric gates (0 overflow, headline at most 3 lines, 44 px controls, anchors clear of sticky headers, focus inside overlays) and a severity-based report.
- **`scripts/delivery_check.py`:** stdlib static gate covering `lang`, title, description, canonical, Open Graph, heading order, `alt`, JSON-LD, `:focus-visible`, `prefers-reduced-motion`, sticky header without `scroll-padding-top`, asset versioning, `robots.txt`, `sitemap.xml` and `llms.txt`. Exits 1 on any `must` failure.
- **`references/qa-metrics.md`:** console snippet with expected readings, anchor check and stale-CSS diagnosis.
- **`--public` mode in the gate:** canonical, Open Graph with image, `robots.txt` and `sitemap.xml` move from advice to `must` when the folder is going live, with a fixture and five tests pinning the severity change and the exit code.
- **Hosting headers:** the gate detects `_headers`, `netlify.toml` and `vercel.json`, and in `--public` mode warns when CSP or HSTS with `max-age` are missing (`HDR-001..003`), with a `site_public` fixture and tests for all three formats.
- **`references/known-defects.md`:** catalogue of the six defects measured in a real review (headline in a narrow column, early breakpoint, tiny controls, anchor under the header, stale CSS and incomplete metadata), each with symptom, before/after measurement, cause, fix and the check that catches it.
- **Tests:** six gate tests with correct and defective fixtures (43 in the package).
- **`references/performance-seo.md`:** per-page SEO minimum (canonical, Open Graph with image, heading order, declared sitemap, `llms.txt`) and deployment security headers.

#### Fixed (found while reviewing a real demo)
- The master gave no measurable criteria: the demo shipped a five-line `h1` from grid auto-placement, 214 px steps at 768, 34–39 px controls, anchors hidden behind the sticky header and stale CSS. All are now explicit gates in the master and in `premium-qa`.
- The master shrinks from 440 to 111 lines, with detail living in `agents/`, `workflows/`, `references/` and the sub-skill.

### - 2026-11-17

#### Changed
- **Multi-skill architecture:** each package moves from a monolithic skill to **master + sub-skills** with real-world usage boundaries. Assets (`references/`, `scripts/`, `templates/`, `tests/`) remain shared at the package root with zero duplication.
- **Root index `skills.json`:** 5 packages, **27 skills** in total, including `premium-web-designer` as a standalone skill.
- **`README.md`:** module and sub-skill tables in both Spanish and English, alongside the standardized package layout.
- **Signature decoupling in `agent-red-team`:** detection rules and patterns are extracted from `scripts/scan_skill.py` into `scripts/rules.json` (with `--rules` CLI support) to eliminate heuristic false positives in local antivirus engines.

#### Added
- **`replica` (14 skills):** master + `replica-recon` (0-1b), `replica-architect` (2), `replica-design` (3), `replica-build` (4), `replica-backend` (5), `replica-test` (6), `replica-diff` (7), `replica-entrepreneur` (8), `replica-brand` (9), `replica-launch` (10), `replica-deploy` (11), `replica-static` (12, opt-in), and `replica-redes` (13). Every sub-skill declares preconditions, method, exit gate, and handoff.
- **`seo-auditor` (6 skills):** master + `seo-audit`, `seo-plan`, `seo-execute`, `seo-serp`, and `seo-compare`, distributing the 11 CLI commands without duplicating the module-to-command table.
- **`agent-red-team` (3 skills):** master + `red-scan` (guidance mode, no files written) and `red-audit` (full audit with independent verification and coverage ledger).
- **`humanizador-anti-ia` (3 skills):** master + `humanizar` (rewriting) and `detector-ia` (scoring only, leaving text untouched).
- **Sub-skill index in every master `SKILL.md`**, including the unified installation note and package-relative paths.
- **Master/sub-skill coherence tests** in `tests/test_coherence.py` (11 tests): ensures no sub-skill duplicates prose from its master (CLI commands may repeat within limits), all include `## Gate de salida` and `## Handoff`, every master indexes its sub-skills, previously fixed contradictions do not regress (`dos condiciones`, `Quick en detalle`, module table, duplicate `rescore`), commands run cleanly from the repo root, and master files stay within size bounds.
- **Activation (trigger) tests** for all 27 skills in `tests/`: deterministic offline lexical router (`trigger_router.py`), a 112-phrase dataset (58 positive and 54 negative), and 13 tests verifying global top-1 routing, intra-package selection, non-overlapping sibling boundaries, out-of-domain phrases, and determinism.

