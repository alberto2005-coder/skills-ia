# 00 · Límites, alcance y letra pequeña

## Qué es clean-room

Dos equipos: uno estudia el comportamiento observable (pantallas, flujos, entradas/salidas); otro construye sin ver el código ni los assets del original. Aquí los dos papeles son tú, pero la disciplina es la misma: **describir comportamiento, no copiar expresión**.

| Se puede reconstruir | No se puede copiar |
|---|---|
| Funciones, flujos, estados, atajos | Código fuente, minificado o no |
| Modelo de datos inferido del comportamiento | Base de datos, esquema exacto, migraciones |
| Patrones de UX e interacción | Copy, textos de UI, emails, mensajes de error literales |
| Estructura de pantalla (densidad, jerarquía) | Logo, iconos, ilustraciones, fotos, vídeos, fuentes propietarias |
| Reglas de negocio visibles (precios, límites) | Catálogo de contenido, red de usuarios, datos de terceros |
| API pública documentada, con tus claves | APIs privadas, endpoints internos, bypass de auth |

## Fuentes permitidas

- Web pública, pricing, help center, changelog, blog, docs de API públicas.
- Store listing y reseñas públicas.
- Vídeos y walkthroughs públicos.
- **Tu propia cuenta**, con tus datos, en uso normal.
- Capturas que hagas tú.

Prohibido: cuentas ajenas, credenciales compartidas, scraping tras login, saltarse paywalls o límites, ingeniería inversa de binarios para extraer código, descifrar tráfico, eludir protecciones técnicas.

## Cuándo parar y avisar

- Los términos del servicio del original prohíben usar la cuenta para construir un competidor.
- El flujo depende de datos licenciados (catálogo musical, mapas, base legal, contenido editorial).
- El valor está en la red (marketplace, mensajería, comunidad): reconstruir la app no te da la red.
- Hay marca registrada, trade dress o patentes que cubren la interacción concreta.
- El usuario pide directamente copiar código, assets o copy del original.

En esos casos: dilo, ofrece la alternativa limpia y sigue solo con lo público.

## Rebrand mínimo antes de publicar

Nombre distinto y comprobado, paleta y tipografía propias, logo propio, copy reescrito, identificadores internos renombrados, dominio propio, sin metadatos del original. `scripts/sweep.py` a 0 es el gate técnico; el registro de marca es un check humano.

## Honestidad de esfuerzo

Dimensiona cada flujo en S (<1 día), M (1-3 días), L (>1 semana) y dilo antes de construir. Un clon "perfecto" no existe: `parity.py` da un número, `imgdiff.py` da regiones, y los gaps conscientes se documentan como tales (`out_of_scope`), nunca se maquillan.
