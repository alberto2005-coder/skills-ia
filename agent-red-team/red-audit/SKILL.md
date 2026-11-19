---
name: red-audit
description: Auditoría de seguridad completa de una skill, MCP o carpeta de instrucciones — escaneo estático, revisión semántica adversarial, verificación independiente de cada hallazgo (confirmed/needs_validation/rejected), ledger de cobertura y informe JSON validable. Úsala solo cuando el usuario pida explícitamente auditoría completa, informe o auditoría a fondo. English: full audit with independent verification, coverage ledger and validatable JSON report.
license: MIT
metadata:
  package: agent-red-team
  version: "3.0.0"
---

# Red Team · Auditoría completa (full audit)

Solo se activa **a petición explícita**. Crea los ficheros que el usuario pida, nunca más.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Todos los comandos se ejecutan desde la raíz del repositorio**.

## Cuándo se usa

- «Auditoría completa», «full audit», «genera el informe», «audita a fondo y guárdame el resultado».
- Antes de integrar una skill de terceros en un pipeline con credenciales.
- Cuando hace falta evidencia verificada, no un veredicto rápido.

## Fase 0 — Modo, alcance y superficies

1. Confirma el alcance: carpeta, ficheros, hooks, MCP, CI.
2. Enumera superficies y anota las ausentes: `SKILL.md` (frontmatter y cuerpo), `scripts/`, hooks del agente, configuración MCP, `templates/`, `references/`, `assets/`, CI.
3. Declara los límites antes de empezar (qué no se podrá verificar y por qué).

## Fase 1 — Escaneo estático

```bash
py agent-red-team/scripts/scan_skill.py --target <ruta> --json
```

Cubre Unicode invisible/ASCII smuggling/bidi, Base64 y hex con alta entropía, inyección en prosa y comentarios (incluye español), AST de Python, shell/JS/TS y las 6 combinaciones **REJECT**. Códigos de salida: `0` apto, `2` bloqueado, `1` ruta inexistente.

## Fase 2 — Revisión semántica adversarial

Lee a mano `SKILL.md` y todo `references/`/`assets/` buscando lo que las regex no ven: scope creep, exfiltración por canal lateral, envenenamiento de `description`, manipulación de configuración global y falta de proporcionalidad entre permisos y propósito. Clasifica con `../references/threat-matrix.md` y localiza el patrón en `../references/attack-catalog.md`.

## Fase 3 — Verificación independiente (obligatoria)

Cada candidato pasa por un revisor nuevo que solo recibe fichero, línea, patrón y propósito declarado, y que intenta **refutarlo**:

1. ¿Está en un fence de documentación o en un ejemplo de test?
2. ¿El patrón solo existe como string, comentario o mensaje de error?
3. ¿La capacidad está justificada por el propósito y el resto del fichero?
4. ¿Hay una explicación benigna verificable (docs, changelog, versión publicada)?

Resultado: `confirmed` (cuenta para veredicto), `needs_validation` (impide APROBADO), `rejected` (se conserva en anexo con su justificación). Los `rejected` no se borran: son la prueba de que se intentó refutar.

## Fase 4 — Saneamiento (solo si se pide)

```bash
py agent-red-team/scripts/sanitize_unicode.py --file ruta/al/SKILL.md
```

Escribe una copia `.sanitized`; **nunca** sobrescribe el original.

## Fase 5 — Informe y ledger

1. Rellena `../templates/risk-report.md` (tabla de verificación + combinaciones REJECT + ledger).
2. Adjunta `../templates/coverage-ledger.json` con las superficies reales y su estado `covered/partial/missing`.
3. Entrega el JSON validable contra `../templates/report-schema.json`.
4. Si el destino es GitHub, exporta SARIF: `py agent-red-team/scripts/export_sarif.py informe.json --output informe.sarif`. Solo salen los `confirmed`; `--include-pending` añade los `needs_validation` como `note` y los `rejected` nunca se exportan.
5. Una superficie `missing` **impide** el veredicto APROBADO y se declara como límite.

## Reglas duras

- Un `RECHAZO` mantiene el bloqueo aunque exista explicación benigna: lo revisa el usuario a mano.
- No se ejecuta el código auditado ni se instalan dependencias.
- Solo se auditan paquetes que el usuario tenga derecho a revisar.
- Nada de probar los payloads del catálogo fuera de un entorno aislado y autorizado.

## Gate de salida

- Ledger completo, sin superficies sin estado.
- Cada hallazgo con `verificacion` y `justificacion_verificacion`.
- JSON validado contra el schema.
- Veredicto coherente con los hallazgos (REJECT → `BLOQUEADO`, `needs_validation` → nunca APROBADO).
- Límites escritos en el informe.

## Handoff

El informe cierra la auditoría. Si el usuario pide limpiar un fichero concreto, Fase 4 (`sanitize_unicode.py`) y solo con su visto bueno; si solo quería el veredicto rápido, `red-scan`.
