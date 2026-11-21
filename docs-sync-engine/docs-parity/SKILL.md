---
name: docs-parity
description: >
  Comprueba que las dos mitades de un documento bilingüe dicen lo mismo:
  misma estructura de encabezados, mismas filas de tabla, mismas anclas y las
  mismas cifras (skills, tests, paquetes) en cada mitad.
  Úsala cuando pidan verificar que la documentación ES y EN no se ha desfasado,
  que una sección se ha quedado atrás, o antes de publicar una release bilingüe.
  English: structural and numeric parity between the two halves of the docs —
  headings, tables, anchors and counts.
license: MIT
metadata:
  package: docs-sync-engine
  version: "1.3.1"
  author: "Alberto Ortiz"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py docs-sync-engine/scripts/docs_parity.py *)
  - Bash(python3 docs-sync-engine/scripts/docs_parity.py *)
---

# Docs Sync Engine · Paridad ES/EN

Una traducción no es un desfase; un documento que dice «79 skills» en español y «81 skills» en inglés sí. Esta sub-skill compara la **forma** de las dos mitades, no la prosa: la prosa puede diferir, la estructura y las cifras no.

## Cuándo se usa

- «¿está la documentación en inglés al día?», «compara el README ES y EN».
- Antes de una release bilingüe, o después de añadir una sub-skill y tocar solo una mitad.
- Cuando `docs-drift-check` pasa pero el documento sigue mintiendo: las rutas existen, la traducción no.

## Alcance y fronteras

| Comprueba | No comprueba |
|---|---|
| Encabezados por nivel en cada mitad | Calidad de la traducción |
| Filas de datos de cada tabla | Corrección técnica del contenido |
| Fences de código y su lenguaje | Que el código del ejemplo funcione |
| Anclas internas de cada mitad | Enlaces externos |
| Cifras con unidad (skills, tests, paquetes) | Fechas y versiones sueltas |
| Rutas y flags del repo, vía `tests/audit_docs.py` | — |

Las referencias rotas son de `docs-drift-check`; los términos, de `docs-terms`; las variables, de `docs-env`. Aquí solo se juzga lo que debe coincidir entre idiomas.

## Método

1. **Elegir documentos.** Por defecto `README.md` y `docs/*.md`; `--docs` acepta ficheros o carpetas.
2. **Localizar las mitades.** El marcador es `## 🇪🇸 Español` y `## 🇬🇧 English` (también se aceptan sin bandera).
3. **Comparar la forma.** Encabezados por nivel, tablas (filas de datos), fences por lenguaje y anclas internas.
4. **Comparar las cifras.** `N skills`, `N tests`, `N paquetes`… deben coincidir en las dos mitades.
5. **Cerrar con el código.** Si existe, se ejecuta `tests/audit_docs.py` como subproceso: el paquete no importa módulos de la raíz.

## Comandos

```bash
# Todo el repositorio
py docs-sync-engine/scripts/docs_parity.py --json

# Un documento, sin la auditoría de la raíz
py docs-sync-engine/scripts/docs_parity.py --docs docs/index.md --no-audit

# Puerta para CI
py docs-sync-engine/scripts/docs_parity.py --fail-on medium
```

`--fail-on high|medium|low|none` (por defecto `high`). Códigos de salida: `0` limpio o por debajo del umbral · `1` umbral superado · `2` ruta ilegible.

## Cómo leer un hallazgo

| Regla | Significado | Arreglo |
|---|---|---|
| `secciones-idioma` | Falta una de las dos mitades | Añadir la sección, no traducir a medias |
| `forma-encabezados` | Un idioma tiene secciones que el otro no | Igualar la estructura, aunque el título cambie |
| `forma-tablas` | Una tabla tiene filas de más o de menos | Añadir la fila que falta en el otro idioma |
| `forma-fences` | Distinto número o lenguaje de bloques | Revisar el ejemplo que solo está en una mitad |
| `cifras` | Un recuento no coincide | Corregir la cifra contra el manifiesto |
| `ancla-rota` | Un enlace interno no apunta a un encabezado | Corregir el ancla de esa mitad |
| `drift-codigo` | `audit_docs.py` encontró un desfase con el repo | Corregir la ruta, flag o recuento señalado |

## Reglas

- Una diferencia de forma es un desfase, no una decisión de estilo.
- Las cifras se corrigen contra el manifiesto o el índice, nunca contra el otro idioma.
- El script no reescribe documentos: informa y sale con el código acordado.

## Gate de salida

- Cero hallazgos `high` sin explicar.
- Toda cifra distinta corregida contra `skills.json`, el manifiesto del paquete o pytest.
- La sección que faltaba añadida en la mitad correcta, no traducida a la carrera.

## Handoff

Si el desfase es una referencia rota, pasa a `docs-drift-check`; si es terminología, a `docs-terms`; si el documento generado quedó viejo, a `docs-arch-gen`. Un documento sin mitades de idioma se declara monolingüe y se sale del alcance en vez de inventar una traducción.
