---
name: test-flaky
description: >
  Busca en los ficheros de test los patrones que producen fallos intermitentes: esperas fijas,
  reloj de pared, azar sin semilla, red real, rutas compartidas y estado entre tests.
  Úsala cuando un test falle unas veces sí y otras no, cuando el CI sea inestable, o antes de
  añadir reintentos que solo esconden el problema.
  English: find the patterns behind intermittent failures — fixed sleeps, wall clock, unseeded
  randomness, real network, shared paths and cross-test state.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py test-architect/scripts/flaky_scan.py *)
  - Bash(python3 test-architect/scripts/flaky_scan.py *)
license: MIT
metadata:
  package: test-architect
  version: "1.0.0"
  author: "Alberto Ortiz"
---

# Test Architect · Tests inestables

Un test que a veces pasa no es medio test: es una fuente de ruido que enseña al equipo a ignorar el rojo. Esta sub-skill localiza la causa en el código del test y la nombra con su línea, en vez de proponer un reintento.

## Cuándo se usa

- «este test falla solo en CI», «la suite es inestable», «¿por qué falla a veces?».
- Antes de añadir `retries` al pipeline: primero se quita la causa.
- Al revisar un test nuevo que duerme medio segundo «por si acaso».

## Alcance y fronteras

| Comprueba | No comprueba |
|---|---|
| Esperas fijas y sondeos sin plazo | Por qué el sistema tarda |
| Reloj de pared y fechas del sistema | Zona horaria del runner |
| Azar sin semilla en el propio test | Aleatoriedad dentro del código de producción |
| Red real y sockets en tests | Latencia de los servicios externos |
| Rutas compartidas y estado global | Aislamiento del sistema de ficheros del runner |

Los tests de integración que **deben** usar red se marcan con `--allow-network` y quedan como excepción declarada, no como hallazgo.

## Método

1. **Seleccionar** los ficheros de test del árbol (`test_*.py`, `*_test.py`).
2. **Clasificar** cada llamada y cada literal contra la tabla de patrones.
3. **Anotar** fichero, línea, regla y el arreglo concreto: control del tiempo, semilla fija, doble de red, ruta temporal.
4. **Ordenar** por severidad y cortar por el umbral pedido.

## Comandos

```bash
py test-architect/scripts/flaky_scan.py --root . --json
py test-architect/scripts/flaky_scan.py --root . --fail-on medium
py test-architect/scripts/flaky_scan.py --paths app/tests --allow-network
```

`--fail-on low|medium|high|none` (por defecto `high`). Códigos de salida: `0` limpio o por debajo del umbral · `1` umbral superado · `2` ruta ilegible.

## Cómo leer un hallazgo

| Regla | Significado | Arreglo |
|---|---|---|
| `espera-fija` | `sleep` a la espera de que algo ocurra | Sondear con plazo o esperar el evento |
| `reloj-de-pared` | `time.time`, `datetime.now`, `date.today` | Inyectar un reloj o congelarlo |
| `aleatorio-sin-semilla` | `random` o `faker` sin semilla en el fichero | Fijar semilla o doble determinista |
| `red-real` | `requests`, `httpx`, `urllib`, `socket` en un test | Doble de red o `--allow-network` declarado |
| `ruta-compartida` | Ruta fija en `/tmp` o equivalente | `TemporaryDirectory` por test |
| `estado-global` | `global` o caché de módulo mutada por tests | Reiniciar estado en `setUp` |
| `bucle-sin-salida` | `while True` en un test | Plazo máximo y fallo explícito |
| `skip-permanente` | `skip` con motivo «flaky» o «temporal» | Arreglar la causa o borrar el test |

## Reglas

- Un reintento no arregla una espera fija: la alarga.
- La semilla va en el test, no en una variable de entorno que a veces no llega.
- La excepción de red se declara por ruta y por motivo, nunca en bloque.
- Un test marcado como flaky sin fecha de revisión es deuda, no una decisión.

## Gate de salida

- Cero hallazgos `high` sin causa explicada y sin fecha.
- Cada `espera-fija` sustituida por sondeo con plazo o por espera de evento.
- Las excepciones de red registradas con `--allow-network` y su motivo.

## Handoff

Si el fallo viene de un contrato entre módulos mal fijado, pasa a `test-contract`; si el test no existe y el módulo es sensible, vuelve a `test-plan`. Un test inestable que dependa de un servicio externo se entrega al dueño de ese servicio.
