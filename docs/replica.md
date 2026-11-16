# Documentación: Replica

## Descripción
Metodología y herramientas para reconstruir cualquier software observando exclusivamente su comportamiento observable (*clean-room*), sin copiar código, activos ni bases de datos propietarias.

## Pipeline por fases
- **Fase 0:** Límites, alcance y verificación de fuentes permitidas (`scope.md`).
- **Fase 1:** Inventario de superficies, flujos y matriz de features (`features.csv`).
- **Fase 1b:** Protocolo de alta complejidad para motores y suites interactivas (`complex-app-spec.md`).
- **Fase 2:** Arquitectura, esquema relacional y rebanadas verticales (`architecture.md`).
- **Fase 3 a 5:** Construcción de diseño, código y lógica de backend.
- **Fase 6:** Plan de pruebas de flujos principales y reporte de fallos (`test-plan.md`).
- **Fase 7 a 10:** Medición de paridad funcional, rebrand y preparación de lanzamiento.
- **Fase 11:** Verificación final antes de despliegue (`preflight.md`).

## Herramientas (`scripts/`)
- `sweep.py`: Verifica que no existan restos de marca, nombres ni colores de la aplicación original.
- `parity.py`: Pondera el avance funcional frente al catálogo de requisitos.
- `imgdiff.py`: Comprobación geométrica y visual de layout.
- `contrast.py`: Validación de accesibilidad y contraste WCAG sobre tokens de color.
- `listing.py`: Validación de textos para tiendas de aplicaciones.

## Modo de uso
```bash
python replica/scripts/parity.py replica/features.csv
python replica/scripts/sweep.py . --avoid "AppReferencia"
```
