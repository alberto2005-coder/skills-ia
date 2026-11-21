# Reparto de la revisión y propiedad de rutas

## Reglas tipo CODEOWNERS

| Patrón | Coincide con | No coincide con |
|---|---|---|
| `src/*.py` | `src/app.py` | `src/auth/app.py` |
| `src/**` | `src/auth/app.py`, `src/app.py` | `tests/app.py` |
| `**/*.md` | `docs/guia.md`, `README.md` | `src/app.py` |
| `?rc/*.yml` | `src/a.yml` | `src/ab.yml` |

**Gana la última coincidencia**: se escriben de lo general a lo específico, como en CODEOWNERS. Si una ruta no coincide con ninguna regla, queda `sin-dueno`.

## Carga y capacidad

| Concepto | Cómo se mide | Umbral sugerido |
|---|---|---|
| Carga | ficheros asignados por revisor | 5–8 por PR |
| Sobrecarga | carga > capacidad declarada | `medium` |
| Respaldo | rutas sensibles con un solo revisor | `low` |
| Cobertura | ficheros sin dueño | `high` |

La carga se mide en ficheros y no en líneas: es predecible y no premia partir un fichero en diez.

## Rutas sensibles

Autenticación, permisos, cobro, migraciones e infraestructura exigen al menos dos revisores o una excepción escrita. Un solo revisor en esas rutas es un punto único de fallo humano, no una eficiencia.

## Cuándo no se usa

- Repositorios de una sola persona: el reparto no aporta, pero la lista de rutas sin dueño sigue siendo útil como inventario.
- PRs de documentación sin reglas: se asignan a mano y se anota.

## Salida

`review_routing.py` devuelve `assignments` (fichero → revisores), `load` (revisor → ficheros) y hallazgos `ruta-sin-dueno`, `revisor-sobrecargado` y `sin-respaldo`.
