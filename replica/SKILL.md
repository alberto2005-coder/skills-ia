---
name: Replica
description: Replica una app comercial por sus funciones y flujos, clean-room y legal. Reconoce la app, planifica stack y datos, reconstruye diseño y pantallas, añade auth/pagos, prueba, mide paridad, lee reseñas reales para mejorar, rebrandea, prepara el lanzamiento y despliega. Úsala cuando el usuario quiera clonar, replicar, reconstruir o "hacer algo como X" app, o medir paridad/rastros de marca de un clon.
---

# Replica

Pipeline de 11 fases para reconstruir **lo que una app hace**, no lo que posee. Cada fase lee lo que escribió la anterior en `replica/` del proyecto y deja su salida ahí.

## Reglas duras

1. **Clean-room.** Estudias comportamiento observable y escribes todo de cero. Nunca copias código, assets, logos, iconos, ilustraciones, textos, bases de datos ni APIs privadas del original.
2. **Solo fuentes permitidas.** Páginas públicas, docs, help center, store listing, reseñas públicas y **tu propia cuenta**. Nunca la cuenta de otro, nunca scraping tras login, nunca saltarse un paywall.
3. **Si los términos del original prohíben construir un competidor con tu cuenta, dilo y limítate a fuentes públicas.** No es una decisión que tome la skill por su cuenta.
4. **Rebrand obligatorio antes de publicar.** Nombre, paleta, logo, copy y voz propios. `deploy` no pasa con `sweep.py` sucio.
5. **Cero datos inventados.** Ni reseñas, ni citas, ni métricas, ni usuarios. Cada afirmación con enlace; si no hay muestra suficiente, se dice `THIN` y no se usa como argumento.
6. **Alcance honesto.** "Clonar" = funciones y flujos. El contenido licenciado, la red de usuarios y las marcas no se clonan. Si algo es semanas de trabajo, se dice antes de empezar.
7. **Nada de asesoría legal.** La skill avisa de los checks (trademark, términos) y el usuario decide con su abogado.

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
| 10 | Lanzamiento | `references/10-launch.md` | landing, `launch/listing.json` |
| 11 | Despliegue | `references/11-deploy.md` | `preflight.md`, app live |

Se puede entrar en cualquier fase suelta (`08` sobre una app que solo estás evaluando es útil). Si la app objetivo es un software de alta densidad interactiva o de productividad (como Microsoft Word, Google Docs o Figma), consulta obligatoriamente `references/01b-apps-complejas.md` para estructurar el AST, el motor de selección, la pila de comandos y el renderizado con fidelidad matemática 1:1. Al empezar una fase, **lee su referencia**; no improvises el método.

## Herramientas

Scripts en `scripts/`, solo stdlib de Python 3.8+, sin red. Rutas relativas a esta skill.

```bash
python scripts/sweep.py . --avoid "App Original" --avoid apporiginal.com --color "#1DB954"
python scripts/parity.py replica/features.csv --markdown --out replica/parity.md
python scripts/imgdiff.py original.png clon.png --out replica/diff/home.png --min-similarity 85
python scripts/contrast.py replica/design/tokens.json
python scripts/reviews.py replica/reviews.csv --themes replica/themes.json --out replica/themes.md
python scripts/listing.py replica/launch/listing.json
```

| Script | Qué hace de verdad |
|--------|--------------------|
| `sweep.py` | Marca, dominio, colores e identificadores del original (`OriginalAppEmbed` incluido). Ignora binarios; exenciones por línea (`sweep:ignore`) y por fichero (`sweep:ignore-file`). Sale 1 si hay restos. |
| `parity.py` | Lee `features.csv`/`.json`, pondera must 3 / should 2 / could 1, `partial` = 0.5, excluye `out_of_scope`. Falla si algún must no está `done`. |
| `imgdiff.py` | Diff de layout sin librerías: mapa de bordes, rejilla, regiones distintas y PNG de calor. Ignora el color, así que un rebrand no penaliza. |
| `contrast.py` | WCAG AA/AAA sobre tus tokens, con pares texto/fondo. |
| `reviews.py` | Temas y citas **literales con URL**; descarta filas sin enlace y marca `THIN` si <3 reseñas o una sola fuente. |
| `listing.py` | Límites de App Store/Play, claims de ranking, keywords desperdiciadas y nombre del original en el listing. |

Plantillas listas para copiar en `templates/`: `features.csv`, `tokens.json`, `reviews.csv`, `themes.json`, `listing.json`, `scope.md`, `architecture.md`, `test-plan.md`, `preflight.md`, `complex-app-spec.md`.

## Cómo ejecutar una fase

1. Lee `references/<fase>.md` y los ficheros de `replica/` que esa fase consume.
2. Si falta una entrada (p. ej. `features.csv`), vuelve a la fase anterior o dilo; no la inventes.
3. Trabaja dentro de `replica/` para los documentos y en el código del proyecto para la app.
4. Pasa las herramientas de la fase. Un gate rojo se arregla, no se ignora.
5. Escribe la salida con su plantilla y actualiza el estado.

## Gates

- **Antes de construir**: alcance escrito, `features.csv` con must, modelo de datos con invariantes.
- **Antes de probar**: flujo principal completo end-to-end, estados vacío/error.
- **Antes de lanzar**: `parity.py` sin must pendientes, `sweep.py` a 0, `contrast.py` AA, `listing.py` 0 errores, 0 bugs S1/S2.
- **Antes de desplegar**: preflight de `references/11-deploy.md` completo y confirmación explícita del usuario.

## Salida esperada de una fase

Un fichero en `replica/` con: qué se hizo, decisiones y por qué, qué queda abierto y qué se ha verificado frente a qué fuente. Sin relleno y sin afirmaciones sin respaldo.

Detalle legal y de alcance en `references/00-limites.md`.
