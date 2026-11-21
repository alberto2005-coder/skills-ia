---
name: refactor-cycles
description: >
  Encuentra los ciclos de imports entre los módulos de un árbol Python resolviendo imports
  absolutos y relativos, y devuelve cada componente fuertemente conexa con sus ficheros. Úsala
  cuando los imports se enreden entre módulos y el arranque dependa del orden. English: find
  import cycles and return each strongly connected component with its files.
license: MIT
metadata:
  package: refactor-surgeon
  version: "1.5.1"
  author: "Alberto Ortiz"
---

# Refactor Cycles

## Objetivo

Saber qué módulos no se pueden separar todavía: mientras dos ficheros se importen en círculo, mover uno rompe el otro, y el corte que propone `refactor-slice` no se puede aplicar de golpe.

## Instrucciones de ejecución

1. Detecta los ciclos del paquete completo, no del fichero que se va a cortar:

```bash
py refactor-surgeon/scripts/import_cycles.py --path src/ --json
```

2. Rompe primero el ciclo más pequeño: extraer el tipo o la constante compartida a un tercer módulo suele bastar.
3. Vuelve a medir después de cada corte; un ciclo puede esconder dos.

## Cómo resuelve los imports

| Forma | Se resuelve contra |
|---|---|
| `import paquete.modulo` | El prefijo más largo que exista como módulo del árbol |
| `from paquete import submodulo` | El submódulo si existe; si no, el módulo base |
| `from . import hermano` | La carpeta del fichero, subiendo `level - 1` niveles |
| `from ..padre import x` | La carpeta del padre, con la misma subida |

Solo cuentan los imports internos al árbol; lo que apunta a la biblioteca estándar o a terceros se ignora. Un módulo que se importa a sí mismo no es un ciclo.

## Límites

- Grafo estático: no ve imports dentro de funciones con `importlib`, ni dependencias que solo existen en tiempo de ejecución.
- Compara nombres de módulo: un paquete instalado con el mismo nombre que una carpeta local puede dar una arista falsa.
- Un ciclo no es un error de comportamiento: es un corte pendiente; el veredicto lo da `refactor-verify` después del cambio.

## Gate de salida

- Cada ciclo listado con sus módulos y sus ficheros, y el árbol analizado declarado.
- Los ciclos se rompen con un corte por vez, con métricas de antes y después.
- Lo que queda en ciclo a propósito se justifica por escrito.

## Handoff

Entrega a `refactor-slice` el orden de corte (primero los grupos fuera de ciclo) y a `refactor-verify` cada ciclo roto, para comprobar que los casos dorados siguen igual.
