# Señales de riesgo en un diff

## Dominios sensibles

| Dominio | Rutas típicas | Por qué |
|---|---|---|
| Autenticación y sesión | `auth/`, `login/`, `session/` | Un fallo abre la puerta a todos |
| Permisos | `rbac/`, `permission/`, `policy/` | Escalada silenciosa de privilegios |
| Cobro | `payment/`, `billing/`, `checkout/` | Dinero real y conciliación |
| Migraciones | `migrations/`, `schema/` | Un cambio mal ordenado pierde datos |
| Infraestructura | `terraform/`, `k8s/`, `helm/`, `Dockerfile` | El cambio no se prueba en local |
| CI y despliegue | `.github/workflows/`, `deploy/` | Afecta a todo el repositorio |
| Dependencias | manifiestos y locks | Licencia, alcance y cadena de suministro |

La lista es una plantilla: cada proyecto añade o quita dominios según su coste real de fallo.

## Señales textuales

| Señal | Patrón | Severidad |
|---|---|---|
| Credencial añadida | `api_key = "..."`, `BEGIN PRIVATE KEY`, `AKIA...`, `ghp_...` | `high` |
| Supresión de check | `skip`, `xfail`, `noqa`, `type: ignore`, `eslint-disable` | `medium` |
| Borrado masivo | muchas más líneas quitadas que añadidas | `medium` |
| Fichero enorme | más de 400 líneas añadidas en uno | `medium` |
| PR enorme | más de 15 ficheros | `medium` |

## Falsos positivos conocidos

- Claves de ejemplo en documentación o fixtures: se confirman a mano y se anotan.
- `skip` legítimo por plataforma: se acepta con el motivo escrito.
- Migraciones pequeñas y reversibles: el dominio sigue siendo sensible, pero el tamaño no agrava.

## Cómo se usa

`review_risk.py` aplica estas señales y devuelve `file`, `line`, `rule`, `severity`, `message` y `fix`. La severidad más alta del fichero manda; el resto queda como contexto para el revisor.
