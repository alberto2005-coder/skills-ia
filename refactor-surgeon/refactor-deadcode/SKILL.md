---
name: refactor-deadcode
description: >
  Encuentra imports que nadie usa y funciones o clases privadas sin referencias en un árbol
  Python, contando usos por identificador entre ficheros, antes de refactorizar. Úsala antes de
  borrar nada, para saber qué imports y funciones privadas nadie usa. English: find unused
  imports and unreferenced private definitions before refactoring.
license: MIT
metadata:
  package: refactor-surgeon
  version: "1.5.0"
---

# Refactor Deadcode

## Objetivo

Quitar lo que ya no se usa antes de cortar módulos: cada nombre muerto que se arrastra acaba copiado en el módulo nuevo y se vuelve a encontrar el mismo problema.

## Instrucciones de ejecución

1. Barre el árbol completo, no un fichero suelto: la vida de una función privada se decide en otro módulo.

```bash
py refactor-surgeon/scripts/dead_code.py --path src/ --json --fail-on medium
```

2. Antes de borrar, confirma con `refactor-harness` que los casos dorados no pasan por ese nombre.
3. Si el nombre es API del paquete, añádelo a `__all__` o pásalo a `--include-public` para verlo sin borrarlo.

## Reglas

| Regla | Severidad | Qué señala |
|---|---|---|
| `import-sin-uso` | baja | El import no se referencia como nombre, atributo ni cadena en su fichero |
| `definicion-sin-uso` | media | Función o clase privada sin ninguna referencia en el árbol |

Los usos se cuentan entre ficheros: `ast.Name`, atributos (`mod.funcion`), decoradores y las cadenas de `getattr`/`hasattr`/`setattr`. Una línea con `# noqa` silencia su import.

## Límites

- Solo Python y solo estático: no ve `importlib`, `eval`, plugins cargados por cadena ni llamadas desde plantillas o tests de otro repositorio.
- Un nombre público sin uso no se reporta salvo con `--include-public`, porque puede ser la API del paquete.
- No ejecuta el código ni mide cobertura: un nombre «sin uso» puede seguir vivo en producción por una ruta que el análisis no ve.

## Gate de salida

- Cada hallazgo con fichero, línea y nombre, y el árbol analizado declarado.
- Los nombres conservados a propósito quedan justificados (API pública, `__all__`, entrada por cadena).
- Los borrados se hacen con los casos dorados grabados y verificados después.

## Handoff

Entrega a `refactor-clones` el árbol ya purgado y a `refactor-verify` la lista de nombres eliminados, para confirmar que ningún caso dorado los usaba.
