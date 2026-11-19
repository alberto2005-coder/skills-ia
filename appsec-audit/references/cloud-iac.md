# Contenedores, Kubernetes, IaC, IAM y CI/CD

Lista de comprobación con el valor concreto que se busca. Un hallazgo sin esta concreción es una opinión.

## Dockerfile

| Comprobación | Valor esperado | Riesgo si falla |
|---|---|---|
| Usuario final | `USER` no root o usuario sin privilegios | Escalada dentro del contenedor |
| Imagen base | Etiqueta fija y mantenida, no `latest` | Superficie desconocida y sin parches |
| Secretos | Ninguno en `ARG`/`ENV`/capas | Secreto en el registro de imágenes |
| Instalación | Sin `curl \| sh` ni repos sin firmar | Ejecución de código en build |
| Puertos y montajes | Solo los necesarios, sin socket de Docker | Escape del contenedor |
| Metadatos | `HEALTHCHECK`, etiquetas de origen | Operación ciega |

## Kubernetes

- `securityContext.runAsNonRoot: true`, `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem`.
- `capabilities.drop: ["ALL"]`, añadir solo las imprescindibles.
- Sin `hostPath`, `hostNetwork`, `hostPID` salvo justificación escrita.
- `automountServiceAccountToken: false` cuando el pod no habla con la API.
- `resources.limits` definidos: sin límites no hay contención de daño.
- `NetworkPolicy` por defecto denegando, con reglas explícitas.
- Secretos vía `Secret`/gestor externo, nunca en `env` del manifiesto versionado.
- `imagePullPolicy` y digest fijado para producción.

## Terraform / CloudFormation

- Recursos públicos: buckets, bases de datos, colas, snapshots. Se comprueba el valor por defecto del proveedor.
- Cifrado en reposo y en tránsito explícito, no heredado.
- Grupos de seguridad con `0.0.0.0/0` solo en 443 y con justificación.
- Registro de auditoría activado y con retención suficiente.
- Versiones de motor y de runtime soportadas.
- `prevent_destroy`, bloqueo de estado y estado remoto cifrado.

## IAM

- Comodines (`*` en acción o recurso) en roles de aplicación.
- `iam:*`, `sts:AssumeRole` sin condición, confianza entre cuentas sin ExternalId.
- Claves de larga duración en lugar de roles; MFA ausente en cuentas privilegiadas.
- Roles encadenables que permiten escalar a administrador.
- Separación entre plano de control y de datos; permisos de lectura sobre todos los buckets.

## CI/CD

- Token con permisos mínimos (`contents: read` por defecto), sin `write-all`.
- Secretos fuera de logs, enmascarados y con alcance por entorno.
- `pull_request_target` con checkout del PR: ejecución de código no confiable con secretos.
- Acciones de terceros fijadas por SHA, no por etiqueta móvil.
- Aprobación manual para entornos productivos.
- Artefactos firmados y procedencia verificada.

## Cómo se reporta

Cada fila incumplida se acompaña de la línea del fichero y de la consecuencia concreta: qué permiso obtiene un atacante y qué puede hacer con él. La configuración por defecto del proveedor se verifica antes de declarar exposición.
