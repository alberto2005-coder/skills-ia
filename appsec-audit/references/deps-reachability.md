# SBOM, CVE y alcanzabilidad

Tres artefactos encadenados: el inventario (`sbom.cdx.json`), los avisos que llegan de fuera (`advisories.json`) y el informe que decide qué se puede explotar (`deps.json`). Todo se calcula leyendo ficheros: no se instala, no se ejecuta y no se consulta la red.

## SBOM CycloneDX 1.5

```bash
py appsec-audit/scripts/sbom.py build <dir> --output <dir>/.appsec-audit/sbom.cdx.json
```

| Manifiesto | Ecosistema | Qué se lee |
|---|---|---|
| `package.json` | `npm` | `dependencies` y `devDependencies` |
| `requirements.txt` | `pypi` | `nombre==versión`, extras y marcadores |
| `pyproject.toml` | `pypi` | `[project] dependencies` (PEP 621) |
| `go.mod` | `golang` | `require`, con `indirect` anotado |

Salida: `bomFormat`, `specVersion 1.5`, `serialNumber` derivado del contenido (uuid5, reproducible), `metadata.tools` con el paquete y un componente por dependencia con `bom-ref = purl`. `--now` fija el timestamp; sin él se omite para no romper la reproducibilidad.

Límites declarados: no resuelve transitivas que solo existen en el lockfile, no interpreta rangos abiertos (`^`, `~`, `>=`) como versión instalada y no cubre Maven, Cargo, NuGet ni Composer. Lo que no lee, se dice en el informe.

## Avisos

```json
{
  "advisories": [
    {
      "id": "CVE-2020-8203",
      "package": "lodash",
      "ecosystem": "npm",
      "affected": "<4.17.21",
      "severity": "high",
      "fixed": "4.17.21",
      "summary": "prototype pollution en zipObjectDeep"
    }
  ]
}
```

`affected` acepta `=`, `<`, `<=`, `>`, `>=` y combinaciones separadas por espacios (todas deben cumplirse). Comparación numérica por segmentos: `1.10.0 > 1.9.3`. Prefijos de prerelease no se interpretan: un aviso con sufijos se marca `unknown`.

## Alcanzabilidad

```bash
py appsec-audit/scripts/sbom.py audit sbom.cdx.json --advisories avisos.json --repo <dir> --output deps.json
```

| Estado | Significado | Qué se hace |
|---|---|---|
| `reachable` | El paquete se importa en código de producción | Hallazgo candidato con evidencia: SBOM + `ruta:línea` del import |
| `test-only` | Solo aparece en ficheros de prueba | Se documenta y se degrada; no puntúa como crítico |
| `not-imported` | Declarado pero sin import | Riesgo latente de cadena de suministro |
| `unknown` | Sin `--repo`, el análisis no se hizo | No se afirma nada |

Detección por ecosistema: `require`/`import`/`from` para npm y pypi (con subruta o nombre normalizado), cadenas de bloque `import` para Go. Se ignoran `node_modules`, `.venv`, `dist`, `build` y ficheros de más de 512 KB. Se considera prueba cualquier ruta con `test`, `tests`, `spec`, `__tests__`, o nombre `test_*`, `*_test.py`, `*.test.js`, `*.spec.ts`.

## Informe y puerta

```json
{
  "sbom": "sbom.cdx.json",
  "repo": ".",
  "components": 42,
  "vulnerable": [
    {
      "purl": "pkg:npm/lodash@4.17.20",
      "name": "lodash",
      "version": "4.17.20",
      "advisories": [
        { "id": "CVE-2020-8203", "severity": "high", "affected": "<4.17.21", "reachability": "reachable" }
      ]
    }
  ],
  "counts": { "components": 42, "vulnerable_components": 1, "reachable": 1, "test_only": 0, "not_imported": 0 },
  "gate": { "blocked": true }
}
```

`audit` sale con 1 si hay algún aviso `reachable` de severidad `critical` o `high`; con `--fail-on none` siempre sale 0. Exit 2 si el SBOM o los avisos no se pueden leer. El resultado entra en `findings.json` como un hallazgo por componente alcanzado, con `CWE-1104` o el CWE que indique el aviso.
