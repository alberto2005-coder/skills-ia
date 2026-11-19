# Métricas, umbrales y sesgos

## Activación

Cada caso se puntúa contra todas las skills del catálogo con el router léxico de
`tests/trigger_router.py` (TF-IDF sobre descripciones, bigramas, cobertura y
nombre). El ranking ordena por puntuación, luego por especificidad (sub-skill
antes que maestro) y luego por nombre, así que el resultado es reproducible.

Un caso **positiva** pasa si la skill esperada es la primera y su puntuación
alcanza el umbral. Una **negativa** pasa si gana la ganadora declarada y la
prohibida no queda primera; que la prohibida puntúe alto sin ganar no invalida
el caso, igual que en la suite de activación. **Fuera de dominio** y **límite**
pasan si ninguna skill supera el umbral.

## Definiciones

| Métrica | Fórmula | Qué detecta |
|---|---|---|
| Precisión | casos aprobados / casos totales | Salud global del conjunto |
| Recall | positivas en primera posición / positivas | Descripciones que no contienen el vocabulario del usuario |
| MRR | media de 1/rango de la esperada en positivas | Cuánto se acerca la skill correcta aunque no gane |
| Falsos negativos | positivas que no quedan primeras | Descripción corta o genérica |
| Falsos positivos | fuera de dominio que superan el umbral | Descripción demasiado ancha |
| Colisiones | pares con Jaccard de tokens ≥ 0,50 | Dos skills que se pisan el alcance |
| Tokens de catálogo | Σ estimación `len(descripción)/4` | Coste de mantener el catálogo en contexto |
| Tokens de cuerpo | `len(SKILL.md)/4` por skill | Coste de cargar una skill completa |

## Umbrales por defecto

| Puerta | Valor | Razón |
|---|---|---|
| Umbral de activación | 0,30 | El mismo que usa `tests/phrases.json`; cambiarlo aquí y no allí rompe la comparación |
| Precisión mínima | 0,95 | Un 5 % de fallos es ruido tolerable; más, no |
| Recall mínimo | 0,98 | Una skill que no se activa con su propia frase es una skill muerta |
| Colisiones | 0 | Un par solapado se arregla en la descripción, no en el informe |
| Tokens de catálogo | 8.000 | ~140 tokens por skill en 43 skills (~6.000) más margen para diez altas |
| Tokens de cuerpo | 5.000 | Límite práctico de lectura completa |
| Líneas de cuerpo | 500 | Recomendación del estándar Agent Skills |

Los límites de tokens son estimaciones por caracteres, no un conteo de
tokenizador: sirven para detectar crecimiento, no para facturar.

## Reparto train/test

El split se calcula con SHA-1 del id del caso: 60 % train, 40 % test. Es estable
entre máquinas y ejecuciones, y no se puede sesgar reordenando el fichero.

Regla de uso: una descripción candidata se elige por su resultado en **test**,
nunca por train. Elegir por train es sobreajustar el conjunto que ya se vio.

## Sesgos conocidos

- **Léxico, no semántico**: «borra el historial» y «elimina el registro» no
  comparten raíz y el router no las relaciona. Un falso negativo puede ser del
  router, no de la descripción.

- **Vocabulario del repositorio**: los casos salen de `phrases.json`, escritas
  por quien conoce las skills. Un usuario real puede formular distinto; el
  conjunto mide lo que mide, no la distribución real de consultas.

- **Umbral único**: 0,3 funciona para este corpus; con descripciones muy cortas
  o muy largas el mismo número cambia de significado.

- **Sin varianza**: al ser determinista no hay pass@k; una repetición da el
  mismo resultado y no aporta información.
