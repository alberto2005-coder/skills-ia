# Agentes, RAG y servidores MCP

El modelo de amenazas no gira alrededor del prompt, sino de **qué puede hacer el sistema cuando el prompt es manipulado**.

## Modelo de amenazas

| Componente | Amenaza | Pregunta de auditoría |
|---|---|---|
| Fuentes de contexto | Inyección indirecta | ¿Qué texto externo entra al contexto y con qué autoridad? |
| Prompt de sistema | Fuga y secuestro | ¿Se filtra? ¿Se puede redefinir desde una herramienta? |
| Herramientas | Agencia excesiva | ¿Qué alcance tiene cada una y quién la aprueba? |
| Memoria y RAG | Fuga entre inquilinos | ¿El filtro por usuario se aplica al recuperar o después? |
| Salida | Sumidero secundario | ¿Se inserta en HTML, SQL o shell sin tratar? |
| Operación | Consumo sin límites | ¿Hay tope por usuario, por hora y por coste? |

## Herramientas: mínimo privilegio efectivo

- Lista cerrada y versionada; nada de herramientas dinámicas por nombre.
- Parámetros con esquema y validación en servidor, no en el prompt.
- Acciones destructivas (borrar, pagar, enviar, desplegar) con confirmación humana.
- Credenciales de la herramienta con el alcance mínimo y rotación.
- Registro de cada invocación con usuario, parámetros y resultado.

## Servidores MCP

- Superficie declarada: tools, resources y prompts expuestos, con su descripción real.
- Validación de argumentos en el servidor MCP, no en el cliente.
- Aislamiento por sesión y por usuario; sin estado compartido entre inquilinos.
- Sin acceso al sistema de ficheros ancho ni shell salvo necesidad demostrada.
- Transporte autenticado y autorización por herramienta, no solo por conexión.
- Dependencias del servidor auditadas como cualquier otro servicio.

## RAG

- Control de acceso aplicado en la consulta (filtro por usuario o tenant), no después.
- Fragmentos citados con origen para poder verificar la respuesta.
- Envenenamiento: quién puede escribir en el índice y con qué revisión.
- Datos sensibles fuera del índice o cifrados y filtrados en recuperación.

## Señales de alarma en el diseño

- El agente puede ejecutar shell, escribir ficheros o llamar APIs de producción sin aprobación.
- El prompt del sistema se construye concatenando contenido de usuarios o webs.
- La misma clave de servicio se usa para todos los usuarios.
- No existe forma de parar al agente ni de reproducir una sesión.
- El registro guarda el prompt completo con datos personales.

## Cómo se reporta

Cada hallazgo indica la fuente que transporta la instrucción, la herramienta que se alcanza y el impacto. «El prompt puede ser inyectado» no es un hallazgo; «el HTML raspado de la web del cliente llega al contexto y puede invocar `send_email` sin confirmación» sí lo es.
