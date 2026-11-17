# Humanizador Anti-IA

> Detección y reescritura de patrones de escritura de IA, en español.  
> Detection and rewriting of AI writing patterns, in Spanish.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice
1. [Propósito](#propósito)
2. [Modos](#modos)
3. [Score 0–100](#score-0100)
4. [Reglas No Negociables](#reglas-no-negociables)
5. [Sub-skills](#sub-skills)
6. [Referencias, Plantilla y Corpus](#referencias-plantilla-y-corpus)
7. [Uso y Tests](#uso-y-tests)

### Propósito
Reescribe textos con cadencia de IA para devolverles ritmo, concreción y voz de autor. No es un sinonimizador: el trabajo está en el contenido y la estructura. El catálogo de **40 patrones numerados** (más fuerte a más débil) es la referencia obligatoria, con pack de tells en español.

**Paquete de 3 skills:** maestro + `humanizar` (reescribe) y `detector-ia` (solo mide).

### Modos
| Modo | Qué toca |
|---|---|
| **Quick** | Vocabulario Tier 1/2, artefactos de chatbot y relleno evidente; no cambia la estructura. |
| **Full** (por defecto) | Catálogo completo: contenido, ritmo, sintaxis, estructura, vocabulario y artefactos; recorte del 20–30% de relleno. |
| **Voice** | Full + calibración con 2–3 párrafos del usuario. |

En Quick solo deben bajar vocabulario y artefactos. En Voice se imitan las decisiones del usuario, no sus frases; con menos de 80 palabras o registro distinto, se dice en vez de inventar un perfil.

### Score 0–100
**Más alto = más IA.** Medición reproducible, no veredicto de autoría.

| Señal | Peso | Qué mide |
|---|---:|---|
| `vocabulario_ia` | 30% | Lista negra por 1000 palabras, con saturación |
| `uniformidad_frases` | 25% | % de frases dentro de ±20% de la media |
| `patrones_estructurales` | 30% | «No solo X sino Y», tríadas, cierre moral, listas simétricas, párrafos uniformes |
| `artefactos_chatbot` | 15% | «Como modelo», «aquí tienes», ofertas de seguimiento |

`total` es la media ponderada. Niveles: `bajo` (<20), `moderado` (<40), `medio` (<60), `alto` (<80), `muy alto` (≥80). Con textos cortos la densidad usa una base mínima de 250 palabras; la uniformidad necesita ≥4 frases. Un informe formal legítimo puede rondar 30–40 sin ser IA: el número se lee junto a los hallazgos.

### Reglas No Negociables
1. **Honestidad factual:** un dato, cifra, cita o fecha sin fuente se marca para verificar; nunca se inventa, redondea ni «aproxima».
2. **Protección de estructura:** no se toca código, frontmatter, enlaces, correos, cifras, nombres propios, rutas, versiones ni tablas. El script los enmascara antes de medir.
3. **Registro:** LinkedIn, email, artículo o informe tienen convenciones distintas; el registro manda sobre el catálogo.
4. **Fidelidad semántica:** se cambia la arquitectura textual y el estilo, no los hechos.

### Sub-skills
| Sub-skill | Qué hace | Toca el texto |
|---|---|---|
| `humanizar` | Reescritura en Quick/Full/Voice, recorte de relleno y score antes/después. | Sí |
| `detector-ia` | Solo puntuar y detectar: señales, datos sin fuente y segmentos protegidos. | No |

### Referencias, Plantilla y Corpus
- `references/03-patrones-numerados.md`: catálogo 1–40 + pack español.
- `references/lista-negra.md`, `01-patrones-sintacticos.md`, `02-tecnicas-reescritura.md`.
- `templates/informe-auditoria.md`: score antes/después, datos a verificar y patrones dejados a propósito.
- `tests/corpus/`: 2 textos de IA, 2 humanos, 1 con datos sin fuente y 1 con código y enlaces.

### Uso y Tests
```bash
py humanizador-anti-ia/scripts/audit_style.py --text "Tu texto aquí..."
py humanizador-anti-ia/scripts/audit_style.py --file borrador.md --markdown
py humanizador-anti-ia/scripts/audit_style.py --file borrador.md --json
py humanizador-anti-ia/scripts/audit_style.py --file borrador.md --score

py -m unittest discover -s humanizador-anti-ia/tests -v
```

---

## 🇬🇧 English

### Table of Contents
1. [Purpose](#purpose)
2. [Modes](#modes)
3. [0–100 Score](#0100-score)
4. [Non-Negotiable Rules](#non-negotiable-rules)
5. [Sub-skills](#sub-skills-1)
6. [References, Template and Corpus](#references-template-and-corpus)
7. [Usage and Tests](#usage-and-tests)

### Purpose
Rewrites AI-cadence text to restore rhythm, specificity and author voice. It is not a synonym swapper: the work is in content and structure. The **40 numbered patterns** catalog (strongest to weakest) is the mandatory reference, with a Spanish tells pack.

**3-skill package:** master + `humanizar` (rewrites) and `detector-ia` (measures only).

### Modes
| Mode | What it touches |
|---|---|
| **Quick** | Tier 1/2 vocabulary, chatbot artifacts and obvious filler; structure untouched. |
| **Full** (default) | Full catalog: content, rhythm, syntax, structure, vocabulary and artifacts; 20–30% filler trim. |
| **Voice** | Full + calibration against 2–3 paragraphs from the user. |

In Quick only vocabulary and artifacts should drop. In Voice the user's decisions are imitated, not their sentences; with fewer than 80 words or a different register, say so instead of inventing a profile.

### 0–100 Score
**Higher = more AI.** A reproducible measurement, not a verdict on authorship.

| Signal | Weight | What it measures |
|---|---:|---|
| `vocabulario_ia` | 30% | Banned vocabulary per 1000 words, saturated |
| `uniformidad_frases` | 25% | % of sentences within ±20% of the mean length |
| `patrones_estructurales` | 30% | "Not only X but Y", triads, moralizing close, symmetric lists, uniform paragraphs |
| `artefactos_chatbot` | 15% | "As a model", "here you go", follow-up offers |

`total` is the weighted mean. Levels: `low` (<20), `moderate` (<40), `medium` (<60), `high` (<80), `very high` (≥80). Short texts use a 250-word floor for density; uniformity needs ≥4 sentences. A legitimate formal report can score 30–40 without being AI: read the number next to the findings.

### Non-Negotiable Rules
1. **Factual honesty:** any unsourced figure, quote or date is flagged for verification; never invented, rounded or "approximated".
2. **Structure protection:** code, frontmatter, links, emails, figures, proper nouns, paths, versions and tables are untouched. The script masks them before measuring.
3. **Register:** LinkedIn, email, article and formal report follow different conventions; register wins over the catalog.
4. **Semantic fidelity:** textual architecture and style change, facts do not.

### Sub-skills
| Sub-skill | Purpose | Edits text |
|---|---|---|
| `humanizar` | Quick/Full/Voice rewrite, filler trim and before/after score. | Yes |
| `detector-ia` | Score and detect only: signals, unsourced data and protected segments. | No |

### References, Template and Corpus
- `references/03-patrones-numerados.md`: catalog 1–40 + Spanish pack.
- `references/lista-negra.md`, `01-patrones-sintacticos.md`, `02-tecnicas-reescritura.md`.
- `templates/informe-auditoria.md`: before/after score, data to verify and patterns left on purpose.
- `tests/corpus/`: 2 AI texts, 2 human texts, 1 with unsourced data and 1 with code and links.

### Usage and Tests
```bash
py humanizador-anti-ia/scripts/audit_style.py --text "Your text here..."
py humanizador-anti-ia/scripts/audit_style.py --file draft.md --markdown
py humanizador-anti-ia/scripts/audit_style.py --file draft.md --json
py humanizador-anti-ia/scripts/audit_style.py --file draft.md --score

py -m unittest discover -s humanizador-anti-ia/tests -v
```
