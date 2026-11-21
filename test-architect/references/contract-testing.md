# Contratos entre módulos con fixtures

Un contrato de test es un fixture compartido por proveedor y consumidor. Si el proveedor cambia un campo y el consumidor no se entera, el fallo aparece en producción con el stack más caro posible.

## Formato del fixture

El proveedor declara campo y especificación:

```json
{
  "id": "integer",
  "email": "string",
  "roles": "array<string>",
  "nickname": "string?",
  "active": "boolean"
}
```

| Especificación | Significado |
|---|---|
| `string`, `number`, `integer`, `boolean`, `object` | Obligatorio, de ese tipo |
| `string?`, `number?` | Opcional: puede faltar o ser `null` |
| `array<string>`, `array<number>` | Lista de elementos de ese tipo |

El consumidor es el payload real que envía o espera:

```json
{"id": 7, "email": "ana@example.com", "roles": ["admin"], "active": true}
```

`nickname` falta y el contrato lo permite: no hay hallazgo. Si faltara `email`, sería `campo-faltante`.

## Qué se comprueba

| Regla | Severidad | Caso |
|---|---|---|
| `campo-faltante` | high | El consumidor no envía un obligatorio |
| `tipo-divergente` | high | `"7"` donde el contrato dice `integer` |
| `nulo-no-permitido` | high | `null` en un campo obligatorio |
| `campo-extra` | low | El consumidor envía algo no declarado |

La comparación es por campo y sin ejecutar código: sirve en un repo que no arranca.

## Cómo se convierte en test

1. El fixture acordado se versiona en el repo, junto al código que lo produce.
2. El test del proveedor comprueba que su salida encaja con el fixture.
3. El test del consumidor comprueba que su entrada encaja con el mismo fixture.
4. Un cambio de contrato toca las dos partes en el mismo commit.

## Frontera con `api-contract-guard`

| Asunto | Dueño |
|---|---|
| Campo, tipo y nulabilidad del payload | `test-contract` |
| Ruta, verbo, código HTTP y SemVer del contrato | `api-contract-guard` (`api-diff`) |
| Cobertura de autenticación de las rutas | `api-contract-guard` (`api-auth-coverage`) |

Si el contrato es OpenAPI y el cambio elimina un endpoint, el impacto es `major` y lo calcula `api-diff`; aquí solo se fija la forma del dato que cruza entre módulos.

## Errores frecuentes

- Fixture copiado en dos sitios: deriva garantizada.
- `array<string>` validado como `list` sin mirar los elementos.
- Campos opcionales que en la práctica siempre llegan: se declaran obligatorios.
- Extras silenciosos que el proveedor ignora hasta que un día los valida.
