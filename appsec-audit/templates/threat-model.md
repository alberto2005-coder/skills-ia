# Modelo de amenazas — {{sistema}}

- **Fecha:** {{fecha}}
- **Alcance:** {{componentes, entornos y versiones revisadas}}
- **Fuera de alcance:** {{exclusiones}}
- **Autorización:** {{referencia}}
- **Frase de negocio:** {{qué se pierde si falla: dinero, datos, disponibilidad, reputación}}

## Activos

| Activo | Valor | Dónde vive | Quién debe verlo |
|---|---|---|---|
| {{datos de cliente}} | {{alto}} | {{tabla, bucket, caché}} | {{rol}} |

## Actores

| Actor | Capacidad real | Autenticación | Qué puede alcanzar |
|---|---|---|---|
| Anónimo | {{red pública}} | ninguna | {{endpoints públicos}} |
| Usuario | {{sesión propia}} | {{sesión/MFA}} | {{sus recursos}} |
| Otro inquilino | {{misma plataforma}} | {{sesión}} | {{solo lo suyo, en teoría}} |
| Servicio de terceros | {{webhook, API externa}} | {{firma/mTLS}} | {{lo que publique}} |
| Pipeline | {{repo, secretos CI}} | {{token}} | {{producción}} |

## Límites de confianza

| # | Frontera | Qué cruza | Quién lo controla | Validación al entrar | Si falla |
|---|---|---|---|---|---|
| B1 | navegador → API | {{petición}} | usuario | {{esquema, token, cuota}} | {{rechazo}} |
| B2 | API → base de datos | {{consulta}} | código | {{parámetros, permisos}} | {{error, no dato}} |
| B3 | CI → producción | {{artefacto}} | pipeline | {{firma, aprobación}} | {{despliegue bloqueado}} |

## Casos de abuso

| # | Frontera | Actor | Acción | Garantía rota | Impacto | Ruta demostrada |
|---|---|---|---|---|---|---|
| T1 | B1 | anónimo | {{acción}} | {{garantía}} | {{impacto}} | sí / no (hipótesis) |

## Mapeo

| # | OWASP 2025 | ASVS 5.0 | Clase (`attack-classes.md`) | Unidad de ledger | Control esperado |
|---|---|---|---|---|---|
| T1 | A01 | V8 | access-control | U-00x | {{permiso por objeto en servidor}} |

## Prioridad

| Prioridad | Casos | Motivo |
|---|---|---|
| Ahora | {{T1}} | {{ruta completa, activo crítico}} |
| Después | {{T2}} | {{requiere privilegio no obtenible hoy}} |
| Aceptado | {{T3}} | {{riesgo declarado por el propietario, con fecha}} |

## Límites del modelo

- {{lo que no se pudo confirmar y por qué}}
- El modelo no sustituye a la auditoría de código: la alimenta.
