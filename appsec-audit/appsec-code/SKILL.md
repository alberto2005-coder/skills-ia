---
name: appsec-code
description: >
  Análisis de seguridad del código con trazado de flujo de datos de fuentes a
  sumideros, en cualquier lenguaje o framework. Cubre inyección (SQL, comando,
  plantilla, deserialización, XXE), control de acceso horizontal y vertical
  (IDOR/BOLA), autenticación y sesión, criptografía mal usada, subida de
  ficheros, SSRF, path traversal y fallos de lógica de negocio.
  Úsala cuando pidan revisar el código en busca de vulnerabilidades, trazar si
  una entrada de usuario llega a una consulta o comando, o auditar permisos y
  reglas de negocio de una API.
  English: source-to-sink analysis of request handlers and data flow in any language,
  covering injection, broken access control, authn/authz, crypto misuse and
  business-logic flaws.
license: MIT
metadata:
  package: appsec-audit
  version: "2.0.1"
  author: "Alberto Ortiz"
---

# AppSec · Código y flujo de datos

El hallazgo no es «usa `eval`»: es «este parámetro de la ruta llega a `eval` sin pasar por la validación que sí aplica el resto del módulo». Lo primero es estilo; lo segundo es una vulnerabilidad.

## Precondiciones

- Inventario de `appsec-recon` con puntos de entrada y datos que acepta cada uno.
- Autorización vigente y alcance escrito.

## Método: de la fuente al sumidero

1. **Fuentes.** `request`, query, body, cabeceras, cookies, fichero subido, cola, webhook, variable de entorno, respuesta de terceros.
2. **Transformaciones.** Validación, parseo, normalización, escapado, ORM, plantilla, serialización. Aquí es donde vive la mitigación real.
3. **Sumideros.** SQL/NoSQL, shell, `eval`, plantillas, deserialización, sistema de ficheros, HTTP saliente, logs, cifrado, `innerHTML`.
4. **Trazado.** Se sigue el dato concreto, no el nombre de la variable. Se anota cada paso con `ruta:línea`.
5. **Veredicto preliminar.** Alcanzable y sin saneo → candidato. Con saneo → se documenta qué lo neutraliza y se descarta.

## Cobertura

| Familia | Qué se busca |
|---|---|
| Inyección | SQL/NoSQL, comando, LDAP, plantilla (SSTI), cabeceras, CRLF |
| Deserialización | Objetos no confiables, `pickle`, YAML inseguro, Java nativo |
| Control de acceso | IDOR/BOLA, escalada vertical, rutas sin comprobación de rol, filtros por cliente |
| Autenticación | Contraseñas, MFA, recuperación, JWT (algoritmo, firma, expiración), sesiones |
| Criptografía | Algoritmos obsoletos, modos, IV, sal, comparación no constante, claves en código |
| Ficheros | Path traversal, subida sin validar tipo/tamaño, ejecución desde uploads |
| Red saliente | SSRF, validación de destino, metadatos cloud |
| Lógica | Límites, cupones, carrito, concurrencia, estados imposibles, idempotencia |

## Reglas de análisis

- **El framework cuenta.** Un ORM con parámetros, un motor de plantillas con autoescape o un middleware CSRF pueden cerrar el hallazgo: se comprueba antes de reportar.
- **Configuración incluida.** Un `eval` en un fichero de test no pesa como uno en una ruta pública; se anota el contexto de exposición.
- **Sin ejecución.** No se lanzan pruebas ni se hacen peticiones al sistema. Se lee y se razona.
- **Un hallazgo, una ruta de explotación.** Si no se puede describir el vector paso a paso, no es un hallazgo: es una duda, y va como tal.

## Herramientas del paquete

```bash
py appsec-audit/scripts/map_flows.py <ruta> --json
```

Lista candidatos `fuente → sumidero` con fichero y línea para priorizar la lectura manual. Es un índice heurístico, no un veredicto: el tribunal decide.

## Gate de salida

- Cada hallazgo con fuente, sumidero, ruta de datos y `CWE`.
- Comprobado si el framework, ORM o middleware mitiga; si mitiga, descartado y anotado.
- Sin hallazgos basados en nombres de variables o en suposiciones.
- Rutas de acceso y rol verificadas contra el código, no contra la documentación.

## Handoff

Entrega los candidatos validados a `appsec-report` con evidencia y confianza preliminar. Los que dependan de infraestructura (permisos de nube, secretos, contenedores) pasan a `appsec-infra`; los de agentes o modelos, a `appsec-llm`.
