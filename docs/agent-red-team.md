# Agent Red Team

> Módulo de auditoría de seguridad y análisis estático para Agent Skills.  
> Security auditing and static analysis module for Agent Skills.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice
1. [Descripción General](#descripción-general)
2. [Arquitectura y Componentes](#arquitectura-y-componentes)
3. [Protocolo de Auditoría en 4 Fases](#protocolo-de-auditoría-en-4-fases)
4. [Modo de Uso](#modo-de-uso)
5. [Salida del Escaneo](#salida-del-escaneo)

### Descripción General
`agent-red-team` evalúa de forma estática la seguridad de paquetes de instrucciones, carpetas de agentes (`SKILL.md`) y scripts auxiliares antes de ser integrados o ejecutados en entornos locales.

### Arquitectura y Componentes
- **`SKILL.md`**: Definición de la habilidad y protocolo de auditoría.
- **`references/threat-matrix.md`**: Matriz de vectores de ataque (Unicode Tags, ASCII Smuggling, Inyección de Prompts indirecta, Tool Squatting).
- **`scripts/scan_skill.py`**: Motor de análisis estático con AST para Python, cálculo de entropía de Shannon y reglas de detección de patrones.
- **`scripts/sanitize_unicode.py`**: Utilidad para purgar caracteres invisibles y comentarios ocultos.
- **`templates/risk-report.md`**: Plantilla estandarizada para informes de riesgo.

### Protocolo de Auditoría en 4 Fases
1. **Fase 1 (Escaneo estático):** Ejecución de `scan_skill.py` sobre la carpeta objetivo sin ejecutar código de la skill analizada.
2. **Fase 2 (Revisión semántica adversarial):** Inspección manual de `SKILL.md` y `references/` buscando vectores que eludan expresiones regulares.
3. **Fase 3 (Saneamiento):** Limpieza opcional de caracteres invisibles con `sanitize_unicode.py`.
4. **Fase 4 (Emisión de veredicto):** Generación del informe con `templates/risk-report.md` (Aprobado, Precaución o Bloqueado).

### Modo de Uso
```bash
# Escaneo estándar por consola
python agent-red-team/scripts/scan_skill.py --target ./ruta-a-skill

# Salida estructurada en JSON
python agent-red-team/scripts/scan_skill.py --target ./ruta-a-skill --json

# Saneamiento de caracteres invisibles
python agent-red-team/scripts/sanitize_unicode.py --file ./ruta/SKILL.md
```

### Salida del Escaneo
El script devuelve un desglose completo de hallazgos clasificados en:
- `CRÍTICA`: Inyecciones directas, payloads Unicode, ejecución arbitraria de comandos.
- `ALTA`: Comentarios HTML sospechosos, comandos encubiertos.
- `MEDIA` / `BAJA`: Bloques de alta entropía y anomalías estructurales.

---

## 🇬🇧 English

### Table of Contents
1. [General Overview](#general-overview)
2. [Architecture and Components](#architecture-and-components)
3. [4-Phase Audit Protocol](#4-phase-audit-protocol)
4. [Usage Instructions](#usage-instructions)
5. [Scanner Output](#scanner-output)

### General Overview
`agent-red-team` statically inspects the security of instruction packages, agent directories (`SKILL.md`), and companion scripts prior to installation or execution in local developer environments.

### Architecture and Components
- **`SKILL.md`**: Master skill definition and audit protocol.
- **`references/threat-matrix.md`**: Threat matrix covering Unicode Tag smuggling, indirect prompt injection, and tool squatting.
- **`scripts/scan_skill.py`**: Static analysis engine featuring Python AST parsing, Shannon entropy scoring, and pattern matching.
- **`scripts/sanitize_unicode.py`**: Sanitization utility that removes zero-width characters and hidden comments.
- **`templates/risk-report.md`**: Standardized risk reporting template.

### 4-Phase Audit Protocol
1. **Phase 1 (Static Scanning):** Run `scan_skill.py` against the target directory without executing target scripts.
2. **Phase 2 (Adversarial Semantic Review):** Manual inspection of `SKILL.md` and `references/` for intent evasion.
3. **Phase 3 (Sanitization):** Optional purification of invisible codepoints using `sanitize_unicode.py`.
4. **Phase 4 (Verdict Issuance):** Generate risk report using `templates/risk-report.md` (Approved, Caution, or Blocked).

### Usage Instructions
```bash
# Standard console scan
python agent-red-team/scripts/scan_skill.py --target ./path-to-skill

# Structured JSON output
python agent-red-team/scripts/scan_skill.py --target ./path-to-skill --json

# Sanitize invisible unicode characters
python agent-red-team/scripts/sanitize_unicode.py --file ./path/SKILL.md
```

### Scanner Output
The script outputs classified security findings:
- `CRITICAL`: Direct overrides, Unicode payloads, arbitrary command execution.
- `HIGH`: Suspicious HTML comments, covert instructions.
- `MEDIUM` / `LOW`: High-entropy string blocks and structural deviations.
