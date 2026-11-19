# Evidencia: {{titulo_o_app}} (plantilla)

> Formato obligatorio de hallazgo en la fase 1 (recon), la fase 7 (paridad) y la
> fase 12 (análisis estático). Inspirado en el formato *evidencia · mapa · límites ·
> desconocidos*: **observación y inferencia nunca van mezcladas**.
>
> Copia una fila por hallazgo en la tabla y amplía en bloque los que sean clave.
> **Un hallazgo sin fuente no es un hallazgo**: se descarta, no se "completa" a ojo.

## 1. Registro de hallazgos (tabla)

| # | Fuente (URL o fichero) | Observación (hecho) | Inferencia (deducción) | Confianza | Límites y desconocidos |
|---|------------------------|---------------------|------------------------|-----------|------------------------|
| H-001 | `https://…/pricing` (2026-11-17) | El plan Pro cuesta 12 €/mes y no tiene límite de proyectos | El precio es un eje de diferenciación posible | high | No sé si hay descuento anual: no lo muestra la página pública |
| H-002 | `replica/screens/onboarding-3.png` (captura propia) | El paso 3 pide dos campos y un checkbox | El onboarding es de 3 pasos con consentimiento explícito | medium | No he visto qué pasa si el checkbox va sin marcar |
| H-003 | 1 reseña suelta en {fuente} | Un usuario menciona "caro" | — (muestra insuficiente, no se usa) | THIN | 1 muestra, 1 sola fuente: no sirve como argumento |

## 2. Bloque ampliado (para cada hallazgo clave)

### H-{{00X}} · {{título corto}}

- **Fuente:** {{URL o ruta de fichero}} · obtenido el {{fecha}} · {{cómo: captura propia / página pública / fichero propio}}
- **Observación:** {{qué vi literalmente, sin interpretar. Si es una pantalla, describe elementos y estados; si es un fichero, cita línea o fragmento corto.}}
- **Inferencia:** {{qué deduzco de esa observación, empezando por "Se deduce que…" o "—". Si no hay deducción, escribe "—".}}
- **Confianza:** `high` | `medium` | `low` | `THIN`
- **Límites y desconocidos:** {{qué no pude verificar, qué asumí, qué falta por mirar. "No consta" es una respuesta válida; el silencio no.}}
- **Usado en:** {{qué decisión, feature o gap depende de esto}}

## 3. Escala de confianza

| Valor | Cuándo | Se puede usar como… |
|-------|--------|---------------------|
| `high` | Fuente directa, reproducible (URL/fichero + fecha), observación clara | Argumento de producto y decisión |
| `medium` | Fuente directa pero parcial, o inferencia bien razonada sobre un hecho observado | Decisión con nota de cautela |
| `low` | Solo una pista indirecta o inferencia con alternativas plausibles sin descartar | Hipótesis a verificar, nunca como hecho |
| `THIN` | Muestra insuficiente: <3 muestras o una sola fuente | **Nada**: se marca y se aparca; no se cita en copy, precios ni landing |

Reglas de la escala:

- `THIN` no se promueve a `high` sin evidencia **nueva**; se añade otra fila, no se reescribe la vieja.
- Confianza en `high` con la casilla "Límites y desconocidos" vacía = hallazgo incompleto, se corrige.
- La observación no se reescribe para que encaje en la inferencia; si contradice la inferencia, se corrige la inferencia.

## 4. Mapa · Límites · Desconocidos (resumen del fichero)

Cierra cada documento de evidencia (`recon.md`, `parity.md`, `static-report.md`) con estas tres secciones:

### Mapa (qué quedó cubierto)

- {{flujo o superficie}} → hallazgos H-00X, H-00Y · confianza media: {{…}}

### Límites (hasta dónde llega esta evidencia)

- {{p. ej. "solo web pública, no he visto la app iOS", "análisis estático solo del JS del bundle, sin el backend"}}

### Desconocidos abiertos (preguntas sin respuesta)

1. {{pregunta concreta + qué haría falta para responderla + quién puede responderla}}
