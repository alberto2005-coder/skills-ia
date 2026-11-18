---
name: refactor-clones
description: Detecta funciones duplicadas con shingles normalizados del AST: dos bloques que solo cambian nombres de variables cuentan como clon exacto, y cada par sale con su similitud y su ubicación.
license: MIT
metadata:
  package: refactor-surgeon
  version: "1.2.0"
---

# Refactor Clones

## Objetivo

Encontrar el código copiado y pegado antes de refactorizar, para arreglar una vez lo que está escrito dos veces.

## Instrucciones de ejecución

1. Escanea la carpeta o el fichero sospechoso:

```bash
py refactor-surgeon/scripts/clone_detect.py --path src/ --json
```

2. En CI usa `--threshold 0.9` para bloquear solo los clones casi idénticos.
3. Abre cada par por su línea y decide: extraer función común, dejar el duplicado con un comentario o unificar.

## Cómo puntúa

| Regla | Similitud | Severidad |
|---|---|---|
| `clon-exacto` | 1.0 tras normalizar | alta |
| `clon-cercano` | ≥ 0.9 | alta |
| `clon-cercano` | entre el umbral y 0.9 | media |

La normalización sustituye cada nombre por su tipo: `def total_facturas(facturas, iva)` y `def suma_albaranes(albaranes, impuesto)` producen la misma secuencia, porque los identificadores no cuentan. Por eso un renombrado aparece como clon exacto y no como falso positivo.

## Parámetros

| Flag | Por defecto | Para qué |
|---|---|---|
| `--shingle` | 8 | tokens por ventana; más grande, más estricto |
| `--min-tokens` | 20 | ignora funciones diminutas |
| `--threshold` | 0.8 | Jaccard mínimo entre ventanas |
| `--fail-on` | `clone` | `none` deja el informe sin romper la puerta |

## Límites

- Compara estructura, no intención: dos funciones con el mismo esqueleto y distinto negocio cuentan como clon.
- No detecta duplicación entre lenguajes ni dentro de expresiones sueltas: la unidad es la función.
- El coste es cuadrático en número de funciones: en un árbol enorme conviene pasar una carpeta, no el repo entero.
- Los `docstring` se ignoran a propósito, así que un clon con documentación distinta sigue apareciendo.

## Gate de salida

- Pares revisados con su decisión escrita: extraer, dejar o unificar.
- Cero clones por encima del umbral sin decisión.
- El umbral y el comando usados quedan anotados junto al resultado.

## Handoff

Entrega a `refactor-harness` las funciones implicadas para congelar su conducta antes de unificarlas, y a `refactor-metrics` el antes y el después de la extracción.
