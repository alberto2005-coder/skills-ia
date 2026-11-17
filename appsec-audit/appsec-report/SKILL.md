---
name: appsec-report
description: >
  Tribunal de validación y entrega del informe de seguridad: revisa si el
  framework, ORM o middleware ya mitiga cada hallazgo, asigna confianza de 1 a
  10 y descarta los falsos positivos que no llegan a 7, calcula la nota A-F y
  redacta el informe final con resumen ejecutivo, vector y parches en diff.
  Úsala cuando haya que filtrar falsos positivos de una auditoría, puntuar
  hallazgos, calificar la seguridad de un proyecto o preparar el informe para
  dirección y para el equipo técnico.
  English: validate findings against framework mitigations, score confidence,
  discard noise, grade the project A-F and produce the executive and technical
  report with diff patches.
---

# AppSec · Tribunal y informe

Un informe con veinte hallazgos de los que doce son ruido es peor que un informe con cinco correctos: consume el tiempo del equipo y quema la credibilidad del revisor.

## Precondiciones

- Candidatos de `appsec-code`, `appsec-infra` y `appsec-llm`, cada uno con evidencia.
- Acceso al código y la configuración para verificar mitigaciones.

## El tribunal

Para cada candidato, responder por escrito:

1. **¿Es alcanzable?** Existe una ruta real desde una entrada controlable hasta el sumidero.
2. **¿Hay mitigación?** Framework, ORM con parámetros, autoescape, middleware, validación en el borde, permiso comprobado en servidor.
3. **¿La configuración aplica en producción?** Un `debug` activo en local no es un hallazgo de producción; uno activo por defecto en el despliegue, sí.
4. **¿Es explotable por quién?** Anónimo, usuario autenticado, otro inquilino, insider.
5. **¿Qué evidencia lo sostiene?** `ruta:línea`, comando y salida, o la ausencia documentada de control.

Confianza **1–10**:

| Valor | Significado |
|---|---|
| 9–10 | Ruta completa verificada y mitigación ausente comprobada |
| 7–8 | Ruta verificada con una duda menor documentada |
| 4–6 | Indicio sólido sin ruta completa |
| 1–3 | Sospecha por patrón |

**Por debajo de 7 se descarta.** No se incluye «por si acaso»: se anota en el registro de descartes con el motivo, que el informe resume en una línea.

## Severidad y nota

Severidad por impacto y explotabilidad reales, no por tipo de CWE. La nota global sale de los hallazgos validados:

| Nota | Criterio |
|---|---|
| A | Sin críticos ni altos; como mucho medios aislados |
| B | Sin críticos; algún alto mitigable a corto plazo |
| C | Un crítico o varios altos |
| D | Varios críticos o un crítico con datos expuestos |
| F | Crítico explotable sin autenticación o compromiso en curso |

`scripts/grade.py` aplica la fórmula de forma determinista: descuenta 25 por crítico, 10 por alto, 3 por medio y 1 por bajo, con suelo en 0, y traduce la puntuación a letra. Los hallazgos descartados no puntúan.

## Informe

Rellenar `templates/report.md` y escribir los hallazgos en `findings.json` (esquema en `../schemas/findings.schema.json`):

- **Resumen ejecutivo** en lenguaje de negocio: qué se puede perder y qué hacer primero, en cinco líneas.
- **Tabla de hallazgos** ordenada por severidad, con `CWE`, `OWASP`, confianza y ubicación.
- **Detalle por hallazgo**: descripción, impacto, vector paso a paso, evidencia y parche en `diff` (antes y después).
- **Descartes**: cuántos y por qué, en una línea.
- **Límites**: qué no se pudo revisar y con qué consecuencia.

## Gate de salida

- Ningún hallazgo por debajo de 7 en el informe.
- Cada uno con evidencia verificable y confianza declarada.
- Nota calculada con el script, no a ojo.
- Resumen ejecutivo comprensible sin leer el detalle técnico.
- Parches en diff aplicables, sin cambios de estilo.
- `findings.json` pasa `validate_findings.py`: sin severidad fuera de `confirmed` y sin unidades `planned` en el ledger.

## Handoff

Entrega el informe al propietario del sistema y, si procede, al equipo que implementa. Los parches se aplican solo con petición explícita; el revisor no toca el código por iniciativa propia. Si aparece un crítico explotable, se avisa antes de terminar el informe.
