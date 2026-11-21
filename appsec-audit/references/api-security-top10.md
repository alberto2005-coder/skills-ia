# API Security Top 10 en el código

Cuatro familias que se escapan del trazado clásico fuente→sumidero porque el fallo está en **quién** puede hacer la operación, no en si el dato está saneado. Cada una con su identificador de OWASP API Security Top 10 (2023), su CWE, la señal que se busca y el patrón que la cierra.

## Mapa

| Familia | OWASP API 2023 | CWE | Regla | Señal |
|---|---|---|---|---|
| BOLA (objeto de otro tenant) | API1:2023 Broken Object Level Authorization | CWE-639 | `bola-sin-scope` | El id del objeto se usa sin filtrar por propietario |
| Mass assignment | API3:2023 Broken Object Property Level Authorization | CWE-915 | `mass-assignment` | El cuerpo de la petición se vuelca entero en el modelo |
| BFLA (función de otro rol) | API5:2023 Broken Function Level Authorization | CWE-285 | `bfla-sin-rol` | La ruta administrativa no comprueba rol |
| SSRF | API7:2023 Server Side Request Forgery | CWE-918 | `ssrf-sin-allowlist` | Una URL del usuario llega al cliente HTTP |

## BOLA — `bola-sin-scope`

**Patrón vulnerable:** `Pedido.objects.get(id=pedido_id)` con el id de la ruta. El objeto existe, la autenticación pasa y el atacante lee el pedido de otro cliente.

**Patrón seguro:** el filtro incluye al propietario o al tenant del token (`Pedido.objects.get(id=..., cliente=request.user.cliente)`); si no hay coincidencia, 404 y no 403, para no filtrar la existencia.

**Qué se comprueba:** que el id de la ruta llegue al ORM junto a un filtro de propiedad, no solo a la autenticación. Fixture: `appsec-audit/tests/fixtures/api_top10/vulnerable/app.py`.

## Mass assignment — `mass-assignment`

**Patrón vulnerable:** `Usuario(**request.json)` o `usuario.update(**payload)`: el cliente manda `is_admin: true` y el modelo lo acepta.

**Patrón seguro:** lista blanca de campos (`ALLOWED_FIELDS`), esquema de entrada con campos extra prohibidos, y permisos elevados asignados solo por una ruta administrativa.

**Qué se comprueba:** que el cuerpo de la petición no se desempaquete directo en el modelo y que los campos sensibles no estén en la lista permitida.

## BFLA — `bfla-sin-rol`

**Patrón vulnerable:** `POST /admin/usuarios` protegido por autenticación pero no por rol; cualquier usuario con sesión ejecuta la función administrativa.

**Patrón seguro:** guarda de rol antes del efecto (`require_role("admin")`), y la misma comprobación en el servicio, no solo en el middleware de la ruta.

**Qué se comprueba:** que cada operación privilegiada tenga una comprobación de función, no solo de identidad. La cobertura de rutas del contrato es de `api-contract-guard`; aquí se juzga el código.

## SSRF — `ssrf-sin-allowlist`

**Patrón vulnerable:** `requests.get(request.json["url"])`; el atacante apunta a `169.254.169.254` o a un servicio interno.

**Patrón seguro:** allowlist de hosts o esquemas, resolución previa y bloqueo de rangos privados y de metadatos, sin seguir redirecciones a otros hosts.

**Qué se comprueba:** que toda URL de usuario pase por una allowlist antes del cliente HTTP, y que la redirección no la esquive.

## Límites

- Un ORM con filtro de tenant cierra BOLA; se comprueba antes de reportar.
- La autenticación no es autorización: un `login_required` no cierra BFLA.
- Un WAF o un esquema estricto reduce mass assignment, pero la lista blanca en el modelo es la prueba.
- La allowlist de SSRF debe cubrir redirecciones y DNS, no solo la primera URL.

## Referencias

- OWASP API Security Top 10 2023: API1, API3, API5 y API7.
- CWE-639, CWE-915, CWE-285 y CWE-918.
- Fixtures: `appsec-audit/tests/fixtures/api_top10/vulnerable/` y `appsec-audit/tests/fixtures/api_top10/safe/`.
