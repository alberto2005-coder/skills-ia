# API Contract Guard

> Defensa de un contrato de API: impacto SemVer entre versiones, cruce de rutas backend/frontend y mock local, sin red ni despliegue.
> API contract defence: SemVer impact between versions, backend/frontend route sync and a local mock, offline and undeployed.

[Español](#español) · [English](#english)

---

## Español

### Índice
1. Propósito
2. Modos
3. Arquitectura
4. Clasificación
5. Herramientas
6. Instalación y uso
7. Tests
8. Límites

### Propósito
`api-contract-guard` responde a tres preguntas antes de publicar: ¿este cambio rompe a quien consume la API?, ¿queda alguna llamada del frontend apuntando a una ruta que ya no existe?, ¿puedo probar el cliente sin levantar el backend? Todo es estático y local; lo único que escucha es un servidor mock en `127.0.0.1`.

### Modos
El maestro no usa flags: el alcance de la petición fija las fases.

| Modo | Fases | Entrega |
|---|---|---|
| **Impacto** | `api-diff` | Nivel SemVer y cambios por ruta |
| **Consistencia** | `api-code-sync` | `dead-call`, `metodo-distinto` y `sin-consumidor` |
| **Prueba** | `api-mock-server` | Servidor local con los ejemplos del contrato |

### Arquitectura
Un maestro y tres sub-skills con assets compartidos. Se instala la carpeta completa.

| Sub-skill | Qué hace |
|---|---|
| `api-contract-guard` | Maestro: ordena diff, cruce y prueba, y firma el veredicto |
| `api-diff` | Compara dos contratos OpenAPI y calcula el impacto SemVer |
| `api-code-sync` | Cruza las rutas del backend con las llamadas del frontend |
| `api-mock-server` | Sirve los ejemplos del contrato desde loopback |

### Clasificación
| Cambio | Nivel |
|---|---|
| Endpoint o método eliminado | `major` |
| Tipo de respuesta modificado | `major` |
| Endpoint o método nuevo | `minor` |
| Solo cambia la documentación | `patch` |

En el cruce, `dead-call` (el frontend llama a algo inexistente) bloquea el despliegue; `metodo-distinto` es media y `sin-consumidor` es baja y se revisa para decidir si el endpoint se retira.

### Herramientas

```bash
py api-contract-guard/scripts/contract_diff.py --old old.json --new new.json --fail-on major
py api-contract-guard/scripts/code_sync.py --backend api.py --frontend app.js --json
py api-contract-guard/scripts/mock_server.py --spec api.json --port 8080
```

Salida del diff:

```json
{
  "version": "major",
  "changes": [
    {"path": "/orders", "method": "GET", "level": "major", "detail": "endpoint eliminado"}
  ]
}
```

Salida del cruce: `findings` con `route`, `method`, `rule`, `severity` y `message`, más el recuento por severidad.

Códigos de salida: `0` limpio o por debajo del umbral · `1` umbral superado · `2` contrato o ruta ilegible. El mock acepta `serve(spec)` para tests y devuelve el puerto efímero que asigna.

### Instalación y uso
Copia la carpeta `api-contract-guard/` completa. Ejemplos de petición:
- «Compara este contrato con el publicado y dime si el cambio es major».
- «¿Queda alguna llamada del frontend a rutas que ya no existen?».
- «Levántame un mock con el contrato para probar el cliente».
- «Protege el contrato antes de la release».

### Tests

```bash
uv run python -m unittest discover -s api-contract-guard/tests -t api-contract-guard/tests
```

11 pruebas: endpoint eliminado como `major`, aditivo como `minor`, tipo de respuesta cambiado, JSON ilegible, rutas que cuadran, `dead-call` que rompe la puerta, `--fail-on none`, fichero ausente y el mock sirviendo ejemplos, devolviendo 404 y sin salir de loopback.

### Límites
Compara JSON OpenAPI, no YAML, y no resuelve `$ref` externos: solo clasifica el primer código de respuesta (`200`/`201`). El cruce lee decoradores y `fetch`/`axios`/`XHR` por expresión regular, así que una ruta construida dinámicamente aparece como `dead-call` y hay que declararla. El mock no valida cuerpos ni aplica reglas de negocio: es un mock, no un emulador.

---

## English

### Index
1. Purpose
2. Modes
3. Architecture
4. Classification
5. Tools
6. Install and use
7. Tests
8. Limits

### Purpose
`api-contract-guard` answers three questions before publishing: does this change break API consumers, is any frontend call still pointing at a route that no longer exists, and can I test the client without starting the backend? Everything is static and local; the only thing listening is a mock server on `127.0.0.1`.

### Modes
The master takes no flags: the request's scope sets the phases.

| Mode | Phases | Deliverable |
|---|---|---|
| **Impact** | `api-diff` | SemVer level and per-route changes |
| **Consistency** | `api-code-sync` | `dead-call`, `metodo-distinto` and `sin-consumidor` |
| **Test** | `api-mock-server` | Local server serving the contract examples |

### Architecture
One master and three sub-skills with shared assets. The whole folder is installed.

| Sub-skill | What it does |
|---|---|
| `api-contract-guard` | Master: orders diff, sync and test, then signs the verdict |
| `api-diff` | Compares two OpenAPI contracts and computes SemVer impact |
| `api-code-sync` | Crosses backend routes with frontend calls |
| `api-mock-server` | Serves the contract examples from loopback |

### Classification
| Change | Level |
|---|---|
| Endpoint or method removed | `major` |
| Response type changed | `major` |
| Endpoint or method added | `minor` |
| Documentation only | `patch` |

In the sync, `dead-call` (the frontend calls something that does not exist) blocks deployment; `metodo-distinto` is medium and `sin-consumidor` is low and reviewed to decide whether the endpoint is retired.

### Tools

```bash
py api-contract-guard/scripts/contract_diff.py --old old.json --new new.json --fail-on major
py api-contract-guard/scripts/code_sync.py --backend api.py --frontend app.js --json
py api-contract-guard/scripts/mock_server.py --spec api.json --port 8080
```

Diff output:

```json
{
  "version": "major",
  "changes": [
    {"path": "/orders", "method": "GET", "level": "major", "detail": "endpoint eliminado"}
  ]
}
```

Sync output: `findings` with `route`, `method`, `rule`, `severity` and `message`, plus the count per severity.

Exit codes: `0` clean or below threshold · `1` threshold exceeded · `2` unreadable contract or path. The mock exposes `serve(spec)` for tests and returns the ephemeral port it picked.

### Install and use
Copy the whole `api-contract-guard/` folder. Example requests:
- "Compare this contract with the published one and tell me whether the change is major".
- "Any frontend call left pointing at routes that no longer exist?".
- "Spin up a mock from the contract so I can test the client".
- "Guard the contract before the release".

### Tests

```bash
uv run python -m unittest discover -s api-contract-guard/tests -t api-contract-guard/tests
```

11 tests: removed endpoint as `major`, additive as `minor`, changed response type, unreadable JSON, matching routes, `dead-call` failing the gate, `--fail-on none`, missing file, and the mock serving examples, returning 404 and staying on loopback.

### Limits
It compares JSON OpenAPI, not YAML, and does not resolve external `$ref`: it only classifies the first response code (`200`/`201`). The sync reads decorators and `fetch`/`axios`/`XHR` through regex, so a dynamically built route shows up as `dead-call` and must be declared. The mock validates no bodies and applies no business rules: it is a mock, not an emulator.
