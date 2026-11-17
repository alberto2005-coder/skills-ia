---
name: replica-design
description: Fase 3 de replica — construye un sistema de diseño propio (tokens, tipografía, espaciado, componentes y estados) a partir del comportamiento observado, sin copiar assets ni paletas del original, y lo valida con contraste WCAG. Úsala cuando haya que definir la UI antes de construir pantallas, o cuando el usuario pida tokens, componentes o accesibilidad de un clon.
---

# Replica · Sistema de diseño (fase 3)

Produce una UI **propia** que resuelve los mismos problemas de uso que la original. Ni paleta, ni iconos, ni ilustraciones, ni copy ajenos.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Todos los comandos se ejecutan desde la raíz del repositorio** (`skills-ia-main/`).

## Precondiciones

- `replica/architecture.md` aprobado.
- `replica/screens/` y `recon.md` con las pantallas clave descritas por función, no por píxeles copiados.

## Método

1. Lee `../references/03-design.md` entero.
2. Extrae de `recon.md` las **decisiones de interacción** (jerarquía, densidad, navegación, feedback, estados), no los valores visuales concretos.
3. Define tokens en `replica/design/tokens.json` desde `../templates/tokens.json`: color, tipografía, espaciado, radios, sombras, breakpoints y estados (hover, focus, disabled, error).
4. Documenta componentes en `replica/design/components.md`: anatomía, variantes, estados, cuándo se usa y cuándo no.
5. Elige una identidad distinta a la del original (color de marca, tipografía, radios). El rebrand de la fase 9 no debe encontrarse con una paleta sospechosamente idéntica.
6. Valida contraste:

```bash
py replica/scripts/contrast.py replica/design/tokens.json
```

7. Corrige hasta AA (AAA donde el par lo permita) sin romper la jerarquía.

## Gate de salida

- `tokens.json` completo (ningún token referenciado sin definir).
- `components.md` con estados vacío, carga, error y éxito para cada componente de datos.
- `contrast.py` en AA o superior en todos los pares texto/fondo.
- Paleta y tipografía declaradas como propias, no derivadas de la original.

## Handoff

`tokens.json` y `components.md` los consume `replica-build` (fase 4). La validación de contraste se repite en `replica-brand` (fase 9) tras el rebrand.
