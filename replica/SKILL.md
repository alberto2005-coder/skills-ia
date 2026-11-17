---
name: replica
description: Replica una app comercial por sus funciones y flujos, clean-room y legal. Orquesta el pipeline completo de 14 fases con aprobación fase a fase y estado en progreso.md: reconoce la app (con foco por función y evidencia obligatoria por hallazgo), planifica stack y datos, reconstruye diseño y pantallas, añade auth/pagos, prueba, mide paridad, lee reseñas reales para mejorar, rebrandea, prepara el lanzamiento (países y redes) y despliega. Úsala cuando el usuario quiera clonar, replicar, reconstruir, ejecutar el pipeline completo o "hacer algo como X" app, o medir paridad/rastros de marca de un clon. English: run the clean-room replica pipeline phase by phase, continue it from progress.md and ask for approval before each phase.
---

# Replica

Pipeline de 14 fases (0-13, con la variante 1b) para reconstruir **lo que una app hace**, no lo que posee. Cada fase lee lo que escribió la anterior en `replica/` del proyecto y deja su salida ahí.

## Reglas duras

1. **Clean-room.** Estudias comportamiento observable y escribes todo de cero. Nunca copias código, assets, logos, iconos, ilustraciones, textos, bases de datos ni APIs privadas del original.
2. **Solo fuentes permitidas.** Páginas públicas, docs, help center, store listing, reseñas públicas y **tu propia cuenta**. Nunca la cuenta de otro, nunca scraping tras login, nunca saltarse un paywall.
3. **Si los términos del original prohíben construir un competidor con tu cuenta, dilo y limítate a fuentes públicas.** No es una decisión que tome la skill por su cuenta.
4. **Rebrand obligatorio antes de publicar.** Nombre, paleta, logo, copy y voz propios. `deploy` no pasa con `sweep.py` sucio.
5. **Cero datos inventados.** Ni reseñas, ni citas, ni métricas, ni usuarios. Cada afirmación con enlace; si no hay muestra suficiente, se dice `THIN` y no se usa como argumento.
6. **Alcance honesto.** "Clonar" = funciones y flujos. El contenido licenciado, la red de usuarios y las marcas no se clonan. Si algo es semanas de trabajo, se dice antes de empezar.
7. **Nada de asesoría legal.** La skill avisa de los checks (trademark, términos) y el usuario decide con su abogado.
8. **Evidencia por hallazgo.** En recon (1), paridad (7) y análisis estático (12) todo hallazgo usa `templates/evidence.md`: **Fuente · Observación · Inferencia · Confianza (high/medium/low/THIN) · Límites y desconocidos**. Observación e inferencia nunca van en la misma casilla; un hallazgo sin fuente se descarta; `THIN` (<3 muestras o una sola fuente) no se usa como argumento ni en copy, y cada documento cierra con *Mapa · Límites · Desconocidos*.
9. **Análisis estático solo opt-in y autorizado.** La fase 12 no se activa por iniciativa propia: exige petición explícita, artefacto propio o autorizado y herramientas ya instaladas. Condiciones y prohibiciones completas en `replica-static`.

## Pipeline

| # | Fase | Referencia | Salida en `replica/` |
|---|------|-----------|----------------------|
| 0 | Límites y alcance | `references/00-limites.md` | `scope.md` |
| 1 | Reconocimiento | `references/01-recon.md` | `recon.md`, `features.csv`, `screens/` |
| 1b| Apps complejas (Word, Figma, Suites) | `references/01b-apps-complejas.md` | `complex-app-spec.md` (AST, Caret, Commands, Layout) |
| 2 | Arquitectura | `references/02-architect.md` | `architecture.md` |
| 3 | Sistema de diseño | `references/03-design.md` | `design/tokens.json`, `design/components.md` |
| 4 | Construcción | `references/04-build.md` | código + `features.csv` actualizado |
| 5 | Backend | `references/05-backend.md` | auth, datos, pagos, `backend.md` |
| 6 | Pruebas | `references/06-test.md` | `test-plan.md`, `bugs.md`, e2e |
| 7 | Paridad | `references/07-diff.md` | `parity.md`, `diff/*.png` |
| 8 | Voz del usuario | `references/08-entrepreneur.md` | `reviews.csv`, `themes.md`, `fix-plan.md` |
| 9 | Marca | `references/09-brand.md` | `brand/*`, código limpio |
| 10 | Lanzamiento | `references/10-launch.md` | landing, `launch/listing.json`, `launch/paises.md` |
| 11 | Despliegue | `references/11-deploy.md` | `preflight.md`, app live |
| 12 | Análisis estático (opt-in) | `references/12-analisis-estatico.md` | `static/static-report.md`, `static/hallazgos-*.json` |
| 13 | Redes (Reels/captions) | `references/13-redes.md` | `launch/redes.md` |

Se puede entrar en cualquier fase suelta (`08` sobre una app que solo estás evaluando es útil). Las fases **12** y **13** son opt-in: la 12 solo si se cumple lo que exige `replica-static` (si no, se marca `n/a` y se sigue en observación de UI); la 13, solo si el usuario la pide y siempre tras la marca (9) y el lanzamiento (10). Si la app objetivo es un software de alta densidad interactiva o de productividad (como Microsoft Word, Google Docs o Figma), consulta obligatoriamente `references/01b-apps-complejas.md` para estructurar el AST, el motor de selección, la pila de comandos y el renderizado con fidelidad matemática 1:1. Al empezar una fase, **lee su referencia**; no improvises el método.

## Sub-skills

El paquete se instala como una unidad: cada fase vive en su sub-skill y **todas comparten** `references/`, `scripts/`, `templates/` y `tests/` de esta carpeta. No se duplican assets; las rutas de cada sub-skill son relativas al paquete (`../references/`, `../scripts/`).

| Sub-skill | Fases | Qué hace |
|---|---|---|
| `replica-recon` | 0, 1, 1b | Límites legales, alcance, inventario de funciones con evidencia y especificación de apps complejas |
| `replica-architect` | 2 | Stack, módulos, modelo de datos con invariantes y contratos |
| `replica-design` | 3 | Tokens, componentes y contraste WCAG con identidad propia |
| `replica-build` | 4 | Construcción por incrementos que cierran flujos `must` |
| `replica-backend` | 5 | Auth, datos, permisos, pagos y jobs |
| `replica-test` | 6 | Plan y ejecución de pruebas, invariantes y bugs por severidad |
| `replica-diff` | 7 | Paridad funcional (`parity.py`) y visual (`imgdiff.py`) con evidencia |
| `replica-entrepreneur` | 8 | Reseñas reales, temas y plan de mejoras |
| `replica-brand` | 9 | Rebrand completo y `sweep.py` a 0 |
| `replica-launch` | 10 | Landing, listing de tiendas y precios por país |
| `replica-deploy` | 11 | Preflight, backups y publicación verificada |
| `replica-static` | 12 (opt-in) | Análisis estático autorizado con límites declarados |
| `replica-redes` | 13 | Guiones de Reels, captions y banco de ganchos |

Esta skill sigue siendo el **maestro**: orquesta el pipeline, guarda `progreso.md` y pide aprobación. Las sub-skills se activan también de forma individual cuando el usuario pide solo una fase.

## Comando maestro `/replica`

`/replica` (o "ejecuta el pipeline replica") arranca **o retoma** el pipeline completo. No es un atajo para saltarse fases: es el mismo método, con estado guardado y aprobación explícita al final de cada una.

1. **Lee `replica/progreso.md`.** Si existe, retoma desde la fase `en curso` o el primer `pendiente`; si no existe, cópialo de `templates/progreso.md` y empieza en la 0. Una fase `aprobada` no se repite sin que el usuario lo pida, y un pipeline empezado no se reinicia.
2. **Recorre las fases en orden**: 0 → 1 → (1b si aplica) → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 y, solo opt-in, 12 y 13. Cada fase lee su referencia, consume lo que dejó la anterior y escribe su salida en `replica/`.
3. **Para al final de cada fase.** Entrega qué se hizo, la salida en `replica/`, los gates pasados (comando y resultado), la evidencia de los hallazgos clave (`templates/evidence.md`) y lo que queda abierto. Pide aprobación explícita: sin un "sí" no se avanza.
4. **Guarda el estado tras cada aprobación** en `replica/progreso.md`: fase actual y estado (`pendiente` · `en curso` · `aprobada` · `bloqueada` · `n/a`), decisiones con su motivo, aprobación con fecha, bloqueos (qué falta y quién decide), pendientes y bitácora. Es lo único que permite retomar en otra sesión.
5. **Un gate rojo bloquea, no se rodea.** Si `parity.py` deja must pendientes, `sweep.py` encuentra restos, `contrast.py` baja de AA, `listing.py` da errores o un hallazgo no tiene fuente, la fase queda `bloqueada` con el motivo escrito: se arregla o el usuario decide el recorte y se anota en los gaps.
6. **12 y 13 son opt-in.** La 12 exige lo que detalla `replica-static`; si no se cumple, se marca `n/a` con el motivo y se sigue en observación de UI. La 13 solo si el usuario la pide, y siempre después de la marca (9) y el lanzamiento (10).
7. **Un cambio sobre una fase aprobada la reabre lo mínimo**: se actualiza `progreso.md`, se re-ejecuta el gate afectado (`sweep.py`, `parity.py`, `imgdiff.py`) y se vuelve a pedir aprobación.

Regla de oro del comando maestro: **nunca avanza dos fases de golpe ni da una fase por aprobada en nombre del usuario.**

## Herramientas

Scripts en `replica/scripts/`, solo stdlib de Python 3.8+, sin red. **Todos los comandos se ejecutan desde la raíz del repositorio** (`skills-ia-main/`); las referencias de lectura son relativas al paquete (`../references/`).

```bash
python replica/scripts/sweep.py . --avoid "App Original" --avoid apporiginal.com --color "#1DB954"
python replica/scripts/parity.py replica/features.csv --markdown --out replica/parity.md
python replica/scripts/imgdiff.py original.png clon.png --out replica/diff/home.png --min-similarity 85
python replica/scripts/contrast.py replica/design/tokens.json
python replica/scripts/reviews.py replica/reviews.csv --themes replica/themes.json --out replica/themes.md
python replica/scripts/listing.py replica/launch/listing.json
```

| Script | Qué hace de verdad |
|--------|--------------------|
| `sweep.py` | Marca, dominio, colores e identificadores del original (`OriginalAppEmbed` incluido). Ignora binarios; exenciones por línea (`sweep:ignore`) y por fichero (`sweep:ignore-file`). Sale 1 si hay restos. |
| `parity.py` | Lee `features.csv`/`.json`, pondera must 3 / should 2 / could 1, `partial` = 0.5, excluye `out_of_scope`. Falla si algún must no está `done`. |
| `imgdiff.py` | Diff de layout sin librerías: mapa de bordes, rejilla, regiones distintas y PNG de calor. Ignora el color, así que un rebrand no penaliza. |
| `contrast.py` | WCAG AA/AAA sobre tus tokens, con pares texto/fondo. |
| `reviews.py` | Temas y citas **literales con URL**; descarta filas sin enlace y marca `THIN` si <3 reseñas o una sola fuente. |
| `listing.py` | Límites de App Store/Play, claims de ranking, keywords desperdiciadas y nombre del original en el listing. |

Plantillas listas para copiar en `templates/`: `features.csv`, `tokens.json`, `reviews.csv`, `themes.json`, `listing.json`, `scope.md`, `architecture.md`, `test-plan.md`, `preflight.md`, `complex-app-spec.md`, `evidence.md`, `progreso.md`, `reels.md`.

Tests de los scripts (stdlib, sin red): `py -m unittest discover -s replica/tests -v`.

## Cómo ejecutar una fase

1. Lee `references/<fase>.md` y los ficheros de `replica/` que esa fase consume.
2. Si falta una entrada (p. ej. `features.csv`), vuelve a la fase anterior o dilo; no la inventes.
3. Trabaja dentro de `replica/` para los documentos y en el código del proyecto para la app.
4. Pasa las herramientas de la fase. Un gate rojo se arregla, no se ignora.
5. Escribe la salida con su plantilla y actualiza el estado.

## Gates

Cada fase define su gate en su sub-skill y el comando maestro no avanza sin él. Reglas transversales que ninguna fase repite:

- **Evidencia**: en recon (1), paridad (7) y análisis estático (12), todo hallazgo que sostenga una decisión lleva su fila de `templates/evidence.md`.
- **Re-sweep**: todo copy nuevo (landing, listing, redes) pasa `sweep.py` antes de publicarse, aunque el código ya esté limpio.
- **Re-tocado**: si se añade copy, pantalla o claim, se repite el gate que cubre ese cambio; un gate verde de la sesión anterior no vale para hoy.

## Salida esperada de una fase

Un fichero en `replica/` con: qué se hizo, decisiones y por qué, qué queda abierto y qué se ha verificado frente a qué fuente. Sin relleno y sin afirmaciones sin respaldo.

Detalle legal y de alcance en `references/00-limites.md`.
