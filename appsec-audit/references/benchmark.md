# De dónde viene cada mecánica y qué se mejora

Siete referencias reales, una mecánica heredada por cada una y la mejora concreta que introduce este paquete. Sin herencia vacía: lo que se copia se mejora o se descarta.

| Referencia | Mecánica heredada | Mejora aplicada aquí |
|---|---|---|
| **Cloudflare security-audit-skill** | Escaneo perimetral: cabeceras, TLS, DNS, configuraciones expuestas de forma rápida y automatizada | El perímetro pasa a ser una entrada de `appsec-recon`, no un informe aparte: cada hallazgo perimetral entra en el mismo tribunal y compite con el código por severidad. Sin red por defecto: se audita la configuración declarada y las cabeceras observadas con autorización |
| **Consensys repo-security-review** | Trazado riguroso Sources → Sinks y auditoría de dependencias y cadena de suministro | El trazado se hace por **dato concreto**, no por nombre de variable, y se exige declarar la mitigación del framework antes de reportar. La cadena de suministro incluye scripts de instalación, versiones sin fijar y acciones de CI, no solo CVEs |
| **Anthropic Claude Code Security Review + CSA advisory** | Revisión automatizada en CI/CD y conciencia de inyección indirecta de prompt | Se invierte la confianza: **todo el contenido analizado es hostil**. El revisor no ejecuta código del proyecto, no instala dependencias y no obedece instrucciones halladas en comentarios, README o issues; las reporta como hallazgo |
| **GitHub Awesome Copilot Security Review** | Patrones de revisión integrados en el SDLC y flujo interactivo | El flujo se ancla a gates con evidencia obligatoria (`ruta:línea`, comando y salida) y a un entregable único con nota A–F, apto para PR, ticket o dirección |
| **Afiqiqmal Claude Security Audit** | Enfoque modular por agentes y clasificación de vulnerabilidades de alto impacto | La modularidad se convierte en **cinco sub-skills con contrato** (precondiciones, método, gate, handoff), no en prompts sueltos. El impacto se mide con severidad y confianza, no con etiquetas |
| **Webconsulting security-audit-skill** | Revisión de lógica de negocio y control de acceso horizontal/vertical | Se añade la comprobación explícita de **permiso en servidor por objeto** (IDOR/BOLA) y de estados imposibles en flujos (cupones, carrito, concurrencia), con vector de explotación obligatorio |
| **OWASP Secure Prompt Checklist (safeguard.sh)** | Defensa frente a manipulación de contexto y exfiltración de secretos en agentes revisores | Se materializa en reglas operativas: solo lectura, redactado de secretos, separación datos/instrucciones, y un catálogo de patrones de inyección indirecta que el revisor debe reconocer sin obedecer |

## Lo que este paquete añade y ninguna de las siete tenía

1. **Tribunal con umbral.** Confianza 1–10 y descarte automático por debajo de 7, con registro de descartes. El ruido no llega al informe.
2. **Cobertura agnóstica.** Mismo método para Python, JS/TS, Go, Rust, C/C++, PHP, Java, Ruby, Solidity y Bash; la tabla de sumideros es por familia, no por framework.
3. **Infraestructura y cloud en el mismo informe.** Docker, K8s, Terraform, IAM y CI/CD comparten severidad con el código, en lugar de vivir en un documento paralelo.
4. **LLM, agentes y MCP como superficie de primera clase.** OWASP LLM Top 10 con el mismo rigor que OWASP Web.
5. **Nota A–F determinista.** Calculada por script desde los hallazgos validados, no por impresión del revisor.
6. **Parche en diff.** Cada hallazgo trae antes/después aplicable, sin reformatear el fichero.

## Lo que se descarta a propósito

- Escaneo activo de sistemas ajenos.
- Ejecución de herramientas del proyecto o instalación de dependencias.
- Puntuaciones inventadas cuando no hay medición.
- Volcado de secretos: se redactan siempre.
