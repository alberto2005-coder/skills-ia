# Changelog / Registro de Cambios

*[Español](#español) · [English](#english)*

---

## Español

Todas las modificaciones notables de este proyecto están documentadas en este archivo.

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

