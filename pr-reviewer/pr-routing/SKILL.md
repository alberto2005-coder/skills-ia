---
name: pr-routing
description: >
  Reparte la revisión de un diff entre revisores según reglas de rutas tipo CODEOWNERS, mide la
  carga de cada uno y detecta ficheros sin dueño o con un solo revisor en zonas sensibles.
  Úsala cuando haya que asignar revisores, comprobar que nadie queda sin revisión o equilibrar
  la carga de un PR grande.
  English: route a diff's review across owners with CODEOWNERS-style path rules, measure each
  reviewer's load and flag unowned files or single-reviewer sensitive paths.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py pr-reviewer/scripts/review_routing.py *)
  - Bash(python3 pr-reviewer/scripts/review_routing.py *)
license: MIT
metadata:
  package: pr-reviewer
  version: "1.0.0"
  author: "Alberto Ortiz"
---

# PR Reviewer · Reparto de la revisión

Un PR con dueño claro se revisa; uno sin dueño se aprueba por cansancio. Esta sub-skill aplica reglas de rutas sobre los ficheros del diff, reparte la carga y hace visible lo que nadie tiene asignado.

## Cuándo se usa

- Hay que pedir revisión y no se sabe a quién.
- Se sospecha que un fichero crítico no tiene dueño declarado.
- Un revisor acumula demasiados ficheros y conviene repartir antes de empezar.

## Alcance y fronteras

| Comprueba | No comprueba |
|---|---|
| Coincidencia de rutas contra las reglas de propiedad | Quién está disponible ni de vacaciones |
| Carga por revisor y ficheros asignados | Calidad de la revisión que hará |
| Rutas sin dueño y sensibles con un solo revisor | Permisos reales en GitHub |
| Orden estable de asignación | Que la regla de equipo esté aprobada |

Las reglas siguen la convención de CODEOWNERS: **gana la última coincidencia**, de lo más general a lo más específico. El fichero de reglas es del proyecto; esta skill no inventa dueños.

## Método

1. **Cargar** las reglas (`pattern → revisores`) y las capacidades declaradas.
2. **Ordenar** las reglas de general a específica para que la última gane.
3. **Asignar** cada fichero del diff a los revisores de la última regla que coincida.
4. **Sumar** la carga por revisor y compararla con su capacidad.
5. **Marcar** ficheros sin regla, revisores por encima de capacidad y rutas sensibles con un único revisor.

## Comandos

```bash
py pr-reviewer/scripts/review_routing.py --diff cambios.patch --owners owners.json --json
py pr-reviewer/scripts/review_routing.py --diff cambios.patch --owners owners.json --fail-on medium
```

`owners.json` declara `routes` con `pattern` y `reviewers`, y `reviewers` con `capacity` opcional. Códigos: `0` reparto limpio o bajo el umbral, `1` umbral superado, `2` parche o reglas ilegibles.

## Formato de `owners.json`

```json
{
  "routes": [
    {"pattern": "**", "reviewers": ["equipo"]},
    {"pattern": "src/auth/**", "reviewers": ["ana", "luis"]}
  ],
  "reviewers": {"ana": {"capacity": 5}, "luis": {"capacity": 5}}
}
```

Los patrones usan `*`, `**` y `?` sobre la ruta relativa del fichero. Una ruta sin coincidencia queda `sin-dueno`.

## Cómo leer un hallazgo

| Regla | Significado | Arreglo |
|---|---|---|
| `ruta-sin-dueno` | Ninguna regla cubre ese fichero | Añadir regla o asignar a mano |
| `revisor-sobrecargado` | Supera la capacidad declarada | Repartir ficheros o subir la capacidad con motivo |
| `sin-respaldo` | Ruta sensible con un solo revisor | Añadir un segundo revisor |

## Reglas

- Una ruta sin dueño es `high`: nadie la va a mirar si no se dice.
- La carga se mide en ficheros, no en líneas, para que sea predecible.
- Un revisor repetido en varias reglas cuenta una vez por fichero.
- Si no hay fichero de reglas, todo el diff queda sin dueño: es un resultado, no un error.

## Gate de salida

- Cero ficheros `sin-dueno` sin asignación manual escrita.
- Ningún revisor por encima de su capacidad sin justificación.
- Toda ruta sensible tiene al menos dos revisores o una excepción declarada.

## Handoff

Los ficheros sin dueño vuelven a `pr-risk` para confirmar su severidad, y el reparto por oleadas se coordina con `pr-order` para no partir cadenas de dependencias entre dos revisores.
