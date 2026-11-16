# Alcance y Límites del Clon: {{app_nombre_propio}}

## 1. Aplicación de Referencia y Clean-Room
- **App de referencia:** {{nombre_app_original}} ({{dominio_original}})
- **Fuentes autorizadas utilizadas:**
  - [ ] Web pública, help center y documentación oficial.
  - [ ] Reseñas públicas en App Store / Play Store / Trustpilot.
  - [ ] Cuenta propia del usuario (uso normal y capturas propias).
- **Límites innegociables:**
  - Cero código, assets, ilustraciones, iconos ni logos copiados del original.
  - Cero APIs privadas ni scraping no autorizado.
  - Rebrand completo antes de publicación.

## 2. Qué se replica vs Qué queda fuera de alcance (Out of Scope)

| Flujo / Capacidad | Estado | Motivo / Justificación |
|---|---|---|
| Autenticación y gestión de perfil | En alcance (Must) | Flujo base requerido |
| Flujo principal: {{core_flow}} | En alcance (Must) | Valor central del producto |
| Catálogo / Red de usuarios del original | Out of scope | Propiedad del original / datos no clonables |
| Integraciones propietarias | Out of scope | Requiere acuerdos comerciales |

## 3. Dimensionamiento y Esfuerzo Estimado

| Módulo / Rebanada | Talla (S/M/L) | Estimación | Dependencias |
|---|---|---|---|
| Slice 1: Flujo central end-to-end | M | 2-3 días | Auth, Base de datos |
| Slice 2: Facturación y suscripciones | M | 2 días | Proveedor de pagos (Stripe) |
| Slice 3: Ajustes y administración | S | 1 día | Slice 1 |

## 4. Riesgos Legales y Términos de Servicio
- **Términos del original:** {{resumen_terminos_competidor}}
- **Marca y Trade Dress:** Sin confusión visual ni similitud fonética en el nombre propio.
