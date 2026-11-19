---
name: replica-brand
description: >
  Fase 9 de replica — rebrandea el clon por completo (nombre, paleta, logo, copy y voz) y limpia cualquier rastro del original en el código, verificándolo con sweep y contraste. Úsala antes de publicar cualquier clon, cuando haya que poner marca propia o cuando queden restos de la app original. English: rebrand name, palette, logo and copy, then drive sweep.py to zero brand leftovers.
license: MIT
metadata:
  package: replica
  version: "2.0.0"
---

# Replica · Marca (fase 9)

Aquí el clon deja de parecer un clon. **Sin este gate no se publica.** No rediseña componentes ni flujos: cambia identidad, copy y restos del original; el sistema de diseño viene de `replica-design`.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Todos los comandos se ejecutan desde la raíz del repositorio**.

## Precondiciones

- Paridad cerrada (fase 7) y plan de mejoras (fase 8).
- `design/tokens.json` de la fase 3.

## Método

1. Lee `../references/09-brand.md` entero.
2. **Nombre y dominio propios.** Comprueba que no colisionan con el original ni con marcas existentes; si hay duda, avisa al usuario.
3. **Identidad visual propia:** paleta, tipografía, radios y tono. No basta con rotar el color: el resultado no debe reconocerse como derivado.
4. **Copy y voz propios:** landing, onboarding, emails, mensajes de error y microcopy. Reescribe desde cero; no parafrasees el copy original.
5. **Logo e iconos propios**, sin partir de los assets del original.
6. Limpia restos y verifica:

```bash
py replica/scripts/sweep.py . --avoid "App Original" --avoid apporiginal.com --color "#1DB954"
py replica/scripts/contrast.py replica/design/tokens.json
```

   `sweep.py` marca nombre, dominio, colores e identificadores del original (incluido `OriginalAppEmbed`), ignora binarios y admite exenciones justificadas (`sweep:ignore`, `sweep:ignore-file`).

7. Un resto intencionado (p. ej. mención comparativa legítima) se exonera con comentario y motivo; no se borra la exención sin explicar.

## Gate de salida

- `sweep.py` en 0 sobre el código y los assets.
- `contrast.py` en AA tras el cambio de paleta.
- Nombre, logo, paleta y copy declarados como propios en `replica/brand/`.
- Cero enlaces, capturas o textos del original en la UI pública.

## Handoff

La marca limpia es requisito de `replica-launch` (fase 10) y de `replica-redes` (fase 13). El re-sweep del copy nuevo se repite allí.
