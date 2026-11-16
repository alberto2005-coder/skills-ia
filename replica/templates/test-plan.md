# Plan de Pruebas y Control de Calidad: {{app_nombre_propio}}

## 1. Cobertura de Flujos Críticos (E2E)

| ID | Flujo / Escenario | Pasos | Resultado Esperado | Estado |
|---|---|---|---|---|
| E2E-01 | Registro y activación | Registro -> Email de confirmación -> Login | Sesión iniciada con éxito | [ ] |
| E2E-02 | Flujo central completo | Crear entidad -> Modificar -> Ver estado | Persistencia correcta en BD | [ ] |
| E2E-03 | Proceso de pago / Checkout | Selección de plan -> Pasarela de pago -> Webhook | Rol de usuario actualizado | [ ] |
| E2E-04 | Casos límite y fallos | Datos inválidos, corte de red, sesión caducada | Mensajes de error claros sin caída | [ ] |

## 2. Registro de Bugs (Severidad S1 a S4)

- **S1 (Bloqueante):** Caída de la app, pérdida de datos, brecha de seguridad.
- **S2 (Grave):** Flujo principal roto sin alternativa disponible.
- **S3 (Moderado):** Fallo secundario con alternativa conocida.
- **S4 (Menor):** Detalle visual o cosmético.

| Bug ID | Severidad | Descripción | Pasos para reproducir | Estado |
|---|---|---|---|---|
| | | | | |
