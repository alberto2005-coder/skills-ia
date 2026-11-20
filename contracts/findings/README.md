# Contrato de hallazgos — `findings.json` v1.0.0

Un solo formato para la salida de todos los auditores del catálogo. El esquema
canónico es [`findings.schema.json`](findings.schema.json) y estas piezas lo
acompañan: el validador con `--fail-on`, el exportador a SARIF 2.1.0 y los
adaptadores de los pilotos.

| Comando | Qué hace |
| --- | --- |
| `emit.py appsec <findings.json> --output ...` | Convierte un informe nativo de `appsec-audit` al contrato |
| `emit.py seo <audit.json> --output ...` | Convierte un informe nativo de `seo-auditor` al contrato |
| `validate_findings.py <findings.json>` | Comprueba forma, huella y coherencia del resumen |
| `validate_findings.py <findings.json> --fail-on high` | Además, sale 3 si algo llega al umbral |
| `findings_to_sarif.py <findings.json> --output x.sarif` | Exporta a SARIF 2.1.0 para Code Scanning |

Códigos de salida: `0` válido · `1` no cumple el contrato · `2` entrada ilegible ·
`3` supera `--fail-on`. El umbral de `--fail-on` acepta `none|info|low|medium|high|critical`
y por defecto es `none`: validar no bloquea nada salvo que se pida.

## Raíz del informe

| Campo | Obligatorio | Qué es |
| --- | --- | --- |
| `schema_version` | sí | Siempre `1.0.0`. Cambia solo con roturas. |
| `tool` | sí | `package`, `skill` y `version` (semver) que produjeron el informe. |
| `summary` | sí | `total`, `by_severity` (siempre las cinco claves, con 0), `score` opcional 0–100 y `note` en una frase. |
| `findings` | sí | Lista de hallazgos. |
| `target` | no | Repositorio, sitio o artefacto auditado. |
| `generated_at` | no | Fecha ISO 8601. |

El resumen se calcula, no se declara: el validador falla si `total` o
`by_severity` no cuadran con la lista. Un resumen obsoleto es peor que ninguno.

## Hallazgo

| Campo | Obligatorio | Notas |
| --- | --- | --- |
| `fingerprint` | sí | `sha256:<32 hex>` calculado por el contrato (ver abajo). |
| `rule_id` | sí | Regla del auditor: `CWE-89`, `SRC-TITLE-001`, `llm-model-cost`. |
| `severity` | sí | `critical` · `high` · `medium` · `low` · `info`. |
| `confidence` | sí | `high` · `medium` · `low`, independiente de la severidad. |
| `title` | sí | 3–160 caracteres, para listas. |
| `message` | sí | Qué pasa y por qué importa. |
| `evidence` | sí | Dato observado: fragmento, cabecera, medición. Sin secretos. |
| `remediation` | sí | Cómo se arregla, concreto. |
| `location` | sí | Ubicación híbrida (abajo). |
| `references` | no | `[{ "id": "CWE-89", "url": "https://..." }]`. |

## Ubicación híbrida

| `type` | `target` | ¿Lleva línea? |
| --- | --- | --- |
| `file` | Fichero de código | Sí, opcional (`line`, `end_line`). |
| `url` | Página o endpoint | Nunca: `line` y `end_line` van a `null`. |
| `resource` | Recurso de infraestructura (`aws:rds:db`) | Nunca. |
| `schema` | Tabla, columna o contrato (`public.users`) | Nunca. |

Un hallazgo de SEO no tiene línea 42: si el contrato la exigiera, el emisor
tendría que inventarla y el SARIF apuntaría a código que no existe. `file` sin
línea es válido y frecuente en auditorías de fuentes.

## Huella

```text
sha256(rule_id | location.type | location.target_normalizado | título_en_minúsculas)[:32]
```

No incluye la línea, así que el mismo defecto sigue siendo el mismo hallazgo
aunque el código se mueva cuarenta líneas; sí incluye el título, así que una
causa distinta es un hallazgo distinto. Los separadores de ruta se normalizan a
`/`, para que Windows y Linux deduplicen igual. El validador **recalcula** la
huella: cualquier emisor que se desvíe se ve al instante, y dos huellas iguales
en el mismo informe son un error.

## SARIF 2.1.0

| `severity` | `level` de SARIF |
| --- | --- |
| `critical`, `high` | `error` |
| `medium` | `warning` |
| `low`, `info` | `note` |

`file` → `physicalLocation` con `region` solo si hay línea (y se recorta a ruta
relativa si cae dentro de `target`); `url` → `artifactLocation.uri`; `resource` y
`schema` → `logicalLocations`. La huella viaja en `partialFingerprints` y cada
`rule_id` genera una regla con `helpUri` tomado de la primera referencia.

## Adaptadores

- **`appsec`**: entran solo los `confirmed`. Un `needs_validation` es una pista,
  no un hallazgo, y un `rejected` está refutado; ambos siguen en el informe nativo,
  que no se modifica. La confianza 1–10 se agrupa en `high` (8–10), `medium` (5–7) y
  `low` (1–4). El CWE se convierte en `rule_id` y en referencia.
- **`seo`**: entran solo las comprobaciones en `fail`. `must` → `high`,
  `should` → `medium`, `nice` → `low`. La cita oficial se convierte en referencia y
  la nota del informe (`score`, veredicto) pasa al resumen.
- **`db`**: el `--json` de `lock_audit`, `drift`, `schema_audit`, `migration_guard`,
  `sql_lint` y `query_trace`. Un hallazgo con `file` y `line` va a la ubicación
  `file`; `drift`, que señala tabla o columna, va a `schema`. La corrección sale del
  `fix` del propio hallazgo o de la tabla de reglas, y el `warning` de
  `migration_guard` se lee como `medium`.
- **`api`**: `contract_diff` (`changes`: `major` → `high`, `minor` → `medium`,
  `patch` → `low`), `auth_coverage` y `code_sync`. Lo que trae fichero y línea va a
  `file`; una ruta o un endpoint (`GET /users/{id}`) va a `url`.
- **`finops`**: `llm_cost_scan`, `infra_cost_scan` y `ci_cost_scan`, los tres con la
  misma forma `{file, line, rule, severity, message}`.

**Duplicados.** La huella no lleva la línea, así que dos llamadas idénticas en el
mismo fichero (por ejemplo `max_tokens` en las líneas 7 y 16) colapsarían en un solo
hallazgo. El emisor los fusiona y deja los dos sitios en `evidence`
(`assistant.py:7 · también en assistant.py:16`): no se pierde ninguno ni se repite
una huella que el validador rechazaría. Una regla sin consejo propio remite a la
guía del paquete en vez de improvisar uno.

## Por qué vive aquí

Cada paquete se instala solo y no puede importar módulos de la raíz, así que el
contrato es herramienta del repositorio: una implementación, un esquema, un
exportador. Los auditores solo lo producen. Si más adelante hace falta que el
validador viaje dentro de cada zip, se copia con un paso de sincronización y un
test que detecte la deriva; hoy sería duplicación de la misma lógica.

---

## English — findings contract — `findings.json` v1.0.0

One format for every auditor in the catalogue. The canonical schema is
[`findings.schema.json`](findings.schema.json); the validator with `--fail-on`,
the SARIF 2.1.0 exporter and the pilot adapters ship next to it.

| Command | What it does |
| --- | --- |
| `emit.py appsec <findings.json> --output ...` | Converts a native `appsec-audit` report to the contract |
| `emit.py seo <audit.json> --output ...` | Converts a native `seo-auditor` report to the contract |
| `validate_findings.py <findings.json>` | Checks shape, fingerprint and summary coherence |
| `validate_findings.py <findings.json> --fail-on high` | Also exits 3 when a finding reaches the threshold |
| `findings_to_sarif.py <findings.json> --output x.sarif` | Exports to SARIF 2.1.0 for Code Scanning |

Exit codes: `0` valid · `1` contract violations · `2` unreadable input · `3`
threshold exceeded. `--fail-on` takes `none|info|low|medium|high|critical` and
defaults to `none`: validating gates nothing unless asked.

### Root fields

| Field | Required | What it is |
| --- | --- | --- |
| `schema_version` | yes | Always `1.0.0`; changes only on breakage. |
| `tool` | yes | `package`, `skill` and semver `version` that produced the report. |
| `summary` | yes | `total`, `by_severity` (all five keys, zeroes included), optional `score` 0–100 and a one-line `note`. |
| `findings` | yes | List of findings. |
| `target` | no | Repository, site or artefact audited. |
| `generated_at` | no | ISO 8601 timestamp. |

The summary is computed, not declared: the validator fails when `total` or
`by_severity` disagree with the list. A stale summary is worse than none.

### Finding

| Field | Required | Notes |
| --- | --- | --- |
| `fingerprint` | yes | `sha256:<32 hex>` produced by the contract. |
| `rule_id` | yes | Auditor rule: `CWE-89`, `SRC-TITLE-001`, `llm-model-cost`. |
| `severity` | yes | `critical` · `high` · `medium` · `low` · `info`. |
| `confidence` | yes | `high` · `medium` · `low`, independent from severity. |
| `title` | yes | 3–160 characters, for lists. |
| `message` | yes | What happens and why it matters. |
| `evidence` | yes | Observed datum: snippet, header, measurement. No secrets. |
| `remediation` | yes | How to fix it, concretely. |
| `location` | yes | Hybrid location (below). |
| `references` | no | `[{ "id": "CWE-89", "url": "https://..." }]`. |

### Hybrid location

| `type` | `target` | Lines? |
| --- | --- | --- |
| `file` | Source file | Yes, optional (`line`, `end_line`). |
| `url` | Page or endpoint | Never: both `null`. |
| `resource` | Infrastructure resource (`aws:rds:db`) | Never. |
| `schema` | Table, column or contract (`public.users`) | Never. |

An SEO finding has no line 42. Forcing one would make the emitter invent it and
SARIF point at code that does not exist. A `file` without a line is valid and
common in source audits.

### Fingerprint

```text
sha256(rule_id | location.type | normalized location.target | lowercased title)[:32]
```

It leaves the line out, so the same defect stays the same finding when the code
moves; it includes the title, so a different cause is a different finding. Path
separators are normalized to `/` so Windows and Linux deduplicate alike. The
validator recomputes it: any emitter that drifts shows up at once, and two equal
fingerprints in one report are an error.

### SARIF 2.1.0

`critical` and `high` → `error`, `medium` → `warning`, `low` and `info` → `note`.
`file` → `physicalLocation` with `region` only when a line exists (and relativized
under `target`); `url` → `artifactLocation.uri`; `resource` and `schema` →
`logicalLocations`. The fingerprint travels in `partialFingerprints` and each
`rule_id` becomes a rule with `helpUri` from its first reference.

### Adapters

- **`appsec`**: only `confirmed` findings enter. A `needs_validation` is a lead,
  not a finding, and a `rejected` one is refuted; both stay in the native report,
  which is left untouched. Confidence 1–10 becomes `high` (8–10), `medium` (5–7)
  and `low` (1–4); the CWE becomes `rule_id` plus a reference.
- **`seo`**: only `fail` checks enter. `must` → `high`, `should` → `medium`,
  `nice` → `low`. The official citation becomes a reference and the report score
  and verdict become the summary's `score` and `note`.
- **`db`**: the `--json` of `lock_audit`, `drift`, `schema_audit`,
  `migration_guard`, `sql_lint` and `query_trace`. Findings with `file` and `line`
  go to the `file` location; `drift`, which points at a table or column, goes to
  `schema`. The fix comes from the finding's own `fix` or the rule table, and
  `migration_guard`'s `warning` reads as `medium`.
- **`api`**: `contract_diff` (`changes`: `major` → `high`, `minor` → `medium`,
  `patch` → `low`), `auth_coverage` and `code_sync`. Findings with a file and line
  go to `file`; a route or endpoint (`GET /users/{id}`) goes to `url`.
- **`finops`**: `llm_cost_scan`, `infra_cost_scan` and `ci_cost_scan`, all three
  with the same `{file, line, rule, severity, message}` shape.

**Duplicates.** The fingerprint leaves the line out, so two identical calls in the
same file (say `max_tokens` on lines 7 and 16) would collapse into one finding. The
emitter merges them and keeps both sites in `evidence`
(`assistant.py:7 · also at assistant.py:16`): nothing is lost and no duplicate
fingerprint is written. A rule with no advice of its own points at the package
guide instead of inventing one.

### Why it lives here

Every package installs on its own and cannot import modules from the repository
root, so the contract is repository tooling: one implementation, one schema, one
exporter. Auditors only produce it. If the validator ever needs to travel inside
each zip, a sync step plus a drift test would copy it; today that would just
duplicate the same logic.
