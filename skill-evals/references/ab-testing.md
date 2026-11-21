# Comparativas A/B de skills y prompts

## Qué se compara

| Métrica | Definición | Unidad |
|---|---|---|
| Eficacia | Muestras correctas / muestras totales | proporción |
| Cumplimiento | Acierto en casos `negative` u obligatorios | proporción |
| Coste | Coste medio por muestra | moneda de la corrida |
| Latencia | Latencia media por muestra | ms |
| Variabilidad | Media de la desviación de la puntuación por caso | puntos de score |

La eficacia puede subir mientras el cumplimiento baja: el caso obligatorio que se rompe no se compensa con diez casos fáciles que se arreglan.

## Muestras y repeticiones

- Una **muestra** es una ejecución de un caso.
- Un **caso con repeticiones** es el mismo id con varias muestras.
- Sin repeticiones no hay variabilidad: se informa `null`, nunca `0`.
- Con dos o tres muestras la variabilidad es una pista, no una prueba.

## Cómo se decide

1. Si B baja el cumplimiento, B pierde aunque gane eficacia.
2. Si B sube eficacia y coste por encima del presupuesto, se declara empate con el motivo.
3. Si B empata en eficacia y baja coste o latencia, B gana.
4. Si B es más variable sin ganar eficacia, no se cambia.
5. Los casos donde B pierde se listan por id: la media no los tapa.

## Errores frecuentes

| Error | Por qué duele | Arreglo |
|---|---|---|
| Comparar con otro conjunto de casos | La diferencia puede ser del conjunto | Declarar casos añadidos o retirados |
| Usar el total de coste | Un PR con más casos parece más caro | Coste por muestra |
| Mirar solo la media | Oculta regresiones puntuales | Diferencia por caso |
| Llamar «mejor» a más rápido | La latencia no mide acierto | Separar eficacia de coste |

## Límites

El script no ejecuta nada ni calcula significancia estadística. Con muestras pequeñas, una diferencia de un caso no es una tendencia: el informe debe decirlo.
