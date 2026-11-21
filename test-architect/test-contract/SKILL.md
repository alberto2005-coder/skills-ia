---
name: test-contract
description: >
  Fija el contrato entre módulos comparando el fixture del proveedor con el payload del
  consumidor: campos obligatorios ausentes, tipos divergentes, nulos no permitidos y extras.
  Úsala cuando un consumidor se rompa al cambiar el proveedor, antes de refactorizar una
  frontera, o para convertir un bug de integración en un test que lo encierre.
  English: pin the contract between modules by diffing the provider fixture against the
  consumer payload — required fields, types, nullability and extras.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py test-architect/scripts/contract_fixtures.py *)
  - Bash(python3 test-architect/scripts/contract_fixtures.py *)
license: MIT
metadata:
  package: test-architect
  version: "1.0.2"
  author: "Alberto Ortiz"
---

# Test Architect · Contratos entre módulos

Un contrato de test es un fixture que ambas partes comparten: si el proveedor cambia un campo y el consumidor no se entera, el fallo aparece en producción. Esta sub-skill compara la forma declarada con el payload real y dice qué falta, qué sobra y qué cambió de tipo.

## Cuándo se usa

- «el consumidor se rompe cuando el proveedor cambia», «fija este contrato con un test».
- Antes de refactorizar la frontera entre dos módulos del mismo repo.
- Para convertir un bug de integración en un fixture que lo detecte la próxima vez.

## Alcance y fronteras

| Comprueba | No comprueba |
|---|---|
| Campos obligatorios y opcionales del fixture | Rutas, métodos ni códigos HTTP |
| Tipos primitivos y arrays de primitivos | Esquema OpenAPI o SemVer del contrato |
| Nulos donde el campo no es opcional | Autenticación de las rutas |
| Campos extra que el proveedor no declara | Compatibilidad hacia atrás de una API pública |

Si el contrato es OpenAPI, un endpoint desaparece o el cambio es `major`, la skill es `api-contract-guard` (`api-diff`). Aquí se fija el **payload** que cruza entre módulos y se convierte en test de integración del proyecto.

## Formato del proveedor

El fixture del proveedor es un objeto JSON de campos a especificación:

| Especificación | Significado |
|---|---|
| `string`, `number`, `integer`, `boolean`, `object` | Campo obligatorio de ese tipo |
| `string?`, `number?` | Campo opcional: puede faltar o ser `null` |
| `array<string>`, `array<number>` | Lista de elementos de ese tipo |

El consumidor es un payload JSON normal. La comparación es por campo, sin ejecutar el código de ninguno de los dos.

## Método

1. **Leer** el fixture del proveedor y el payload del consumidor.
2. **Comparar** campo a campo: obligatoriedad, tipo y nulo.
3. **Anotar** el extra que el consumidor envía y el proveedor no declara.
4. **Cerrar** convirtiendo el fixture acordado en el test que ambas partes ejecutan.

## Comandos

```bash
py test-architect/scripts/contract_fixtures.py --provider p.json --consumer c.json --json
py test-architect/scripts/contract_fixtures.py --provider p.json --consumer c.json --fail-on medium
```

`--fail-on low|medium|high|none` (por defecto `high`). Códigos de salida: `0` limpio o por debajo del umbral · `1` umbral superado · `2` fichero ilegible.

## Cómo leer un hallazgo

| Regla | Significado | Arreglo |
|---|---|---|
| `campo-faltante` | El consumidor no envía un campo obligatorio | Añadirlo o declararlo opcional con motivo |
| `tipo-divergente` | El payload no cumple el tipo declarado | Corregir el dato o el contrato |
| `nulo-no-permitido` | `null` en un campo obligatorio | Hacerlo opcional o prohibir el nulo |
| `campo-extra` | El consumidor envía algo que el proveedor no declara | Declararlo o dejar de enviarlo |

## Reglas

- El fixture es la verdad compartida: si cambia, cambian las dos partes en el mismo commit.
- Un campo opcional se declara con `?` y se prueba también ausente.
- Un extra silencioso es deuda: o se declara o se elimina.
- El contrato se prueba sin red y sin arrancar el proveedor.

## Gate de salida

- Cero `campo-faltante`, `tipo-divergente` o `nulo-no-permitido` sin resolver.
- Extras declarados o eliminados.
- El fixture vive en el repo y lo usan las dos partes.

## Handoff

Si el cambio es de ruta, verbo o versión del contrato HTTP, pasa a `api-contract-guard`; si el consumidor no tiene test que lo respalde, vuelve a `test-plan`. El fixture acordado se entrega al dueño del proveedor para que lo mantenga.
