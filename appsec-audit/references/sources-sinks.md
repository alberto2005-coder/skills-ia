# Fuentes y sumideros por lenguaje

Tabla de trabajo para el trazado. Un candidato es un par `fuente → sumidero` alcanzable sin saneo; el tribunal decide después.

## Fuentes

| Contexto | Ejemplos |
|---|---|
| HTTP | query, body, cabeceras, cookies, path params, multipart |
| Framework | `request.args`, `req.body`, `$_GET`, `params[:id]`, `HttpServletRequest` |
| Ficheros | uploads, CSV importados, configuración editable, plantillas de usuario |
| Colas y eventos | mensajes SQS/Rabbit/Kafka, webhooks, cron con parámetros |
| Terceros | respuesta de API externa, HTML raspado, metadatos de imagen |
| Entorno | variables de entorno, secretos, argumentos de línea de comandos |

## Sumideros por familia

| Familia | Python | JS/TS | Go | PHP | Java | Ruby | C/C++ |
|---|---|---|---|---|---|---|---|
| SQL | `execute`, `raw`, f-string en query | `query`, `$queryRawUnsafe` | `db.Query` con `fmt.Sprintf` | `mysqli_query` con concatenación | `createQuery` concatenado | `where("... #{x}")` | — |
| Comando | `os.system`, `subprocess(..., shell=True)` | `child_process.exec` | `exec.Command` con `sh -c` | `shell_exec`, `system` | `Runtime.exec` | backticks, `system` | `system`, `popen` |
| Código | `eval`, `exec`, `pickle.loads` | `eval`, `new Function`, `vm` | — | `eval`, `unserialize` | `ScriptEngine`, `ObjectInputStream` | `eval`, `Marshal.load` | `dlopen` no confiable |
| Plantilla | `render_template_string`, Jinja sin autoescape | `innerHTML`, `dangerouslySetInnerHTML` | `template.HTML` | `echo` sin escapar | JSP sin `c:out` | `raw`, `html_safe` | — |
| Fichero | `open` con ruta de usuario | `fs.readFile` con path | `os.Open` concatenado | `include`, `fopen` | `File` con ruta | `File.read` | `fopen` con ruta |
| Red | `requests.get(url)` de usuario | `fetch(url)` | `http.Get` | `file_get_contents` | `URL.openConnection` | `Net::HTTP` | `curl_easy` |
| Deserialización | `yaml.load` sin SafeLoader | `node-serialize` | `gob` no confiable | `unserialize` | `readObject` | `Marshal.load` | — |

## Mitigaciones que cierran un candidato

- Consultas parametrizadas u ORM con binding real (no interpolación en el ORM).
- Autoescape activo en el motor de plantillas, o escapado explícito en el punto de salida.
- Validación por lista blanca en el borde, aplicada al dato que llega al sumidero.
- `shell=False` con lista de argumentos, sin concatenación.
- Resolución de rutas con comprobación de prefijo tras `realpath`.
- Lista blanca de destinos para peticiones salientes y bloqueo de rangos internos.
- Deserialización con esquema estricto o formatos seguros (JSON con validación).

## Errores de lectura que generan falsos positivos

- Confundir el nombre de la variable con el dato: `user_id` puede venir de la sesión, no del cliente.
- Dar por hecho que un ORM parametriza cuando se le pasa SQL crudo.
- Ignorar el middleware: CSRF, autenticación o permisos pueden estar en un decorador que no se ve en el handler.
- Olvidar la ruta de exposición: el mismo código en un job interno no tiene el mismo riesgo que en un endpoint público.
