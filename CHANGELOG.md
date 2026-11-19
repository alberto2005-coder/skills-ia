# Changelog / Registro de Cambios

*[Español](#español) · [English](#english)*

---

## Español

Todas las modificaciones notables de este proyecto están documentadas en este archivo.

### - 2026-11-19 · Fase 1: el manifiesto como fuente única de la versión

#### Añadido

- **`tests/version_guard.py`:** guardia para PRs y pushes. Compara el manifiesto de cada paquete entre la base (`--base REV`, por defecto `HEAD~1`) y el árbol actual: si hay ficheros cambiados dentro del paquete y la `version` del manifiesto no sube, falla indicando el paquete, el número de ficheros y la versión que sigue vigente. `--bumped` imprime `<paquete> <versión>` de las subidas, que es lo que necesitarán los workflows de publicación.
- **Seis tests** de la guardia en `tests/test_version_guard.py`, sobre repositorios git temporales: cambio sin subir, cambio con subida, cambios fuera de paquetes, subidas detectadas, paquete nuevo y versión no semver.
- **Dos tests** en `tests/test_lint_frontmatter.py` para la coherencia de versiones: índice contra manifiesto y `metadata.version` contra manifiesto.
- **CI:** el job de lint hace `fetch-depth: 0` y ejecuta `tests/version_guard.py --base`, con `github.event.pull_request.base.sha` o `github.event.before` según el evento.

#### Cambiado

- **`tests/lint_frontmatter.py`:** nueva comprobación `lint_versions`. El manifiesto de cada paquete es la fuente única: el índice raíz y el `metadata.version` de cada `SKILL.md` deben coincidir con él, y la versión debe ser `X.Y.Z`. Los avisos del índice ya no se sobrescriben al mezclarse con los de versión.
- **`tests/sync_skill_metadata.py`:** toma la versión del manifiesto del paquete en lugar del índice raíz.
- **`README.md` y `docs/index.md`:** documentan la guardia y su comando en la lista de puertas.

#### Verificado

- Los 12 paquetes ya coincidían en las tres copias, así que ninguna versión necesitó sincronizarse.
- `run_tests.py` → **697 tests, 13/13 suites**; `pytest`; `ruff check .` limpio; `tests/lint_frontmatter.py` OK con 79 `SKILL.md`; `tests/metrics_gate.py` → 0 hallazgos `high` y 0 clones.

### - 2026-11-19 · Puertas de CI documentadas en el índice

#### Cambiado

- **`docs/index.md`:** la sección «Tests» deja de listar solo `run_tests.py` y enumera los comandos del workflow (`pytest`, `ruff`, `tests/lint_frontmatter.py`, `tests/metrics_gate.py`), con qué valida cada uno: frontmatter por PyYAML, techo de métricas en `tests/metrics_baseline.json` y matriz 3.9/3.14 en Linux, macOS y Windows.

#### Verificado

- `run_tests.py` y `pytest -q` → **689 tests, 13/13 suites**; `ruff check .` limpio; `tests/lint_frontmatter.py` OK con 79 `SKILL.md`; `tests/metrics_gate.py` → **0 hallazgos `high` y 0 clones**; `markdownlint-cli2` → 0 avisos en 189 Markdown.

### - 2026-11-19 · El lint de frontmatter valida con PyYAML

#### Cambiado

- **`tests/lint_frontmatter.py`:** deja de partir el bloque línea a línea y lo valida con `yaml.safe_load`, así que un YAML inválido (por ejemplo una `description` con «English: …» dentro) es un problema del lint y no un falso OK. `name` y `description` deben ser texto, y la longitud de la descripción se mide sin el salto que añade el escalar plegado.
- **Dependencia:** PyYAML ya estaba en el grupo `dev` de `pyproject.toml`, así que no hizo falta añadir nada ni tocar `uv.lock`.

#### Añadido

- **Dos tests** en `tests/test_lint_frontmatter.py`: el bloque con dos puntos y espacio dentro de `description` se reporta como YAML inválido, y la descripción plegada `>` se acepta.

#### Verificado

- El lint sobre los 79 `SKILL.md` que le toca → OK; `parse_frontmatter` sobre los 81 del repo, fixtures incluidas → 81 válidos.
- `run_tests.py` → **689 tests, 13/13 suites**; `ruff check .` limpio.

### - 2026-11-19 · Frontmatter válido en YAML: 41 `SKILL.md` corregidos

#### Corregido

- **`description` con dos puntos:** 41 de los 81 `SKILL.md` declaraban la descripción como escalar plano con dos puntos y espacio dentro, casi siempre el sufijo «English: …». Para un parser YAML real el bloque era inválido (`mapping values are not allowed here`), así que la app rechazaba el paquete con «SKILL.md must open with a YAML frontmatter block».
- **Forma adoptada:** esas descripciones pasan a escalar plegado `description: >` con el texto indentado dos espacios, el mismo formato que ya usaban `premium-web-designer` y `skill-evals`. El texto no cambia: el valor es la misma cadena.
- **Verificado:** `safe_load` de PyYAML sobre los 81 bloques → **81/81 válidos**; `name` y el resto de claves intactos; CRLF preservado.

### - 2026-11-19 · Techo de métricas a cero: dieciocho funciones partidas en seis paquetes

#### Cambiado (interno)

- **`seo-auditor`:** `render_markdown` (V(G) 29), `render_html` (24 y 178 líneas), `audit_web` (40 y 184 líneas), `handle_starttag` (23 con anidamiento 12), `rich_preview` (25), `audit_headers` (21), `build` (154 líneas), `build_plan` (24) y los dos `analyze` de `indexcheck` (22) y `hreflang` (22) quedan partidos por responsabilidad: cabecera, grupos y datos medidos en el informe; ajustes, robots, cabeceras, canonical, sitemap y presencia en el índice; carga de robots, sondeo de `llms.txt`, crawl, sitemap y ensamblado de checks en el rastreo. Los dos `handle_starttag` despachan por etiqueta con una tabla en lugar de anidar ramas.
- **`agent-red-team`:** `_validate_rules` (27), `analyze_python_ast` (33 con anidamiento 8) y `scan_target` (24) se reparten en validadores por sección de las reglas, hallazgos por tipo de nodo del AST y escaneo por fichero.
- **`appsec-audit`:** los `main` de `apply_patch` (25) y `sbom` (22) delegan en un helper por subcomando y `validate_ledger` (34) valida raíz, unidad y listas por separado.
- **`db-architect`:** `build_model` (21 con anidamiento 8) aplica cada tipo de sentencia con su propio aplicador detrás de una tabla, sin cambiar el orden de texto del que depende `drift`.
- **`premium-web-designer`:** `check_page` (28 y 160 líneas) agrupa sus quince comprobaciones por concern y `handle_starttag` (anidamiento 9) despacha por etiqueta.
- **`replica`:** `read_png` (27) separa lectura de chunks, validación de IHDR y reconstrucción de filtros; `check_platform` (26) separa longitud, keywords, capturas y términos vetados.
- **`tests/metrics_baseline.json`:** el techo de hallazgos `high` baja de **26 a 0**. Los recuentos por función no cambian de comportamiento: los informes, los códigos de salida y los mensajes de error son los que fijan las suites.

#### Verificado

- `run_tests.py` → **687 tests, 13/13 suites**; `ruff check .` limpio; `tests/lint_frontmatter.py` OK con 79 `SKILL.md`; `tests/metrics_gate.py` → **0 hallazgos `high` y 0 clones**.

### - 2026-11-19 · `pytest` en CI, una sola escala de severidad y helpers por paquete

#### Añadido

- **`pytest` en CI:** un paso `uv run --locked pytest -q` dentro del job de matriz, justo después de `run_tests.py`, así que el comando que usa el usuario corre en cada push sobre la matriz 3.9/3.14 y en Linux, macOS y Windows.
- **`docs/index.md` — «Severidad y `--fail-on`:** escala canónica, distinción entre riesgo (`severity`) y puerta (`severity_level`/`gate`), y la tabla de valores válidos de `--fail-on` para las 17 herramientas que lo aceptan.
- **`scripts/appsec_util.py`, `db_util.py` y `finops_util.py`:** un módulo por paquete (nombre único, para que dos suites no compartan módulo en `pytest`) con `force_utf8_output`, `relative_parts`, `split_top_level` e `iter_files` parametrizado. Se queda dentro de cada paquete a propósito: la autosuficiencia es un invariante con test propio.
- **Gate de métricas en CI:** `tests/metrics_gate.py` ejecuta `code_metrics` y `clone_detect` sobre el repo y compara el resultado con el techo aceptado en `tests/metrics_baseline.json` (`high` ≤ 26 y 0 clones con `--min-tokens 120 --threshold 0.95`); crecer por encima rompe el job de lint, que lo invoca en el paso «Code metrics ratchet».
- **Cuatro tests de contrato:** `seo-auditor/tests/test_severity_contract.py` (5) fija que cada registro de `checks` lleve solo `severity_level` y que `findings` declare riesgo y puerta en escalas distintas; `appsec-audit/tests/test_format_contract.py` (2) valida el payload contra `findings.schema.json` y exige `TOOL_VERSION` y `format_version` en el SARIF; `tests/test_versions.py` (2) cruza la versión de frontmatter, `skills.json` e índice raíz; `tests/test_docs_sync.py` (2) compara la tabla `--fail-on` de `docs/index.md` con las opciones reales de cada script y los recuentos de tests documentados con el descubrimiento de pytest.

#### Cambiado (contrato)

- **`severity` unificada:** `critical` → `high` → `medium` → `low` (`info` donde aplica, `reject` en `agent-red-team`). `appsec-audit` pasa de `critica/alta/media/baja` a la escala canónica en `detect_tools`, `validate_findings`, el esquema JSON, `export_sarif` y `grade`; `grade` sigue aceptando las variantes en español como alias. `agent-red-team` deja de emitir `CRÍTICA/ALTA/MEDIA/BAJA` y emite la misma escala, lo que arregla el SARIF: sus `LEVELS` ya esperaban inglés y todo caía en `note`.
- **`migration_guard.py`:** la severidad `warning` pasa a `medium`; `--fail-on warning` se mantiene como alias para no romper pipelines existentes.
- **`premium-web-designer`:** `severity` pasa a la escala de riesgo (`high`/`medium`/`low`) y el nivel de puerta se conserva en `gate` (`must`/`should`/`nice`).

#### Corregido

- **`validate_findings._check_finding` (complejidad 47):** partida en diez validadores (`_check_fields`, `_check_identity`, `_check_verdict`, `_check_location`, `_check_severity`, `_check_confirmed`, `_check_pending`, `_check_source_unit`, `_check_fingerprint`), con el mismo orden de errores.
- **`audit_style.analyze_text` (179 líneas):** partida en `_sentence_stats`, `_text_signals`, `_readability_score`, `_repeated_starts`, `_score_block` y `_issue_list`; el diccionario de salida y los textos de `issues` no cambian.
- **`agent-red-team`, severidades mezcladas:** `scan_skill.py` traduce al cargar cualquier severidad declarada en las reglas (`rules.json` migrado a la escala canónica) y rechaza la que no reconoce. Sin eso, un `SKILL.md` con «ignore all previous instructions» se detectaba con `CRÍTICA`, nadie la puntuaba y el veredicto salía **APROBADO con score 0**; ahora da 90 y BLOQUEADO. Cargar reglas también valida la forma de cada entrada y no rechaza un fichero que omita `network_imports`, que es opcional.

#### Documentación

- **`premium-web-designer/AGENTS.md` eliminado:** duplicaba reglas de `SKILL.md`, estaba solo en inglés y, al vivir dentro de la carpeta instalable, un agente podía leerlo como instrucciones de proyecto globales.
- **18 `SKILL.md`:** desaparece el espacio huérfano que dejó la retirada de `(skills-ia-main/)` («desde la raíz del repositorio** .»).
- **Estructura estándar aclarada** en `README.md` y `docs/index.md`: `scripts/`, `tests/` y `skills.json` están en todos los paquetes; `references/` y `templates/` solo cuando hacen falta (cuatro paquetes no las tienen).
- **Docs de severidad alineadas** en `docs/agent-red-team.md`, `docs/db-architect.md`, `docs/premium-web-designer.md`, `docs/seo-auditor.md`, `appsec-audit/SKILL.md`, `appsec-deps/SKILL.md` y las referencias de appsec.
- **Formato Markdown normalizado en los 79 ficheros:** encabezados, listas y fences quedan rodeados de una línea en blanco, sin líneas dobles ni espacios finales y con salto final de fichero, conservando CRLF, frontmatter, tablas y saltos duros de dos espacios. `.markdownlint.json` fija las convenciones del repo: activas las reglas de estructura (MD022, MD031, MD032, MD040, MD047) y desactivadas con criterio las de estilo que chocan con el formato existente (MD013 líneas largas, MD024 solo entre hermanos, MD029 numeración de pasos, MD034 URLs desnudas, MD036 negrita como rótulo, MD041 plantillas que empiezan en `##`, MD060 estilo de tablas). `npx markdownlint-cli2 "**/*.md"` sale con **0 avisos en 190 ficheros**.
- **Errores estructurales corregidos de paso:** pipes escapados dentro de celdas en `appsec-audit/references/cloud-iac.md` y `prompt-injection-defense.md` (metían columnas de más en la tabla), lenguaje `text` en seis fences que no lo declaraban, `##` para los cinco grupos y el «Pack español» del catálogo del humanizador (eran varios H1 en el mismo documento) y fuera el `:` final del encabezado de `replica/templates/complex-app-spec.md`.

#### Versiones

- **`findings.json` formato 2.0:** `init_audit.py` y `normalize_sarif.py` declaran `format_version`, el esquema lo documenta y `export_sarif.py` deja de caer en un `1.2.0` fijo: `tool.driver.version` sale de `appsec_util.TOOL_VERSION` (2.0.0) y las propiedades del run llevan `format_version`. El SBOM usa la misma constante en vez de su `1.3.0` propio.
- **`seo-auditor` 3.0.0:** los registros de `checks` del JSON dejan de usar `severity` para la puerta y pasan a `severity_level`, así que en todo el paquete `severity` es siempre el riesgo (`high`/`medium`/`low`) y solo aparece en `findings`. Ajustados `analyze.py`, el informe (que ahora agrega `counts_by_level` en vez de `counts_by_severity`), el plan, el comparador, la CLI y `TOOL_VERSION` del motor, que pasa a 3.0.0.
- **`appsec-audit` 2.0.0, `agent-red-team` 3.0.0, `db-architect` 2.0.0 y `premium-web-designer` 3.0.0:** el JSON cambia de forma incompatible (severidad canónica en `appsec-audit` y `agent-red-team`, `warning` → `medium` en `migration_guard`, `severity`/`gate` en `premium-web-designer`), así que el salto es de major. Sincronizados el `skills.json` de cada paquete, el frontmatter del maestro y de sus sub-skills, la plantilla de informe de red team y el índice raíz, que pasa a **5.0.0** con fecha **2026-11-19**.

#### Verificado

- `run_tests.py` → **687 tests, 13/13 suites**; `pytest -q` → 687; `ruff check .` limpio; `tests/lint_frontmatter.py` OK con 79 `SKILL.md`; `tests/metrics_gate.py` dentro del techo (26 `high`, 0 clones); `markdownlint-cli2` con 0 avisos en 190 Markdown.

### - 2026-11-19 · Puertas que sí cierran, `pytest` desde la raíz y recuentos alineados

#### Corregido (contrato de las herramientas)

- **`db-architect/scripts/query_trace.py` y `schema_audit.py`:** `--fail-on` deja de aceptar `low`; quedan `medium|none` y `medium|high|none`. Un umbral que ninguna regla puede alcanzar es una puerta que nunca cierra.
- **`docs-sync-engine/scripts/docs_drift.py`:** `--fail-on` solo `high|none`, las dos únicas severidades que emite.
- **`api-contract-guard/scripts/contract_diff.py`:** si ningún contrato declara versión, `version` sale como `"none"` en lugar de inventar una cifra; el impacto SemVer se calcula igual.
- **`replica/scripts/sweep.py`:** un directorio vacío devuelve **2** («no se escaneó nada») y no 0, que se confundía con un barrido limpio.
- **`premium-web-designer/scripts/delivery_check.py`:** `HTML-004` pasa a `must` al auditar con `--public`.

#### Añadido

- **`pytest` desde la raíz:** `conftest.py` que añade cada `tests/` a `sys.path` y `[tool.pytest.ini_options]` en `pyproject.toml` con `--import-mode=importlib` y las 13 rutas de test. Los tres `config.py` de paquete pasan a `appsec_config.py`, `pwd_config.py` y `evals_config.py` (22 imports actualizados), y los `test_structure.py`, `test_report.py`, `test_templates.py` y `test_security.py` repetidos dejan de resolverse al mismo módulo.
- **Flags reales de `seo-auditor` documentados:** `--allow-local` (loopback y rangos privados, en `audit`, `index`, `serp`, `perf`, `headers`, `schema`, `hreflang` y `onpage`) y `--no-rich-preview` (omite `schema/rich-preview.html`), en `seo-auditor/USAGE.md` y `docs/seo-auditor.md`.

#### Corregido (herramientas)

- **`db-architect`:** el `CREATE TABLE` sin `;` final se analiza; `seed_gen` parte `DECIMAL(10,2)` sin romper la columna y no confunde una FK autorreferenciada con un ciclo; `drift` aplica las operaciones en orden de texto y entiende `op.create_table`, `op.add_column` y el resto de Alembic; `query_trace` solo cuenta llamadas del cuerpo del bucle y distingue el ORM; `schema_audit` con `fix` genera `CREATE INDEX`; `lock_audit` ignora los comentarios en línea; las tres lecturas de SQL usan `errors="replace"`.
- **`seo-auditor`:** decodificación con el `charset` real (`httpbody.py`) y detección de codificación al leer ficheros; `heading_sequence` respeta el orden del documento; `robots` captura `TimeoutError` y `socket.timeout` y se evalúa con `AUDITOR_AGENT`; `web_audit.fetch` mide el TTFB al primer byte; `sitemap` usa el opener seguro; `--allow-local` en los ocho comandos de red (`audit`, `index`, `serp`, `perf`, `headers`, `schema`, `hreflang`, `onpage`); `--rate` y `--timeout` validados; la descripción mínima del SERP sube a 70 caracteres; una respuesta sin `Content-Type` que empieza por `<` se analiza.
- **`replica` y `premium-web-designer`:** `imgdiff` sale 2 con un PNG corrupto y cuenta las filas sobrantes; `sweep` informa `skipped_large_files`; `contrast` falla cuando no hay pares por defecto; `listing` normaliza `avoid`; `parity` rechaza prioridad desconocida y filas que no son objetos; `delivery_check` resuelve rutas relativas, mira `<style>` en línea y documenta sus códigos de salida.
- **Resto:** `code_sync` compara ruta→conjunto de métodos y detecta el método de `fetch`; `llm_cost_scan` reconoce `Model.create`; `auth_coverage` tolera `SyntaxError` y no confunde `@author_only` con una guarda; `mock_server` cruza verbo y `{param}`; `docs_drift` y `terms_check` (BOM) afinados; `set(item.parts)` en ocho scripts; `hotspots` sin git, con rutas normalizadas y una sola `V(G)`; `golden_harness`, `evalkit`, `ci_cost_scan`, `cost_diff` y `changelog_gen` corregidos; `finops_analyzer` aplica la regla del 10–25 %.

#### Documentación

- Recuentos alineados con los tests reales: `docs/appsec-audit.md` 122 → **125**, `docs/refactor-surgeon.md` 42 → **44** y `docs/db-architect.md` «seis scripts» → **ocho**, en español y en inglés.

#### Verificado

- `uv run pytest -q` → **673 passed** en 13 suites; `run_tests.py` → las 13 suites OK con 673 tests; `ruff check .` limpio; `tests/lint_frontmatter.py` OK con 79 `SKILL.md`.

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

### - 2026-11-19 · Phase 1: the manifest as the single source of the version

#### Added

- **`tests/version_guard.py`:** a guard for pull requests and pushes. It compares each package manifest between the base (`--base REV`, `HEAD~1` by default) and the current tree: if files inside the package changed and the manifest `version` did not go up, it fails with the package, the file count and the version that is still in place. `--bumped` prints `<package> <version>` for the bumps, which is what the publishing workflows will need.
- **Six tests** for the guard in `tests/test_version_guard.py`, over temporary git repositories: change without a bump, change with a bump, changes outside packages, detected bumps, new package and non-semver version.
- **Two tests** in `tests/test_lint_frontmatter.py` for version coherence: index against manifest and `metadata.version` against manifest.
- **CI:** the lint job checks out with `fetch-depth: 0` and runs `tests/version_guard.py --base`, using `github.event.pull_request.base.sha` or `github.event.before` depending on the event.

#### Changed

- **`tests/lint_frontmatter.py`:** new `lint_versions` check. Each package manifest is the single source: the root index and every `SKILL.md` `metadata.version` must match it, and the version must be `X.Y.Z`. Index findings are no longer overwritten when merged with the version ones.
- **`tests/sync_skill_metadata.py`:** reads the version from the package manifest instead of the root index.
- **`README.md` and `docs/index.md`:** document the guard and its command in the gate list.

#### Verified

- All 12 packages were already aligned across the three copies, so no version had to be synced.
- `run_tests.py` → **697 tests, 13/13 suites**; `pytest`; `ruff check .` clean; `tests/lint_frontmatter.py` OK with 79 `SKILL.md`; `tests/metrics_gate.py` → 0 `high` findings and 0 clones.

### - 2026-11-19 · CI gates documented in the index

#### Changed

- **`docs/index.md`:** the "Tests" section no longer lists only `run_tests.py`; it names the workflow commands (`pytest`, `ruff`, `tests/lint_frontmatter.py`, `tests/metrics_gate.py`) and what each one checks: frontmatter through PyYAML, the metrics ceiling in `tests/metrics_baseline.json`, and the 3.9/3.14 matrix on Linux, macOS and Windows.

#### Verified

- `run_tests.py` and `pytest -q` → **689 tests, 13/13 suites**; `ruff check .` clean; `tests/lint_frontmatter.py` OK with 79 `SKILL.md`; `tests/metrics_gate.py` → **0 `high` findings and 0 clones**; `markdownlint-cli2` → 0 issues across 189 Markdown files.

### - 2026-11-19 · Frontmatter lint validates with PyYAML

#### Changed

- **`tests/lint_frontmatter.py`:** it no longer splits the block line by line and validates it with `yaml.safe_load`, so invalid YAML (for example a `description` containing "English: …") is a lint problem instead of a false OK. `name` and `description` must be text, and the description length is measured without the newline the folded scalar adds.
- **Dependency:** PyYAML was already in the `dev` group of `pyproject.toml`, so nothing had to be added and `uv.lock` is untouched.

#### Added

- **Two tests** in `tests/test_lint_frontmatter.py`: the block with a colon and a space inside `description` is reported as invalid YAML, and the folded `>` description is accepted.

#### Verified

- The lint over the 79 `SKILL.md` it covers → OK; `parse_frontmatter` over all 81 in the repo, fixtures included → 81 valid.
- `run_tests.py` → **689 tests, 13/13 suites**; `ruff check .` clean.

### - 2026-11-19 · Valid YAML frontmatter: 41 `SKILL.md` files fixed

#### Fixed

- **`description` containing a colon:** 41 of the 81 `SKILL.md` files declared the description as a plain scalar with a colon and a space inside it, mostly the "English: …" suffix. A real YAML parser rejected the block (`mapping values are not allowed here`), so the app refused the package with "SKILL.md must open with a YAML frontmatter block".
- **Shape adopted:** those descriptions become a folded scalar `description: >` with the text indented by two spaces, the format `premium-web-designer` and `skill-evals` already used. The text does not change: the value is the same string.
- **Verified:** PyYAML `safe_load` over the 81 blocks → **81/81 valid**; `name` and the remaining keys untouched; CRLF preserved.

### - 2026-11-19 · Metrics ceiling down to zero: eighteen functions split across six packages

#### Changed (internal)

- **`seo-auditor`:** `render_markdown` (V(G) 29), `render_html` (24 and 178 lines), `audit_web` (40 and 184 lines), `handle_starttag` (23 with nesting 12), `rich_preview` (25), `audit_headers` (21), `build` (154 lines), `build_plan` (24) and both `analyze` functions in `indexcheck` (22) and `hreflang` (22) are split by responsibility: header, groups and measured data in the report; directives, robots, headers, canonical, sitemap and presence in the index; robots loading, `llms.txt` probing, crawl, sitemap and check assembly in the crawler. Both `handle_starttag` implementations dispatch by tag through a table instead of nesting branches.
- **`agent-red-team`:** `_validate_rules` (27), `analyze_python_ast` (33 with nesting 8) and `scan_target` (24) become validators per rules section, findings per AST node type and a scan per file.
- **`appsec-audit`:** the `main` functions in `apply_patch` (25) and `sbom` (22) delegate to one helper per subcommand, and `validate_ledger` (34) validates the root, each unit and its lists separately.
- **`db-architect`:** `build_model` (21 with nesting 8) applies each statement kind through its own applier behind a table, without changing the text order `drift` depends on.
- **`premium-web-designer`:** `check_page` (28 and 160 lines) groups its fifteen checks by concern, and `handle_starttag` (nesting 9) dispatches by tag.
- **`replica`:** `read_png` (27) separates chunk reading, IHDR validation and filter reconstruction; `check_platform` (26) separates length, keyword, screenshot and avoid-term checks.
- **`tests/metrics_baseline.json`:** the `high` ceiling drops from **26 to 0**. Behaviour is unchanged: reports, exit codes and error messages are the ones the suites pin.

#### Verified

- `run_tests.py` → **687 tests, 13/13 suites**; `ruff check .` clean; `tests/lint_frontmatter.py` OK with 79 `SKILL.md`; `tests/metrics_gate.py` → **0 `high` findings and 0 clones**.

### - 2026-11-19 · `pytest` in CI, a single severity scale and per-package helpers

#### Added

- **`pytest` in CI:** a `uv run --locked pytest -q` step inside the matrix job, right after `run_tests.py`, so the command the user actually runs executes on every push across the 3.9/3.14 matrix and on Linux, macOS and Windows.
- **`docs/index.md` — "Severity and `--fail-on`":** the canonical scale, the split between risk (`severity`) and gate (`severity_level`/`gate`), and the valid `--fail-on` values for the 17 tools that accept it.
- **`scripts/appsec_util.py`, `db_util.py` and `finops_util.py`:** one module per package (unique name, so two suites never share a module under `pytest`) with `force_utf8_output`, `relative_parts`, `split_top_level` and a parameterised `iter_files`. It stays inside each package on purpose: self-containment is an invariant with a test of its own.
- **Metrics gate in CI:** `tests/metrics_gate.py` runs `code_metrics` and `clone_detect` over the repo and compares the result with the ceiling in `tests/metrics_baseline.json` (`high` ≤ 26 and 0 clones with `--min-tokens 120 --threshold 0.95`); exceeding it fails the lint job, which calls it in the "Code metrics ratchet" step.
- **Four contract tests:** `seo-auditor/tests/test_severity_contract.py` (5) pins that every `checks` record carries only `severity_level` and that `findings` declare risk and gate on separate scales; `appsec-audit/tests/test_format_contract.py` (2) validates the payload against `findings.schema.json` and requires `TOOL_VERSION` and `format_version` in the SARIF; `tests/test_versions.py` (2) cross-checks the frontmatter version, `skills.json` and the root index; `tests/test_docs_sync.py` (2) compares the `--fail-on` table in `docs/index.md` with each script's real choices and the documented test counts with pytest discovery.

#### Changed (contract)

- **Unified `severity`:** `critical` → `high` → `medium` → `low` (`info` where relevant, `reject` in `agent-red-team`). `appsec-audit` moves from `critica/alta/media/baja` to the canonical scale in `detect_tools`, `validate_findings`, the JSON schema, `export_sarif` and `grade`; `grade` still accepts the Spanish variants as aliases. `agent-red-team` stops emitting `CRÍTICA/ALTA/MEDIA/BAJA` and emits the same scale, which fixes its SARIF: `LEVELS` already expected English, so everything fell through to `note`.
- **`migration_guard.py`:** `warning` becomes `medium`; `--fail-on warning` is kept as an alias so existing pipelines do not break.
- **`premium-web-designer`:** `severity` moves to the risk scale (`high`/`medium`/`low`) while the gate level is kept in `gate` (`must`/`should`/`nice`).

#### Fixed

- **`validate_findings._check_finding` (complexity 47):** split into ten validators (`_check_fields`, `_check_identity`, `_check_verdict`, `_check_location`, `_check_severity`, `_check_confirmed`, `_check_pending`, `_check_source_unit`, `_check_fingerprint`) with the same error order.
- **`audit_style.analyze_text` (179 lines):** split into `_sentence_stats`, `_text_signals`, `_readability_score`, `_repeated_starts`, `_score_block` and `_issue_list`; the output dictionary and `issues` wording are unchanged.
- **`agent-red-team`, mixed severities:** `scan_skill.py` now translates any severity declared by the rules at load time (`rules.json` migrated to the canonical scale) and rejects one it does not recognise. Without it, a `SKILL.md` containing "ignore all previous instructions" was detected as `CRÍTICA`, nothing scored it and the verdict came out **APPROVED with score 0**; it now scores 90 and BLOCKS. Loading rules also validates each entry's shape and no longer rejects a file that omits `network_imports`, which is optional.

#### Documentation

- **`premium-web-designer/AGENTS.md` removed:** it duplicated `SKILL.md` rules, was English-only and, living inside the installable folder, could be read by an agent as project-wide instructions.
- **18 `SKILL.md` files:** the orphaned space left by removing `(skills-ia-main/)` ("from the repository root** .") is gone.
- **Standard structure clarified** in `README.md` and `docs/index.md`: `scripts/`, `tests/` and `skills.json` are in every package; `references/` and `templates/` only when needed (four packages have neither).
- **Severity docs aligned** in `docs/agent-red-team.md`, `docs/db-architect.md`, `docs/premium-web-designer.md`, `docs/seo-auditor.md`, `appsec-audit/SKILL.md`, `appsec-deps/SKILL.md` and the appsec references.
- **Markdown formatting normalised across the 79 files:** headings, lists and fences are surrounded by one blank line, with no double blanks, no trailing spaces and a final newline, keeping CRLF, frontmatter, tables and two-space hard breaks. `.markdownlint.json` pins the repo conventions: structure rules stay on (MD022, MD031, MD032, MD040, MD047) and the style rules that clash with the existing format are off with a reason (MD013 long lines, MD024 siblings only, MD029 step numbering, MD034 bare URLs, MD036 bold as a label, MD041 templates starting at `##`, MD060 table style). `npx markdownlint-cli2 "**/*.md"` reports **0 issues across 190 files**.
- **Structural errors fixed along the way:** escaped pipes inside cells in `appsec-audit/references/cloud-iac.md` and `prompt-injection-defense.md` (they added phantom columns to the table), `text` as the language of six fences that had none, `##` for the five groups and the "Pack español" section of the humanizer catalogue (they were several H1s in one document) and the trailing `:` dropped from the `replica/templates/complex-app-spec.md` heading.

#### Versions

- **`findings.json` format 2.0:** `init_audit.py` and `normalize_sarif.py` declare `format_version`, the schema documents it and `export_sarif.py` no longer falls back to a hardcoded `1.2.0`: `tool.driver.version` comes from `appsec_util.TOOL_VERSION` (2.0.0) and the run properties carry `format_version`. The SBOM uses the same constant instead of its own `1.3.0`.
- **`seo-auditor` 3.0.0:** the JSON `checks` records stop using `severity` for the gate and switch to `severity_level`, so across the package `severity` is always risk (`high`/`medium`/`low`) and only appears in `findings`. `analyze.py`, the report (which now aggregates `counts_by_level` instead of `counts_by_severity`), the plan, the comparator, the CLI and the engine's `TOOL_VERSION`, now 3.0.0, were updated.
- **`appsec-audit` 2.0.0, `agent-red-team` 3.0.0, `db-architect` 2.0.0 and `premium-web-designer` 3.0.0:** the JSON changes incompatibly (canonical severities in `appsec-audit` and `agent-red-team`, `warning` → `medium` in `migration_guard`, `severity`/`gate` in `premium-web-designer`), so this is a major bump. The `skills.json` of each package, the master and sub-skill frontmatter, the red-team report template and the root index are all in sync; the index moves to **5.0.0** dated **2026-11-19**.

#### Verified

- `run_tests.py` → **687 tests, 13/13 suites**; `pytest -q` → 687; `ruff check .` clean; `tests/lint_frontmatter.py` OK with 79 `SKILL.md`; `tests/metrics_gate.py` within the ceiling (26 `high`, 0 clones); `markdownlint-cli2` with 0 issues across 190 Markdown files.

### - 2026-11-19 · Gates that actually close, `pytest` from the root and aligned counts

#### Fixed (tool contract)

- **`db-architect/scripts/query_trace.py` and `schema_audit.py`:** `--fail-on` no longer accepts `low`; the choices are `medium|none` and `medium|high|none`. A threshold no rule can reach is a gate that never closes.
- **`docs-sync-engine/scripts/docs_drift.py`:** `--fail-on` only `high|none`, the only two severities it emits.
- **`api-contract-guard/scripts/contract_diff.py`:** when neither contract declares a version, `version` comes out as `"none"` instead of inventing a number; the SemVer impact is computed the same way.
- **`replica/scripts/sweep.py`:** an empty directory returns **2** ("nothing was scanned") rather than 0, which was indistinguishable from a clean sweep.
- **`premium-web-designer/scripts/delivery_check.py`:** `HTML-004` moves to `must` when auditing with `--public`.

#### Added

- **`pytest` from the root:** a `conftest.py` that adds every `tests/` to `sys.path` plus `[tool.pytest.ini_options]` in `pyproject.toml` with `--import-mode=importlib` and the 13 test paths. The three package `config.py` files become `appsec_config.py`, `pwd_config.py` and `evals_config.py` (22 imports updated), and the repeated `test_structure.py`, `test_report.py`, `test_templates.py` and `test_security.py` stop resolving to the same module.
- **`seo-auditor`'s real flags documented:** `--allow-local` (loopback and private ranges, on `audit`, `index`, `serp`, `perf`, `headers`, `schema`, `hreflang` and `onpage`) and `--no-rich-preview` (skips `schema/rich-preview.html`), in `seo-auditor/USAGE.md` and `docs/seo-auditor.md`.

#### Fixed (tools)

- **`db-architect`:** a `CREATE TABLE` without a trailing `;` is analysed; `seed_gen` splits `DECIMAL(10,2)` without breaking the column and no longer mistakes a self-referencing FK for a cycle; `drift` applies operations in text order and understands `op.create_table`, `op.add_column` and the rest of Alembic; `query_trace` only counts calls inside the loop body and tells ORM calls apart; `schema_audit` with `fix` emits `CREATE INDEX`; `lock_audit` ignores inline comments; the three SQL reads use `errors="replace"`.
- **`seo-auditor`:** decoding with the real `charset` (`httpbody.py`) and encoding sniffing when reading files; `heading_sequence` follows document order; `robots` catches `TimeoutError` and `socket.timeout` and is evaluated with `AUDITOR_AGENT`; `web_audit.fetch` measures TTFB at the first byte; `sitemap` uses the safe opener; `--allow-local` on the eight network commands (`audit`, `index`, `serp`, `perf`, `headers`, `schema`, `hreflang`, `onpage`); `--rate` and `--timeout` validated; the SERP minimum description rises to 70 characters; a response without `Content-Type` that starts with `<` is analysed.
- **`replica` and `premium-web-designer`:** `imgdiff` exits 2 on a corrupt PNG and counts extra rows; `sweep` reports `skipped_large_files`; `contrast` fails when there are no default pairs; `listing` normalises `avoid`; `parity` rejects unknown priority and rows that are not objects; `delivery_check` resolves relative routes, inspects inline `<style>` and documents its exit codes.
- **Rest:** `code_sync` compares route→set of methods and detects `fetch`'s method; `llm_cost_scan` recognises `Model.create`; `auth_coverage` tolerates `SyntaxError` and does not mistake `@author_only` for a guard; `mock_server` matches verb and `{param}`; `docs_drift` and `terms_check` (BOM) refined; `set(item.parts)` in eight scripts; `hotspots` without git, with normalised paths and a single `V(G)`; `golden_harness`, `evalkit`, `ci_cost_scan`, `cost_diff` and `changelog_gen` fixed; `finops_analyzer` applies the 10–25 % rule.

#### Documentation

- Counts aligned with the real tests: `docs/appsec-audit.md` 122 → **125**, `docs/refactor-surgeon.md` 42 → **44** and `docs/db-architect.md` "six scripts" → **eight**, in Spanish and English.

#### Verified

- `uv run pytest -q` → **673 passed** across 13 suites; `run_tests.py` → all 13 suites OK with 673 tests; `ruff check .` clean; `tests/lint_frontmatter.py` OK with 79 `SKILL.md`.

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

### - 2026-11-16

#### Added

- **`agent-red-team`:** static scan against invisible Unicode characters, Python AST parsing and a risk-report template.
- **`humanizador-anti-ia`:** style auditor for rhythmic variation (coefficient of variation), a Spanish readability index, a list of natural substitutions and a report template.
- **`replica`:** end-to-end app specification protocol, complex interactive-engine protocol (document AST, command history, geometric layout) and scope, architecture, test and preflight templates.
- **`seo-auditor`:** unified audit engine across web, source, local and hybrid modes, with modular technical, semantic, structured-data and strategic-roadmap SEO references.
- **`docs/`:** per-component technical documentation.
