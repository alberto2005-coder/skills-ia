# Humanizador Anti-IA

> Módulo de reescritura estilística y variabilidad rítmica en español.  
> Stylistic rewriting and sentence burstiness module for Spanish prose.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice
1. [Propósito y Enfoque](#propósito-y-enfoque)
2. [Métricas Estadísticas Evaluadas](#métricas-estadísticas-evaluadas)
3. [Reglas Clave de Edición](#reglas-clave-de-edición)
4. [Archivos y Referencias](#archivos-y-referencias)
5. [Ejecución del Auditor Estilístico](#ejecución-del-auditor-estilístico)

### Propósito y Enfoque
Este módulo reescribe borradores con cadencia mecánica de IA para dotarlos de ritmo asimétrico, precisión léxica y naturalidad de autor, erradicando muletillas comunes y homogeneidad sintáctica.

### Métricas Estadísticas Evaluadas
- **Burstiness (Coeficiente de Variación $\ge 0.45$):** Alternancia entre oraciones cortas (4–8 palabras) y subordinadas complejas (22–35 palabras).
- **Legibilidad Fernández-Huerta:** Fórmula matemática ajustada al idioma español que pondera sílabas y longitud de oraciones.
- **Diversidad léxica (Type-Token Ratio):** Mide la variedad de vocabulario evitando redundancias repetitivas.
- **Detección de patrones:** Cuenta guiones largos (`—`), perífrasis pasivas y secuencias de oraciones monótonas.

### Reglas Clave de Edición
1. **Ruptura de tríadas:** Evitar enumeraciones automáticas de 3 adjetivos o complementos simétricos.
2. **Cero conectores robóticos:** Prohibir transiciones escolares como *"En conclusión"*, *"Asimismo"*, *"Cabe destacar"*, *"Por otro lado"*.
3. **Cierre seco:** Cortar el texto en el último dato o hecho útil; suprimir moralejas aspiracionales finales.
4. **Voz activa:** Eliminar la pasiva analítica y los gerundios de posterioridad.

### Archivos y Referencias
- `SKILL.md`: Directrices y flujo de trabajo.
- `references/lista-negra.md`: Términos sobreutilizados y sustituciones directas.
- `references/01-patrones-sintacticos.md`: Análisis de perplejidad y burstiness.
- `references/02-tecnicas-reescritura.md`: Técnicas de staccato y anclas sensoriales.
- `scripts/audit_style.py`: Auditor determinista.
- `templates/informe-auditoria.md`: Plantilla de informe comparativo.

### Ejecución del Auditor Estilístico
```bash
# Auditar texto directo
python humanizador-anti-ia/scripts/audit_style.py --text "Tu texto aquí..."

# Auditar archivo con salida en Markdown
python humanizador-anti-ia/scripts/audit_style.py --file borrador.md --markdown

# Auditar archivo con salida estructurada en JSON
python humanizador-anti-ia/scripts/audit_style.py --file borrador.md --json
```

---

## 🇬🇧 English

### Table of Contents
1. [Purpose and Approach](#purpose-and-approach)
2. [Statistical Metrics Evaluated](#statistical-metrics-evaluated)
3. [Core Editing Rules](#core-editing-rules)
4. [Files and References](#files-and-references)
5. [Running the Stylistic Auditor](#running-the-stylistic-auditor)

### Purpose and Approach
This module rewrites text with synthetic AI cadence into natural, organic Spanish prose with authentic author voice, asymmetric rhythm, and enriched lexical entropy.

### Statistical Metrics Evaluated
- **Burstiness (Coefficient of Variation $\ge 0.45$):** Marked contrast between short punchy sentences (4–8 words) and extended compound clauses (22–35 words).
- **Fernández-Huerta Readability:** Standard readability formula specifically calibrated for Spanish syllable structures.
- **Lexical Diversity (Type-Token Ratio):** Ratio between unique vocabulary and total word count.
- **Pattern Detection:** Flags em-dashes (`—`), passive constructions, and repetitive consecutive sentence lengths.

### Core Editing Rules
1. **Triad Breaking:** Avoid symmetrical lists of 3 adjectives or parallel verbs.
2. **Zero Robotic Connectors:** Ban formulaic transitions such as *"En conclusión"*, *"Asimismo"*, *"Cabe destacar"*.
3. **Abrupt Closures:** End texts on the final actionable fact; purge generic philosophical wrap-ups.
4. **Active Voice:** Replace periphrastic passive structures with direct action verbs.

### Files and References
- `SKILL.md`: Core directives and editorial workflow.
- `references/lista-negra.md`: Banned clichés and organic replacements.
- `references/01-patrones-sintacticos.md`: Perplexity and burstiness mechanics.
- `references/02-tecnicas-reescritura.md`: Staccato, juxtaposition, and sensory grounding.
- `scripts/audit_style.py`: Deterministic evaluator.
- `templates/informe-auditoria.md`: Comparative audit report template.

### Running the Stylistic Auditor
```bash
# Evaluate raw text string
python humanizador-anti-ia/scripts/audit_style.py --text "Your text here..."

# Evaluate file with Markdown output
python humanizador-anti-ia/scripts/audit_style.py --file draft.md --markdown

# Evaluate file with JSON output
python humanizador-anti-ia/scripts/audit_style.py --file draft.md --json
```
