---
name: humanizar
description: Reescribe un texto para quitarle los patrones de IA en modo Quick, Full o Voice — contenido, ritmo, estructura y vocabulario, con recorte de relleno del 20-30%, calibración de voz con párrafos propios del usuario, protección de código/enlaces/datos y score antes/después. Úsala cuando pidan humanizar, naturalizar, «quitar el tono de IA», imitar la voz del usuario o reescribir un texto para que suene a persona. English: rewrite the text to remove the AI patterns, trim the filler and keep the user's voice.
license: MIT
metadata:
  package: humanizador-anti-ia
  version: "2.0.0"
---

# Humanizador · Reescribir (`humanizar`)

Devuelve ritmo, concreción y voz. No es un sinonimizador: el trabajo está en el contenido y la estructura.

Assets compartidos del paquete: `../references/`, `../scripts/`, `../templates/`. **Todos los comandos se ejecutan desde la raíz del repositorio**.

## Cuándo se usa

- «Humaniza esto», «quítale el tono de IA», «hazlo sonar natural».
- Adaptar un borrador a LinkedIn, email, artículo o informe.
- Reescribir con la voz del usuario a partir de una muestra.

Si el usuario **solo** quiere saber cuánta IA tiene un texto, sin tocarlo, usa `detector-ia`.

## Modos

**Quick** toca vocabulario Tier 1/2, artefactos de chatbot y relleno evidente, sin cambiar la estructura; en Quick solo deben bajar vocabulario y artefactos, y si las otras señales no bajan se dice. **Full** (por defecto) aplica todo el catálogo y recorta el 20-30% de relleno. **Voice** es Full más calibración con 2-3 párrafos del usuario: no copies sus frases, imita sus decisiones, y con menos de 80 palabras o registro distinto dilo en vez de inventar un perfil.

## Flujo obligatorio

1. **Registro y modo.** Identifica LinkedIn / email / artículo / informe y confirma el modo. Si no dicen nada: Full. El registro manda sobre el catálogo.
2. **Puntúa el original.** `py humanizador-anti-ia/scripts/audit_style.py --file borrador.md --score` (más alto = más IA). Anota las cuatro señales y `datos_a_verificar`.
3. **Catálogo.** Recorre `../references/03-patrones-numerados.md` entero, de arriba abajo: contenido (1-10), ritmo (11-20), vocabulario (21-28), estructura (29-35), artefactos (36-40). Usa `../references/lista-negra.md` y `../references/01`/`02` como apoyo.
4. **Reescribe** según el modo, respetando registro, honestidad y protección.
5. **Recorta relleno** (Full/Voice): 20-30% de palabras sin perder información. Si el texto ya es denso, dilo y no fuerces el porcentaje.
6. **Vuelve a puntuar** y compara señal por señal. Si el total no baja, explica qué no se pudo tocar y por qué.
7. **Informe** con `../templates/informe-auditoria.md`: score antes/después, patrones corregidos, datos a verificar, contenido protegido y patrones dejados a propósito.

## Reglas no negociables

1. **Honestidad factual.** Un dato, cifra, cita o fecha sin fuente se **marca para verificar**; nunca se inventa, redondea ni «aproxima».
2. **Protección de estructura.** No se toca código, frontmatter YAML, enlaces, correos, cifras, nombres propios, rutas, versiones, claves, comandos ni tablas: el script los enmascara y restaura, y si hay que cambiar algo dentro se pide permiso.
3. **Fidelidad semántica.** Se cambia la arquitectura textual y el estilo, no los hechos.

El resto de reglas de edición (ritmo, vocabulario, gramática) están en el maestro y en `../references/03-patrones-numerados.md`.

## Gate de salida

- Score después ≤ score antes, o explicación de por qué no.
- Cero datos inventados y lista de `datos_a_verificar` entregada.
- Código, enlaces y frontmatter intactos (verificar con el diff, no a ojo).
- Registro respetado (sin fragmentos en un informe, sin epígrafes en un email).
- Informe con antes/después y patrones dejados a propósito.

## Handoff

Si después el usuario quiere una segunda pasada objetiva sin reescritura, `detector-ia`.
