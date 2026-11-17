# Informe de Auditoría y Humanización Estilística

## Resumen Ejecutivo

- **Texto evaluado:** {{titulo_o_archivo}}
- **Registro detectado:** {{LinkedIn / email / artículo / informe formal}}
- **Modo aplicado:** {{Quick / Full / Voice}}
- **Resultado:** {{APROBADO / REQUIERE REESCRITURA}}
- **Puntuación IA (0-100, más alto = más IA):** {{score_total_original}} → **{{score_total_final}}**
- **Índice de Burstiness (CV):** {{burstiness_cv}} (Mínimo recomendado: 0.45)
- **Diversidad Léxica (TTR):** {{ttr}}
- **Legibilidad (Fernández-Huerta):** {{legibilidad}} / 100

> Recordatorio: el score mide señales contables del texto, no certifica autoría. Se interpreta junto a los hallazgos.

---

## 1. Puntuación 0-100 por señal

| Señal | Original | Final | Peso | Qué mide |
|---|---|---|---|---|
| Vocabulario IA | {{vocabulario_ia_orig}} | {{vocabulario_ia_final}} | 30% | Clichés por cada 1000 palabras |
| Uniformidad de frases | {{uniformidad_orig}} | {{uniformidad_final}} | 25% | % de frases dentro de ±20% de la media |
| Patrones estructurales | {{estructura_orig}} | {{estructura_final}} | 30% | «No solo X sino Y», tríadas, cierres, listas simétricas |
| Artefactos de chatbot | {{artefactos_orig}} | {{artefactos_final}} | 15% | «Como modelo de lenguaje», «espero que te ayude» |
| **TOTAL (más alto = más IA)** | **{{score_total_original}}** | **{{score_total_final}}** | 100% | Media ponderada |

Niveles: `bajo` (<20) · `moderado` (<40) · `medio` (<60) · `alto` (<80) · `muy alto` (≥80).

Cómo se ha medido: `py scripts/audit_style.py --file {{archivo}} --score`. Todo el cálculo sale del texto; no hay red ni estimaciones externas.

---

## 2. Métricas Cuantitativas

| Métrica | Original (Borrador) | Humanizado (Final) | Objetivo |
|---|---|---|---|
| Total oraciones | | | |
| Longitud media | | | 12 – 18 palabras |
| Frases cortas (≤ 8 palabras) | | | ≥ 20% del total |
| Frases largas (≥ 22 palabras) | | | ≥ 20% del total |
| Coeficiente de variación (CV) | | | ≥ 0.45 |
| Clichés / Conectores IA detectados | | | 0 |
| Guiones largos (—/–) | | | 0 |
| Palabras recortadas (relleno) | — | {{porcentaje_recorte}}% | 20 – 30% en modo Full |

---

## 3. Datos a Verificar (no se reescriben)

Datos, cifras y atribuciones detectadas sin fuente en el propio texto. **No se han corregido ni completado**: se marcan para que el autor los verifique.

| Fragmento | Tipo | Detalle | Acción |
|---|---|---|---|
| {{fragmento_1}} | {{dato sin fuente / atribución vaga}} | `{{detalle}}` | Verificar fuente antes de publicar |
| | | | |

- [ ] Todos los datos marcados tienen fuente confirmada antes de publicar.
- [ ] Ninguna cifra se ha sustituido por otra inventada durante la reescritura.

---

## 4. Clichés y Patrones IA Eliminados

| Patrón (nº del catálogo) | Frase o Cliché Detectado | Sustitución Aplicada | Motivo |
|---|---|---|---|
| | | | |

---

## 5. Contenido Protegido (intacto)

| Tipo | Nº de bloques | Comprobado |
|---|---|---|
| Bloques de código | | [ ] |
| Código en línea | | [ ] |
| Enlaces / correos | | [ ] |
| Frontmatter YAML | | [ ] |
| Cifras y nombres propios | | [ ] |

> Cualquier cambio dentro de estos bloques requiere permiso explícito del autor.

---

## 6. Comparativa Antes / Después

### Fragmento Original (Borrador con sesgo IA)
> {{texto_original}}

### Fragmento Reescrito (Humanizado)
> {{texto_humanizado}}

---

## 7. Patrones que se han dejado a propósito

Patrones del catálogo marcados «a veces es legítimo» que encajan con el registro y por eso **no** se han tocado.

| Patrón | Dónde | Por qué se mantiene |
|---|---|---|
| | | |

---

## 8. Conclusión Editorial
{{conclusión_editorial_y_observaciones}}

- **Qué ha bajado y cuánto:** {{resumen_del_delta_por_señal}}
- **Qué no se pudo tocar:** {{limitaciones}}
- **Siguiente paso recomendado:** {{siguiente_paso}}
