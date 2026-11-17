---
name: replica-entrepreneur
description: Fase 8 de replica — lee reseñas y comentarios públicos reales de la app original, extrae temas con citas literales y URL, descarta muestras insuficientes y convierte lo aprendido en un plan de mejoras propio. Úsala para decidir qué mejorar del clon con voz de usuario real, no con suposiciones. English: read public reviews, extract themes with literal quotes and URLs, and turn the user voice into a fix plan.
license: MIT
metadata:
  package: replica
  version: "2.0.0"
---

# Replica · Voz del usuario (fase 8)

El clon ya funciona; ahora se decide **qué duele de verdad** en esta categoría. Solo con reseñas reales y citables.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Todos los comandos se ejecutan desde la raíz del repositorio** (`skills-ia-main/`).

## Precondiciones

- Producto construido y con paridad medida (fase 7).
- Reseñas públicas recogidas a mano en `replica/reviews.csv` (desde `../templates/reviews.csv`), con enlace a cada una.

## Método

1. Lee `../references/08-entrepreneur.md` entero.
2. Recoge reseñas de fuentes públicas permitidas (stores, foros, review sites). Nada de scraping tras login ni de reseñas privadas.
3. Ejecuta:

```bash
py replica/scripts/reviews.py replica/reviews.csv --themes replica/themes.json --out replica/themes.md
```

   El script extrae temas y citas **literales con URL**, descarta filas sin enlace y marca `THIN` si hay menos de 3 reseñas o una sola fuente.
4. Un tema `THIN` no se usa como argumento ni en copy: se anota como pendiente de más muestra.
5. Convierte los temas sólidos en `replica/fix-plan.md`: qué cambiar, por qué (cita), coste estimado y criterio de éxito. Prioriza por frecuencia × gravedad, no por lo que suene bonito.
6. Lo que no se va a hacer también se escribe, con el motivo.

## Reglas

- Cero citas inventadas, parafraseadas como si fueran literales, o sin URL.
- Cero métricas de usuarios que no estén en la fuente.
- No se copia el copy de las reseñas al producto: se usa para decidir, no como texto de marketing.

## Gate de salida

- `themes.md` generado con citas y URL.
- Cada tema usado en `fix-plan.md` tiene ≥3 muestras o dos fuentes independientes.
- `THIN` visible y excluido de las decisiones.
- Plan con criterio de éxito por acción.

## Handoff

`themes.md` y `fix-plan.md` informan `replica-brand` (fase 9) y el copy de lanzamiento (`replica-launch`, fase 10).
