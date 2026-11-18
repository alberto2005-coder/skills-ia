# Refactor Surgeon

> Refactorizar con red: medir complejidad, congelar la conducta con casos dorados, cortar por el grafo de llamadas y verificar que nada cambió.
> Refactoring with a safety net: measure complexity, freeze behaviour with golden cases, cut along the call graph and verify nothing moved.

[Español](#español) · [English](#english)

---

## Español

### Índice
1. Propósito
2. Modos
3. Arquitectura
4. Umbrales
5. Herramientas
6. Instalación y uso
7. Tests
8. Límites

### Propósito
`refactor-surgeon` cambia la forma del código sin cambiar lo que hace. El método es siempre el mismo: medir, congelar la conducta, cortar un grupo por vez y comprobar que los mismos casos devuelven lo mismo. La ejecución del código ajeno es una decisión explícita (`--allow-exec`), no un efecto colateral.

### Modos
El maestro no usa flags: el alcance de la petición fija las fases.

| Modo | Fases | Entrega |
|---|---|---|
| **Diagnóstico** | `refactor-metrics` | Complejidad, anidamiento y mantenibilidad |
| **Priorización** | `refactor-hotspots` | Ficheros ordenados por churn × complejidad |
| **Red de seguridad** | `refactor-harness` | Casos dorados grabados |
| **Purga** | `refactor-deadcode` | Imports y definiciones sin uso |
| **Desenredo** | `refactor-cycles` | Ciclos a romper antes de cortar |
| **Corte** | `refactor-slice` + `refactor-metrics` | Grupos a extraer y métricas del después |
| **Cierre** | `refactor-verify` | Veredicto con o sin discrepancias |

### Arquitectura
Un maestro y ocho sub-skills con scripts compartidos. Se instala la carpeta completa.

| Sub-skill | Qué hace |
|---|---|
| `refactor-surgeon` | Maestro: ordena medir, congelar, cortar y verificar |
| `refactor-metrics` | `V(G)`, anidamiento, parámetros, líneas y nota de mantenibilidad |
| `refactor-hotspots` | Churn de `git log` × complejidad, con «no medido» explícito |
| `refactor-harness` | Graba y reproduce casos dorados antes y después |
| `refactor-deadcode` | Imports y definiciones privadas que nadie referencia |
| `refactor-clones` | Duplicación entre funciones por shingles normalizados del AST |
| `refactor-cycles` | Ciclos de imports entre módulos, con sus ficheros |
| `refactor-slice` | Componentes conexas del grafo de llamadas como cortes |
| `refactor-verify` | Compara la conducta contra el snapshot |

### Umbrales
| Métrica | Límite por defecto |
|---|---|
| Complejidad `V(G)` | 10 |
| Anidamiento | 4 |
| Parámetros | 6 |
| Líneas por función | 60 |

Superar el doble del límite convierte el hallazgo en severidad alta; la nota de mantenibilidad parte de 100 y penaliza complejidad y anidamiento, así que sirve para comparar el mismo módulo antes y después, no entre proyectos.

### Herramientas

```bash
py refactor-surgeon/scripts/code_metrics.py --path src/ --json --fail-on medium
py refactor-surgeon/scripts/golden_harness.py --cases cases.json --snapshot golden.json --record --allow-exec
py refactor-surgeon/scripts/golden_harness.py --cases cases.json --snapshot golden.json --verify --allow-exec
py refactor-surgeon/scripts/slice_analyzer.py --path src/grande.py --json
py refactor-surgeon/scripts/hotspots.py --path . --since 2026-01-01T00:00:00 --json
py refactor-surgeon/scripts/dead_code.py --path src/ --json --fail-on medium
py refactor-surgeon/scripts/import_cycles.py --path src/ --json
py refactor-surgeon/scripts/clone_detect.py --path src/ --json
```

El fichero de casos declara el módulo y las llamadas:

```json
{"module": "src/app.py", "cases": [{"function": "sumar", "args": [1, 2]}]}
```

Sin `--allow-exec` el arnés solo valida el fichero y no importa nada. Una excepción se graba como conducta observable, con su tipo y mensaje.

Códigos de salida: `0` limpio o verificado · `1` umbral superado o discrepancia · `2` ruta o snapshot ilegible.

### Instalación y uso
Copia la carpeta `refactor-surgeon/` completa. Ejemplos de petición:
- «Mide la complejidad de este módulo y dime por dónde empezar».
- «Graba casos dorados antes de que toque nada».
- «Divide este fichero de 900 líneas en módulos».
- «Verifica que el refactor no cambió el comportamiento».

### Tests

```bash
uv run python -m unittest discover -s refactor-surgeon/tests -t refactor-surgeon/tests
```

41 pruebas: función simple limpia, función anidada por encima de los límites, `--fail-on none`, firma ancha, ruta ausente, grupos del grafo, fichero que no parsea, grabación y verificación sin discrepancias, cambio de conducta detectado, ejecución sin permiso, snapshot ausente y seis del detector de clones (renombrado como clon exacto, funciones distintas sin hallazgos, funciones diminutas ignoradas, umbral que filtra el par, `--fail-on none` y ruta ausente) y ocho del detector de código muerto (módulo limpio, import sin uso con su línea, `# noqa`, función privada muerta, función viva desde otro fichero, definición pública oculta sin `--include-public`, `--fail-on none` y ruta ausente) y siete del detector de ciclos (imports lineales limpios, ciclo de dos módulos, ciclo de tres, imports relativos dentro de un paquete, autoimport ignorado, `--fail-on none` y ruta ausente) y siete de hotspots (sin `--since`, sin repositorio, churn y complejidad medidos, ventana que filtra, orden y `--top`, `--fail-on hotspot` y clon shallow).

### Límites
Las métricas se calculan sobre la sintaxis, no ejecutando el código; no miden acoplamiento entre módulos ni cobertura. El grafo solo ve llamadas por nombre dentro del mismo fichero: métodos, imports y llamadas dinámicas no aparecen. El detector de código muerto cuenta identificadores, así que `importlib`, `eval`, plugins cargados por cadena y usos desde fuera del árbol quedan fuera. El arnés ejecuta en el proceso actual, sin aislamiento ni límite de tiempo propio, y compara resultados serializados, así que un objeto no serializable se compara como texto.

---

## English

### Index
1. Purpose
2. Modes
3. Architecture
4. Thresholds
5. Tools
6. Install and use
7. Tests
8. Limits

### Purpose
`refactor-surgeon` changes the shape of the code without changing what it does. The method never varies: measure, freeze behaviour, cut one group at a time and check that the same cases return the same results. Running someone else's code is an explicit decision (`--allow-exec`), never a side effect.

### Modes
The master takes no flags: the request's scope sets the phases.

| Mode | Phases | Deliverable |
|---|---|---|
| **Diagnosis** | `refactor-metrics` | Complexity, nesting and maintainability |
| **Prioritisation** | `refactor-hotspots` | Files ranked by churn × complexity |
| **Safety net** | `refactor-harness` | Golden cases recorded |
| **Purge** | `refactor-deadcode` | Unused imports and definitions |
| **Untangle** | `refactor-cycles` | Cycles to break before cutting |
| **Cut** | `refactor-slice` + `refactor-metrics` | Groups to extract and after metrics |
| **Close** | `refactor-verify` | Verdict with or without mismatches |

### Architecture
One master and eight sub-skills with shared scripts. The whole folder is installed.

| Sub-skill | What it does |
|---|---|
| `refactor-surgeon` | Master: orders measure, freeze, cut and verify |
| `refactor-metrics` | `V(G)`, nesting, parameters, lines and maintainability score |
| `refactor-hotspots` | `git log` churn × complexity, with an explicit "not measured" |
| `refactor-harness` | Records and replays golden cases before and after |
| `refactor-deadcode` | Imports and private definitions nothing references |
| `refactor-clones` | Duplication between functions by normalised AST shingles |
| `refactor-cycles` | Import cycles between modules, with their files |
| `refactor-slice` | Connected components of the call graph as cuts |
| `refactor-verify` | Compares behaviour against the snapshot |

### Thresholds
| Metric | Default limit |
|---|---|
| `V(G)` complexity | 10 |
| Nesting | 4 |
| Parameters | 6 |
| Lines per function | 60 |

Exceeding twice the limit raises the finding to high severity; the maintainability score starts at 100 and penalises complexity and nesting, so it compares the same module before and after, not across projects.

### Tools

```bash
py refactor-surgeon/scripts/code_metrics.py --path src/ --json --fail-on medium
py refactor-surgeon/scripts/golden_harness.py --cases cases.json --snapshot golden.json --record --allow-exec
py refactor-surgeon/scripts/golden_harness.py --cases cases.json --snapshot golden.json --verify --allow-exec
py refactor-surgeon/scripts/slice_analyzer.py --path src/grande.py --json
py refactor-surgeon/scripts/hotspots.py --path . --since 2026-01-01T00:00:00 --json
py refactor-surgeon/scripts/dead_code.py --path src/ --json --fail-on medium
py refactor-surgeon/scripts/import_cycles.py --path src/ --json
py refactor-surgeon/scripts/clone_detect.py --path src/ --json
```

The cases file declares the module and the calls:

```json
{"module": "src/app.py", "cases": [{"function": "sumar", "args": [1, 2]}]}
```

Without `--allow-exec` the harness only validates the file and imports nothing. An exception is recorded as observable behaviour, with its type and message.

Exit codes: `0` clean or verified · `1` threshold exceeded or mismatch · `2` unreadable path or snapshot.

### Install and use
Copy the whole `refactor-surgeon/` folder. Example requests:
- "Measure this module's complexity and tell me where to start".
- "Record golden cases before anything is touched".
- "Split this 900-line file into modules".
- "Verify the refactor did not change behaviour".

### Tests

```bash
uv run python -m unittest discover -s refactor-surgeon/tests -t refactor-surgeon/tests
```

41 tests: clean simple function, nested function over the limits, `--fail-on none`, wide signature, missing path, call-graph groups, unparsable file, record and verify with no mismatches, changed behaviour detected, execution without permission, missing snapshot and six for the clone detector (rename as exact clone, distinct functions clean, tiny functions ignored, threshold filtering the pair, `--fail-on none` and missing path) and eight for the dead-code detector (clean module, unused import with its line, `# noqa`, dead private function, live function from another file, public definition hidden without `--include-public`, `--fail-on none` and missing path) and seven for the cycle detector (clean linear imports, two-module cycle, three-module cycle, relative imports inside a package, self-import ignored, `--fail-on none` and missing path) and seven for hotspots (no `--since`, not a repository, churn and complexity measured, window filtering, ordering and `--top`, `--fail-on hotspot` and a shallow clone).

### Limits
Metrics come from the syntax, not from running the code; they measure neither module coupling nor coverage. The graph only sees name-based calls inside the same file: methods, imports and dynamic calls are invisible. The dead-code detector counts identifiers, so `importlib`, `eval`, plugin loading by string and uses from outside the tree stay out of reach. The harness runs in the current process, with no isolation and no per-case timeout, and compares serialised results, so a non-serialisable object is compared as text.
