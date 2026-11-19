---
name: appsec-infra
description: >
  Auditoría de infraestructura como código y despliegue: Dockerfile e imágenes,
  manifiestos de Kubernetes, Terraform, CloudFormation, entornos cloud,
  permisos IAM efectivos, buckets y bases de datos expuestas, secretos de
  despliegue y privilegios de CI/CD.
  Úsala cuando pidan revisar un Dockerfile, auditar manifiestos de Kubernetes o
  Terraform, comprobar permisos IAM excesivos, detectar recursos públicos en la
  nube o endurecer un pipeline de integración y despliegue.
  English: review containers, Kubernetes, Terraform, cloud exposure, IAM
  permissions and CI/CD privileges for over-permissioning and public exposure.
license: MIT
metadata:
  package: appsec-audit
  version: "2.0.0"
---

# AppSec · Infraestructura y cloud

La mayoría de incidentes reales no empiezan con una inyección: empiezan con un bucket público, un rol con `*` o un contenedor que corre como root con la clave de producción dentro.

## Precondiciones

- Inventario de infraestructura de `appsec-recon`.
- Acceso de lectura a los ficheros de IaC y a la configuración del pipeline.
- Sin credenciales de nube activas: se audita la declaración, no se consulta la cuenta, salvo autorización explícita.

## Método

1. **Contenedores.** Imagen base y su mantenimiento, usuario final, capas y secretos en `ARG`/`ENV`, puertos, volúmenes, `--privileged`, montaje del socket, healthchecks.
2. **Kubernetes.** `securityContext`, `runAsNonRoot`, capabilities, `hostPath`, `hostNetwork`, límites de recursos, políticas de red, secretos en claro, `automountServiceAccountToken`.
3. **Terraform y CloudFormation.** Recursos públicos por defecto, cifrado en reposo y tránsito, grupos de seguridad abiertos, logs y retención, versiones de motor obsoletas.
4. **IAM.** Permisos efectivos frente a los necesarios: comodines, `iam:*`, roles encadenables, confianza entre cuentas, claves de larga duración, MFA.
5. **CI/CD.** Permisos del token, secretos en logs, ejecución de código de PRs sin aprobación, acciones de terceros sin versión fija, `pull_request_target` y similares.
6. **Superficie.** Almacenamiento público, bases de datos accesibles, paneles sin autenticación, metadatos expuestos.

## Cobertura mínima

- Contenedor: usuario, base, secretos y capabilities con veredicto por ítem.
- Kubernetes: workloads con privilegios y su justificación, o ausencia de ella.
- IaC: recursos públicos y ausencia de cifrado, con línea exacta.
- IAM: permisos excesivos concretos, no «podría ser más restrictivo».
- Pipeline: qué puede hacer un colaborador externo con un PR.

## Reglas

- **No se aplica nada**: ni `terraform plan` contra la cuenta, ni `kubectl`, ni builds. Se lee la declaración.
- Un permiso amplio solo es hallazgo si se puede explotar: se describe el camino (quién lo obtiene y qué consigue).
- La configuración por defecto del proveedor se comprueba antes de reportar: muchos recursos nacen cifrados o privados.

## Gate de salida

- Cada hallazgo con recurso, línea y efecto concreto.
- Comprobados los valores por defecto del proveedor antes de declarar exposición.
- Cadena de explotación descrita: acceso inicial → permiso → impacto.
- Separado lo observado de lo que requiere consultar la cuenta real.

## Handoff

Entrega a `appsec-report` los hallazgos con su vector y confianza. Los secretos encontrados vuelven a `appsec-recon` para consolidar el inventario; los componentes de IA desplegados, a `appsec-llm`.
