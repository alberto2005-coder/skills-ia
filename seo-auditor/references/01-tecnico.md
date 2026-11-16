# Diagnóstico Técnico SEO

Audita la infraestructura, rastreabilidad, indexabilidad y arquitectura técnica del sitio.

## Áreas Clave de Inspección

### 1. Rastreabilidad e Indexabilidad
- **HTTP Status Codes:** Identificar códigos de estado 4xx (errores de cliente), 5xx (errores de servidor), y cadenas o bucles de redirección 3xx.
- **Directivas Robots:**
  - `robots.txt`: Verificar directivas de bloqueo accidental (`Disallow: /`), referencias a sitemaps XML y reglas conflictivas.
  - Meta tag `<meta name="robots" content="...">`: Verificar que páginas indexables no contengan `noindex` ni `nofollow`.
  - Cabecera HTTP `X-Robots-Tag`: Comprobar si se aplican directivas a nivel de cabecera en archivos o recursos estáticos.

### 2. Canónicas y Duplicidad Técnica
- **Etiqueta `<link rel="canonical" href="...">`:**
  - Debe ser una URL absoluta y canónica autorreferencial en páginas originales.
  - No debe apuntar a URLs que devuelvan 4xx o redirecciones 3xx.
  - Debe evitar inconsistencias entre protocolo (`http` vs `https`) y trailing slashes.

### 3. Internacionalización (Hreflang)
- Cuando existan múltiples idiomas o regiones, verificar que las etiquetas `hreflang` cuenten con enlaces de retorno bidireccionales recíprocos y correspondan a códigos ISO válidos.

### 4. Renderizado y Rendimiento Observable
- **Dependencia de JavaScript:** Evaluar si el contenido esencial (título, texto principal, enlaces) se encuentra presente en el HTML inicial o si depende enteramente del renderizado en cliente (CSR).
- **Recursos críticos:** Detección de bloqueos de renderizado y buenas prácticas de carga de fuentes y estilos.

### 5. Estructura de Enlaces Internos
- Detección de enlaces rotos internos.
- Páginas huérfanas (sin enlaces internos entrantes dentro de la muestra rastreada).
- Profundidad de clics excesiva para contenidos prioritarios.

## Salida Esperada en Diagnóstico Técnico
Para cada hallazgo:
- **Ubicación:** URL o ruta del archivo.
- **Evidencia literal:** Extracto del código o cabecera observada.
- **Severidad:** Critical / High / Medium / Low.
- **Recomendación:** Acción técnica concreta y reproducible para corregir el problema.
