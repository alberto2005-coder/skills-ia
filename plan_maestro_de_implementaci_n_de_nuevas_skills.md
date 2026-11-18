# Plan Maestro de Implementación: 5 Nuevos Paquetes para `skills-ia`

Este plan define la arquitectura, especificaciones técnicas, scripts deterministas y baterías de pruebas para ampliar el repositorio de **7 paquetes (43 skills)** a **12 paquetes (65 skills)**, respetando al 100 % las convenciones establecidas en `README.md`, `skills.json` y `run_tests.py`.

---

## 1. Resumen Ejecutivo y Orden de Implementación

Para maximizar el valor técnico y reutilizar patrones ya probados en `appsec-audit`, `seo-auditor` y `replica`, se recomienda implementar los paquetes en el siguiente orden:

| Orden | Paquete | Sub-skills | Total Skills | Enfoque Técnico Principal |
| :--- | :--- | :---: | :---: | :--- |
| **1** | `finops-auditor` | 3 | 4 | Auditoría estática de costes en SDKs de LLM, Infraestructura y CI/CD. |
| **2** | `db-architect` | 4 | 5 | Análisis de esquemas SQL/ORM, guardián de migraciones, detección `N+1` y seeds. |
| **3** | `api-contract-guard` | 3 | 4 | Diff de contratos OpenAPI, sincronización backend-frontend y servidor mock. |
| **4** | `refactor-surgeon` | 4 | 5 | Métricas AST, tests de caracterización (*golden master*) y refactorización por fases. |
| **5** | `docs-sync-engine` | 3 | 4 | Detección de deriva documental, generación de diagramas Mermaid y changelogs Git. |
| **Total** | **5 nuevos paquetes** | **17** | **22** | **Nuevo total del repo: 12 paquetes y 65 skills.** |

---

## 2. Reglas Invariantes y Estándar de Arquitectura

Todo paquete nuevo debe cumplir estrictamente estas reglas antes de considerarse terminado:

### 2.1. Estructura de Directorios Obligatoria
```text
<nombre-paquete>/
├── SKILL.md                  # Maestro: orquesta, fija límites, modos y rúbrica
├── <sub-skill-1>/
│   └── SKILL.md              # Sub-skill independiente con frontmatter propio
├── <sub-skill-2>/
│   └── SKILL.md
├── references/               # Catálogos de reglas, heurísticas y tablas de referencia
│   └── rules.md
├── scripts/                  # Scripts CLI deterministas (SOLO Python 3.9+ stdlib)
│   ├── __init__.py
│   └── <script>.py
├── templates/                # Plantillas Markdown/JSON para informes finales
│   └── report.md
├── tests/                    # Suite unittest 100 % offline
│   ├── __init__.py
│   ├── fixtures/             # Archivos de prueba (código, SQL, YAML, JSON)
│   └── test_<modulo>.py
└── skills.json               # Índice local con el array de skills del paquete
```

### 2.2. Reglas de Código y Dependencias
1. **Cero dependencias en producción (`scripts/`):** Prohibido importar librerías de terceros en `scripts/`. Incluso el parseo de frontmatter YAML o archivos `.yml` debe resolverse con `re`, `json` o parsers ligeros propios en Python estándar (`PyYAML` solo está permitido dentro de `tests/` o herramientas de `dev`).
2. **Interfaz CLI uniforme:** Todos los scripts en `scripts/` deben usar `argparse` y soportar como mínimo:
   * `--path <ruta>`: Archivo o directorio objetivo.
   * `--json`: Salida estructurada en JSON puro para consumo determinista del agente o tests.
   * `--fail-on <severidad>`: Código de salida no nulo (`sys.exit(1)`) si se supera el umbral configurado.
3. **Rutas relativas en `SKILL.md`:** Las sub-skills deben referenciar recursos compartidos usando rutas relativas al paquete (`../references/`, `../scripts/`, `../templates/`).
4. **Rúbrica determinista:** Cada paquete maestro debe calcular una puntuación normalizada en el rango $0 \le \text{score} \le 100$ o una calificación discreta (`A` a `F`), acompañada siempre de evidencia reproducible (archivo, línea y regla disparada).

---

## 3. Especificación Detallada por Paquete

### Paquete 1: `finops-auditor` (4 skills)

#### Archivos y Sub-skills
* `finops-auditor/SKILL.md`: Maestro. Modos `Quick` (escaneo rápido en chat) y `Full` (informe completo con estimación de ahorro mensual y plan de acción).
* `finops-auditor/finops-llm-scan/SKILL.md`: Audita llamadas a APIs de IA (`openai`, `anthropic`, `google.genai`, `boto3` Bedrock, `litellm`).
* `finops-auditor/finops-infra-scan/SKILL.md`: Audita Terraform (`.tf`), Dockerfiles y manifiestos Kubernetes (`.yaml`).
* `finops-auditor/finops-ci-opt/SKILL.md`: Audita workflows en `.github/workflows/*.yml`.

#### Scripts en `finops-auditor/scripts/`
1. **`llm_cost_scan.py`** (`ast`, `re`, `json`, `pathlib`):
   * Detecta llamadas a completions/messages sin parámetro `max_tokens` o `max_output_tokens`.
   * Detecta ausencia de *prompt caching* en system prompts extensos ($> 1000$ caracteres).
   * Detecta uso de modelos de alto coste (ej. `opus`, `gpt-4`, `o1`, `pro`) dentro de funciones etiquetadas o estructuradas como clasificadores/extractores simples.
   * Detecta bucles `while` / `for` con llamadas LLM sin contador de iteraciones máximo (*circuit breaker*).
2. **`infra_cost_scan.py`** (`re`, `json`, `pathlib`):
   * Busca buckets S3/GCS sin bloque `lifecycle_rule`.
   * Busca grupos de logs (CloudWatch) sin `retention_in_days`.
   * Detecta instancias/pods sin `limits` de CPU/memoria o sin reglas de autoescalado.
3. **`ci_cost_scan.py`** (`re`, `json`, `pathlib`):
   * Verifica si los workflows usan acciones de caché (`actions/cache`, caché de `uv`, `pip`, `npm`).
   * Detecta triggers redundantes (`push` y `pull_request` ejecutando la misma suite pesada sin `concurrency: cancel-in-progress`).
4. **`finops_score.py`** (`json`, `math`):
   * Agrega los hallazgos de los tres escáneres y calcula el índice de eficiencia financiera $0 \le S_{\text{finops}} \le 100$.

#### Tests Unitarios (`finops-auditor/tests/`)
* `test_llm_cost_scan.py`: Fixtures Python con un bucle infinito llamando a `client.messages.create()` sin `max_tokens` (debe marcar severidad `HIGH`) vs. llamada acotada con caché (debe pasar limpio).
* `test_infra_cost_scan.py`: Fixtures `.tf` con S3 sin ciclo de vida y Kubernetes sin `resources.limits`.
* `test_ci_cost_scan.py`: Fixtures `.yml` de GitHub Actions con y sin bloque `concurrency`.
* `test_finops_score.py`: Verifica determinismo matemático del score ante distintos volúmenes de hallazgos.

---

### Paquete 2: `db-architect` (5 skills)

#### Archivos y Sub-skills
* `db-architect/SKILL.md`: Maestro. Flujo obligatorio `Audit -> Guard -> Optimize`. Prohibición explícita de ejecutar migraciones destructivas sin aprobación humana.
* `db-architect/db-schema-audit/SKILL.md`: Revisa modelos ORM y DDL SQL.
* `db-architect/db-migration-guard/SKILL.md`: Evalúa el riesgo de bloqueo de tablas en archivos de migración.
* `db-architect/db-query-trace/SKILL.md`: Detecta consultas `N+1` estáticas en el código.
* `db-architect/db-seed-gen/SKILL.md`: Genera fixtures SQL/JSON sintéticos respetando claves foráneas.

#### Scripts en `db-architect/scripts/`
1. **`schema_audit.py`** (`re`, `ast`, `sqlite3`, `json`):
   * Valida DDL SQL usando un motor `sqlite3` en memoria (`:memory:`) para comprobar sintaxis e integridad referencial sin tocar bases de datos externas.
   * Detecta columnas `FOREIGN KEY` sin índice asociado, tablas sin `PRIMARY KEY` y columnas críticas sin restricción `NOT NULL`.
2. **`migration_guard.py`** (`re`, `json`):
   * Analiza migraciones SQL/Alembic/Django y clasifica operaciones por nivel de bloqueo:
     * `CRITICAL`: `DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, `ALTER COLUMN TYPE` sin estrategia expand-contract.
     * `WARNING`: `CREATE INDEX` sin `CONCURRENTLY` en tablas existentes, `ADD COLUMN ... DEFAULT` no nulo.
   * Verifica la existencia de sentencia de reversión (`DOWN` / `downgrade()`).
3. **`query_trace.py`** (`ast`, `re`, `json`):
   * Recorre el AST de Python buscando nodos `ast.For` o `ast.AsyncFor` que contengan llamadas a métodos típicos de ORM (`.get(`, `.filter(`, `.execute(`, `.query(`, `await session.`).
4. **`seed_gen.py`** (`random`, `uuid`, `datetime`, `json`, `sqlite3`):
   * Parsea un esquema SQL, ordena las tablas topológicamente según sus dependencias `REFERENCES` y genera registros deterministas usando una semilla fija (`--seed 42`).

#### Tests Unitarios (`db-architect/tests/`)
* `test_schema_audit.py`: Prueba SQL válido en `:memory:` y verifica detección de FK sin índice.
* `test_migration_guard.py`: Verifica que una migración con `DROP COLUMN` y sin `downgrade()` devuelva código de salida `1` con `--fail-on critical`.
* `test_query_trace.py`: Fixture Python con un bucle `for user in users: db.query(Order).filter_by(user_id=user.id)` (debe detectarlo) vs. `selectinload` fuera del bucle (no debe dar falso positivo).
* `test_seed_gen.py`: Verifica que dos ejecuciones con `--seed 42` produzcan exactamente el mismo JSON/SQL bit a bit.

---

### Paquete 3: `api-contract-guard` (4 skills)

#### Archivos y Sub-skills
* `api-contract-guard/SKILL.md`: Maestro. Calcula el impacto SemVer (`MAJOR`, `MINOR`, `PATCH`) entre versiones de una API.
* `api-contract-guard/api-diff/SKILL.md`: Compara dos especificaciones OpenAPI/Swagger en JSON.
* `api-contract-guard/api-code-sync/SKILL.md`: Cruza rutas declaradas en backend contra llamadas en frontend.
* `api-contract-guard/api-mock-server/SKILL.md`: Levanta un servidor HTTP mock temporal basado en el contrato.

#### Scripts en `api-contract-guard/scripts/`
1. **`contract_diff.py`** (`json`, `difflib`, `pathlib`):
   * Compara `old_spec.json` y `new_spec.json`.
   * Clasifica cambios: endpoint eliminado (`MAJOR`), nuevo campo `required` en request (`MAJOR`), cambio de tipo en response (`MAJOR`), nuevo endpoint o campo opcional (`MINOR`).
2. **`code_sync.py`** (`ast`, `re`, `json`):
   * Extrae rutas de backend (decoradores `@app.get`, `@router.post` en FastAPI/Flask o `app.get(` en Express) y llamadas de frontend (`fetch(`, `axios.get(`).
   * Reporta rutas consumidas por el frontend que no existen en el backend (*dead calls*) y endpoints sin consumidor.
3. **`mock_server.py`** (`http.server`, `json`, `urllib.parse`, `threading`):
   * Lee los `paths` y `examples` de un contrato JSON y levanta un servidor HTTP local que responde con el código de estado y payload mockeado correspondiente.

#### Tests Unitarios (`api-contract-guard/tests/`)
* `test_contract_diff.py`: Compara dos fixtures OpenAPI y valida que la clasificación SemVer sea `MAJOR` cuando se elimina un campo de respuesta.
* `test_code_sync.py`: Crea un mini-proyecto temporal con `backend.py` y `client.js` y verifica el cruce de rutas coincidentes y rotas.
* `test_mock_server.py`: Levanta `mock_server.py` en el puerto efímero `0` (`127.0.0.1`), realiza una petición interna con `urllib.request` en el mismo proceso y cierra el servidor limpiamente (0 tráfico externo).

---

### Paquete 4: `refactor-surgeon` (5 skills)

#### Archivos y Sub-skills
* `refactor-surgeon/SKILL.md`: Maestro. Impone la regla de oro: *ninguna refactorización sin red de seguridad previa*.
* `refactor-surgeon/refactor-metrics/SKILL.md`: Calcula complejidad ciclomática, acoplamiento y deuda técnica.
* `refactor-surgeon/refactor-harness/SKILL.md`: Genera tests de caracterización (*golden master*) antes de modificar código.
* `refactor-surgeon/refactor-slice/SKILL.md`: Guía la extracción de módulos y funciones cohesivas.
* `refactor-surgeon/refactor-verify/SKILL.md`: Ejecuta la verificación post-cambio y compara salidas.

#### Scripts en `refactor-surgeon/scripts/`
1. **`code_metrics.py`** (`ast`, `math`, `json`, `tokenize`):
   * Calcula la complejidad ciclomática de McCabe por función mediante conteo de nodos de decisión en el AST (`If`, `For`, `While`, `ExceptHandler`, `With`, `Assert`, `comprehension`, `BoolOp`), siguiendo $V(G) = 1 + \sum \text{puntos de decisión}$.
   * Mide profundidad máxima de anidamiento, líneas por función y número de parámetros.
   * Genera una puntuación de mantenibilidad normalizada $0 \le M \le 100$.
2. **`golden_harness.py`** (`ast`, `inspect`, `json`, `importlib.util`):
   * Inspecciona funciones puras o deterministas indicadas por el usuario, ejecuta un conjunto de entradas definidas en un JSON de casos y graba las salidas exactas en `golden_snapshot.json`.
3. **`slice_analyzer.py`** (`ast`, `collections`, `json`):
   * Construye un grafo interno de llamadas entre funciones dentro de un archivo grande para sugerir grupos de funciones fuertemente cohesionadas candidatas a extraerse a un módulo separado.
4. **`verify_gate.py`** (`subprocess`, `unittest`, `json`):
   * Ejecuta `unittest` y compara los resultados actuales contra `golden_snapshot.json`. Devuelve `PASS` o `FAIL` con el diff exacto de cualquier regresión.

#### Tests Unitarios (`refactor-surgeon/tests/`)
* `test_code_metrics.py`: Verifica que una función lineal tenga complejidad $V(G) = 1$ y una función con 4 `if/elif` y 1 bucle `for` tenga $V(G) = 6$.
* `test_golden_harness.py`: Graba un snapshot de una función de cálculo de impuestos y verifica que `verify_gate.py` detecta un cambio de redondeo de $0.01$.
* `test_slice_analyzer.py`: Verifica la detección de dos subgrafos independientes dentro de un archivo Python monolítico de fixture.

---

### Paquete 5: `docs-sync-engine` (4 skills)

#### Archivos y Sub-skills
* `docs-sync-engine/SKILL.md`: Maestro. Calcula la salud documental del repositorio ($0 \le S_{\text{docs}} \le 100$).
* `docs-sync-engine/docs-drift-check/SKILL.md`: Detecta desincronización entre código, `.env.example` y Markdown.
* `docs-sync-engine/docs-arch-gen/SKILL.md`: Genera diagramas de dependencias en Mermaid desde los imports reales.
* `docs-sync-engine/docs-changelog/SKILL.md`: Genera borradores de `CHANGELOG.md` desde el historial de Git.

#### Scripts en `docs-sync-engine/scripts/`
1. **`drift_check.py`** (`ast`, `re`, `pathlib`, `json`):
   * Extrae variables de entorno leídas en el código (`os.environ.get`, `os.getenv`, `process.env`) y las cruza con las documentadas en `.env.example` y `README.md`.
   * Extrae todas las rutas de archivos referenciadas en enlaces Markdown (`[texto](ruta/archivo)`) y comprueba que existan en el disco.
   * Extrae flags CLI documentados (`--flag`) y comprueba si aparecen en los parsers del código.
2. **`arch_mermaid.py`** (`ast`, `pathlib`, `json`):
   * Analiza los `import` y `from ... import` internos de un proyecto Python y emite un bloque `graph TD` de Mermaid limpio sin ciclos ocultos.
3. **`changelog_gen.py`** (`subprocess`, `re`, `datetime`, `json`):
   * Ejecuta `git log` con formato estructurado en un repositorio local, agrupa commits por prefijo convencional (`feat:`, `fix:`, `refactor:`, `docs:`) y lista los archivos afectados.
4. **`docs_score.py`** (`json`):
   * Pondera enlaces rotos, variables de entorno sin documentar y comandos obsoletos para emitir el veredicto final.

#### Tests Unitarios (`docs-sync-engine/tests/`)
* `test_drift_check.py`: Fixture con un `README.md` que apunta a `scripts/inexistente.py` y un código que lee `API_SECRET_KEY` ausente en `.env.example` (debe reportar ambos errores).
* `test_arch_mermaid.py`: Verifica que dado un directorio con `a.py` importando `b.py`, la salida contiene `a --> b`.
* `test_changelog_gen.py`: Crea un repositorio Git efímero en `tempfile.TemporaryDirectory()`, realiza 3 commits (`feat:`, `fix:`, `docs:`) y verifica la agrupación resultante.

---

## 4. Plan de Pruebas Transversales e Integración (`tests/` y `skill-evals`)

Además de los `unittest` internos de cada paquete, la integración en `skills-ia` exige superar **4 baterías de pruebas transversales** ejecutadas mediante `uv run python run_tests.py`:

### 4.1. Pruebas de Activación y Cero Colisiones (`phrases.json`)
Para cada una de las **22 nuevas skills**, se deben añadir casos en el conjunto de evaluación de triggers (`skill-evals` / `tests/`):
* **Casos Positivos ($\ge 5$ frases por skill):** Prompts naturales en español e inglés que deben activar exactamente esa skill (maestro o sub-skill).
* **Casos Negativos ($\ge 5$ frases por skill):** Prompts cercanos que NO deben activar la skill.
* **Pruebas de Frontera entre Hermanas (Anti-colisión):**
  * `db-architect` vs. `appsec-audit` (ej. *"revisa índices y claves foráneas en mi SQL"* debe activar `db-schema-audit`, mientras que *"busca inyección SQL en este endpoint"* debe activar `appsec-code`).
  * `finops-auditor` vs. `appsec-infra` (ej. *"optimiza el coste de estos buckets S3 y tokens LLM"* debe activar `finops-auditor`, mientras que *"revisa permisos IAM públicos en S3"* debe activar `appsec-infra`).
  * `refactor-surgeon` vs. `replica-build` (ej. *"reduce la complejidad ciclomática de este módulo sin cambiar su salida"* debe activar `refactor-surgeon`).
  * `docs-sync-engine` vs. `seo-audit` (ej. *"comprueba si el README coincide con las variables .env del código"* debe activar `docs-sync-engine`).

### 4.2. Pruebas de Coherencia Estructural y Cero Dependencias
Añadir o verificar en `tests/` las siguientes aserciones automáticas sobre los 5 paquetes nuevos:
1. **Validación de `skills.json`:** Todos los `name` declarados en `<paquete>/skills.json` coinciden con los `SKILL.md` existentes y están registrados en el `skills.json` de la raíz.
2. **Validación de Frontmatter YAML:** Todo `SKILL.md` contiene frontmatter válido con `name` (kebab-case idéntico al directorio) y `description` no vacía.
3. **Integridad de Rutas Relativas:** Toda referencia `../references/...`, `../scripts/...` o `../templates/...` dentro de una sub-skill apunta a un fichero real en disco.
4. **Auditoría AST de Cero Dependencias:** Un test estático recorre todos los archivos `.py` dentro de `<paquete>/scripts/` con `ast.parse` y verifica que todos los `Import` e `ImportFrom` pertenecen exclusivamente a `sys.stdlib_module_names` (Python 3.9+) o a módulos locales del propio paquete.

### 4.3. Ejecución Local y CI
Antes de hacer `push`, validar toda la suite con:
```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run python run_tests.py
```
Verificar que `.github/workflows/tests.yml` ejecuta automáticamente tanto los `unittest` de los 5 paquetes nuevos como los tests transversales de activación y coherencia.

---

## 5. Checklist Final de Documentación e Integración

Para dejar cada paquete completamente integrado en el repositorio principal:

- [ ] Crear guía técnica en `docs/<paquete>.md` siguiendo el formato de `docs/appsec-audit.md` y `docs/seo-auditor.md` (modos, sub-skills, rúbrica de puntuación, ejemplos de CLI y límites).
- [ ] Enlazar las 5 nuevas guías en `docs/index.md`.
- [ ] Registrar los 5 paquetes y sus 22 skills en el archivo raíz `skills.json` (actualizando el conteo total a 12 paquetes y 65 skills).
- [ ] Actualizar `README.md` en ambas secciones (**Español** y **English**):
  - Actualizar el contador general (`12 paquetes, 65 skills` / `12 packages, 65 skills`).
  - Añadir las 5 filas en la tabla principal de **Módulos y Sub-skills**.
  - Añadir las 5 subtablas detallando maestro + sub-skills de cada nuevo paquete.
- [ ] Ejecutar `docs-sync-engine` (dogfooding) sobre el propio repositorio `skills-ia` para verificar que cero enlaces o rutas del `README.md` y `docs/` estén rotos.