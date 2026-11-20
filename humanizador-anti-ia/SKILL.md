---
name: humanizador-anti-ia
description: >
  Humaniza y reescribe textos en español para quitarles los patrones de escritura de IA, con catálogo numerado de 40 patrones (más fuerte a más débil), pack de tells en español, puntuación 0-100 determinista de 4 señales medibles, modos Quick/Full/Voice, detección de registro (LinkedIn, email, newsletter, informe) y reglas de honestidad factual y protección de código. Úsala cuando pidan humanizar un texto, quitarle el tono de IA, reescribirlo para que suene natural o auditarlo de forma objetiva. English: choose the anti-AI writing mode, detect the register and set the factual honesty policy.
license: MIT
metadata:
  package: humanizador-anti-ia
  version: "2.1.0"
  author: "Alberto Ortiz"
---

# Humanizador Anti-IA

Reescribe textos generados por modelos de lenguaje o excesivamente corporativos para devolverles ritmo, concreción y voz de autor. No es un sinonimizador: la mayor parte del trabajo está en el contenido y la estructura, no en cambiar palabras.

**Documento obligatorio:** `references/03-patrones-numerados.md`. Recórrelo entero antes de reescribir y vuelve a comprobarlo al terminar. El resto de referencias lo desarrolla, no lo sustituye.

## Cuándo usar esta skill

- Cuando pidan humanizar, naturalizar o «quitar el tono de IA» de un texto.
- Para adaptar borradores de artículos, emails, posts de LinkedIn, landing pages o informes.
- Para auditar de forma objetiva cuántas señales de IA tiene un texto (score 0-100 reproducible).

---

## Sub-skills

El paquete se instala como una unidad: las sub-skills comparten `references/`, `scripts/` y `templates/` de esta carpeta.

| Sub-skill | Qué hace | Toca el texto |
|---|---|---|
| `humanizar` | Reescritura en modo Quick/Full/Voice con recorte de relleno y score antes/después | Sí |
| `detector-ia` | Solo puntuar y detectar: señales, datos sin fuente y segmentos protegidos | No |

Esta skill es el **maestro**: define modos, registro, honestidad factual y protección. El procedimiento vive en `humanizar`; la medición sin edición, en `detector-ia`.

## Modos de trabajo

| Modo | Qué toca | Cuándo usarlo |
|---|---|---|
| **Quick** | Solo vocabulario (Tier 1 y 2), artefactos de chatbot y relleno evidente. No cambia la estructura. | Prisa, textos cortos, o cuando el usuario solo quiere «quitar las palabras raras». |
| **Full** *(por defecto)* | Todo el catálogo: contenido, ritmo, sintaxis, estructura, vocabulario y artefactos. Incluye auditoría estructural y **recorte del 20-30% de relleno**. | Cualquier encargo normal. Es el modo que se aplica si el usuario no especifica. |
| **Voice** | Full + calibración con **2-3 párrafos de escritura propia del usuario**. Se imitan sus hábitos: longitud media de frase, uso de paréntesis, comillas, muletillas, grado de formalidad y tipo de cierre. | Cuando el texto debe sonar a una persona concreta (su LinkedIn, su newsletter, su firma). |

El procedimiento de cada modo (qué tocar y en qué orden) está en `humanizar`. El maestro fija qué significa cada modo, el registro y lo que no se negocia.

---

## Registro: qué significa «humano» en cada caso

Antes de reescribir, identifica el registro. No hay un único «tono humano»; hay convenciones distintas, y aplicar las de un registro a otro estropea el texto.

| Registro | Señales para detectarlo | Qué es «humano» aquí | Qué NO hacer |
|---|---|---|---|
| **Post de LinkedIn / red social** | Primera persona, hashtags, emojis, párrafos de una línea, llamada a comentar | Frases cortas y fragmentos, anécdota concreta, una idea por línea, cierre sin moraleja | Nada de fragmentos en un informe; aquí sí valen |
| **Email** | Saludo, destinatario, asunto, despedida | Frases directas, contexto compartido, una petición clara, cierre con nombre | No convertir en artículo ni añadir epígrafes |
| **Artículo / newsletter** | Título, párrafos, ejemplos, quizá enlaces | Voz propia, ejemplos concretos, variación de ritmo, subtítulos concretos | No meter jerga de consultoría ni listas de tres |
| **Informe formal / técnico** | Epígrafes, tablas, cifras, tercera persona | Precisión, voz activa cuando se sabe el agente, frases completas, cierre con decisión y siguiente paso | **Nada de fragmentos**, nada de coloquialismos, nada de «tú» si el documento no lo usa |

Reglas transversales: el registro manda sobre el catálogo. Si un patrón marcado «a veces es legítimo» encaja con el registro (una raya en un diálogo, una pasiva en un método), se deja y se anota. Si el texto mezcla registros, se elige el dominante y se avisa.

---

## Reglas estrictas de edición

### 1. Honestidad factual (no negociable)

- Si el texto contiene una **estadística, cifra, cita o fecha sin fuente**, se **marca como «verificar»** en el informe. Nunca se reescribe inventando el dato, el autor ni el estudio.
- Tampoco se redondea, se actualiza ni se «aproxima» una cifra para que suene mejor.
- Si el dato es imprescindible y no hay fuente, se deja tal cual con la marca, o se reformula como afirmación cualitativa **sin cifra nueva**: «muchos equipos» en lugar de «el 68%».
- Las atribuciones vagas («estudios demuestran», «expertos coinciden») se tratan igual: se marcan para verificar.
- `audit_style.py` las detecta y las lista en `datos_a_verificar`; el informe las recoge en su apartado propio.

### 2. Protección de estructura

No se toca, ni para «mejorar el estilo»:

- bloques de código (```` ``` ```` y `~~~`), código en línea (`` ` ``);
- frontmatter YAML (el bloque `---` inicial);
- enlaces y correos (URL, `mailto:`, direcciones);
- valores de datos: cifras, unidades, nombres propios, rutas, versiones, claves, comandos;
- tablas y su alineación.

El script enmascara estos segmentos antes de medir (`mask_protected`) y puede restaurarlos (`restore_masked`), de modo que una reescritura no los altere. Si hay que cambiar algo dentro de un bloque protegido, se avisa y se pide permiso; no se hace en silencio.

### 3. Ritmo y estructura

- **Contraste deliberado:** alterna frases de 4-8 palabras con subordinadas de 22-35. Prohibido encadenar 3 o más oraciones de longitud homogénea.
- **Ruptura de simetría:** rompe las tríadas (*«rápido, intuitivo y escalable»*) y las listas de tres viñetas idénticas.
- **Cero conectores robóticos:** *En conclusión, Cabe destacar, Es importante señalar, Asimismo, Por otro lado, En resumen, Sin lugar a dudas, En última instancia*.
- **Cierre seco:** fuera la moraleja aspiracional; se corta en el último hecho, decisión o siguiente paso.

### 4. Vocabulario

- Purga Tier 1 (ver catálogo, grupo C): *crucial, fascinante, holístico, multifacético, inquebrantable, meticuloso, intrincado, paradigmático, tapiz, crisol*.
- Tier 2 por densidad: *potenciar, optimizar, fomentar, brindar, abarcar, maximizar, agilizar*.
- Verbos directos sobre perífrasis: «llevar a cabo un análisis» → «analizar».

### 5. Gramática en español

- Rayas (—/–) solo para incisos reales o diálogo; nunca decorativas.
- Sin gerundio de posterioridad («lanzó la campaña, logrando…»).
- Voz activa cuando el agente se conoce.
- Sin pasiva analítica de relleno («ha sido implementado por»).

### 6. Fidelidad semántica

Se conservan hechos, argumentos y datos. Se cambia la arquitectura textual y el estilo, no el contenido. Si al recortar el 20-30% se pierde un matiz relevante, se conserva el matiz y se recorta otra cosa.

---

## Puntuación 0-100 (`scripts/audit_style.py`)

Python 3.9+, solo stdlib, sin red. **Más alto = más IA.** Todos los comandos se ejecutan desde la raíz del repositorio . Es una medición reproducible del texto, no un veredicto sobre quién lo escribió.

```bash
py humanizador-anti-ia/scripts/audit_style.py --text "Tu texto aquí..."
py humanizador-anti-ia/scripts/audit_style.py --file borrador.md --markdown
py humanizador-anti-ia/scripts/audit_style.py --file borrador.md --json
py humanizador-anti-ia/scripts/audit_style.py --file borrador.md --score
```

### Las cuatro señales

Vocabulario IA (30%), uniformidad de frases (25%), patrones estructurales (30%) y artefactos de chatbot (15%); `total` es su media ponderada. La definición de cada señal, los niveles y el detalle del cálculo están en `detector-ia`.

Notas de calibración, para que nadie lea el número como una verdad absoluta:

- Las densidades usan una base mínima de 250 palabras: un texto corto no se extrapola a «20 por cada 1000».
- El vocabulario pesa menos que el conjunto contenido+estructura a propósito. Cambiar palabras sin tocar la estructura es maquillaje.
- Un texto humano informal suele quedar por debajo de 25. Un texto formal bien escrito puede llegar a 30-40 sin ser IA: por eso el informe se lee junto a los hallazgos, no solo con el número.
- La uniformidad necesita al menos 4 frases; con menos, vale 0 y el detalle lo indica.

### Salida `--score`

JSON plano con `total`, `nivel`, las cuatro claves, `detalle` (recuentos que justifican cada señal) y `datos_a_verificar`. Sale con código 0: mide, no aprueba ni suspende.

Salida real (misma entrada que el ejemplo): `py humanizador-anti-ia/scripts/audit_style.py --file humanizador-anti-ia/tests/corpus/ia_01_articulo.txt --score`

```json
{
  "total": 74.4,
  "nivel": "alto",
  "vocabulario_ia": 100.0,
  "uniformidad_frases": 62.5,
  "patrones_estructurales": 95.9,
  "artefactos_chatbot": 0.0,
  "detalle": {"palabras": 154, "frases": 8, "...": "recuentos por señal"},
  "datos_a_verificar": []
}
```

### Compatibilidad con el uso anterior

Se mantienen `--text`, `--file`, `--json`, `--markdown` y los códigos de salida (0 aprobado, 2 requiere reescritura, 1 error). El JSON del análisis conserva `burstiness_cv`, `banned_phrases`, `issues` y `passed`, y añade `score`, `datos_a_verificar` y `protected_segments`.

---

## Flujo

El flujo obligatorio (registro y modo → puntuar → catálogo → reescribir → recortar → volver a puntuar → informe) está en `humanizar`, que es quien lo ejecuta.

---

## Tests

```bash
py -m unittest discover -s humanizador-anti-ia/tests -v
```

Corpus en `tests/corpus/`: 2 textos sintéticos de IA (`ia_*.txt`), 2 humanos (`humano_*.txt`), 1 con datos sin fuente y 1 con código y enlaces. Verifican que el score separa IA de humano, que el código y las URLs no se tocan, que se detecta el dato sin fuente y que el JSON tiene las cuatro claves.
