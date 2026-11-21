---
name: pr-order
description: >
  Secuencia la lectura de un diff por las dependencias reales entre los ficheros cambiados: capas,
  imports locales y ciclos, agrupados en oleadas para no revisar un consumidor antes que su base.
  Úsala cuando el PR toque varios módulos acoplados o cueste seguir el hilo de los cambios.
  English: order a diff's reading by the real dependencies between changed files — layers, local
  imports and cycles — grouped into waves so no consumer is read before its base.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py pr-reviewer/scripts/review_order.py *)
  - Bash(python3 pr-reviewer/scripts/review_order.py *)
license: MIT
metadata:
  package: pr-reviewer
  version: "1.0.0"
  author: "Alberto Ortiz"
---

# PR Reviewer · Orden de lectura

Revisar en orden alfabético obliga a reconstruir el contexto en cada fichero. Revisar en orden de dependencia deja que cada lectura apoye la siguiente. Esta sub-skill construye el grafo de imports locales entre los ficheros del diff y lo convierte en oleadas.

## Cuándo se usa

- El PR mueve una función de un módulo a otro y hay que leer el destino antes que los consumidores.
- Varios ficheros se importan entre sí y no está claro cuál es la base.
- Un PR grande necesita un plan de lectura para dos revisores en paralelo.

## Alcance y fronteras

| Comprueba | No comprueba |
|---|---|
| Imports locales entre ficheros del diff | Dependencias externas ni su versión |
| Oleadas topológicas y ciclos | Corrección del diseño de capas |
| Ficheros cambiados que nadie importa ni importan | Cobertura de tests de esos ficheros |
| Orden estable y reproducible | Que el diff compile |

Solo se leen imports de Python (`import x`, `from .x import y`). En otros lenguajes el fichero queda en la primera oleada con la nota `sin-grafo`, que es una limitación declarada y no un fallo del PR.

## Método

1. **Listar** los ficheros que toca el parche.
2. **Resolver** cada import local a otro fichero del diff, por ruta relativa o por paquete.
3. **Construir** el grafo dirigido `importa → es importado`.
4. **Agrupar** por nivel: una oleada contiene los ficheros cuyas dependencias ya salieron.
5. **Señalar** los ciclos y meterlos juntos en la última oleada, sin fingir un orden que no existe.

## Comandos

```bash
py pr-reviewer/scripts/review_order.py --diff cambios.patch --root . --json
py pr-reviewer/scripts/review_order.py --diff cambios.patch --root . --out orden.json
```

`--root` permite resolver imports relativos al árbol real; sin él se usa el directorio del parche. `--json` imprime el plan, `--out` lo escribe. Códigos: `0` plan generado, `2` parche o raíz ilegibles.

## Cómo leer un hallazgo

| Regla | Significado | Arreglo |
|---|---|---|
| `ciclo-dependencias` | Dos o más ficheros se importan en círculo | Romper el ciclo antes de mergear |
| `sin-grafo` | Lenguaje no soportado o import no resuelto | Leer ese fichero aparte, sin orden inferido |
| `huerfano` | El fichero no importa ni es importado en el diff | Confirmar que el cambio tiene sentido aislado |

## Reglas

- El orden es una ayuda de lectura, no una aprobación: un ciclo se reporta, no se esconde.
- La oleada 1 se lee primero porque no depende de nada del diff.
- Un `huerfano` puede ser legítimo (script, configuración); se marca para confirmarlo.
- El plan debe ser idéntico entre ejecuciones: el desempate es alfabético.

## Gate de salida

- Todos los ficheros del diff aparecen en alguna oleada.
- Los ciclos están identificados con sus ficheros.
- El plan es reproducible y cabe en el tiempo de revisión acordado.

## Handoff

El plan alimenta a `pr-risk` para revisar primero las oleadas que tocan dominio sensible, y a `pr-routing` para repartir oleadas completas entre revisores sin cortar una cadena de dependencias.
