# Changelog / Registro de Cambios

*[Español](#español) · [English](#english)*

---

## Español

Todas las modificaciones notables de este proyecto están documentadas en este archivo.

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

