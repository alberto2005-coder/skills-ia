# Agent Red Team

> Auditoría de seguridad de skills, MCP y carpetas de instrucciones.  
> Security audit for skills, MCP servers and instruction folders.

[🇪🇸 Español](#-español) · [🇬🇧 English](#-english)

---

## 🇪🇸 Español

### Índice

1. [Descripción General](#descripción-general)
2. [Modos de Operación](#modos-de-operación)
3. [Sub-skills](#sub-skills)
4. [Protocolo en 6 Fases (0–5)](#protocolo-en-6-fases-05)
5. [Nivel RECHAZO y Code Fences](#nivel-rechazo-y-code-fences)
6. [Componentes](#componentes)
7. [Uso](#uso)
8. [Salida y Códigos](#salida-y-códigos)
9. [Límites](#límites)

### Descripción General

`agent-red-team` evalúa de forma estática paquetes de instrucciones, servidores MCP, carpetas de agentes (`SKILL.md`) y scripts auxiliares antes de instalarlos o ejecutarlos. Combina análisis determinista (AST de Python, entropía, Unicode invisible, patrones de inyección) con revisión semántica adversarial y verificación independiente de cada hallazgo.

**Paquete de 3 skills:** el maestro elige el modo; `red-scan` y `red-audit` ejecutan cada uno.

### Modos de Operación

| Modo | Cuándo | Qué entrega | ¿Escribe ficheros? |
|---|---|---|---|
| **guidance** (por defecto) | «¿esta skill es segura?», «mírame este `SKILL.md`» | Veredicto y hallazgos en el chat, con `fichero:línea` y evidencia | No |
| **auditoría completa** | Solo si se pide: «auditoría completa», «informe», «audita a fondo» | Informe, ledger de cobertura y JSON validable | Sí, los que pida el usuario |

Si la petición es ambigua, se pregunta antes de crear archivos. Ninguno de los dos modos autoriza a ejecutar el código auditado.

### Sub-skills

| Sub-skill | Qué hace |
|---|---|
| `red-scan` | Escaneo rápido en modo guidance: veredicto, hallazgos y límites en el chat, sin crear ficheros. |
| `red-audit` | Auditoría completa: superficies, escaneo estático, revisión adversarial, verificación independiente, ledger e informe JSON. |

### Protocolo en 6 Fases (0–5)

1. **Fase 0 — Modo, alcance y superficies.** Confirmar modo; enumerar `SKILL.md` (frontmatter y cuerpo), `scripts/`, hooks, MCP, `templates/`, `references/`, `assets/` y CI; anotar las ausentes; declarar límites.
2. **Fase 1 — Escaneo estático.** `scan_skill.py` (apoyado en `rules.json`) sobre la ruta objetivo, sin ejecutar nada del objetivo.
3. **Fase 2 — Revisión semántica adversarial.** Lectura manual de scope creep, exfiltración por canal lateral, envenenamiento de `description`, manipulación de configuración global y proporcionalidad de permisos.
4. **Fase 3 — Verificación independiente (obligatoria).** Un revisor nuevo intenta **refutar** cada candidato. Resultado: `confirmed`, `needs_validation` o `rejected` (los rechazados se conservan en anexo con su justificación).
5. **Fase 4 — Saneamiento (solo si se pide).** `sanitize_unicode.py` escribe una copia `.sanitized`; nunca sobrescribe el original.
6. **Fase 5 — Informe y ledger (solo auditoría completa).** `templates/risk-report.md` + `coverage-ledger.json` + JSON validado contra `report-schema.json`.

### Nivel RECHAZO y Code Fences

Seis combinaciones fallan **siempre**, aunque cada señal por separado fuese media (por fichero): credenciales SSH con salida de red, RCE con canal de retorno, payload ofuscado ejecutado, secretos con canal de salida, persistencia y cadena de suministro sin versión fijada. Una sola combinación da severidad `reject`, veredicto `BLOQUEADO - MALICIOSO / CRÍTICO` y código de salida 2.

**Code fences:** lo documentado dentro de un fence no es un hallazgo vivo, salvo que el fence sea ejecutable (`bash`, `sh`, `python`, `js`, `ts`…). El Unicode invisible cuenta siempre.

### Componentes

- `SKILL.md` (maestro) + `red-scan/SKILL.md` + `red-audit/SKILL.md`.
- `references/threat-matrix.md`: OWASP LLM Top 10 / MITRE ATLAS.
- `references/attack-catalog.md`: 15 ataques con qué hace, cómo se ve y checklist.
- `scripts/scan_skill.py`: motor estático (`--target`, `--json`, `--rules`).
- `scripts/rules.json`: reglas y firmas de detección desacopladas del código fuente.
- `scripts/sanitize_unicode.py`: copia saneada de un fichero.
- `templates/risk-report.md`, `coverage-ledger.json`, `report-schema.json`.
- `tests/fixtures/skill_maliciosa/` (inerte) y `skill_limpia/` (payload documentado que no debe dar positivo).

### Uso

```bash
# Escaneo por consola
py agent-red-team/scripts/scan_skill.py --target ./ruta-a-skill

# Salida JSON
py agent-red-team/scripts/scan_skill.py --target ./ruta-a-skill --json

# Con archivo de reglas personalizado
py agent-red-team/scripts/scan_skill.py --target ./ruta-a-skill --rules ./mis-reglas.json

# Saneamiento
py agent-red-team/scripts/sanitize_unicode.py --file ./ruta/SKILL.md

# Tests del paquete
py -m unittest discover -s agent-red-team/tests -v
```

### Salida y Códigos

Severidades en JSON: `reject` → `critical` → `high` → `medium` → `low` (el informe las rotula RECHAZO/CRÍTICA/ALTA/MEDIA/BAJA). Códigos de salida: `0` apto, `2` bloqueado por `critical` o `reject`, `1` ruta inexistente.

### Límites

- Solo se auditan paquetes que el usuario tenga derecho a revisar.
- El análisis es estático: no ejecuta el código ni instala dependencias.
- Una superficie ausente no es una superficie cubierta; una superficie `missing` impide el veredicto APROBADO.
- Las firmas viven desacopladas en `scripts/rules.json` (solo datos pasivos) para evitar falsos positivos heurísticos en antivirus locales; ningún archivo del paquete ejecuta cargas útiles.

---

## 🇬🇧 English

### Table of Contents

1. [Overview](#overview)
2. [Operating Modes](#operating-modes)
3. [Sub-skills](#sub-skills-1)
4. [6-Phase Protocol (0–5)](#6-phase-protocol-05)
5. [REJECT Level and Code Fences](#reject-level-and-code-fences)
6. [Components](#components)
7. [Usage](#usage)
8. [Output and Exit Codes](#output-and-exit-codes)
9. [Limits](#limits)

### Overview

`agent-red-team` statically inspects instruction packages, MCP servers, agent folders (`SKILL.md`) and companion scripts before installation or execution. It combines deterministic analysis (Python AST, entropy, invisible Unicode, injection patterns) with adversarial semantic review and independent verification of every finding.

**3-skill package:** the master picks the mode; `red-scan` and `red-audit` do the work.

### Operating Modes

| Mode | When | Deliverable | Writes files? |
|---|---|---|---|
| **guidance** (default) | "Is this skill safe?", "look at this `SKILL.md`" | Verdict and findings in chat, with `file:line` and evidence | No |
| **full audit** | Only on request: "full audit", "report", "audit thoroughly" | Report, coverage ledger and validatable JSON | Yes, only what the user asks for |

Ambiguous requests are clarified before creating files. Neither mode authorizes executing the audited code.

### Sub-skills

| Sub-skill | Purpose |
|---|---|
| `red-scan` | Quick guidance scan: verdict, findings and limits in chat, no files created. |
| `red-audit` | Full audit: surfaces, static scan, adversarial review, independent verification, ledger and JSON report. |

### 6-Phase Protocol (0–5)

1. **Phase 0 — Mode, scope and surfaces.** Confirm mode; list `SKILL.md` (frontmatter and body), `scripts/`, hooks, MCP, `templates/`, `references/`, `assets/` and CI; record missing surfaces; declare limits.
2. **Phase 1 — Static scan.** `scan_skill.py` (backed by `rules.json`) against the target path, without executing any of it.
3. **Phase 2 — Adversarial semantic review.** Manual review of scope creep, side-channel exfiltration, `description` poisoning, global config tampering and permission proportionality.
4. **Phase 3 — Independent verification (mandatory).** A fresh reviewer tries to **refute** each candidate. Result: `confirmed`, `needs_validation` or `rejected` (rejected findings are kept in an annex with their justification).
5. **Phase 4 — Sanitization (only on request).** `sanitize_unicode.py` writes a `.sanitized` copy; the original is never overwritten.
6. **Phase 5 — Report and ledger (full audit only).** `templates/risk-report.md` + `coverage-ledger.json` + JSON validated against `report-schema.json`.

### REJECT Level and Code Fences

Six combinations always fail, even when each signal alone would be medium (per file): SSH credentials with network output, RCE with a return channel, executed obfuscated payload, secrets with an output channel, persistence, and unpinned supply chain. A single combination yields `reject` severity, a `BLOCKED - MALICIOUS / CRITICAL` verdict and exit code 2.

**Code fences:** content inside a fence is not a live finding unless the fence is executable (`bash`, `sh`, `python`, `js`, `ts`…). Invisible Unicode always counts.

### Components

- `SKILL.md` (master) + `red-scan/SKILL.md` + `red-audit/SKILL.md`.
- `references/threat-matrix.md`: OWASP LLM Top 10 / MITRE ATLAS.
- `references/attack-catalog.md`: 15 attacks with behavior, appearance and checklist.
- `scripts/scan_skill.py`: static engine (`--target`, `--json`, `--rules`).
- `scripts/rules.json`: detection rules and signatures decoupled from the source code.
- `scripts/sanitize_unicode.py`: sanitized copy of a file.
- `templates/risk-report.md`, `coverage-ledger.json`, `report-schema.json`.
- `tests/fixtures/skill_maliciosa/` (inert) and `skill_limpia/` (documented payload that must not trigger).

### Usage

```bash
# Console scan
py agent-red-team/scripts/scan_skill.py --target ./path-to-skill

# JSON output
py agent-red-team/scripts/scan_skill.py --target ./path-to-skill --json

# With custom rules file
py agent-red-team/scripts/scan_skill.py --target ./path-to-skill --rules ./custom-rules.json

# Sanitization
py agent-red-team/scripts/sanitize_unicode.py --file ./path/SKILL.md

# Package tests
py -m unittest discover -s agent-red-team/tests -v
```

### Output and Exit Codes

Severities in JSON: `reject` → `critical` → `high` → `medium` → `low` (reports label them REJECT/CRITICAL/HIGH/MEDIUM/LOW). Exit codes: `0` clean, `2` blocked by `critical` or `reject`, `1` path not found.

### Limits

- Only packages the user is entitled to review are audited.
- Analysis is static: it does not execute code or install dependencies.
- An absent surface is not a covered surface; a `missing` surface prevents an APPROVED verdict.
- Signatures live decoupled in `scripts/rules.json` (passive data only) to prevent heuristic false positives in local antivirus engines; no file in this package executes payloads.
