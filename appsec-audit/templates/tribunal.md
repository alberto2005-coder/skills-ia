# Tribunal de validación — {{proyecto}}

Una fila por candidato. Sin las cinco respuestas no hay veredicto.

| # | Candidato | ¿Alcanzable? | ¿Mitigación? | ¿Aplica en producción? | ¿Quién explota? | Evidencia | Confianza | Veredicto |
|---|---|---|---|---|---|---|---|---|
| C1 | {{título}} | sí/no | {{framework/middleware/none}} | sí/no | {{anónimo/usuario/inquilino/insider}} | `{{ruta:línea}}` | {{1-10}} | aceptado / descartado |

## Reglas

- Confianza **< 7** ⇒ descartado. Se anota el motivo: no alcanzable, mitigado, no explotable, requiere privilegios no obtenibles.
- La mitigación se verifica en el código, no en la documentación.
- Un candidato duplicado por dos sub-skills se fusiona con la evidencia más fuerte.
- El veredicto se escribe antes de redactar el informe.

## Registro de descartes

| # | Motivo | Qué lo cierra |
|---|---|---|
| C{{n}} | {{mitigado / no alcanzable / no explotable}} | {{decorador, ORM, autoescape, permiso}} |

## Resumen

- Candidatos: {{n}} · Aceptados: {{n}} · Descartados: {{n}}
- Críticos aceptados: {{n}} · Altos: {{n}} · Medios: {{n}} · Bajos: {{n}}
- Nota calculada: **{{A-F}}** ({{puntuación}}/100) con `scripts/grade.py`.
