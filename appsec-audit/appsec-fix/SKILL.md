---
name: appsec-fix
description: >
  Remediación de los hallazgos confirmados: propone el parche, lo aplica solo
  con aprobación explícita, verifica el cierre con una prueba posterior, ejecuta
  la PoC únicamente en un sandbox declarado y busca variantes del mismo fallo en
  el resto del código. Incluye apply_patch.py con dry-run por defecto y política
  de sandbox. Úsala cuando pidan arreglar un hallazgo, aplicar el parche,
  comprobar que queda cerrado o revisar si el mismo fallo está en otro sitio.
  English: remediate confirmed findings with approval, dry-run patches,
  sandboxed verification and variant analysis.
license: MIT
metadata:
  package: appsec-audit
  version: "2.0.0"
---

# AppSec · Remediación

Un parche sin prueba de cierre es una hipótesis con formato de diff. Esta fase convierte un hallazgo confirmado en un cambio aplicado, verificado y sin hermanos olvidados.

## Precondiciones

- Hallazgo `confirmed` en `findings.json`, con `patch` y vector de explotación.
- Aprobación del propietario del código para tocar el fichero, y del sistema para ejecutar pruebas.
- Un sandbox declarado si hay que ejecutar algo: contenedor, VM o runner efímero, sin datos de producción y con salida de red por defecto cerrada.

## Ciclo de un parche

1. **Dry-run.** `apply_patch.py` comprueba que el diff aplica limpio contra el fichero actual y muestra el resultado. No escribe.
2. **Aprobación.** Se enseña el diff, el impacto y la prueba de cierre. Sin `--yes` explícito no se aplica nada; la aprobación verbal no cuenta.
3. **Aplicación.** Se guarda copia `.orig` y se escribe el fichero. Nunca se tocan ficheros fuera del diff ni se reformatea lo que no cambia.
4. **Verificación.** Test, reproducción de la PoC o comprobación estática que demuestre que el vector ya no funciona. La ejecución exige `--sandbox` declarado; sin él, el comando no se lanza.
5. **Variantes.** El mismo fallo se busca por causa raíz en el resto del código: mismo sink, mismo patrón, mismo helper. Cada variante es un hallazgo propio o una nota de que se revisó y no existe.
6. **Cierre.** El hallazgo pasa a corregido con la evidencia de la verificación; si la prueba falla, el parche se revierte desde `.orig` y el hallazgo sigue abierto.

```bash
py appsec-audit/scripts/apply_patch.py app/api.py --diff parche.diff
py appsec-audit/scripts/apply_patch.py app/api.py --diff parche.diff --apply --yes --sandbox contenedor-auditoria --verify "pytest -q tests/test_api.py"
```

La política completa de sandbox, reversión y análisis de variantes está en [`../references/remediation.md`](../references/remediation.md).

## Reglas duras

- **Nada se aplica sin confirmación explícita.** Ni «es un cambio pequeño», ni «ya lo apruebo luego».
- Sin sandbox declarado no hay ejecución: ni tests, ni PoC, ni `curl`, ni instalación de dependencias.
- Una PoC se ejecuta solo contra el sandbox, nunca contra producción ni contra sistemas de terceros.
- El parche no cambia comportamiento fuera del fallo: sin refactors, sin renombrados, sin actualizar dependencias de paso.
- Si la verificación no se puede ejecutar, el hallazgo queda `needs_validation` con el motivo, no «corregido».
- Revertir es parte del ciclo: `.orig` se conserva hasta que el cierre esté probado.

## Gate de salida

- Diff aplicado con aprobación registrada y copia `.orig` disponible.
- Verificación ejecutada en sandbox declarado, con su salida como evidencia.
- Variantes buscadas por causa raíz y su resultado escrito.
- Hallazgo cerrado solo con prueba; si no, revertido y declarado.
- Ningún fichero fuera del diff modificado.

## Handoff

Devuelve el hallazgo cerrado a `appsec-report` con la evidencia de la verificación y las variantes encontradas, que entran como candidatos nuevos. `appsec-ci` recibe la prueba para que el workflow la repita en cada PR; si la variante abre una superficie nueva, vuelve a `appsec-threat`.
