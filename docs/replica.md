# Replica

> Metodología y pipeline de reconstrucción funcional clean-room de software.  
> Clean-room functional reverse-engineering methodology and pipeline for software.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice
1. [Filosofía Clean-Room](#filosofía-clean-room)
2. [Pipeline de 11 Fases](#pipeline-de-11-fases)
3. [Protocolo para Software de Alta Complejidad](#protocolo-para-software-de-alta-complejidad)
4. [Herramientas Deterministas](#herramientas-deterministas)
5. [Plantillas Disponibles](#plantillas-disponibles)
6. [Modo de Uso](#modo-de-uso)

### Filosofía Clean-Room
`replica` reconstruye **lo que una aplicación hace**, no lo que posee. Se basa exclusivamente en comportamiento observable desde fuentes públicas y cuentas propias en uso normal. Nunca se copia código fuente, bases de datos privadas ni activos protegidos.

### Pipeline de 11 Fases
- **Fase 0 (Límites):** Delimitar alcance, qué entra y qué queda fuera (`scope.md`).
- **Fase 1 (Reconocimiento):** Mapeo de pantallas, flujos y catálogo de features (`features.csv`).
- **Fase 1b (Apps Complejas):** Especificación de motores de alta densidad (`complex-app-spec.md`).
- **Fase 2 (Arquitectura):** Stack, DDL con invariantes y rebanadas verticales (`architecture.md`).
- **Fases 3 a 5 (Construcción):** Sistema de diseño, frontend, auth, backend y pagos.
- **Fase 6 (Pruebas):** Casos de prueba E2E y matriz de bugs S1–S4 (`test-plan.md`).
- **Fases 7 a 10 (Validación):** Medición de paridad funcional, rebrand y preparación de lanzamiento.
- **Fase 11 (Despliegue):** Checklist preflight obligatorio antes de publicar (`preflight.md`).

### Protocolo para Software de Alta Complejidad
Para suites interactivas (procesadores de texto, hojas de cálculo, editores visuales tipo Figma/Word), la Fase 1b descompone el sistema en 8 subsistemas independientes:
1. Modelo de Documento (Document AST).
2. Motor de Selección y Caret (coordenadas de rango y navegación por teclado).
3. Pila de Comandos e Historial Transaccional (Undo/Redo con batching).
4. Cascada de Estilos y Formato (herencia de 4 niveles).
5. Motor de Paginación y Geometría (line-breaking, huérfanas/viudas, hojas A4/Carta).
6. Estructuras Complejas (tablas matriciales con merge e imágenes inline/wrap).
7. Shell de UI y Ergonomía (Ribbon, regla interactiva, barra de estado).
8. Persistencia e Interoperabilidad (JSON nativo, DOCX y PDF).

### Herramientas Deterministas
- `parity.py`: Calcula el porcentaje de paridad funcional y valida que ningún requisito *must* quede pendiente.
- `sweep.py`: Escanea el código en busca de nombres, marcas, dominios o identificadores de la app original.
- `contrast.py`: Valida contraste de color WCAG AA/AAA sobre los tokens de diseño.
- `imgdiff.py`: Compara similitud de layout sin penalizar el cambio de color o marca.
- `reviews.py`: Analiza citas de reseñas públicas reales.
- `listing.py`: Valida textos de tienda para App Store y Google Play.

### Plantillas Disponibles
Ubicadas en `replica/templates/`: `scope.md`, `complex-app-spec.md`, `architecture.md`, `test-plan.md`, `preflight.md`, `features.csv`, `tokens.json`, `reviews.csv`, `themes.json`, `listing.json`.

### Modo de Uso
```bash
# Comprobar paridad funcional frente a features.csv
python replica/scripts/parity.py replica/features.csv

# Verificar limpieza de marcas e identificadores del original
python replica/scripts/sweep.py . --avoid "AppOriginal" --avoid apporiginal.com
```

---

## 🇬🇧 English

### Table of Contents
1. [Clean-Room Philosophy](#clean-room-philosophy)
2. [11-Phase Pipeline](#11-phase-pipeline)
3. [Complex Software Protocol](#complex-software-protocol)
4. [Deterministic Tools](#deterministic-tools)
5. [Available Templates](#available-templates)
6. [Usage Instructions](#usage-instructions-1)

### Clean-Room Philosophy
`replica` reconstructs **what an application does**, not what it owns. It studies strictly observable behavior from public documentation and own normal-use accounts. No proprietary code, assets, or database schemas are ever copied.

### 11-Phase Pipeline
- **Phase 0 (Boundaries):** Scope definition, what is in/out of scope (`scope.md`).
- **Phase 1 (Reconnaissance):** Surface mapping, user flows, and feature matrix (`features.csv`).
- **Phase 1b (Complex Apps):** High-density engine specification (`complex-app-spec.md`).
- **Phase 2 (Architecture):** Stack decisions, schema with constraints, and vertical slices (`architecture.md`).
- **Phases 3 to 5 (Build):** Design tokens, frontend implementation, auth, backend, and billing.
- **Phase 6 (Testing):** E2E test plan and S1–S4 bug tracking (`test-plan.md`).
- **Phases 7 to 10 (Validation):** Parity measurement, rebranding sweep, and store listing preparation.
- **Phase 11 (Deployment):** Mandatory preflight gate checklist prior to going live (`preflight.md`).

### Complex Software Protocol
For high-density interactive tools (word processors, spreadsheets, canvas editors), Phase 1b decomposes the engine into 8 decoupled subsystems:
1. Document AST Model.
2. Selection & Caret Engine (range coordinates and full keyboard navigation).
3. Command Stack & Transactional History (Undo/Redo with typing batching).
4. Style Cascading & Formatting (4-level inheritance).
5. Pagination & Geometry Engine (line-breaking, orphan/widow control, page sheets).
6. Complex Structures (matrix tables with cell merging and inline/wrapped images).
7. UI Shell & Ergonomics (Ribbon tabs, interactive ruler, status bar metrics).
8. Persistence & Interoperability (native JSON AST, DOCX import/export, and PDF).

### Deterministic Tools
- `parity.py`: Calculates functional parity percentage and enforces that all *must* features are complete.
- `sweep.py`: Scans the codebase to ensure zero traces of original brand names, domains, or identifiers remain.
- `contrast.py`: Validates WCAG AA/AAA color contrast ratios on design tokens.
- `imgdiff.py`: Structural layout difference comparison.
- `reviews.py`: Extracts and clusters verifiable user review quotes.
- `listing.py`: Validates App Store and Google Play listing limits and rules.

### Available Templates
Located in `replica/templates/`: `scope.md`, `complex-app-spec.md`, `architecture.md`, `test-plan.md`, `preflight.md`, `features.csv`, `tokens.json`, `reviews.csv`, `themes.json`, `listing.json`.

### Usage Instructions
```bash
# Check functional parity progress
python replica/scripts/parity.py replica/features.csv

# Run brand sweep to verify zero leftover traces of original app
python replica/scripts/sweep.py . --avoid "OriginalApp" --avoid originalapp.com
```
