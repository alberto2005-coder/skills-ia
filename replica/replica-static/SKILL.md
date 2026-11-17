---
name: replica-static
description: Fase 12 de replica (opt-in) — análisis estático de binarios o apps propias o autorizadas para extraer strings, rutas y endpoints con herramientas ya instaladas, separando observación de inferencia y con límites declarados. Úsala solo si el usuario lo pide y aporta el artefacto legalmente; nunca para DRM, logins ajenos ni paywalls.
---

# Replica · Análisis estático (fase 12, opt-in)

Amplía el reconocimiento cuando la UI no basta. **No se activa por iniciativa propia.**

Assets compartidos: `../references/`, `../scripts/`. **Comandos desde la raíz del repositorio** (`skills-ia-main/`).

## Condiciones de entrada (las tres)

1. El usuario lo pide explícitamente.
2. Aporta binarios, APK, `app.asar` o JS **propios o con autorización por escrito**.
3. Las herramientas necesarias ya están instaladas: la skill las detecta con `shutil.which`, **no instala nada**.

Si falta cualquiera, la fase se marca `n/a` en `progreso.md` con el motivo y se continúa en observación de UI.

## Prohibiciones absolutas

- DRM, cifrado comercial, ofuscación deliberada para impedir el análisis.
- Saltarse logins, paywalls o límites de cuenta ajena.
- Credenciales, tokens o datos de terceros.
- Copiar código descompilado al proyecto: se extrae **comportamiento**, no código.
- Con código fuente completo disponible, se usan las herramientas normales del agente y esta fase no aplica.

## Método

1. Lee `../references/12-analisis-estatico.md` entero: reglas anti-DRM/login/paywall, tabla de herramientas y limitaciones de cada conclusión.
2. Detecta herramientas con `shutil.which` (`strings`, `objdump`, `jadx`, `unzip`, `node`...). Anota cuáles hay y cuáles no: las que falten son un límite, no un fallo.
3. Extracción determinista con el `extract.py` stdlib descrito en la referencia (sin instalar nada) y, si el usuario las tiene, las herramientas externas.
4. Separa siempre **Observación** (lo que aparece literal) de **Inferencia** (lo que se deduce) de **Límites** (lo que no se pudo verificar). Un string sin contexto no prueba una función.
5. Salidas en `replica/static/`: `static-report.md` y `hallazgos-*.json` con fuente, confianza y límites.
6. Todo hallazgo que sostenga una decisión lleva fila de `../templates/evidence.md`.

## Gate de salida

- Condiciones de entrada documentadas (quién autorizó y qué artefacto).
- Cada hallazgo con observación, inferencia y límite separados.
- Herramientas ausentes declaradas como límite.
- Cero código, assets o datos del original incorporados al proyecto.

## Handoff

Los hallazgos vuelven a `replica-recon` (fase 1) como evidencia adicional y, si cambian el alcance, reabren la fase mínima afectada.
