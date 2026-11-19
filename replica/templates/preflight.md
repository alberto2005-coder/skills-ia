# Preflight de Despliegue: {{app_nombre_propio}}

Fecha: {{fecha_utc}}  
Versión / Commit: {{commit_hash}}  
Responsable: {{responsable}}

---

## 1. Gates Automáticos de Scripts

| Tool / Check | Comando Ejecutado | Criterio de Pase | Resultado |
|---|---|---|---|
| **Paridad** | `python scripts/parity.py replica/features.csv` | 0 must pendientes | [ ] PASS |
| **Limpieza de Marca** | `python scripts/sweep.py . --avoid "{{original}}"` | 0 rastros detectados | [ ] PASS |
| **Contraste de Color** | `python scripts/contrast.py replica/design/tokens.json` | 100% WCAG AA | [ ] PASS |
| **Listing de Tienda** | `python scripts/listing.py replica/launch/listing.json` | 0 errores bloqueantes | [ ] PASS |

---

## 2. Checklist Operativo y de Infraestructura

- [ ] **Bugs abiertos:** 0 bugs clasificados como S1 o S2 en `replica/bugs.md`.
- [ ] **Variables de entorno:** Configuradas en el entorno destino (cero secretos en el repositorio).
- [ ] **Migraciones de BD:** Ejecutadas limpiamente y verificadas desde cero en staging.
- [ ] **Dominio y Certificados:** Dominio propio activo, DNS propagado y HTTPS forzado.
- [ ] **Correos transaccionales:** Dominio verificado con SPF, DKIM y DMARC activos.
- [ ] **Pasarela de pagos:** Modo live con claves reales y webhook apuntando al dominio de producción.
- [ ] **Smoke test en producción:**
  - [ ] Registro de usuario real.
  - [ ] Flujo principal de la aplicación completado de punta a punta.
  - [ ] Pago real de prueba (importe mínimo) y confirmación de webhook.
  - [ ] Recepción de correo de notificación.
  - [ ] Cierre de sesión y recuperación de contraseña.
- [ ] **Plan de Rollback:** Procedimiento documentado para revertir al release anterior y preservar datos.

---

## 3. Autorización de Publicación

- [ ] Confirmación explícita del usuario recibida para publicar en producción o enviar a revisión de tiendas.
