# Catálogo Numerado de Patrones de Escritura IA

**Referencia obligatoria de la skill.** Antes de reescribir, recórrelo entero; después de reescribir, vuelve a comprobarlo.

Marco conceptual: **«Wikipedia: Signs of AI writing»** (la lista de indicios que la comunidad de Wikipedia usa para detectar texto generado). Aquí no se copia su texto: los patrones están reescritos y ejemplificados en español, y se les añade el «Pack español» de la última sección.

## Cómo leer este catálogo

- **Orden:** de más fuerte (1) a más débil (40). «Fuerte» significa *más fiable como señal*: si aparece, es difícil que sea casualidad, y no se arregla cambiando una palabra.
- **Grupos:** A contenido · B ritmo y sintaxis · C vocabulario por niveles · D estructura · E artefactos de chatbot.
- **Artefactos (E):** son señales decisivas cuando aparecen, pero triviales de borrar. Por eso van al final: son la victoria más fácil, no la más importante.
- **Regla de los datos:** ningún patrón autoriza a inventar. Si un dato no tiene fuente, se marca; no se «humaniza» rellenándolo (ver regla de honestidad en `SKILL.md`).
- **La puntuación** de `scripts/audit_style.py` solo mide lo que se puede contar: vocabulario, uniformidad de frases, estructura y artefactos. El catálogo te dice *qué* cambiar; el score te dice *cuánto* queda.

**Niveles de vocabulario (grupo C):**

- **Tier 1** — se cambia siempre que aparezca: delata de inmediato.
- **Tier 2** — se cambia por densidad: una aparición pasa, cuatro en un párrafo no.
- **Tier 3** — solo si se acumulan o si el texto entero es de relleno: son palabras normales que la IA sobreusa.

---

## A. Contenido

Lo que se dice, no cómo se dice. Es lo más difícil de disimular y lo primero que hay que arreglar.

### 1. Importancia inflada

**Qué delata:** cada hecho «juega un papel crucial», «marca un hito» o «deja una huella imborrable». El texto afirma trascendencia en lugar de demostrarla.

**Antes:** «La apertura de la nueva sede marca un hito histórico y juega un papel crucial en la expansión de la compañía.»

**Después:** «La nueva sede abre en marzo. Allí se trasladan 40 personas y dos líneas de montaje.»

**¿A veces es legítimo?** Solo si el texto es explícitamente celebrativo (nota de prensa de aniversario) y el hecho es, de verdad, el primero de su clase. Aun así, una vez por texto.

### 2. Falsa profundidad (retórica hueca)

**Qué delata:** frases solemnes que no dicen nada comprobable. Suena a conclusión, pero no hay sujeto, cifra ni consecuencia.

**Antes:** «En un mundo donde el cambio es la única constante, abrazar la incertidumbre se convierte en el verdadero motor del crecimiento.»

**Después:** «El año pasado cambiamos de proveedor tres veces. La cuarta funcionó porque dejamos de exigir contrato anual.»

**¿A veces es legítimo?** En un discurso o en un ensayo de opinión, una frase de este tipo puede abrir o cerrar. Nunca dos seguidas, y nunca en un informe.

### 3. Dato sin fuente

**Qué delata:** porcentajes, importes y «3 de cada 4» presentados como evidencia sin decir de dónde salen. La IA los rellena con verosimilitud estadística.

**Antes:** «El 87% de las empresas fracasa en su primer intento de transformación digital.»

**Después:** «El 87% de las empresas fracasa en su primer intento de transformación digital **(verificar: no consta fuente en el original)**.»

**¿A veces es legítimo?** Sí: un dato puede venir de una fuente obvia para el lector (auditoría interna citada antes en el mismo documento). Si no está en el texto, no es obvio.

**Regla dura:** el dato se marca, **jamás se sustituye por otro inventado**. El reescritor no rellena huecos.

### 4. Moraleja aspiracional de cierre

**Qué delata:** el último párrafo no aporta información: resume el tono y mira al futuro. «El camino por recorrer será largo, pero…».

**Antes:** «El futuro es prometedor. A medida que avanzamos, solo quienes se atrevan a innovar escribirán el próximo capítulo.»

**Después:** «El piloto termina en junio. Si funciona, se extiende a las otras dos plantas en septiembre.»

**¿A veces es legítimo?** En un discurso motivacional, sí, una vez. En artículos, emails e informes, nunca: se corta en el último dato útil.

### 5. Definición enciclopédica de apertura

**Qué delata:** el texto empieza explicando qué es una cosa que el lector ya conoce («La ciberseguridad se define como…»). La IA calienta motores antes de decir algo.

**Antes:** «La gestión de inventarios se define como el conjunto de procesos destinados a controlar la entrada y salida de mercancías.»

**Después:** «Teníamos 12.000 referencias y solo 300 se movían cada semana. El resto ocupaba pasillo.»

**¿A veces es legítimo?** En una enciclopedia o en material didáctico introductorio, sí. En un blog, un email o una propuesta, no.

### 6. Atenuación apilada (hedging)

**Qué delata:** «podría potencialmente llegar a influir en cierta medida». Tres matices en una frase que no compromete a nada.

**Antes:** «Este enfoque podría potencialmente resultar beneficioso en determinados contextos, aunque su impacto dependería de diversos factores.»

**Después:** «Este enfoque funciona en equipos pequeños. Con más de 30 personas, el coste de coordinación se come la ganancia.»

**¿A veces es legítimo?** Sí, en ciencia y en textos legales, donde la incertidumbre es información. Ahí se cuantifica: «no podemos descartar», «con n=12 no es concluyente».

### 7. Consenso inventado

**Qué delata:** «expertos coinciden», «son muchos los que señalan». No hay nadie con nombre ni declaración.

**Antes:** «Los expertos coinciden en que la automatización redefine el mercado laboral.»

**Después:** «El informe de la OCDE de 2024 estima que el 27% de los puestos cambiará de tareas antes de 2030.»

**¿A veces es legítimo?** Solo con una fuente nombrada en la misma frase. Sin nombre, es una opinión disfrazada de dato.

### 8. Meta-anuncio de lo que viene

**Qué delata:** el texto habla de sí mismo: «en este artículo exploraremos», «a continuación veremos». Ocupa espacio antes de empezar.

**Antes:** «En el presente artículo exploraremos las claves que te permitirán comprender a fondo esta cuestión.»

**Después:** «Tres cosas explican la subida del precio: el flete, el arancel y la rotación de personal.»

**¿A veces es legítimo?** En un manual largo, un índice o un «qué vas a encontrar» ayuda de verdad. Una línea, no un párrafo.

### 9. Beneficio genérico intercambiable

**Qué delata:** la promesa sirve para cualquier producto de cualquier sector: «ahorra tiempo», «mejora la experiencia», «aumenta la productividad».

**Antes:** «Nuestra solución optimiza tus procesos y mejora la experiencia de tus clientes.»

**Después:** «Cierra la caja del día en dos minutos en vez de veinte, y sin cuadrar a mano.»

**¿A veces es legítimo?** En un eslogan, nunca en el cuerpo. En el cuerpo, un beneficio sin magnitud ni escenario no es un beneficio.

### 10. Autoridad vaga («estudios demuestran»)

**Qué delata:** la misma estructura que el consenso inventado, pero con soporte pseudoacadémico: «investigaciones recientes», «la ciencia dice».

**Antes:** «Diversos estudios demuestran que dormir bien mejora la productividad.»

**Después:** «Un ensayo de 2019 con 400 enfermeras encontró menos errores de medicación en turnos con dos siestas de 20 minutos.»

**¿A veces es legítimo?** Si citas autor y año, sí. Si no puedes, borra la atribución y deja la afirmación como opinión propia.

---

## B. Ritmo y sintaxis

### 11. Longitud de frase uniforme (burstiness plano)

**Qué delata:** todas las frases miden entre 18 y 24 palabras. No hay ninguna de cinco ni ninguna de treinta y cinco. Es la firma estadística más medida.

**Antes:** «La herramienta permite gestionar los proyectos de forma centralizada. El equipo puede consultar el estado de cada tarea en tiempo real. Los responsables obtienen informes automáticos cada semana.»

**Después:** «Todo está en un tablero. El equipo lo mira cuando quiere; los informes llegan solos los viernes y casi nadie los abre, pero el día que falta uno se nota.»

**¿A veces es legítimo?** Sí, en instrucciones paso a paso y en avisos legales: ahí la regularidad es funcional. Fuera de eso, es un tic.

### 12. Tríada simétrica de adjetivos

**Qué delata:** «rápido, intuitivo y escalable». Tres adjetivos de la misma categoría, separados por comas, con «y» final. Es el molde más reconocible de la IA en español.

**Antes:** «La plataforma es rápida, intuitiva y escalable.»

**Después:** «La plataforma responde en menos de un segundo y aguanta picos de 5.000 sesiones. La curva de aprendizaje, según los becarios, es de una tarde.»

**¿A veces es legítimo?** En una lista de características reales, sí, si cada adjetivo tiene detrás un hecho. Si no, sobran dos.

### 13. «No solo X, sino también Y»

**Qué delata:** la construcción se repite como plantilla de énfasis. Casi siempre se puede decir lo mismo con dos frases normales.

**Antes:** «La medida no solo reduce costes, sino que también mejora la moral del equipo.»

**Después:** «La medida reduce costes. De paso, el equipo dejó de pedir horas extra.»

**¿A veces es legítimo?** Sí, cuando el contraste es la noticia y la segunda parte sorprende. Una vez por texto, no tres.

### 14. Cadena de conectores de transición

**Qué delata:** «Asimismo», «Por otro lado», «En este sentido», «Por consiguiente» abriendo frases seguidas. La IA necesita anunciar la lógica porque no confía en el orden.

**Antes:** «Asimismo, el sistema registra incidencias. Por otro lado, permite asignar responsables. En este sentido, facilita el seguimiento.»

**Después:** «El sistema registra incidencias y asigna responsables. El seguimiento sale de ahí, sin más.»

**¿A veces es legítimo?** En textos muy largos, un conector cada varios párrafos ayuda a orientarse. En cadena, no.

### 15. Paralelismo de párrafos

**Qué delata:** todos los párrafos siguen la misma plantilla: afirmación, explicación, ejemplo, cierre. Se pueden intercambiar de orden sin que se note.

**Antes:** «La primera ventaja es la velocidad. Esto se debe a que el sistema cachea las consultas. Por ejemplo, en pruebas internas… La segunda ventaja es la seguridad. Esto se debe a que…»

**Después:** «Lo que más se nota es la velocidad: las consultas repetidas salen de caché. La seguridad la dejamos para el final, porque el modelo de permisos todavía nos está dando guerra.»

**¿A veces es legítimo?** En una comparativa con criterios fijos (A vs B, criterio por criterio), la simetría es la función. Ahí se mantiene a propósito.

### 16. Inciso decorativo con raya

**Qué delata:** la raya (—) metida para añadir un matiz que podría ir entre comas o en otra frase. En español la raya existe, pero la IA la usa como firma.

**Antes:** «El equipo —que llevaba meses sin vacaciones— entregó el proyecto —con dos semanas de retraso— sin protestar.»

**Después:** «El equipo llevaba meses sin vacaciones. Entregó el proyecto dos semanas tarde y nadie protestó.»

**¿A veces es legítimo?** Sí, para un inciso realmente parentético y una sola vez por página. En diálogo, la raya es obligatoria.

### 17. Gerundio de posterioridad

**Qué delata:** «Lanzó la campaña, logrando triplicar las ventas». El gerundio indica consecuencia posterior, uso que en español suena a traducción automática.

**Antes:** «Rediseñaron la web, consiguiendo duplicar las suscripciones en tres meses.»

**Después:** «Rediseñaron la web. En tres meses las suscripciones se duplicaron.»

**¿A veces es legítimo?** Sí, cuando la acción es simultánea: «Entró corriendo, gritando el nombre de su hija». Ahí el gerundio describe cómo, no qué pasó después.

### 18. Pasiva analítica con agente difuso

**Qué delata:** «ha sido implementado por el equipo», «fueron tomadas las medidas». Esconde quién hace qué y alarga la frase.

**Antes:** «La decisión fue tomada por la dirección tras ser evaluadas las distintas opciones disponibles.»

**Después:** «La dirección decidió el martes, después de comparar tres opciones.»

**¿A veces es legítimo?** Sí, cuando el agente es irrelevante o desconocido: «La planta fue construida en 1972». Y en texto técnico, para describir procesos.

### 19. Pregunta retórica con respuesta obvia

**Qué delata:** «¿Quieres mejorar tus resultados? La respuesta es sí.» La pregunta no busca información: rellena.

**Antes:** «¿Quieres que tu equipo rinda más? La clave está en la comunicación.»

**Después:** «Los equipos que hablan de los errores en la reunión semanal tardan la mitad en corregirlos.»

**¿A veces es legítimo?** En copy de anuncio, con moderación. En un artículo o un informe, abre con el hecho, no con la pregunta.

### 20. Nebulosa nominal

**Qué delata:** sustantivos abstractos encadenados con «de»: «la implementación de la optimización del proceso». El verbo desaparece y la frase pesa.

**Antes:** «La implementación de la optimización de los procesos de atención supuso una reducción de los tiempos de espera.»

**Después:** «Optimizamos la atención y la espera bajó de nueve minutos a cuatro.»

**¿A veces es legítimo?** En títulos de apartado y en lenguaje administrativo muy reglado. En el cuerpo, conviértelo en verbo.

---

## C. Vocabulario por niveles

### 21. Tier 1 — cambio inmediato

**Qué delata:** palabras que en español casi solo aparecen en texto generado: *crucial, fascinante, holístico, multifacético, inquebrantable, meticuloso, intrincado, paradigmático, resonante, crisol, tapiz*.

**Antes:** «Un enfoque holístico resulta crucial para abordar un problema tan multifacético.»

**Después:** «Hay que mirar el problema entero: si arreglas solo el almacén, el cuello de botella se muda a transporte.»

**¿A veces es legítimo?** «Meticuloso» o «intrincado» existen y sirven cuando describen algo concreto. La prueba: ¿podrías señalar con el dedo lo que describe? Si no, fuera.

### 22. Tier 2 — cambio por densidad

**Qué delata:** verbos de consultoría que la IA usa como comodín: *potenciar, optimizar, fomentar, brindar, abarcar, impulsar, maximizar, agilizar*.

**Antes:** «Potenciamos sinergias que optimizan recursos y fomentan la colaboración entre áreas.»

**Después:** «Juntamos compras y logística en una mesa. Dejaron de comprar dos veces lo mismo.»

**¿A veces es legítimo?** Una aparición aislada pasa. Tres en un párrafo convierten el texto en folleto.

### 23. Tier 3 — solo si se acumulan

**Qué delata:** *importante, clave, eficiente, completo, sólido, integral, estratégico*. Son palabras normales; el problema es la densidad.

**Antes:** «Es importante destacar que una gestión eficiente y un enfoque integral resultan clave para un crecimiento sólido.»

**Después:** «Sin control de stock, el crecimiento se paga en devoluciones.»

**¿A veces es legítimo?** Sí, casi siempre. Solo se tocan cuando el párrafo entero está hecho de ellas.

### 24. Metáforas gastadas

**Qué delata:** *el rico tapiz de*, *faro de esperanza*, *piedra angular*, *crisol de culturas*, *punta de lanza*, *arma de doble filo*. La IA las usa para dar brillo sin contenido.

**Antes:** «La educación es la piedra angular de una sociedad y un faro para las generaciones futuras.»

**Después:** «Sin profesores en las aulas, ninguna reforma educativa llega a nada.»

**¿A veces es legítimo?** Casi nunca en prosa profesional. En un discurso, una metáfora propia (no de este catálogo) puede funcionar.

### 25. Verbos comodín y perífrasis

**Qué delata:** «llevar a cabo», «hacer uso de», «proceder a la realización de». Tres palabras donde cabe una.

**Antes:** «Procedimos a la realización de un análisis con el objetivo de llevar a cabo la identificación de cuellos de botella.»

**Después:** «Analizamos dónde se atascaba el pedido.»

**¿A veces es legítimo?** En textos jurídicos y normativos, donde la fórmula tiene efecto legal. Fuera de ahí, no.

### 26. Hype tecnológico

**Qué delata:** *revolucionario, disruptivo, sinérgico, escalable, de última generación, transformador*. Adjetivos de folleto que no resisten una pregunta de seguimiento.

**Antes:** «Una solución disruptiva y escalable que revoluciona la gestión del talento.»

**Después:** «Contrata, da de alta y paga en la misma pantalla. Con 200 empleados tarda lo mismo que con 20.»

**¿A veces es legítimo?** Si el texto es un comunicado de producto y el término viene definido con una cifra, se tolera. En análisis, no.

### 27. Calcos del inglés

**Qué delata:** *apalancar, impactar en, soportar (un proceso), delivery, insights, mindset*. Traducción literal de un original inglés.

**Antes:** «Apalancamos insights para impactar en el delivery del equipo.»

**Después:** «Usamos los datos de soporte para cambiar cómo se entrega el trabajo.»

**¿A veces es legítimo?** En sectores donde el término inglés ya es el estándar (software, finanzas), sí, siempre que el lector lo use. Si no, traduce.

### 28. Superlativos y absolutos

**Qué delata:** *el mejor del mercado, líder indiscutible, único en su clase, sin precedentes*. La IA no mide y aun así corona.

**Antes:** «Somos el líder indiscutible del sector, con la solución más completa del mercado.»

**Después:** «Somos el tercer proveedor por cuota, según el informe de mayo. La ventaja: integramos nómina y turnos sin módulos extra.»

**¿A veces es legítimo?** Con un ranking que lo respalde y la fuente al lado. Sin eso, es publicidad engañosa.

---

## D. Estructura

### 29. Lista de tres elementos simétrica

**Qué delata:** tres viñetas de longitud casi idéntica, con la misma forma gramatical. Se ve el molde antes de leer.

**Antes:**
«- Mejora la comunicación interna.

- Aumenta la motivación del equipo.
- Reduce la rotación de personal.»

**Después:**
«Mejora la comunicación interna: las decisiones se anuncian el mismo día.
La rotación bajó cuatro puntos en el primer semestre, aunque parte del efecto se debe a la subida salarial de marzo. La motivación no la medimos; no tenemos datos.»

**¿A veces es legítimo?** En una checklist, un índice o un resumen de requisitos, la simetría es útil. En prosa argumentativa, rompe al menos una viñeta.

### 30. Conclusión que repite la introducción

**Qué delata:** el apartado final dice lo mismo que el primero con otras palabras. No añade dato ni decisión.

**Antes:** «En conclusión, la transformación digital es un proceso clave que requiere adaptación constante y visión a largo plazo.»

**Después:** «Decisión: prorrogamos el piloto tres meses y medimos en junio. Si no baja el tiempo de cierre, cancelamos.»

**¿A veces es legítimo?** En un informe formal, un cierre que fija decisiones y siguientes pasos es obligatorio. Lo que sobra es el resumen del resumen.

### 31. Párrafos de longitud idéntica

**Qué delata:** cinco párrafos de cuatro frases cada uno. El ojo lo nota como textura plana antes de contar nada.

**Antes:** «[Párrafo de 4 frases] [Párrafo de 4 frases] [Párrafo de 4 frases] [Párrafo de 4 frases]»

**Después:** «[Párrafo de 1 frase] [Párrafo de 7 frases] [Párrafo de 2 frases] [Párrafo de 5 frases]»

**¿A veces es legítimo?** En una ficha técnica o un glosario, sí. En prosa, varía: un párrafo de una línea da énfasis gratis.

### 32. Encabezados paralelos en abstracto

**Qué delata:** «Optimización de procesos», «Mejora de la experiencia», «Impulso de la innovación». Todos sustantivos abstractos con la misma fórmula.

**Antes:**
«## Optimización de procesos

## Mejora de la experiencia

## Impulso de la innovación»

**Después:**
«## Cómo cerramos la caja en dos minutos

## Lo que dicen los clientes que se fueron

## Lo que probamos y no funcionó»

**¿A veces es legítimo?** En documentación normativa o académica, los títulos neutros ayudan a buscar. En un artículo, un título concreto se lee.

### 33. Esquema «afirmación + ejemplo + mini-conclusión» en cada párrafo

**Qué delata:** todos los párrafos cierran con una frase que reinterpreta lo anterior («Esto demuestra que…»). El texto se comenta a sí mismo.

**Antes:** «…Esto demuestra la importancia de la formación continua. …Esto pone de manifiesto el valor del liderazgo. …Esto evidencia la necesidad de medir.»

**Después:** «…Ahí se acabó el debate. …El resto lo decidió el presupuesto. …Y en marzo volvimos a medir.»

**¿A veces es legítimo?** En texto académico, un cierre interpretativo por sección es correcto. En tres párrafos seguidos con la misma fórmula, no.

### 34. Viñetas con forma y longitud idénticas

**Qué delata:** cada viñeta empieza con verbo en infinitivo y mide lo mismo. La IA rellena hasta cuadrar el bloque.

**Antes:**
«- Implementar procesos automatizados de control.

- Establecer métricas claras de seguimiento.
- Fomentar la comunicación entre departamentos.»

**Después:**
«Lo primero fue el control: una hoja que se rellena sola.
Las métricas llegaron después, y solo tres.
De la comunicación entre departamentos nos ocupamos en septiembre; antes no había nada que comunicar.»

**¿A veces es legítimo?** En requisitos, procedimientos y rúbricas, la forma paralela es correcta. En un post o un email, no.

### 35. Anuncio del recorrido

**Qué delata:** «Primero veremos X, después Y y, por último, Z». Anuncia la estructura en vez de usarla.

**Antes:** «Primero analizaremos el contexto, después revisaremos las herramientas disponibles y, por último, extraeremos conclusiones.»

**Después:** «El contexto primero: sin él, cualquier herramienta parece buena. Al final, dos que descartamos y por qué.»

**¿A veces es legítimo?** En un curso, una ponencia o un documento largo, el mapa ayuda. En un texto de 600 palabras, es relleno puro.

---

## E. Artefactos de chatbot

### 36. Negación de capacidades o identidad de modelo

**Qué delata:** «Como modelo de lenguaje, no puedo acceder a…». Solo aparece si el texto se copió de un chat.

**Antes:** «Como modelo de lenguaje, no tengo acceso a información en tiempo real sobre tu empresa.»

**Después:** Borrar la frase. Si hacía falta un dato, pedirlo o marcarlo como pendiente.

**¿A veces es legítimo?** Nunca en un texto final. Es un residuo de conversación, no escritura.

### 37. Apertura de servicio («Claro, aquí tienes»)

**Qué delata:** el texto empieza confirmando el encargo en vez de entregar el contenido.

**Antes:** «¡Claro! Aquí tienes el texto que me pediste, con un tono más cercano.»

**Después:** Borrar la primera línea y empezar por el primer párrafo útil.

**¿A veces es legítimo?** En un email real a una persona, un saludo breve es normal. La fórmula «aquí tienes el texto» delata copia de chat.

### 38. Cierre de asistente («Espero que esto te ayude»)

**Qué delata:** el texto termina ofreciendo ayuda, no concluyendo.

**Antes:** «Espero que esta información te resulte útil. ¡No dudes en preguntarme si necesitas algo más!»

**Después:** «Queda pendiente confirmar el presupuesto con Ana antes del viernes.»

**¿A veces es legítimo?** En un email de cortesía, una despedida es normal, pero con nombre y contexto, no con la fórmula genérica.

### 39. Oferta de seguimiento

**Qué delata:** «¿Quieres que amplíe algún apartado?». Un texto publicado no pregunta eso.

**Antes:** «¿Te gustaría que profundice en alguno de estos puntos o que lo adapte a otro formato?»

**Después:** Borrar. Si el texto necesita un siguiente paso, se escribe como acción concreta.

**¿A veces es legítimo?** En un chat de trabajo, sí. En cualquier entregable, no.

### 40. Placeholders y metacomentarios

**Qué delata:** «[tu ciudad]», «{{nombre}}», «Tienes razón, permíteme corregirlo». Restos de plantilla o de conversación.

**Antes:** «En [tu ciudad], la demanda creció un [X]% el año pasado. Tienes razón, permíteme reformularlo.»

**Después:** «En Valencia la demanda creció un 12% el año pasado (fuente: padrón municipal, enero).»

**¿A veces es legítimo?** Los placeholders son legítimos en una plantilla sin rellenar, nunca en un texto entregado. Y el metacomentario, jamás.

---

## Pack español

Los tells que aparecen **en español** y que un detector entrenado en inglés no ve. El script `audit_style.py` cuenta varios de ellos en las señales de vocabulario, estructura y artefactos.

## Muletillas y fórmulas de apertura

| Fórmula | Por qué delata | Qué hacer |
|---|---|---|
| «En el panorama actual…» / «En el vertiginoso mundo de…» | Apertura de folleto; no aporta contexto verificable | Empezar por el hecho o el problema concreto |
| «En la era digital…» | Igual, con más épica | Borrar y entrar en materia |
| «Sumérgete en…» / «Sumergirse en…» | Metáfora acuática de blog de 2015 | «Lee», «mira», «entra en» |
| «Descubre cómo…» | Promesa de revelación sin contenido | «Cómo se hace X: …» |
| «El poder de…» | Sustantiviza una capacidad sin decir cuál | Nombrar la acción y su efecto |
| «Llevar al siguiente nivel» | Beneficio vacío y ubicuo | Cifra o escenario concreto |
| «Desbloquear el potencial» | Calco de *unlock potential* | «Conseguir», «mejorar», con dato |
| «No es solo X, es Y» | Tesis por contraste, comodín de LinkedIn | Afirmar Y directamente |
| «Un antes y un después» | Hipérbole de hito | Describir qué cambió y cuándo |

## Cierres y conectores

| Fórmula | Por qué delata | Qué hacer |
|---|---|---|
| «En resumen» / «En definitiva» / «En última instancia» | Anuncia el cierre en vez de cerrar | Cortar en el último dato útil |
| «El futuro es ahora» / «El futuro es prometedor» | Moraleja aspiracional | Sustituir por decisión o fecha |
| «El camino por recorrer…» | Metáfora de trayecto sin destino | Borrar |
| «Sin duda» / «Sin lugar a dudas» | Énfasis redundante | Suprimir |
| «Más que nunca» | Urgencia sin prueba | Fecha o cifra que la justifique |
| «Cabe destacar» / «Es importante señalar» | Anuncia que va a decir algo | Decirlo |

## Puntuación y tipografía

| Tell | Por qué delata | Qué hacer |
|---|---|---|
| Raya (—) como inciso decorativo | Firma de traducción del inglés | Comas, paréntesis o punto |
| Puntos suspensivos retóricos («y entonces…») | Suspense falso en texto expositivo | Punto y seguido |
| Emoji decorativo en texto formal (🚀, ✨, 💡) | Mezcla de registro | Fuera, salvo red social y con intención |
| Negritas en cada tercera palabra | Énfasis indiscriminado | Una negrita por idea, como mucho |

## Adjetivos hinchados (ES)

*crucial, fascinante, vibrante, robusto, holístico, multifacético, inquebrantable, meticuloso, intrincado, primordial, paradigmático, resonante, transformador, disruptivo, sinérgico, ilimitado.*

Prueba rápida: si quitas el adjetivo, ¿se pierde información? Si no, sobra.

## Antes / después (pack español)

**1. Apertura de folleto**

- Antes: «En el panorama actual, la formación continua se ha convertido en un pilar fundamental para el éxito profesional.»
- Después: «Quien no actualiza sus herramientas cada dos años acaba aprendiendo a usar las viejas.»

**2. «Sumérgete»**

- Antes: «Sumérgete en esta guía y descubre cómo transformar tu forma de vender.»
- Después: «Esta guía explica cómo cambiar el guion de ventas en cuatro pasos.»

**3. LinkedIn con moraleja**

- Antes: «El liderazgo no es solo un cargo, es una responsabilidad. El futuro es ahora: lidera con propósito.»
- Después: «Dirigí un equipo de nueve personas durante tres años. Lo que funcionó: decir el presupuesto en voz alta desde el primer día.»

**4. Lista de tres simétrica**

- Antes:
  «- Escucha activa.

  - Comunicación efectiva.
  - Liderazgo inspirador.»
- Después: «Escuchaba más de lo que hablaba. Lo demás vino solo, y no siempre.»

**5. Cierre con moraleja**

- Antes: «En definitiva, el camino no es fácil, pero quienes perseveran acaban brillando.»
- Después: «El piloto acaba en junio. Decidimos en julio.»

**6. Puntos suspensivos y raya**

- Antes: «La clave —y esto lo cambia todo— está en los datos… y en cómo los usamos.»
- Después: «La clave está en los datos. Y sobre todo en quién los limpia.»

**7. Adjetivos hinchados**

- Antes: «Una propuesta robusta, holística y transformadora para un mercado vibrante.»
- Después: «Una propuesta con dos módulos: stock y facturación. Cuesta 4.000 euros y tarda seis semanas.»

**8. «No solo X sino Y» en un email**

- Antes: «Este cambio no solo reduce el tiempo de respuesta, sino que también mejora la satisfacción del cliente.»
- Después: «Con este cambio respondemos en dos horas en vez de un día. Las quejas por demora bajaron a la mitad.»

---

## Uso dentro del flujo de la skill

1. Pasa el texto por `py scripts/audit_style.py --file <texto> --score` y anota las cuatro señales.
2. Recorre este catálogo de arriba abajo: arregla primero el contenido (A), luego el ritmo (B) y la estructura (D). El vocabulario (C) es lo último: cambiar palabras sin tocar la estructura es maquillaje.
3. Si un patrón marcado «a veces es legítimo» encaja con el registro del texto, **déjalo** y dilo en el informe.
4. Vuelve a puntuar. Si el total no baja de 40, el problema no era el vocabulario.
5. No inventes datos para rellenar huecos: van a la lista de «datos a verificar».
