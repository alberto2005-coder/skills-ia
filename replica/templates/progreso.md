# Progreso del pipeline `/replica`: {{app_nombre_propio}}

Plantilla de estado retomable (comando maestro `/replica`, ver `SKILL.md`).
Se actualiza **al final de cada fase, tras la aprobación del usuario**.

- **Fase actual:** {{NN}} — {{nombre_fase}} · estado: `pendiente` | `en curso` | `aprobada` | `bloqueada`
- **Última actualización:** {{fecha_utc}}
- **Siguiente acción:** {{qué se hace al retomar, en una frase}}

## Historial de fases

| # | Fase | Estado | Aprobación del usuario (fecha) | Salida en `replica/` |
|---|------|--------|--------------------------------|----------------------|
| 0 | Límites y alcance | pendiente | — | `scope.md` |
| 1 | Reconocimiento (foco: {{función observable}}) | pendiente | — | `recon.md`, `features.csv` |
| 1b| Apps complejas (si aplica) | n/a | — | `complex-app-spec.md` |
| 2 | Arquitectura | pendiente | — | `architecture.md` |
| 3 | Sistema de diseño | pendiente | — | `design/` |
| 4 | Construcción | pendiente | — | código + `features.csv` |
| 5 | Backend | pendiente | — | `backend.md` |
| 6 | Pruebas | pendiente | — | `test-plan.md`, `bugs.md` |
| 7 | Paridad | pendiente | — | `parity.md`, `diff/` |
| 8 | Voz del usuario | pendiente | — | `reviews.csv`, `themes.md` |
| 9 | Marca | pendiente | — | `brand/` |
| 10 | Lanzamiento (países) | pendiente | — | `launch/listing.json`, `launch/paises.md` |
| 11 | Despliegue | pendiente | — | `preflight.md` |
| 12 | Análisis estático (opt-in) | pendiente | — | `static/static-report.md` |
| 13 | Redes (Reels/captions) | pendiente | — | `launch/redes.md` |

Estado de la columna: `pendiente` (no empezada) · `en curso` (trabajando) · `aprobada`
(el usuario la dio por buena; solo entonces avanza) · `bloqueada` (ver tabla de bloqueos) ·
`n/a` (no aplica a este proyecto).

## Decisiones

<!-- Formato: - (fecha) Decisión — por qué — quién la aprobó -->
- ({{fecha}}) {{decisión}} — {{motivo}} — {{usuario}}

## Bloqueos

<!-- Formato: - (fecha) Motivo — qué haría falta para desbloquear — quién decide -->
- ({{fecha}}) {{motivo}} — {{qué falta}} — {{quién}}

## Pendientes de aprobación

- Fase {{NN}}: resumen entregado el {{fecha}} → **esperando respuesta** (no se avanza sin ella).

## Bitácora de cambios

<!-- Solo hechos nuevos: qué fase añadió qué, con fecha. No se borra historial. -->
- ({{fecha}}) Fase {{NN}}: {{qué se añadió/corrigió}}.
