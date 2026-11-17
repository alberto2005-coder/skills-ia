# Catálogo de clases de ataque

Cada unidad del ledger usa **una** clase. La clase agrupa el fallo raíz, no el síntoma: un IDOR y un panel sin permiso son `access-control`, aunque uno sea una lectura y el otro una pantalla.

| Clase | Qué cubre | CWEs frecuentes | OWASP 2025 | ASVS 5.0 |
|---|---|---|---|---|
| `injection` | SQL, comando, plantilla, LDAP, XPath, expresión | CWE-89, CWE-78, CWE-94, CWE-917 | A05 | V1 |
| `deserialization` | Objetos, YAML, pickle, JSON con clases, firmas ausentes | CWE-502, CWE-611 | A05, A08 | V1 |
| `auth` | Contraseñas, MFA, recuperación, federación, fijación | CWE-287, CWE-384, CWE-620 | A07 | V6, V9, V10 |
| `session` | Cookie, expiración, rotación, cierre, tokens de sesión | CWE-613, CWE-384, CWE-1004 | A07 | V7 |
| `access-control` | Permiso por objeto y por función, IDOR/BOLA, escalada | CWE-284, CWE-639, CWE-862, CWE-863 | A01 | V8 |
| `data-isolation` | Separación entre inquilinos, filtros por propietario, caché compartida | CWE-639, CWE-200, CWE-566 | A01 | V8, V14 |
| `crypto` | Algoritmos, modos, aleatoriedad, gestión de claves | CWE-327, CWE-330, CWE-326 | A04 | V11 |
| `secrets` | Claves en código, historial, logs, artefactos, variables mal acotadas | CWE-798, CWE-532, CWE-312 | A02, A04 | V13, V14 |
| `logic` | Estados imposibles, cupones, reembolsos, carreras de negocio | CWE-840, CWE-362 | A06 | V2 |
| `race-condition` | TOCTOU, doble gasto, contadores sin bloqueo | CWE-362, CWE-367 | A06, A10 | V2, V15 |
| `supply-chain` | Dependencias, lockfiles, typosquatting, scripts de instalación | CWE-1104, CWE-829, CWE-937 | A03 | V15 |
| `dependencies` | CVE en componentes y alcanzabilidad del código afectado | CWE-1104, CWE-1395 | A03 | V15 |
| `cicd` | Permisos de acciones, secretos de pipeline, artefactos sin firma | CWE-829, CWE-345, CWE-494 | A03, A08 | V15 |
| `cloud-infra` | IAM, buckets, security groups, metadatos, cifrado en reposo | CWE-732, CWE-284, CWE-311 | A02 | V13, V14 |
| `ssrf` | Peticiones a destinos controlados por el atacante, metadatos cloud | CWE-918 | A01 | V1, V12 |
| `file-handling` | Subida, tipo, tamaño, path traversal, entrega y permisos | CWE-22, CWE-434, CWE-73 | A01, A05 | V5 |
| `client-side` | XSS, DOM, postMessage, CORS, dependencias del navegador | CWE-79, CWE-346, CWE-942 | A05 | V1, V3 |
| `protocol` | HTTP, WebSocket, gRPC, MQTT, TLS mal negociado | CWE-319, CWE-444, CWE-295 | A02, A04 | V12, V13 |
| `llm-agent` | Inyección de prompt, agencia excesiva, fuga de contexto, MCP | CWE-1427, CWE-1426 | A05, A06 | V1, V2 |
| `logging-monitoring` | Eventos ausentes, sin alerta, con datos personales | CWE-117, CWE-223, CWE-778 | A09 | V16 |
| `privacy` | Datos personales en trazas, retención, minimización, exportación | CWE-359, CWE-532 | A04 | V14 |
| `availability` | Falta de cuotas, agotamiento, bucles, coste sin límite | CWE-770, CWE-400 | A06, A10 | V2, V13 |
| `memory-safety` | Desbordamientos, use-after-free, doble liberación (nativo) | CWE-787, CWE-125, CWE-416 | A05, A10 | V1, V15 |
| `webhook` | Firma ausente, repetición, destino no verificado | CWE-345, CWE-294 | A08 | V4, V12 |

## Cómo se elige

- **El fallo raíz manda.** Un XSS almacenado por una entrada sin validar es `injection` si el sumidero es el intérprete y `client-side` si el fallo es de codificación en el navegador; se elige la que describa el control ausente.
- **Una unidad, una clase.** Si un endpoint acumula dos clases, son dos unidades del ledger.
- **Sin clases inventadas.** `ledger.py` rechaza cualquier clase fuera de esta tabla; si falta una, se amplía aquí, en el esquema y en el script a la vez.
- **La clase no fija la severidad.** `dependencies` con CVE no alcanzable no es crítico; `access-control` en un panel interno tampoco.

## Cobertura mínima por clase

Para cerrar una unidad, la comprobación registrada en `checks` debe decir qué se miró y con qué resultado. Ejemplos válidos: «trazado `POST /orders` → `get_order()` → consulta parametrizada», «import de `lodash` solo en tests», «bucket con política pública denegada en el plan de Terraform».
