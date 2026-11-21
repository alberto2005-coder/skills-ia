---
name: pr-risk
description: >
  Puntúa el riesgo de cada fichero de un diff: dominios sensibles, tamaño del cambio, claves
  expuestas, manifiestos y locks tocados, y supresiones de checks.
  Úsala cuando el PR sea grande, toque zonas críticas o haya que justificar por dónde empieza
  la revisión.
  English: score each file in a diff by sensitive domain, change size, leaked keys, manifest and
  lock edits and disabled checks, so the review starts where the cost of a mistake is highest.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py pr-reviewer/scripts/review_risk.py *)
  - Bash(python3 pr-reviewer/scripts/review_risk.py *)
license: MIT
metadata:
  package: pr-reviewer
  version: "1.0.0"
  author: "Alberto Ortiz"
---

# PR Reviewer · Riesgo del diff

Un PR no se revisa de arriba abajo: se revisa por coste del error. Esta sub-skill lee el parche unificado y devuelve una severidad por fichero con la señal que la dispara, para que el revisor sepa qué mirar con lupa y qué puede leer en diagonal.

## Cuándo se usa

- El diff pasa de la docena de ficheros y no está claro por dónde empezar.
- Alguien toca sesión, permisos, cobro o migraciones y quiere saber si el cambio es de alto riesgo.
- Antes de aprobar, para comprobar que no se cuela un secreto ni una dependencia nueva sin revisar.

## Alcance y fronteras

| Comprueba | No comprueba |
|---|---|
| Dominio sensible por ruta y por símbolo tocado | Si el código es seguro: eso es `appsec-audit` |
| Tamaño del cambio por fichero y por hunk | Si el diseño del cambio es correcto |
| Patrones de secreto en las líneas añadidas | Si el secreto es real o de ejemplo |
| Ficheros de dependencias y locks | Vulnerabilidades de esas dependencias |
| `skip`, `xfail`, `noqa` y supresiones añadidas | Que el check suprimido fuera necesario |

Las señales son textuales: un secreto detectado puede ser una clave de prueba y una ruta «sensible» puede no serlo en ese proyecto. El informe lo dice con `file` y `line` para que una persona lo confirme.

## Método

1. **Partir** el parche en ficheros con sus líneas añadidas y quitadas.
2. **Clasificar** la ruta: autenticación, pagos, migraciones, infraestructura, CI o código normal.
3. **Medir** el tamaño: líneas por fichero, ficheros del PR y proporción de borrado.
4. **Buscar** secretos y supresiones solo en las líneas que entran.
5. **Puntuar** cada fichero con la señal más grave y ordenar el informe por severidad.

## Comandos

```bash
py pr-reviewer/scripts/review_risk.py --diff cambios.patch --json
py pr-reviewer/scripts/review_risk.py --diff cambios.patch --max-files 20 --fail-on medium
```

`--diff` es un parche unificado (`git diff` o `gh pr diff`), `--max-files` y `--max-lines` ajustan el umbral de tamaño, `--json` y `--out` cambian la salida. Códigos: `0` limpio o por debajo de `--fail-on`, `1` umbral superado, `2` parche ilegible.

## Cómo leer un hallazgo

| Regla | Significado | Arreglo |
|---|---|---|
| `ruta-sensible` | El fichero vive en un dominio caro de romper | Revisión dedicada y test que cubra el caso |
| `secreto-expuesto` | Una línea añadida parece una credencial | Rotar la clave y moverla a un secreto |
| `diff-grande` | El fichero o el PR excede el presupuesto | Partir el PR o justificar el tamaño |
| `borrado-masivo` | Se quitan muchas más líneas de las que entran | Confirmar que el borrado es intencional |
| `dependencia-tocada` | Cambian manifiestos o locks | Revisar versión, licencia y alcance |
| `check-desactivado` | Entra un `skip`, `noqa` o supresión | Justificar o retirar antes de mergear |

## Reglas

- La severidad más alta del fichero manda; el resto se conserva como contexto.
- Un secreto detectado es `high` siempre, aunque parezca de ejemplo.
- Un PR grande no se aprueba «porque los tests pasan»: se parte o se justifica.
- La lista de dominios sensibles es editable en el proyecto, no una verdad universal.

## Gate de salida

- Todos los ficheros del diff tienen una entrada con severidad y señal.
- Cero hallazgos `high` sin revisión humana declarada.
- El tamaño del PR está dentro del presupuesto o tiene justificación escrita.

## Handoff

Los ficheros marcados por seguridad pasan a `appsec-audit` con la ruta y la línea; los que fallan por falta de pruebas, a `test-architect`. El orden de lectura de los ficheros restantes lo fija `pr-order`.
