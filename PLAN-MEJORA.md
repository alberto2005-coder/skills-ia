# Plan personalizado de búsqueda y mejora por skill

> **Objetivo:** que cada skill de este repositorio haga *lo mismo* (o mejor) que los repos famosos de su categoría, manteniendo la filosofía del repo: **cero dependencias, solo stdlib de Python, determinismo, estructura estándar**.
>
> **Regla del plan:** primero busco y analizo los referentes; luego te traigo un diff concreto (qué copio, qué adapto, qué descarto) **por skill**; tú lo apruebas; solo entonces toco archivos.
>
> ⚠️ Las cifras de estrellas son aproximadas y vienen de artículos de terceros: verificar en GitHub antes de citarlas.

---

## Fase 0 — Verificación base (antes de tocar nada)

| # | Tarea | Por qué |
|---|-------|---------|
| 0.1 | **Procedencia de `replica/`: trabajo original de este repositorio**, no una adaptación de `Jakeschincariol/replica-skill` ni de ningún otro. Anotarlo en `docs/benchmark/` para que no se replantee. Las ideas de referentes se anotan como "funcionalidad tomada de X", sin código. | Trazabilidad: saber qué es propio y qué es prestado |
| 0.2 | Leer la **Agent Skills spec oficial** (`anthropics/skills` → `/spec` y `/template`) y validar los 4 `SKILL.md` (frontmatter `name`/`description`, límites de tamaño, progressive disclosure) | Todas las skills del ecosistema siguen ese formato |
| 0.3 | Inventario de los scripts actuos: ¿tienen tests? (referentes traen `tests/`; nosotros no) | Un gate rojo sin tests no es confiable |
| 0.4 | Crear `docs/benchmark/` donde guardar el análisis de cada referente (qué tiene la skill, qué nos falta) | Trazabilidad de por qué cambia lo que cambia |

**Búsqueda transversal (herramientas de descubrimiento de skills):**
- `ComposioHQ/awesome-claude-skills` (~78k ★) — amplitud
- `travisvn/awesome-claude-skills` (~15k ★) — lista corta y curada
- `jqueryscript/awesome-agent-skills` — directorio ordenado por estrellas
- `anthropics/skills` (~190k ★) — spec oficial + `skill-creator`
- `skills.sh` — registro para publicar después

---

## Fase 1 — `replica/` (la de ingeniería inversa) → igual que **morluto/rea**

**Referente principal:** `morluto/rea` — *"Reverse Engineer Anything"*, ~465k ★, MCP + CLI + skill `reverse-engineer-anything`, MIT.
**Referentes secundarios:**
- `Jakeschincariol/replica-skill` — skill de referencia de la comunidad (11 skills, scripts de nombre similar); **no es origen de la nuestra**, solo comparatoria
- `aldushmedia/clonar` — versión española de las mismas 11 skills + comando maestro `/clonar`
- `EncidXVII/claude-reverse-engineering-skill` — 14 playbooks, evals de trigger, CI con Ghidra

### Qué hace REA y nosotros no (lo que hay que igualar)

| Capa | REA | `replica/` actual | Acción |
|------|-----|-------------------|--------|
| **Formato de evidencia** | Devuelve `evidencia · mapa · límites · desconocidos` y separa **observación / inferencia / no resuelto** en cada conclusión | No impone un formato de hallazgo | **Nuevo** `references/01b` o plantilla `evidence.md` con las 4 columnas; obligatorio en fase 1 (recon) y 7 (paridad) |
| **Alcance incremental** | *"Elige una función, no la app entera"* — método de 5 pasos; análisis completo → resumen → módulo → función | Recon de app completa de golpe | Añadir **paso 0 de foco** en `01-recon.md`: una función observable y medible por iteración |
| **No repetir análisis** | Guarda el resultado y vuelve a él (`detail: summary` / `full`) | Cada fase relee todo | Regla de **caché de análisis**: si `recon.md` existe, se reutiliza; solo se refina |
| **Límites de uso** | DISCLAIMER.md + *"REA no es para repos con código fuente completo: usa tus herramientas normales"* + uso autorizado | Reglas duras de clean-room ya presentes | **Completar** con: nada de DRM/paywall/logins ajenos, análisis solo de binarios/apps que te pertenezcan o estén autorizados |
| **Profundidad de análisis** | Bajo nivel: strings, imports, IPC, esquemas, APK/JS/.NET | Solo observación de UI y fichas públicas | Nueva referencia `12-analisis-estatico.md` **opt-in**: si hay `app.asar`/APK/JS legible *obtenido legalmente*, guía de extracción de strings/rutas/endpoints con scripts stdlib (grep determinista). Se puede usar Ghidra/JADX/objdump **si el usuario los tiene**: la skill los orquesta, no los instala (igual que REA con Hopper/Ghidra/IDA) |
| **Evidencia con límites** | *"Cada conclusión con evidencia y limitaciones"* | Cero datos inventados ya existe | Reforzar: todo hallazgo lleva `fuente` + `confianza` + `qué no pude verificar` |
| **Empaquetado** | `.claude-plugin`, `.codex-plugin`, plugins multiagente | Solo carpetas | **Hecho, genérico y multi-skill:** índice `skills.json` raíz + `skills.json` por carpeta (array de skills), sin manifiestos de proveedor |
| **Tests** | `tests/` + mutation testing | Sin tests | `tests/` para `parity.py`, `sweep.py`, `imgdiff.py`, `contrast.py`, `reviews.py`, `listing.py` |

### De `aldushmedia/clonar` (habla español, muy cercano a nosotros)
- ✅ **Comando maestro** `/replica` que recorre las 12 fases en orden y pide aprobación al final de cada una → `progreso.md` con estado retomable.
- ✅ `paises.md` localizado: métodos de pago, moneda, facturación electrónica y atención por WhatsApp **por país**.
- ✅ Fase **`redes`** (guiones de Reels/captions) — nos falta (ellos tienen 12, nosotros 11).
- ✅ Tests con **patrones en español**.

### De `EncidXVII/claude-reverse-engineering-skill`
- `evals/`: tests de *trigger* (¿se activa la skill con las frases correctas?) y de comportamiento.
- CI que lintkea el frontmatter.

**Salida Fase 1:** diff aprobado + lista de ficheros a crear/modificar.

---

## Fase 2 — `agent-red-team/` → igual que **cloudflare/security-audit-skill**

**Referentes:**
| Repo | Qué aporta |
|------|------------|
| `cloudflare/security-audit-skill` (~11.6k ★, MIT) | 6 fases, **coverage ledger**, verificación independiente de hallazgos, esquema JSON, modos *guidance* vs *full audit* |
| `screem500/prompt-injection-auditor` (Apache-2.0) | Catálogo de ataques + checklist de defensa + **validación medida** (8.3 → 43.3 pts, 0 falsos positivos) |
| `ki-stuff/skill-auditor` (MIT) | Nivel **REJECT** por *combinación* de patrones; ignorar patrones dentro de code fences |
| `aliksir/claude-code-skill-security-check` | 26 categorías, salida **SARIF**, revisión multi-agente |
| `NovaCode37/claude-security-skills` | Todo stdlib (¡encaja con nuestra filosofía!), usable como paso de CI |
| `mukul975/Anthropic-Cybersecurity-Skills` | Catálogo de skills oficiales de ciberseguridad |

### Mejoras propuestas
1. **Modos de operación** (patrón Cloudflare): *guidance* por defecto (consultas puntuales) vs *auditoría completa* solo si el usuario lo pide explícitamente. Evita que la skill cree archivos sin permiso.
2. **Verificación independiente**: cada candidato pasa por un "verificador nuevo" que intente *refutarlo* antes de marcarlo `confirmed`. Reduce falsos positivos (motivo nº1 de desconfianza en estas skills).
3. **Coverage ledger** (`coverage-ledger.json`): qué superficies ya se cubrieron, para no repetir y para detectar huecos.
4. **Esquema de salida** (`report-schema.json`): `confirmed | needs_validation | rejected` + severidad. Añadir salida **SARIF** opcional para la pestaña Security de GitHub.
5. **Escala REJECT**: combinaciones que fallan siempre (leer `.ssh` + enviar por `curl` en el mismo fichero).
6. **Excepción de code fences**: un patrón documentado dentro de ``` no es una inyección viva.
7. **Catálogo de ataques** con payloads educativos y checklist de defensa (patrón `prompt-injection-auditor`), basado en incidentes reales (EchoLeak CVE-2025-32711).
8. **Tests con fixtures**: `/tests/fixtures` con skills maliciosas de ejemplo y corpus endurecido.

---

## Fase 3 — `humanizador-anti-ia/` → igual que **blader/humanizer**

**Referentes:**
| Repo | Qué aporta |
|------|------------|
| `blader/humanizer` (~63k ★, MIT) | 26 patrones **ordenados de más fuerte a más débil**, basado en *Wikipedia: Signs of AI writing*; "muestra tu trabajo" (primer rewrite → crítica → final); no tocar código/enlaces/datos |
| `Aboudjem/humanizer-skill` (MIT) | **55 patrones** + puntuación **0–100** calculada de 4 señales medibles, no del recuento |
| `keez97/humanizer` | Prioriza los patrones **estructurales** (párrafos intercambiables, frases todas de 20 palabras) sobre el cosmético; honestidad sobre lo que no puede hacer |
| `shir-danishyar/humanize` | **Registro** (email vs LinkedIn vs artículo), calibración de voz, linter stdlib para CI |
| `Aparnabuilds/humanizer` | Vocabulario **por niveles** (Tier 1 se cambia al instante, Tier 3 solo por densidad) + **honestidad factual** (no inventar datos) |
| `duathron/humanizer-ext` | Soporte multi-idioma con packs por idioma — aquí: **pack en español** |
| `zhuyansen/awesome-humanizer-skills` | Directorio de 283 repos de esta familia, con tests ejecutados |

### Mejoras propuestas
1. **Catálogo numerado y jerarquizado** en `references/`: patrones de fuerte a débil (como blader) y con **pares antes/después**, no solo descripción.
2. **Pack en español**: los referentes son casi todos en inglés; nuestro valor diferencial es detectar los tells **en español** (muletillas, "en el panorama actual", "sumérjete", "no solo X sino Y", em-dash, cierre moral, estructura de horaarena). Adaptar también *Wikipedia: Signos de escritura con IA* (versión ES).
3. **Puntuación 0–100 determinista** en `audit_style.py`: separar en 4 señales (densidad de vocabulario, varianza de longitud de frase/burstiness, patrones estructurales, artefactos de chatbot) — igual que Aboudjem, *una puntuación que se puede reproducir*.
4. **Modos** Quick / Full / Voice (como `humanizer-ext`): Voice calibra contra 2–3 párrafos de escritura del usuario.
5. **Registro**: detectar si es post de LinkedIn, email, artículo o informe formal y ajustar qué significa "humano" en cada caso.
6. **Regla de honestidad**: si el texto tiene una estadística sin fuente, se marca en vez de reescribirla (patrón Aparnabuilds).
7. **Protección de estructura**: no tocar código, frontmatter, enlaces ni datos (patrón blader).
8. **Corpus de tests** ES + EN con textos sintéticos de IA y textos humanos, para verificar que el detector separa (falsos positivos = fallo).

---

## Fase 4 — `seo-auditor/` → igual que **seo-skills/geo-audit-skill**, **wishfy-ai** e **IndexPulse**

**Referentes:**
| Repo | Qué aporta |
|------|------------|
| `seo-skills/geo-audit-skill` / `geo-audit-skill` (MIT) | *"Cada número es reproducible de la evidencia registrada"*; CLI computa, el modelo explica; `--rescore` **sin red**; envelope schema congelado |
| `wishfy-ai/google-seo-geo-aeo-audit-skill` (MIT) | Cada hallazgo **cita el doc oficial**; severidad MUST/SHOULD/NICE; veredicto en una línea; `audit.json` + `audit.md` |
| `yanivgoldenberg/seo-geo-skill` | Rúbrica de **100 puntos en 6 dimensiones**, benchmark público, escrituras con **dry-run** |
| `Cognitic-Labs/geoskills` | Partición en 6 skills: audit / fix-content / fix-schema / fix-llmstxt / **compare** / **monitor** |
| `mykpono/ultimate-seo-geo` | 3 modos: **Audit → Plan → Execute** |
| `umutxyp/Seo-Promt-Master` | Base de conocimiento citada (Google/Bing/official docs) |
| `coreyhaines31/marketingskills` | Framework de SEO audit del que se adaptan muchas skills |

### Mejoras propuestas
1. **Rúbrica 0–100 con dimensiones** (técnico / contenido / schema / GEO / E-E-A-T) y **veredicto en una línea**: `Not Ready / Competitive / Leading` — nada de consejos sin nota.
2. **Cada comprobación con cita**: id estable + severidad `must/should/nice` + URL del doc de Google/Bing que la respalda.
3. **Evidencia reproducible**: `audit.json` (máquina) + `audit.md` (persona), y **re-score offline** (`--rescore`) sin volver a tocar la red.
4. **Modos Audit → Plan → Execute** con escrituras en **dry-run** por defecto (nada se escribe en el sitio sin `--apply` + confirmación).
5. **Capa GEO avanzada** que nos falta: `llms.txt`, allow-list de crawlers por motor (`OAI-SearchBot`, `ClaudeBot`, `PerplexityBot`, `GPTBot`), separando **search / user-fetch / training**; E-E-A-T (autor, fechas, `sameAs`); bloques de respuesta de 134–167 palabras.
6. **`compare` / `monitor`**: diff entre dos auditorías para medir lo que cambió tras un deploy.
7. **Crawl respetuoso**: robots.txt en cada link, 1 req/s, tope de páginas declarado en el informe.
8. **CI opcional**: GitHub Action que publique snapshots (como yanivgoldenberg).

### 4.b — Módulos de **IndexPulse** (`alberto2005-coder/gestion_web`) a igualar

> ✅ **Licencias:** fuera de la mesa, ya está resuelto — no se tramita ni se condiciona nada por licencias de ningún repo (`gestion_web`, `morluto/rea` ni ninguno).
> 📌 **Criterio de código:** **mismas funciones, nunca el mismo código.** La base es **`gestion_web` (IndexPulse), de Alberto, mejorado**: se parte de su lógica y se lleva a `seo-auditor/` (reescrita en Python stdlib para encajar con "cero dependencias", ya que IndexPulse va con Express/Node). De los demás referentes (`rea`, `geo-audit-skill`, `blader/humanizer`…) se toman **ideas y funcionalidades**, no líneas de código.

| # | Módulo IndexPulse | Nuestro equivalente nuevo (stdlib) | Notas |
|---|-------------------|-------------------------------------|-------|
| 1 | **Diagnóstico de indexación**: presencia en Google/Bing/DuckDuckGo/Yahoo/Yandex | `scripts/indexcheck.py` — consulta `site:`/endpoint público por motor, marca `THIN` si el motor no deja comprobarlo de forma fiable | Nunca inventar "indexada/no indexada" sin evidencia |
| 1b | **Directivas técnicas**: robots.txt (Disallow/Allow), `<meta robots>`, cabecera `X-Robots-Tag`, `<link canonical>`, detección de sitemap | Ampliar `audit.py` / `01-tecnico.md` con las 5 comprobaciones cruzadas (p. ej. `noindex` en meta pero `X-Robots-Tag` limpio = conflicto) | Todas reproducibles desde la respuesta HTTP guardada |
| 2 | **Simulador SERP en vivo**: Google escritorio (favicon, migas, medidor de píxeles ~580 px), Google móvil, Bing, **tarjetas sociales** (OG + Twitter → WhatsApp/Facebook/LinkedIn/X) | `scripts/serp.py` → genera `serp/preview.html` (autocontenido, sin JS externo) con medidor de ancho de título/descripción y aviso de truncamiento; incluye editor con dos flag `--title` / `--description` para iterar | Estimación de píxeles con métrica de fuente aproximada, etiquetada `estimate` |
| 3 | **Velocidad y Core Web Vitals**: puntuación 0–100, LCP/FCP/CLS/TBT/TTFB/Speed Index, crawl budget, inventario de recursos | `scripts/perf.py`: TTFB, peso HTML, compresión Gzip/Brotli, nº de CSS/JS externos, latencia Googlebot/Bingbot (User-Agent propio) → **medido**. CWV reales (LCP/CLS/TBT/Speed Index) solo con `--pagespeed` (API pública, **opt-in**) o enlace a PSI; sin API → `ESTIMATE`, jamás un número inventado | Coherente con la regla "cero datos inventados" |
| 4 | **Auditoría de seguridad HTTP**: score 0–100, HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, mixed content | `scripts/headers.py` → score reproducible + severidad por cabecera ausente/mal configurada + detección de recursos HTTP en páginas HTTPS | Encaja con la sección "seguridad" que ya tiene el `seo-audit-skill` de SEOmator |
| 5 | **Schema.org / Rich Snippets**: inspector JSON-LD (lista todos los `@type`) + simulador de resultados enriquecidos (estrellas `AggregateRating`, precio/stock `Offers`, `FAQPage`) | Ampliar `references/04-schema.md` + `scripts/schema.py` → inventario JSON-LD + `rich-preview.html` con lo que Google *podría* mostrar y qué falta para ello | |
| 6 | **SEO internacional `hreflang`**: detección, validación de pares, autorreferencia, `<html lang>` | Ampliar `references/01-tecnico.md` con checklist de pares hreflang (falta retorno, idioma mal escrito, sin `x-default`) | |
| 7 | **Auditoría on-page exhaustiva**: score 0–100, recuento de palabras y ratio texto/HTML, jerarquía `<h1>`–`<h4>` (H1 ausente/duplicado), imágenes sin `alt` con galería de muestra, **densidad de palabras clave** con tabla | Ampliar `02-contenido.md` + `scripts/content.py` (o extender `audit.py`): ratio, jerarquía de encabezados, tabla de densidad de keywords | La galería visual de imágenes sin `alt` se simplifica a lista de rutas (sin render) |
| 8 | **Checklist unificada + exportación PDF**: todos los fallos (indexación, SEO, seguridad, velocidad, schema) con filtros 🔴 crítico / 🟡 aviso / 🟢 aprobado | `templates/audit-report.md` + `scripts/report.py` → informe unificado con mapeo `must→🔴 / should→🟡 / nice→🟢` y salida **`report.html` imprimible** (el usuario hace "Imprimir → PDF", igual que IndexPulse) | Generar PDF real exigiría librerías → violaría cero dependencias; el HTML print-friendly cumple lo mismo |

**Comprobación final de la Fase 4:** ejecutar la auditoría sobre la misma URL que IndexPulse y verificar que cubrimos los mismos 8 bloques (checklist de paridad, igual que `parity.py` hace con features).

---

## Fase 5 — Empaquetado y publicación (transversal)

1. **Empaquetado genérico multi-skill** (hecho): índice raíz `skills.json` + manifiesto `skills.json` dentro de **cada carpeta**, con **array `skills`** — una carpeta aloja 1 o N skills sin cambiar el formato. Formato propio vendor-neutral: sirve para Claude, Codex, Cursor, Gemini, OpenCode… **Sin manifiestos `.claude-plugin`**. Descubrimiento básico igual posible escaneando `**/SKILL.md`.
2. Tests stdlib para **todos** los scripts + CI (frontmatter lint + ejecución en Win/mac/Linux).
3. README bilingüe actualizado con tabla de módulos y "qué hace de verdad" cada script.
4. Trazabilidad en `CHANGELOG`/`docs/benchmark/` de qué funcionalidad viene de qué proyecto (sin código ajeno).
5. `CHANGELOG.md` por skill con la versión de la mejora.
6. Opcional: publicar en `skills.sh` para descarga con `npx skills add`.

---

## Orden de ejecución y esfuerzo estimado

| Orden | Fase | Skills | Dificultad |
|-------|------|--------|-----------|
| 1 | Fase 0 — verificación base | todas | Baja |
| 2 | **Fase 1 — replica (la prioritaria)** | `replica/` | **Alta** |
| 3 | Fase 2 — red team | `agent-red-team/` | Media |
| 4 | Fase 3 — humanizador | `humanizador-anti-ia/` | Media |
| 5 | Fase 4 — SEO | `seo-auditor/` | Media |
| 6 | Fase 5 — empaquetado | todas | Baja |

## Qué NO voy a hacer sin tu visto bueno
- Copiar código de ningún referente: **mismas funciones, código propio**. La base de mejora es `gestion_web`; de `rea` y demás solo ideas y funcionalidades. (Licencias: ya resuelto, no se contempla.)
- Romper la regla de **cero dependencias** (si un referente usa `playwright`, `Lighthouse` o APIs de terceros, se queda como *opt-in* documentado, nunca como requisito).
- Ejecutar scripts de repos de terceros fuera de una carpeta temporal aislada.
- Nada que vaya contra las **reglas duras de clean-room** de `replica/`.

---

## Confirmación pendiente de ti
1. ¿Empiezo por la **Fase 0 + Fase 1 (`replica`)**, que es la que pediste con `morluto/rea`?
2. ¿Quieres que en la Fase 1 incluya el **comando maestro `/replica` + `progreso.md`** (idea de `clonar`) o lo dejamos aparte?
3. ¿Acepto añadir la fase **12 "análisis estático opt-in"** (usa jadx/Ghidra/objdump si el usuario ya los tiene), o prefieres mantener la skill puramente de UI/observación?
