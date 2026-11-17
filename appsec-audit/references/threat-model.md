# Modelo de amenazas, OWASP 2025 y ASVS 5.0

Tres piezas: el mapa (activos, actores, límites), la lista de lo que puede romperse y el mapeo que permite hablar el mismo idioma que el resto del equipo. El mapeo no sustituye al análisis: lo hace comparable.

## Límites de confianza

Un límite es toda frontera donde el nivel de confianza cambia. Por cada una se responden cuatro cosas:

| Pregunta | Qué se escribe |
|---|---|
| ¿Qué cruza? | Dato, credencial, fichero, instrucción, evento |
| ¿Quién lo controla? | Navegador, usuario, tercero, job de CI, otro servicio |
| ¿Qué se valida al entrar? | Esquema, firma, permiso, cuota, tamaño |
| ¿Qué pasa si la validación falla? | Rechazo, degradación, fallo abierto, ejecución |

Fronteras típicas: navegador → API, API → base de datos, API → cola, worker → proveedor externo, CI → producción, agente → herramienta, servicio → servicio con mTLS o sin él, contenedor → host.

## OWASP Top 10:2025

| ID | Categoría | Qué se pregunta en el modelo |
|---|---|---|
| A01 | Broken Access Control | ¿Cada objeto y cada función comprueba permiso en servidor, para este actor? |
| A02 | Security Misconfiguration | ¿La configuración por defecto del despliegue es la segura, o la cómoda? |
| A03 | Software Supply Chain Failures | ¿Qué tercero, imagen o acción de CI puede cambiar sin que lo veamos? |
| A04 | Cryptographic Failures | ¿Dónde hay datos sensibles sin cifrar, con clave débil o reutilizada? |
| A05 | Injection | ¿Todo dato que cruza una frontera llega a un intérprete sin codificar? |
| A06 | Insecure Design | ¿Falta un control por diseño —límite de intentos, aprobación, cuota—? |
| A07 | Authentication Failures | ¿Cómo se prueba la identidad y qué pasa al fallar el factor? |
| A08 | Software or Data Integrity Failures | ¿Se verifica la firma o el origen de lo que se carga y se actualiza? |
| A09 | Security Logging and Alerting Failures | ¿El evento queda registrado y alguien lo mira a tiempo? |
| A10 | Mishandling of Exceptional Conditions | ¿Un error deja el sistema en estado inseguro o filtra detalle interno? |

Diferencia con 2021: entran A03 (cadena de suministro, antes A06) y A10 (condiciones excepcionales); SSRF pasa a A01; A02 sube a segunda posición.

## ASVS 5.0

17 capítulos, publicados en mayo de 2025. Se citan por capítulo y requisito (`v5.0.0-1.2.5`) cuando el control es concreto.

| Cap. | Título | Se usa para |
|---|---|---|
| V1 | Encoding and Sanitization | Inyección, codificación de salida, deserialización segura |
| V2 | Validation and Business Logic | Validación de entrada y abuso de flujos de negocio |
| V3 | Web Frontend Security | Cabeceras, cookies, origen, recursos de terceros |
| V4 | API and Web Service | REST, GraphQL, WebSocket, límites de mensaje |
| V5 | File Handling | Subida, almacenamiento y entrega de ficheros |
| V6 | Authentication | Identidad, contraseñas, MFA, proveedores |
| V7 | Session Management | Sesión, expiración, fijación, cierre |
| V8 | Authorization | Permisos por objeto y por función |
| V9 | Self-contained Tokens | JWT y tokens firmados: validación y revocación |
| V10 | OAuth and OIDC | Flujos delegados, scopes, redirects |
| V11 | Cryptography | Algoritmos, modos, gestión de claves |
| V12 | Secure Communication | TLS, certificados, canales internos |
| V13 | Configuration | Configuración segura de app, servidor y componentes |
| V14 | Data Protection | Datos sensibles en reposo, memoria, trazas y backups |
| V15 | Secure Coding and Architecture | Inventario de componentes, actualización, diseño seguro |
| V16 | Security Logging and Error Handling | Eventos, alertas, errores sin fuga |
| V17 | WebRTC | TURN, media y señalización en tiempo real |

## De la amenaza a la unidad de cobertura

| Paso | Salida |
|---|---|
| Activo + actor + frontera | Una frase que nombra el límite |
| Caso de abuso | Historia corta con acción y garantía rota |
| Mapeo | `A0x` + `Vn` + clase del catálogo (`attack-classes.md`) |
| Unidad de ledger | `surface` (el punto de entrada), `subsystem`, `attack_class` |
| Control esperado | Qué se valida, dónde y con qué evidencia se comprueba |

Una amenaza sin unidad en el ledger no se audita: `ledger.py gaps --strict` la deja fuera y la auditoría no puede cerrarse como completa.
