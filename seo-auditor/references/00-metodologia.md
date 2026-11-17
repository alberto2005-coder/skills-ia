# Metodología y Seguridad en Auditoría SEO

## Principios Fundamentales
1. **Evidencia antes que opinión:** Todo hallazgo se sustenta en evidencia directa (código fuente, cabecera HTTP, URL rastreada o fragmento de contenido). `audit.json` guarda esa evidencia para poder recalcular la puntuación con `--rescore` sin volver a la red.
2. **Separación rigurosa de estados:**
   - **Observado:** comprobado en la respuesta HTTP o en el archivo analizado (confianza alta).
   - **Inferido / `estimate`:** deducido de una métrica aproximada (ancho de título en píxeles, ratio texto/HTML, bloque-respuesta). Siempre se etiqueta.
   - **No comprobado (`skip`):** no se pudo verificar con el alcance actual. Nunca se clasifica como error.
3. **Cero promesas o alucinaciones:** no se inventan tráfico, posiciones, backlinks, Core Web Vitals ni presencia en motores de IA. Si falta un dato externo (Search Console, PageSpeed Insights), se declara.
4. **No invasivo:** la auditoría es de solo lectura. Cualquier escritura pasa por el modo Execute con dry-run (ver `SKILL.md`).

## Severidad y su icono en el informe

| Severidad | Icono | Significado | Ejemplo |
|---|---|---|---|
| `must` | 🔴 crítico | Bloquea rastreo, indexación o cumplimiento; se corrige primero | `Disallow: /`, `noindex` en página prioritaria, JSON-LD roto, mixed content |
| `should` | 🟡 aviso | Desviación con impacto directo en clics o comprensión | título que se recorta, falta canonical, cabeceras de seguridad ausentes, imágenes sin `alt` |
| `nice` | 🟢 mejora opcional | Oportunidad sin evidencia de daño; no bloquea | `x-default`, ratio texto/HTML, `llms-full.txt`, longitud de descripción |
| — | 🟢 aprobado | La comprobación pasa | — |
| — | ⚪ no comprobado | No aplica o no se pudo medir | cabeceras en modo `source` |

## Rúbrica 0–100

| Dimensión | Peso |
|---|---:|
| Técnico | 25 |
| Contenido | 20 |
| Schema | 15 |
| GEO | 15 |
| Seguridad | 10 |
| Rendimiento | 15 |

Fórmula reproducible:

```
score_dimensión = 100 * aprobados / (aprobados + fallidos)
total = media ponderada de las dimensiones evaluadas
```

Las dimensiones sin comprobaciones ejecutadas (p. ej. Seguridad en modo `source`) se excluyen y su peso se redistribuye. Los `skip` no penalizan.

## Veredicto en una línea

| Puntuación | Veredicto |
|---|---|
| ≥ 85 | `Leading` |
| 60–84.9 | `Competitive` |
| < 60 | `Not Ready` |

El veredicto se escribe en la cabecera del informe.

**Regla de bloqueo:** si existe al menos un fallo `must`, el veredicto **no puede ser `Leading`** aunque la media supere 85. Se degrada a `Competitive` y la línea del veredicto indica cuántos bloqueos quedan (`verdict_capped_by_must` en `audit.json`). La fórmula no se altera: se evita maquillar la nota.

## Taxonomía heredada (compatibilidad)

Los hallazgos siguen exportando `severity` legacy (`critical`/`high`/`medium`/`low`) para no romper integraciones anteriores. El mapeo es `must→high`, `should→medium`, `nice→low`; el campo autoritativo es `severity_level`.

## Límites de Seguridad y Rastreo
- **Protección SSRF:** el rastreador bloquea IPs privadas, redes locales y esquemas no seguros. En modo `local` solo se admite loopback (`localhost`, `127.0.0.1`, `::1`). La validación se repite en **cada salto** de una redirección: una URL pública que redirija a `127.0.0.1` o a una IP privada se rechaza sin llegar a pedirla.
- **Exclusiones:** nunca se inspeccionan `.env`, claves privadas, credenciales, `.git`, `node_modules`, `vendor`, `build`, `dist`, `output` ni `reports`.
- **Crawl respetuoso:** robots.txt se consulta y se respeta; 1 petición/segundo por defecto; tope de páginas y profundidad se declaran en el informe (`crawl` en `audit.json`).
- **Escrituras:** nada se escribe en el sitio sin `--apply` + confirmación explícita; los borradores viven en `output/` marcados `DRAFT`.
