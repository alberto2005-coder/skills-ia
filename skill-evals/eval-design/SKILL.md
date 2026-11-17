---
name: eval-design
description: >
  Diseña el conjunto de casos de evaluación de una skill a partir de las frases
  de activación del repositorio: positivas, negativas con ganadora esperada,
  fuera de dominio y casos límite, con ids estables y reparto train/test 60/40
  por hash. Comprueba cobertura del catálogo, describe cada caso con su tipo y
  split, y detecta skills sin positivas antes de ejecutar nada.
  Úsala cuando pidan preparar los casos de una evaluación, ampliar el dataset
  de triggers, añadir casos límite o revisar que phrases.json cubre el catálogo.
  English: design a versionable eval case set from trigger phrases, add boundary
  cases, split train/test and check catalog coverage.
license: MIT
metadata:
  package: skill-evals
  version: "1.0.0"
---

# Skill Evals · Diseño de casos

Un conjunto de casos es un contrato: dice qué debe pasar antes de saber qué pasa. Esta fase lo escribe y lo valida, sin ejecutar el router más que para comprobar que las skills esperadas existen.

## Precondiciones

- `tests/phrases.json` con `skills` (positivas y negativas) y, si existe, `out_of_domain`.
- Catálogo de `SKILL.md` descubrible desde la raíz del repositorio.
- Umbral de activación acordado (0,3 por defecto en este repositorio).

## Método

1. **Extraer** una caso por positiva, con id `pos:<skill>:<n>` y `expect` = la skill.
2. **Convertir** cada negativa en `neg:<skill>:<n>` con `expect` = ganadora declarada y `forbid` = la skill que no debe activarse.
3. **Añadir** fuera de dominio tal cual (`ood:<n>`, sin `expect`) y dos límites sintéticos: una frase genérica de dos tokens y una frase vacía, ambas sin ganadora.
4. **Repartir** train/test por hash SHA-1 del id: 60 % train, 40 % test. El reparto no cambia entre máquinas ni entre ejecuciones.
5. **Validar** esquema, ids únicos, tipos y splits permitidos, y que toda skill del catálogo tenga al menos una positiva con su nombre.

## Formato del caso

```json
{
  "id": "pos:appsec-recon:1",
  "prompt": "define el alcance y los límites legales antes de auditar",
  "expect": "appsec-recon",
  "kind": "positive",
  "split": "train"
}
```

`kind` ∈ `positive`, `negative`, `boundary`, `out_of_domain`. `expect: null` significa «ninguna skill debe superar el umbral». `forbid` solo aparece en negativas.

## Comandos

```bash
py skill-evals/scripts/design.py --from-phrases tests/phrases.json --out skill-evals/reports/cases.json
py skill-evals/scripts/design.py --check --cases skill-evals/reports/cases.json
py skill-evals/scripts/optimize.py --skill appsec-recon --cases skill-evals/reports/cases.json
```

## Optimización de descripción

Cuando una skill pierde sus propias positivas, el problema suele estar en la
descripción, no en el caso. `optimize.py` cierra el ciclo sin modelo:

1. extrae los términos que usan las frases **de train** que fallan y la
   descripción no contiene;
2. propone candidatos que los añaden (varias tallas, orden determinista);
3. evalúa cada candidato en train y descarta el que no mejora ni el que añade
   colisiones;
4. elige el ganador por **test**, nunca por train;
5. emite el diff unificado y la mejora de precisión/recall antes y después.

Sin `--apply` no se escribe nada: el cambio se revisa y lo aplica quien decide.
La generación solo mira train; test se usa una vez, para elegir.

`--check` no escribe: valida el fichero existente y sale con 1 si hay problemas. `--json` emite el resumen máquina.

## Criterios de un buen caso

- **Una intención por caso**: si la frase pide dos cosas, se parte en dos.
- **Vocabulario real**: se copian fórmulas que un usuario escribiría, no jerga interna del repositorio.
- **Negativa con ganadora**: una negativa sin `winner` no distingue «no debe activarse» de «no se activa nada».
- **Límite explícito**: los casos límite documentan el comportamiento en el borde, no rellenan cuota.
- **Cobertura antes que volumen**: 2–3 positivas por skill bien elegidas valen más que 20 variaciones de la misma frase.

## Gate de salida

- Fichero de casos válido: formato, ids únicos, tipos y splits correctos.
- Toda skill del catálogo tiene al menos una positiva.
- Reparto train/test calculado y estable por hash.
- Casos límite y fuera de dominio presentes.
- Ningún caso con `expect` inexistente o con `forbid` fuera del catálogo.
- Si hubo optimización, el diff y las métricas antes/después están adjuntos y el
  cambio no se aplicó sin pedirlo.

## Handoff

Entrega a `eval-run` la ruta del fichero de casos, el umbral y el recuento por tipo y split. Si hay skills sin positivas, se detiene aquí: ejecutar un conjunto incompleto produce un recall falso.
