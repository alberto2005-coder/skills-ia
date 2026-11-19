---
name: red-scan
description: >
  Escaneo rápido de seguridad de una skill, MCP o carpeta de instrucciones, con veredicto y hallazgos en el chat, sin crear ficheros. Úsala para la pregunta puntual «¿esta skill es segura?», «mírame este SKILL.md» o «¿qué hace este script?» antes de instalar algo de terceros. English: quick scan, give the verdict in chat and create no files.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(py agent-red-team/scripts/*)
  - Bash(python3 agent-red-team/scripts/*)
license: MIT
metadata:
  package: agent-red-team
  version: "3.1.0"
---

# Red Team · Scan rápido (guidance)

Modo **guidance**: responde en el chat y no escribe nada en disco. Es el modo por defecto.

Assets compartidos del paquete: `../references/`, `../scripts/`, `../templates/`. **Todos los comandos se ejecutan desde la raíz del repositorio**.

## Cuándo se usa

- Consulta puntual antes de instalar o copiar una skill.
- Revisión de un `SKILL.md`, un script o un `references/` suelto.
- El usuario pide veredicto, no informe.

Si el usuario pide «auditoría completa», «informe» o «genera el ledger», cambia a `red-audit`. Si la petición es ambigua («échale un ojo»), **pregunta** antes de crear archivos.

## Método

1. Ejecuta el motor estático:

```bash
py agent-red-team/scripts/scan_skill.py --target <ruta_carpeta_o_archivo>
py agent-red-team/scripts/scan_skill.py --target <ruta> --json
```

2. Lee el resultado con la escala de severidad: `reject` → `critical` → `high` → `medium` → `low` (el informe las rotula RECHAZO/CRÍTICA/ALTA/MEDIA/BAJA).
3. Revisa a mano lo que las regex no ven, usando `../references/threat-matrix.md` para clasificar y `../references/attack-catalog.md` para reconocer el patrón:
   - contradicción entre el propósito declarado y lo que pide hacer;
   - exfiltración por canal lateral (datos en URLs de imágenes o enlaces);
   - `description` con palabras clave universales para secuestrar enrutamiento;
   - escritura en configuración global (`~/.bashrc`, `authorized_keys`, hooks) o del agente.
4. Aplica la excepción de **code fences** del maestro: lo documentado no es payload vivo; los fences ejecutables y el Unicode invisible sí cuentan.
5. Entrega en el chat: veredicto, hallazgos con `fichero:línea` y evidencia literal, y qué no se pudo verificar.

## Reglas duras

- No se crean ficheros, ledger, informe ni `.sanitized` en este modo.
- No se ejecuta el código auditado ni se instalan sus dependencias.
- Una superficie ausente no es una superficie cubierta: si no se miró `scripts/`, se dice.
- Un `RECHAZO` es bloqueo, no una advertencia: se comunica como tal.
- Si algo no se puede confirmar ni refutar, se dice «necesita validación», no se aprueba por descarte.

## Gate de salida

1. Veredicto en una línea.
2. Tabla de hallazgos: severidad · fichero:línea · evidencia · lectura.
3. Límites del escaneo (qué no se pudo ver).
4. Recomendación: instalar, instalar con precaución, no instalar.

## Handoff

Si el usuario quiere informe, ledger o verificación independiente por hallazgo, `red-audit`.
