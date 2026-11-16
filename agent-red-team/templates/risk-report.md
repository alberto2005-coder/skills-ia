# Informe de Auditoría de Seguridad Red Team: {{skill_name}}

Fecha: {{fecha_utc}}  
Ruta auditada: `{{target_path}}`  
Veredicto Ejecutivo: **{{APROBADO / PRECAUCION / BLOQUEADO}}**  
Puntuación de Riesgo: **{{score_riesgo}} / 100** (0 = Seguro, 100 = Malicioso)

---

## 1. Resumen Ejecutivo y Superficie de Ataque

- **Total archivos analizados:** {{total_archivos}}
- **Total líneas de código (LOC):** {{total_loc}}
- **Dependencias e imports detectados:** {{imports_list}}
- **Capacidades implícitas:**
  - Red / Conexiones salientes: {{SI / NO}}
  - Ejecución de comandos / Shell: {{SI / NO}}
  - Acceso a archivos fuera del workspace: {{SI / NO}}
  - Unicode invisible / ASCII smuggling: {{SI / NO}}

---

## 2. Tabla de Hallazgos Técnicos

| ID | Severidad | Vector (OWASP / MITRE ATLAS) | Archivo:Línea | Evidencia Literal | Impacto / Riesgo |
|---|---|---|---|---|---|
| SEC-01 | CRÍTICA / ALTA / MEDIA / BAJA | | | | |

---

## 3. Coherencia de Cadena de Suministro (Supply Chain Check)

- **Propósito declarado en frontmatter:** {{declared_purpose}}
- **Coherencia con el código implementado:** {{COHERENTE / DESPROPORCIONADO / ENGAÑOSO}}
- **Observaciones sobre permisos:** {{observaciones_permisos}}

---

## 4. Recomendación y Plan de Acción

- [ ] **Acción recomendada:** {{APROBAR / SANEAR_CON_SCRIPT / RECHAZAR}}
- **Pasos a seguir:**
  1. {{paso_1}}
  2. {{paso_2}}
