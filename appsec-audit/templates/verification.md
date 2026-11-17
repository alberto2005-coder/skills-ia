# Verificación independiente — {{ID}}

Plantilla para quien **refuta**, no para quien encontró. Se rellena sin ver el informe previo: si el verificador conoce el veredicto, confirma en lugar de comprobar.

## Lo único que se entrega

| Campo | Valor |
|---|---|
| `id` | {{ID}} |
| Ubicación | `{{ruta}}:{{línea}}` |
| CWE | {{CWE-xxx}} |
| Patrón observado | {{qué construcción aparece, sin interpretarla}} |
| Propósito declarado del fichero | {{para qué existe este código según el proyecto}} |

## Lo que no se entrega

Evidencia redactada, veredicto, confianza, recomendación, parche, historial del hallazgo y razonamiento de quien lo encontró. Todo eso sesga la revisión: `{{ID}}` se verifica desde cero.

## Preguntas de refutación

1. **¿Está en una zona no ejecutable?** Comentario, documentación, fixture de test, cadena de ejemplo, código muerto.
2. **¿El dato llega al sumidero?** Traza la fuente hasta la operación: si no hay camino, no hay hallazgo.
3. **¿Hay mitigación efectiva?** Framework, ORM parametrizado, autoescape, middleware, validación en el borde, permiso comprobado en servidor.
4. **¿La configuración es la de producción?** Un `debug` local no es un hallazgo; el mismo valor en el despliegue, sí.
5. **¿Existe una explicación benigna verificable?** Changelog, issue, documentación o versión publicada que lo justifique.

## Veredicto

| Veredicto | Cuándo | Campos que exige `findings.json` |
|---|---|---|
| `confirmed` | Ruta completa y mitigación ausente comprobadas | `verdict`, `confidence` ≥ 7, `severity`, `exploit` (2+ pasos) y `patch` |
| `needs_validation` | Indicio sólido sin ruta completa o sin dato de producción | `verdict`, `confidence`, `unresolved` con el dato exacto que falta |
| `rejected` | Una de las preguntas 1–5 lo refuta | `verdict`, `confidence` y `reason` con la refutación |

Los campos `confirmed` los completa quien reporta con la evidencia del paquete; el verificador solo decide el veredicto, la confianza y el motivo.

## Justificación

{{Una frase con la comprobación concreta que sostiene el veredicto: qué se abrió, qué se leyó y qué se descartó. Sin adjetivos.}}

## Salida

{{`confirmed` / `needs_validation` / `rejected` → qué cambia en `findings.json` y, si aplica, qué superficie o unidad del ledger vuelve a `hunting`.}}
