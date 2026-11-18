---
name: refactor-harness
description: Graba casos dorados de un módulo antes de refactorizarlo y los reproduce después, ejecutando solo con permiso explícito y tratando la excepción como conducta observable.
license: MIT
metadata:
  package: refactor-surgeon
  version: "1.2.0"
---

# Refactor Harness

## Objetivo

Tener una red de seguridad barata cuando el módulo no tiene tests: congelar qué devuelve cada llamada antes de tocar una línea.

## Instrucciones de ejecución

1. Declara los casos en un JSON con el módulo y las llamadas:

```json
{"module": "src/app.py", "cases": [{"function": "sumar", "args": [1, 2]}]}
```

2. Graba antes del cambio y verifica después:

```bash
py refactor-surgeon/scripts/golden_harness.py --cases cases.json --snapshot golden.json --record --allow-exec
py refactor-surgeon/scripts/golden_harness.py --cases cases.json --snapshot golden.json --verify --allow-exec
```

3. Sin `--allow-exec` solo valida el fichero de casos: importar y ejecutar código ajeno es una decisión explícita.

## Reglas

- Los casos cubren el camino feliz y los bordes conocidos; una excepción también se graba con su tipo y mensaje.
- El snapshot se versiona junto al cambio para que la comparación sobreviva a la sesión.
- Un caso que no se puede ejecutar sin efectos externos se declara fuera del arnés.

## Límites

- Ejecuta el módulo en el proceso actual: sin aislamiento y sin límite de tiempo propio.
- No genera casos por sí solo a partir de la firma: los declara quien refactoriza.
- La comparación es por resultado serializado; un objeto que no es serializable se compara como texto.

## Gate de salida

- Snapshot grabado antes del primer corte.
- Verificación sin discrepancias sobre el código refactorizado.
- Los casos no cubiertos se nombran como riesgo aceptado.

## Handoff

Entrega a `refactor-verify` el snapshot y la lista de casos; si ya hay tests, añade este arnés solo para lo que los tests no tocan.
