# Arquitectura: {{app_nombre_propio}}

## 1. Decisiones de Stack

| Decisión | Opción Elegida | Alternativa Descartada | Justificación |
|---|---|---|---|
| Frontend | | | |
| Backend | | | |
| Base de datos | | | |
| Autenticación | | | |
| Pagos | | | |
| Hosting | | | |

## 2. Esquema de Base de Datos (DDL)

```sql
-- Tablas principales, relaciones con ON DELETE y constraints de invariantes
```

## 3. Especificación de API

| Método | Endpoint | Auth Requerida | Parámetros / Body | Respuesta | Errores Posibles |
|---|---|---|---|---|---|
| POST | /api/v1/... | Bearer JWT | | 200 OK | 400, 401, 422 |

## 4. Rebanadas Verticales de Construcción (Build Order)

1. **Slice 1 (Crítica end-to-end):** {{flujo_principal_completo}}
2. **Slice 2:** {{flujo_secundario}}
3. **Slice 3:** {{flujo_soporte}}

## 5. Riesgos Técnicos e Invariantes
- **Idempotencia:** Webhooks de pagos protegidos contra ejecuciones duplicadas.
- **Zonas horarias:** Fechas almacenadas en UTC en base de datos; conversión local en UI.
- **Aislamiento multi-inquilino (si aplica):** `tenant_id` obligatorio en todas las consultas.
