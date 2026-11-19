# Informe de Auditoría de Seguridad Red Team: {{skill_name}}

Fecha: {{fecha_utc}}  
Ruta auditada: `{{target_path}}`  
Modo: **{{guidance / auditoría completa}}**  
Veredicto Ejecutivo: **{{APROBADO / PRECAUCIÓN / BLOQUEADO}}**  
Puntuación de Riesgo: **{{score_riesgo}} / 100** (0 = Seguro, 100 = Malicioso)  
Nivel REJECT: **{{sí / no}}** {{combos_disparados}}

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
- **Lectura en una línea:** {{veredicto_en_una_frase}}

---

## 2. Tabla de Hallazgos Técnicos

| ID | Severidad | Verificación | Vector (OWASP / MITRE ATLAS) | Archivo:Línea | Evidencia Literal | Impacto / Riesgo |
|---|---|---|---|---|---|---|
| SEC-01 | CRÍTICA / ALTA / MEDIA / BAJA | confirmed / needs_validation / rejected | | | | |

> Reglas de la tabla: cada fila lleva un `id` estable; la evidencia es el fragmento
> mínimo que demuestra el patrón (nunca un secreto completo); las filas `rejected`
> se conservan con su justificación benigna para que la decisión sea auditable.

---

## 3. Verificación Independiente (refutación de candidatos)

Cada candidato pasó por un revisor nuevo que recibió solo el fichero, la línea y el
patrón, y cuyo objetivo era **refutarlo** (encontrar la explicación benigna).

| Candidato | Intento de refutación | Resultado | Justificación |
|---|---|---|---|
| SEC-01 | ¿Está en un fence de documentación? ¿Es un ejemplo de test? ¿Solo es legible como string? | confirmed / needs_validation / rejected | |

- **confirmed:** se intentó refutar y no se pudo; la explicación benigna no aplica.
- **needs_validation:** no se pudo ni refutar ni confirmar (falta contexto, cadena
  ofuscada ilegible, fichero binario, dependencia externa).

- **rejected:** existe una explicación benigna verificable; queda registrado igualmente.

**Un informe con cualquier `needs_validation` no puede emitirse como APROBADO.**

---

## 4. Combinaciones del Nivel REJECT

| Combo | Señales observadas | Archivo:Línea | Acción |
|---|---|---|---|
| RJ-01 Credenciales SSH con salida de red | | | Rechazar |
| RJ-02 RCE con canal de retorno | | | Rechazar |
| RJ-03 Payload ofuscado ejecutado | | | Rechazar |
| RJ-04 Secretos de entorno con canal de salida | | | Rechazar |
| RJ-05 Persistencia en el entorno | | | Rechazar |
| RJ-06 Cadena de suministro sin versión fijada | | | Rechazar |

Una sola combinación disparada basta para **BLOQUEADO**, aunque cada señal por
separado hubiera sido MEDIA.

---

## 5. Coherencia de Cadena de Suministro (Supply Chain Check)

- **Propósito declarado en frontmatter:** {{declared_purpose}}
- **Coherencia con el código implementado:** {{COHERENTE / DESPROPORCIONADO / ENGAÑOSO}}
- **Observaciones sobre permisos:** {{observaciones_permisos}}

---

## 6. Ledger de Cobertura

| Superficie | Ficheros | Checks | Estado | Notas |
|---|---|---|---|---|
| SKILL.md (frontmatter) | | | covered / partial / missing | |
| SKILL.md (cuerpo) | | | | |
| scripts/ | | | | |
| hooks del agente | | | | |
| MCP config | | | | |
| templates/ | | | | |
| references/ | | | | |

Copia máquina-legible en `coverage-ledger.json`. Superficies en `missing` **no
pueden** dar veredicto APROBADO: se declaran como límite del informe.

---

## 7. Recomendación y Plan de Acción

- [ ] **Acción recomendada:** {{APROBAR / SANEAR_CON_SCRIPT / RECHAZAR}}
- **Pasos a seguir:**
  1. {{paso_1}}
  2. {{paso_2}}

---

## 8. Salida JSON

El informe debe poder entregarse también como JSON validable contra
`templates/report-schema.json` (mismo directorio). Estructura mínima:

```json
{
  "herramienta": "agent-red-team",
  "version": "3.0.0",
  "target": "{{target_path}}",
  "fecha": "{{fecha_utc}}",
  "modo": "auditoria_completa",
  "veredicto": "BLOQUEADO",
  "puntuacion_riesgo": 100,
  "rechazo": true,
  "combos_reject": ["RJ-01"],
  "findings": [
    {
      "id": "REJ-01",
      "titulo": "Lectura de claves SSH y envío por red en el mismo script",
      "severidad": "critical",
      "nivel": "REJECT",
      "categoria": "Exfiltración de credenciales",
      "fichero": "scripts/sync_env.py",
      "linea": 12,
      "evidencia": "CLAVE_PRIVADA = Path.home() / \".ssh\" / \"id_rsa\"",
      "verificacion": "confirmed",
      "justificacion_verificacion": "El fichero importa urllib y envía el contenido; no es documentación ni test.",
      "recomendacion": "No instalar y rotar las claves expuestas."
    }
  ],
  "cobertura": [
    {
      "superficie": "scripts/",
      "ficheros": ["scripts/sync_env.py"],
      "checks": ["AST", "combinaciones REJECT"],
      "estado": "covered",
      "notas": ""
    }
  ]
}
```

Correspondencia de etiquetas entre la tabla y el JSON:

| Tabla (ES) | JSON (`severidad`) | `nivel` |
|---|---|---|
| RECHAZO | `critical` | `REJECT` |
| CRÍTICA | `critical` | `normal` |
| ALTA | `high` | `normal` |
| MEDIA | `medium` | `normal` |
| BAJA | `low` | `normal` |

`verificacion` solo admite `confirmed`, `needs_validation` o `rejected`, y `id`
sigue el patrón `^[A-Z]{2,4}-[0-9]{2,3}$` (por ejemplo `SEC-01`, `REJ-01`).
