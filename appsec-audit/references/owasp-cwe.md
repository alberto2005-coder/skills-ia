# Mapeo OWASP y CWE

Cada hallazgo se etiqueta con una categoría OWASP y un CWE. Sin esa etiqueta no se puede priorizar ni comparar entre auditorías.

## OWASP Top 10 (2021) para aplicaciones web

| ID | Categoría | CWEs frecuentes |
|---|---|---|
| A01 | Broken Access Control | CWE-284, CWE-639 (IDOR), CWE-862, CWE-863 |
| A02 | Cryptographic Failures | CWE-327, CWE-330, CWE-798 (claves en código) |
| A03 | Injection | CWE-89 (SQL), CWE-78 (comando), CWE-79 (XSS), CWE-94, CWE-502 |
| A04 | Insecure Design | CWE-209, CWE-256, CWE-522 |
| A05 | Security Misconfiguration | CWE-16, CWE-611 (XXE), CWE-1004 |
| A06 | Vulnerable Components | CWE-1104, CWE-937 |
| A07 | Identification and Authentication Failures | CWE-287, CWE-384, CWE-620 |
| A08 | Software and Data Integrity Failures | CWE-345, CWE-494, CWE-829 |
| A09 | Logging and Monitoring Failures | CWE-117, CWE-223, CWE-778 |
| A10 | SSRF | CWE-918 |

## CWE Top 25: los que más aparecen en auditorías

CWE-79 (XSS), CWE-787 y CWE-125 (memoria), CWE-89 (SQLi), CWE-20 (validación), CWE-1254, CWE-416 (use after free), CWE-78 (comando), CWE-94 (inyección de código), CWE-22 (path traversal), CWE-352 (CSRF), CWE-434 (subida de ficheros), CWE-862/863 (permisos), CWE-476 (null deref), CWE-287 (autenticación), CWE-190 (desbordamiento), CWE-502 (deserialización), CWE-77, CWE-119, CWE-798 (credenciales embebidas), CWE-918 (SSRF), CWE-306 (sin autenticación), CWE-362 (condición de carrera), CWE-269 (privilegios), CWE-732 (permisos de fichero), CWE-200 (exposición de información).

## OWASP LLM Top 10 (2025)

| ID | Riesgo | Qué se comprueba |
|---|---|---|
| LLM01 | Prompt Injection | Contenido externo que altera objetivos o provoca llamadas a herramientas |
| LLM02 | Sensitive Information Disclosure | Secretos o datos de otros usuarios en contexto, trazas o respuestas |
| LLM03 | Supply Chain | Modelos, adaptadores y paquetes de terceros sin verificación |
| LLM04 | Data and Model Poisoning | Base de conocimiento o fine-tuning manipulables |
| LLM05 | Improper Output Handling | Salida del modelo usada en HTML, SQL, shell o APIs |
| LLM06 | Excessive Agency | Herramientas con más alcance del necesario o sin confirmación |
| LLM07 | System Prompt Leakage | Instrucciones internas accesibles desde la conversación |
| LLM08 | Vector and Embedding Weaknesses | Recuperación sin control de acceso por documento |
| LLM09 | Misinformation | Afirmaciones sin fuente usadas para decidir |
| LLM10 | Unbounded Consumption | Coste o latencia sin límites por usuario |

## Cómo se puntúa

- La categoría OWASP describe la familia; el CWE, el defecto concreto.
- La severidad no se hereda del CWE: un CWE-79 en un panel interno autenticado no es igual que en un comentario público.
- Si un hallazgo encaja en dos categorías, se elige la que describe el fallo raíz y se menciona la otra en el detalle.
