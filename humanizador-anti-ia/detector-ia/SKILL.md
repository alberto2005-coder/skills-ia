---
name: detector-ia
description: Mide y detecta señales de escritura de IA en un texto sin modificarlo — score 0-100 determinista de 4 señales, patrones detectados, datos sin fuente y segmentos protegidos, en JSON, Markdown o consola. Úsala cuando pidan puntuar un texto, saber si parece de IA, comparar dos textos por estilo o auditar un borrador sin reescribirlo. English: score the text for AI signals, say whether it reads as AI-generated, without editing it, and list the unsourced data.
---

# Humanizador · Detector (`detector-ia`)

**Solo mide. No reescribe.** Si el usuario quiere que el texto cambie, usa `humanizar`.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Todos los comandos se ejecutan desde la raíz del repositorio** (`skills-ia-main/`).

## Cuándo se usa

- «¿Esto parece escrito por IA?», «puntúa este texto».
- Comparar dos versiones de un mismo texto por estilo.
- Auditar un borrador ajeno sin tocarlo.

## Método

```bash
py humanizador-anti-ia/scripts/audit_style.py --text "Tu texto aquí..."
py humanizador-anti-ia/scripts/audit_style.py --file borrador.md
py humanizador-anti-ia/scripts/audit_style.py --file borrador.md --markdown
py humanizador-anti-ia/scripts/audit_style.py --file borrador.md --json
py humanizador-anti-ia/scripts/audit_style.py --file borrador.md --score
```

**Más alto = más IA.** Es una medición reproducible del texto, no un veredicto sobre quién lo escribió.

## Las cuatro señales

| Señal | Peso | Qué mide |
|---|---:|---|
| `vocabulario_ia` | 30% | Lista negra por 1000 palabras, con saturación |
| `uniformidad_frases` | 25% | % de frases dentro de ±20% de la media |
| `patrones_estructurales` | 30% | «No solo X sino Y», tríadas, cierre moral, listas simétricas, párrafos uniformes |
| `artefactos_chatbot` | 15% | «Como modelo», «aquí tienes», ofertas de seguimiento |

Niveles: `bajo` (<20), `moderado` (<40), `medio` (<60), `alto` (<80), `muy alto` (≥80).

## Cómo leer el número (sin engañarse)

- Texto corto: la densidad usa base mínima de 250 palabras, no se extrapola.
- La uniformidad necesita ≥4 frases; con menos vale 0 y el detalle lo indica.
- Un texto humano informal suele quedar <25; un informe formal legítimo puede llegar a 30-40 sin ser IA. **El número se lee junto a los hallazgos.**
- El código y los enlaces se enmascaran antes de medir: si aparecen clichés dentro de un bloque de código, no cuentan.

## Qué entregar

1. Puntuación total y nivel.
2. Las cuatro señales con su contribución, no solo el total.
3. Hallazgos concretos con la frase citada (patrón + ubicación).
4. `datos_a_verificar`: estadísticas, cifras, citas o fechas sin fuente.
5. `protected_segments`: qué quedó fuera de la medición.

## Reglas duras

- **No se modifica el texto** en este modo, ni siquiera «un par de palabras».
- El score no se presenta como prueba de autoría: es una heurística reproducible.
- Nada de acusar a una persona por el resultado.
- Si el texto es demasiado corto para medir una señal, se dice; no se rellena el hueco.

## Gate de salida

- Salida generada en el formato pedido (consola, Markdown o JSON).
- Las cuatro señales y el `detalle` presentes.
- `datos_a_verificar` y `protected_segments` reportados.
- Cero ediciones al texto original.

## Handoff

Si el usuario decide reescribir tras ver el informe, `humanizar` con el modo adecuado.
