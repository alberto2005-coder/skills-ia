---
name: docs-arch-gen
description: Genera un borrador del documento de arquitectura leyendo el árbol de Python: módulo, docstring de responsabilidad y funciones de entrada, más el comando para regenerarlo.
license: MIT
metadata:
  package: docs-sync-engine
  version: "1.1.0"
---

# Docs Arch Gen

## Objetivo

Tener un documento de arquitectura que se pueda regenerar en vez de releer: la estructura sale del árbol, no de la memoria de nadie.

## Instrucciones de ejecución

1. Genera el borrador:

```bash
py docs-sync-engine/scripts/arch_gen.py --root <paquete> --out docs/arquitectura.md --title "Arquitectura"
```

2. Revisa el diff contra el documento vigente y commitea solo los cambios reales.
3. Si un módulo aparece como `(sin docstring de módulo)`, ese es el primer arreglo: falta la responsabilidad escrita.

## Qué produce

| Sección | Contenido |
|---|---|
| Tabla de módulos | Ruta, primera línea del docstring y entradas principales |
| Cómo regenerar | Comando exacto usado |

## Límites

- Solo Python y solo docstrings de módulo: comentarios sueltos y documentación inline no se leen.
- Ignora `tests/` y las carpetas de entorno por defecto.
- No dibuja diagramas ni describe el flujo entre módulos: eso lo escribe la persona.

## Gate de salida

- Borrador regenerado y diff revisado.
- Cada módulo sin docstring está listado como deuda.
- El comando de regeneración queda dentro del documento.

## Handoff

Entrega a `docs-drift-check` las rutas nuevas y a `docs-changelog` la entrada del documento actualizado.
