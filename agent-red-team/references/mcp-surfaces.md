# Superficies MCP

Qué se mira en un servidor MCP y qué señal lo delata. La taxonomía de prompt injection y el OWASP LLM Top 10 no se repiten aquí: viven en `appsec-audit/appsec-llm`.

## Mapa de superficies

| Superficie | Qué se revisa | Señal típica | Regla del escáner |
|---|---|---|---|
| Transporte | Esquema y destino del endpoint | `http://` fuera de loopback | `transporte-sin-tls` |
| Arranque | Comando que lanza el servidor | `npx -y paquete`, `sh -c`, `uvx` sin versión | `comando-sin-version`, `stdio-shell` |
| Tools | Nombre, descripción y esquema | Descripción que ordena ignorar instrucciones | `tool-envenenada` |
| Resources | Rutas que expone | Lectura fuera del directorio declarado | revisión manual |
| Prompts | Plantillas que inyectan contenido del servidor | Texto del servidor entra en el contexto sin marcar | revisión manual |
| Permisos | Scopes de escritura, borrado o red | `filesystem: write`, `network: true` | `permiso-excesivo` |
| Autoaprobación | `autoApprove`, `alwaysAllow` | `*` o tools con shell/escritura | `autoaprobacion-amplia` |
| Tokens | Dónde vive el secreto y cuánto dura | Token literal, sin caducidad, reenviado a terceros | `token-en-claro` |

## Transporte

- `stdio` no significa seguro: el cliente ejecuta un comando local con los permisos del usuario.
- SSE y HTTP añaden red: sin TLS, el token y los resultados de las tools viajan en claro.
- Un endpoint en `localhost` es aceptable para desarrollo, pero no para un servidor compartido.

## Arranque

- `npx -y paquete` descarga la última versión en cada arranque: fija `paquete@1.4.2`.
- `sh -c "…"` convierte argumentos en ejecución: si un arg viene de fuera, es inyección de comandos.
- Un `pip install` dentro del comando mezcla dependencias del proyecto con las del servidor.

## Tools, resources y prompts

- **Descripción envenenada:** «ignore previous instructions», «always call this tool», «do not tell the user». Es una señal de superficie, no una clasificación completa de ataque.
- **Esquema laxo:** parámetros libres que acaban en rutas o comandos; el servidor decide qué hacer con ellos.
- **Resource fuera de alcance:** el servidor declara leer `./docs` y acepta `../`.
- **Prompt del servidor:** una plantilla que inserta contenido remoto en el contexto sin delimitarlo.

## Permisos y autoaprobación

- Escritura, borrado o red declarados por el servidor deben corresponder con su propósito; si no, se reduce el scope.
- `autoApprove: ["*"]` elimina la confirmación humana de todas las tools, incluidas las destructivas.
- Una allowlist de solo lectura (`read_doc`, `search`) es aceptable si está justificada.

## Tokens

- Un token literal en `mcp.json` se considera expuesto: se rota, no solo se mueve.
- Un token de usuario reenviado a un servidor de terceros es suplantación: el servidor ve lo que ve el usuario.
- Preferir tokens de corta duración y un gateway que los intercambie por scope.

## Límites

- El escáner lee ficheros, no habla con el servidor: no descubre tools que solo se anuncian en tiempo de ejecución.
- Un servidor ofuscado o empaquetado no es auditable en texto plano; se declara `needs_validation`.
- La ausencia de señal no es una garantía: la revisión manual de la descripción de cada tool sigue siendo obligatoria.
