# Metodología y Seguridad en Auditoría SEO

## Principios Fundamentales
1. **Evidencia antes que opinión:** Todo hallazgo debe sustentarse en evidencia directa y comprobable (código fuente, cabecera HTTP, URL rastreada o fragmento de contenido).
2. **Separación rigurosa de estados:**
   - **Observado:** Comprobado directamente en la respuesta HTTP o en el archivo analizado.
   - **Inferido:** Deducido a partir de patrones o señales parciales.
   - **No comprobado (Unknown):** Elemento que no se ha podido verificar con las herramientas o el alcance actual. Nunca debe clasificarse como error.
3. **Cero promesas o alucinaciones:** No inventar datos de tráfico, posiciones de búsqueda ni presencia garantizada en motores de IA (GEO).
4. **No invasivo y solo lectura:** Las auditorías nunca alteran el código fuente auditado ni realizan modificaciones en servidores de producción.

## Clasificación de Severidad

| Nivel | Definición | Ejemplo |
|---|---|---|
| **Critical** | Bloqueo generalizado de rastreo o indexación; desastres técnicos que anulan páginas prioritarias. | `Disallow: /` en producción, etiqueta `noindex` en toda la web, bucles infinitos de redirección en la home. |
| **High** | Problema importante con impacto directo en el rendimiento orgánico de páginas clave. | Páginas prioritarias sin título o canonical incorrecto, enlaces internos rotos masivos, canibalización crítica. |
| **Medium** | Desviación de buenas prácticas o impacto indirecto en la rastreabilidad o comprensión. | Títulos duplicados en categorías secundarias, imágenes sin atributo `alt`, Schema.org con advertencias no críticas. |
| **Low** | Oportunidades de optimización y mejoras cosméticas sin evidencia de daño orgánico. | Optimización de longitud de meta description, limpieza de cadenas de redirección internas de un solo salto. |

## Niveles de Confianza

- **High:** Dato verificado fehacientemente en la respuesta del servidor o en el archivo de plantilla/código.
- **Medium:** Deducción razonable basada en convenciones del framework o patrones de URLs.
- **Low:** Hipótesis preliminar que requiere acceso a Google Search Console, herramientas de analítica o validación humana.

## Límites de Seguridad y Rastreo
- **Protección SSRF:** El rastreador web bloquea accesos a IPs privadas, redes locales y esquemas no seguros (`file://`, puertos internos no autorizados). En modo `local` únicamente se admite loopback (`localhost`, `127.0.0.1`, `::1`).
- **Exclusiones de archivos sensibles:** Nunca inspeccionar ni indexar carpetas como `.env`, claves privadas (`id_rsa`), credenciales (`credentials.json`), `.git`, `node_modules`, `vendor`, `build` o `dist`.
- **Rastreo responsable:** Respeto estricto a límites de concurrencia, profundidad (por defecto hasta 3 niveles) y cantidad de páginas (por defecto 30, configurable con un tope seguro).
