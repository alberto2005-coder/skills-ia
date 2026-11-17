# Remediación: parche, sandbox y variantes

Un parche es una hipótesis hasta que una prueba demuestra que el vector ya no funciona. Este documento fija el orden, quién aprueba y dónde se ejecuta.

## Ciclo

| Paso | Quién | Salida |
|---|---|---|
| 1. Dry-run | Revisor | Diff que aplica limpio contra el fichero actual, sin escribir |
| 2. Aprobación | Propietario del código | Confirmación explícita del diff y de la prueba de cierre |
| 3. Aplicación | `apply_patch.py --apply --yes` | Fichero modificado y copia `.orig` |
| 4. Verificación | Sandbox declarado | Test o PoC que demuestra el cierre, con su salida |
| 5. Variantes | Revisor | Mismo fallo buscado por causa raíz en el resto del código |
| 6. Cierre | `appsec-report` | Hallazgo corregido con evidencia, o revertido y abierto |

`apply_patch.py` sin `--apply --yes` no escribe nada. Con `--verify` y sin `--sandbox` se niega: ejecutar es un acto distinto de parchear.

## Qué cuenta como sandbox declarado

| Requisito | Detalle |
|---|---|
| Aislamiento | Contenedor efímero, VM o runner desechable; nunca la máquina del revisor con credenciales |
| Datos | Sin datos de producción ni personales; fixtures sintéticos |
| Red | Salida cerrada por defecto; se abre solo al destino necesario y se declara |
| Credenciales | Ninguna del sistema auditado; secretos de prueba propios del sandbox |
| Límite | Tiempo máximo, CPU y memoria acotados; se destruye al terminar |
| Registro | Comando exacto, versión y salida guardados como evidencia |

Nombrar el sandbox (`--sandbox contenedor-auditoria`) deja constancia de cuál se usó. Un nombre sin contrato detrás no es un sandbox: es una promesa.

## Prueba de cierre

Vale cualquiera de estas, con su salida:

- Test que antes fallaba y ahora pasa, citando el caso del hallazgo.
- PoC que en el sandbox ya no consigue el efecto (mismo payload, mismo endpoint simulado).
- Comprobación estática que demuestra que el sink desapareció (consulta parametrizada, permiso en servidor, codificación).

No vale «he revisado el diff y está bien». Si la prueba no se puede ejecutar, el hallazgo queda `needs_validation` con el motivo escrito.

## Reversión

- `.orig` se conserva hasta que el cierre esté probado; revertir es copiar de vuelta o `git checkout -- <fichero>`.
- Si la verificación falla, se revierte antes de proponer otra cosa: no se acumulan parches sobre un estado que no se entiende.
- Un parche que toca más de lo que dice el diff se revierte y se replantea.

## Análisis de variantes

Por cada hallazgo confirmado, buscar la **causa raíz**, no el síntoma:

| Pregunta | Ejemplo |
|---|---|
| ¿Dónde más se usa este sink? | Todas las llamadas a `execute(` con concatenación |
| ¿Quién más llama a este helper? | El wrapper de permisos que no comprueba propietario |
| ¿El mismo patrón está en otro lenguaje o servicio? | El endpoint equivalente en el servicio viejo |
| ¿La configuración se replica en otros entornos? | El mismo `debug` en staging y producción |

Cada variante encontrada es un hallazgo nuevo con su propio fingerprint; cada variante revisada y descartada se anota en el ledger como `covered` con la comprobación. El informe dice cuántas se buscaron y cuántas se encontraron.

## Lo que no se hace

- Aplicar en lote sin revisar cada diff.
- Mezclar el parche de seguridad con refactors, renombrados o actualizaciones.
- Desactivar tests, bajar cobertura o añadir supresiones para que pase la verificación.
- Ejecutar la PoC fuera del sandbox, «solo para comprobar».
- Cerrar un hallazgo porque el parche está escrito: se cierra cuando la prueba pasa.
