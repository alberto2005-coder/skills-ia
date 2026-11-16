---
name: humanizador-anti-ia
description: Humaniza y reescribe textos para eliminar patrones de escritura de IA basándose en "Wikipedia: Signs of AI writing", burstiness (variabilidad sintáctica), perplejidad léxica y legibilidad. Incluye auditoría determinista en Python, glosario anti-clichés, guías sintácticas y plantillas de informes. Actívala siempre que el usuario pida humanizar un texto, quitarle el tono de IA, reescribirlo para que suene natural/humano o superar detectores como ZeroGPT, GPTZero, Turnitin u Originality.ai.
---

# Humanizador Anti-IA

Reescribe textos generados por modelos de lenguaje o excesivamente corporativos para dotarlos de ritmo orgánico, asimetría humana, precisión léxica y naturalidad de autor, eliminando huellas estadísticas y estilísticas típicas de la IA.

## Cuándo usar esta skill

- Cuando el usuario pida "humanizar" un texto, hacerlo sonar más natural, desenfadado o quitarle el tono robótico/académico plano.
- Para adaptar borradores de artículos, ensayos, landing pages, posts o correos y superar filtros editoriales o detectores de IA (GPTZero, ZeroGPT, Turnitin, Originality.ai).
- Para auditar objetivamente si un texto presenta indicios sintácticos o léxicos de haber sido escrito por un LLM.

---

## Módulos y Referencias de la Skill

| # | Documento | Foco |
|---|---|---|
| **01** | `references/lista-negra.md` | Lista negra de clichés, conectores mecánicos prohibidos y sustituciones en español |
| **02** | `references/01-patrones-sintacticos.md` | Explicación profunda de Perplexity, Burstiness y vicios estructurales de LLMs |
| **03** | `references/02-tecnicas-reescritura.md` | Técnicas prácticas: Staccato, corte en seco, anclas sensoriales y yuxtaposición |
| **04** | `templates/informe-auditoria.md` | Plantilla para informes editoriales y comparativas antes/después |

---

## Reglas estrictas de edición

### 1. Ritmo y estructura (Burstiness)
- **Contraste deliberado:** Alterna de forma marcada frases puñetazo (4 a 8 palabras) con oraciones complejas y subordinadas (22 a 35 palabras). Prohibido encadenar 3 o más oraciones de longitud homogénea.
- **Ruptura de simetría:** Rompe las tríadas clásicas de adjetivos (*"rápido, intuitivo y escalable"*). Varía los arranques de párrafo para que no empiecen con el mismo conector ni con artículos idénticos.
- **Cero conectores robóticos:** Prohíbe muletillas mecánicas de transición (*En conclusión*, *Cabe destacar*, *Es importante señalar*, *Asimismo*, *Por otro lado*, *En resumen*, *Sin lugar a dudas*, *En última instancia*). Une mediante yuxtaposición o puntuación natural.

### 2. Vocabulario y riqueza léxica (Perplejidad)
- **Purga de clichés de LLM:** Consulta `references/lista-negra.md` y erradica adjetivos inflados y metáforas poéticas forzadas (*crucial*, *fascinante*, *tapiz*, *panorama en constante evolución*, *desentrañar*, *sumergirse en*, *testamento de*, *faro de*, *catalizador*, *revolucionar*, *potenciar*, *brindar*, *abarcar*, *multifacético*, *sinergia*, *holístico*).
- **Verbos directos sobre perífrasis:** Sustituye perífrasis abstractas por acciones directas. Habla como un profesional real con experiencia práctica.

### 3. Gramática en español y tono
- **Prohibición de guiones largos (— o –):** La IA abusa de incisos explicativos entre rayas. Sustitúyelos por comas, paréntesis o punto y seguido.
- **Evitar la voz pasiva y el gerundio de posterioridad:** Transforma construcciones pasivas (*"ha sido implementado por"*) en voz activa directa, y no uses gerundios que indiquen consecuencia posterior.
- **Cierre seco sin moralejas:** Elimina el sermón aspiracional final (*"a medida que miramos hacia el futuro..."*). Termina el texto en seco con el último hecho o conclusión útil.
- **Fidelidad semántica:** Conserva intactos todos los hechos, datos y argumentos técnicos; altera únicamente la arquitectura textual y el estilo.

---

## Herramienta de Auditoría Determinista (`scripts/`)

Script en Python 3.8+ (solo librería estándar) para verificar métricas objetivas:

```bash
# Auditar un texto directo
python scripts/audit_style.py --text "Tu texto reescrito aquí..."

# Auditar un archivo y exportar en Markdown o JSON
python scripts/audit_style.py --file borrador.md --markdown
python scripts/audit_style.py --file borrador.md --json
```

**Métricas evaluadas por el script:**
- **Burstiness (CV):** Coeficiente de variación (debe ser $\ge 0.45$).
- **Legibilidad:** Índice Fernández-Huerta para español.
- **Diversidad léxica:** Type-Token Ratio (TTR).
- **Detección de patrones:** Clichés de lista negra, guiones largos (—), abuso de pasiva y oraciones homogéneas consecutivas.

---

## Flujo de trabajo obligatorio

1. **Revisión previa:** Revisa `references/lista-negra.md` y `references/01-patrones-sintacticos.md` para interiorizar los patrones a evitar.
2. **Reescritura integral:** Aplica las técnicas de `references/02-tecnicas-reescritura.md` alternando conscientemente longitudes de frase, inyectando vocabulario preciso y suprimiendo moralejas.
3. **Auditoría automática:** Si dispones de entorno de ejecución, corre `python scripts/audit_style.py --file <archivo>` para comprobar que el Burstiness supera 0.45 y los clichés estén en cero. Corrige cualquier observación antes de entregar.
4. **Entrega de resultados:** Presenta el texto humanizado limpio y, si el usuario lo solicita, adjunta la comparativa usando `templates/informe-auditoria.md`.
