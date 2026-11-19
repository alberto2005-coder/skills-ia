# 12 · Análisis estático (opt-in)

Objetivo: extraer **observables** (strings, rutas, endpoints, APIs, imports) de binarios o bundles que **te pertenecen o estén autorizados**, para alimentar la evidencia del recon y de la paridad.

> **Fase OPT-IN.** No entra sola en el pipeline: solo se ejecuta si el usuario la pide **y** se cumplen las dos condiciones de "Entradas". Si no se cumplen, se dice claramente *"análisis estático no disponible"* y **la skill se queda en la fase de observación de UI** (fase `01-recon.md`). Esta fase **no** sustituye nunca a la observación de comportamiento: complementa.

## Entradas (las dos, obligatorias)

1. **Binario/app de tu propiedad o autorizado legalmente**, ya en disco: `app.asar`, JS extraído de un bundle, APK, fichero `.exe`/`.so`, etc. Descargado o extraído por el usuario con su licencia en regla.
2. **Herramientas ya instaladas por el usuario** (`jadx`, `ghidra`, `objdump`, `apktool`, `strings`). La skill **las detecta, no las instala, no las descarga, no compila nada**.

## Cuándo NO usar esta fase

- **Hay código fuente completo** (repo propio, SDK público, source maps): usa las herramientas normales del agente (leer, buscar, editar). Esta fase es para cuando *no* hay fuente legible.
- Faltan las condiciones de arriba → se responde "no disponible" y se continúa en observación de UI.
- El objetivo es extraer **código para copiarlo**: prohibido (ver "Reglas duras" más abajo y `00-limites.md`).
- El software es de terceros **sin autorización**.

## Reglas duras de esta fase

1. **Nada de DRM ni protecciones técnicas.** No se descifra, no se desempaqueta lo que está cifrado, no se eluden verificaciones de licencia, firmas ni activación.
2. **Nada de saltarse logins, paywalls o límites.** Si el contenido solo se ve tras un pago o una sesión, ahí no se entra.
3. **Nada de credenciales ajenas.** Ni compartidas, ni adivinadas, ni extraídas de nadie.
4. **Análisis solo de software propio o autorizado.** Si hay duda sobre la autorización, no se ejecuta esta fase.
5. **Clean-room intacto:** lo que se saca del binario son **hechos observables** (una ruta, un string, un import). El código descompilado o el smali **no se copian ni se pegan** en el proyecto; se citan como evidencia con su fuente.
6. **Formato de evidencia obligatorio** (ver "Salida"): Observación · Inferencia · Límites siempre separados, con `templates/evidence.md`.

## Paso 1 · Detección (sin instalar nada)

`shutil.which` de stdlib: si no está, no está. Ejecuta la comprobación y di el resultado en voz alta:

```bash
py -c "import shutil; print({n: shutil.which(n) for n in ['strings','jadx','apktool','analyzeHeadless','objdump']})"
```

Salida esperada (ejemplo):

```text
{'strings': 'C:\\Program Files\\Git\\usr\\bin\\strings.EXE', 'jadx': None, 'apktool': None, 'analyzeHeadless': None, 'objdump': '...'}
```

- Las que devuelven `None` **no se usan** y se anotan como "no disponible" en el informe (con la lista exacta de las que faltan).
- **Nunca** se instala, se descarga ni se compila una herramienta para esta fase; tampoco se propone `pip install`.
- Antes de invocar cualquiera, se pide su ayuda (`<herramienta> --help` o `-help`) para confirmar los flags de **esa** versión instalada: los comandos de la tabla son orientativos y la skill no inventa flags.

### Qué devuelve cada herramienta y hasta dónde llega cada conclusión

| Herramienta | Cómo se detecta | Comando orientativo | Qué devuelve | Qué **NO** prueba (limitación) |
|---|---|---|---|---|
| `strings` | `shutil.which("strings")` | `strings -a -n 8 <fichero>` | Cadenas ASCII embebidas (textos, rutas sueltas, mensajes) | Una cadena puede ser de una librería, un recurso o un mensaje muerto: no prueba que exista esa función ni que se use en tu flujo |
| `extract.py` (stdlib, siempre disponible) | va incluida (Paso 2) | `py extract.py <fichero>` | strings + URLs + rutas + endpoints + emails en JSON ordenado | Solo texto **plano** visible; nada ofuscado, comprimido o cifrado; sin contexto de ejecución |
| `apktool` | `shutil.which("apktool")` | `apktool d <apk> -o <dir>` | `AndroidManifest.xml`, recursos, smali | El manifest es autoridad para permisos/componentes; el smali no dice la *intención* ni nada del backend remoto |
| `jadx` | `shutil.which("jadx")` | `jadx -d <dir> <apk>` | Manifest, recursos y código de Java/Kotlin descompilado | El descompilado es **observación**, no fuente para copiar; identificadores ofuscados/traducidos; no refleja el comportamiento en runtime |
| `objdump` | `shutil.which("objdump")` | `objdump -p <fichero>` (imports) | Secciones, imports/exports, desensamblado (ELF/Mach-O/PE según build) | Un import no prueba que la función se llame en tu flujo; no ve cadenas dinámicas ni lógica resuelta en runtime |
| `ghidra` (headless) | `shutil.which("analyzeHeadless")` | `analyzeHeadless <proyecto> <nombre> -import <fichero>` (confirmar con `-help`) | Descompilado C, símbolos, referencias cruzadas | Análisis de una imagen estática; sin símbolos es lento e incierto; nada de comportamiento en runtime ni de APIs remotas |

**Limitaciones de cada conclusión (techo de confianza):**

| Conclusión que quieres sacar | Confianza máxima razonable | Por qué |
|---|---|---|
| "Este fichero contiene la cadena X" | `high` | Reproducible: `extract.py`/`strings` lo devuelven igual siempre |
| "La app declara la ruta /api/v3/checkout" | `medium` | Es observación de texto en el bundle; no prueba que exista ese endpoint en el servidor |
| "La app declara el permiso CAMERA / usa el SDK Y" | `high` (manifest) / `medium` (SDK) | El manifest es fiable; un SDK embebido puede no estar activo en tu flujo |
| "Este bloque de código hace X" (desensamblado) | `low` | Requiere seguir llamadas y validar en runtime; casi siempre hay explicaciones alternativas |
| "El original funciona igual que lo que vi en UI" | `medium` con evidencia cruzada | Hace falta contrastar con la observación de la fase 01 |
| "Esta funcionalidad es viable en mi clon" | `medium` | Muestra técnica, no negocio: sigue sin decirte si conviene |

## Paso 2 · Extracción determinista con stdlib

Guarda este script como `replica/static/extract.py` (solo stdlib, 3.9+, sin red, salida determinista: listas únicas ordenadas) y ejecútalo sobre cada fichero:

```python
#!/usr/bin/env python3
"""extract.py - Observables estaticos de un fichero (strings, rutas, endpoints, APIs).

Solo stdlib, sin red. Salida deterministica: claves ordenadas, listas unicas
ordenadas y recortadas a MAX_POR_LISTA.

Uso:
    py extract.py app.asar
    py extract.py bundle.js --out hallazgos-bundle.json
    py extract.py app.apk --json --min-string 8

Codigos de salida: 0 ok, 2 error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAX_BYTES = 50_000_000
MAX_POR_LISTA = 500

PATRONES = [
    ("urls", re.compile(rb"https?://[^\s\"'<>]{4,300}")),
    ("endpoints", re.compile(rb"(?<![\w/])/(?:api|v[0-9]+|graphql|rest)(?:/[A-Za-z0-9._\-]{1,60}){1,6}")),
    ("rutas", re.compile(rb"(?<![\w/])/(?:[A-Za-z0-9._\-]{1,60}/){2,}[A-Za-z0-9._\-]{1,60}")),
    ("emails", re.compile(rb"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.\-]{1,64}\.[A-Za-z]{2,24}")),
]
def recortar(texto: str) -> str:
    return texto.strip().rstrip(".,;:)]}'\"")


def extraer(data: bytes, min_string: int) -> dict:
    hallazgos = {}
    for nombre, patron in PATRONES:
        vistos = set()
        for m in patron.finditer(data):
            valor = recortar(m.group(0).decode("utf-8", errors="replace"))
            if valor:
                vistos.add(valor)
        lista = sorted(vistos)
        hallazgos[nombre] = {"total": len(lista), "valores": lista[:MAX_POR_LISTA]}

    rx = re.compile(rb"[\x20-\x7e]{" + str(min_string).encode() + rb",}")
    strings = {recortar(m.group(0).decode("utf-8", errors="replace")) for m in rx.finditer(data)}
    strings = sorted(s for s in strings if s)
    hallazgos["strings"] = {"total": len(strings), "valores": strings[:MAX_POR_LISTA]}
    return hallazgos


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Observables estaticos (strings, rutas, endpoints) de un fichero.")
    parser.add_argument("fichero")
    parser.add_argument("--out", help="Escribir JSON en este fichero")
    parser.add_argument("--json", action="store_true", help="Imprimir JSON en stdout")
    parser.add_argument("--min-string", type=int, default=8, help="Longitud minima de string (def. 8)")
    args = parser.parse_args(argv)

    try:
        with open(args.fichero, "rb") as fh:
            data = fh.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            print(f"[x] {args.fichero}: mas de {MAX_BYTES} bytes, no se analiza.", file=sys.stderr)
            return 2
    except OSError as exc:
        print(f"[x] No se pudo leer {args.fichero}: {exc}", file=sys.stderr)
        return 2

    resultado = {
        "fichero": args.fichero,
        "bytes": len(data),
        "min_string": args.min_string,
        "recorte": MAX_POR_LISTA,
        "hallazgos": extraer(data, args.min_string),
    }
    texto = json.dumps(resultado, ensure_ascii=False, indent=2, sort_keys=True)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(texto + "\n")
        print("[+] Escrito en " + args.out)
    if args.json or not args.out:
        print(texto if args.json else "[*] Resumen:")
        if not args.json:
            for nombre in sorted(resultado["hallazgos"]):
                print("    %-12s %5d" % (nombre, resultado["hallazgos"][nombre]["total"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Notas de determinismo: mismo fichero → mismo JSON (orden de claves y de valores fijo); `total` guarda el recuento real aunque `valores` esté recortado a 500; el recorte se declara, no se esconde.

## Paso 3 · Evidencia obligatoria

Cada hallazgo va con el formato `templates/evidence.md`:

- **Fuente:** ruta del fichero + herramienta usada (`extract.py`, `strings`, `apktool`…) + fecha.
- **Observación:** el hecho literal ("el bundle contiene la cadena `/api/v3/checkout`").
- **Inferencia:** la deducción, marcada como tal ("se deduce que la app consume una API versionada") — nunca dentro de la casilla de observación.
- **Confianza:** `high` / `medium` / `low` / `THIN` según la tabla "Limitaciones de cada conclusión". Si una conclusión solo es `low`, se escribe `low` y no se usa como justificación de arquitectura.
- **Límites y desconocidos:** qué no se pudo ver (ofuscación, backend, versión del binario…).

## Salida

Todo en `replica/static/`:

```text
replica/static/
├── static-report.md        # informe principal (usa templates/evidence.md + cierre Mapa · Límites · Desconocidos)
├── extract.py              # el extractor stdlib (si se usó)
├── hallazgos-<fichero>.json  # salida cruda determinista por fichero
└── raw/                    # volcados de las herramientas externas (strings.txt, manifest.xml…)
```

`static-report.md`:

```markdown
# Análisis estático: <App>  (opt-in)
## Condiciones        (binario de qué es / autorización · herramientas detectadas con shutil.which · cuáles NO están)
## Hallazgos          (tabla evidence.md: Fuente · Observación · Inferencia · Confianza · Límites)
## Mapa               (qué observables quedan cubiertos y en qué fase se usan)
## Límites            (qué NO demuestra este análisis; ver tabla de limitaciones)
## Desconocidos       (preguntas abiertas → cómo se responderían desde UI o backend propios)
## Herramientas       (cuál se ejecutó, cuál no estaba disponible y por qué)
```

Si **no** se cumplen las condiciones, no se crea `replica/static/`: se anota en `recon.md` una línea *"análisis estático no disponible (falta X)"* y se continúa en observación de UI.

## Checklist

- [ ] Las dos condiciones de Entradas se cumplen y se documentan (binario con autorización + herramientas detectadas).
- [ ] Ninguna herramienta se instaló ni se descargó; las `None` de `shutil.which` se declaran como no disponibles.
- [ ] El código descompilado/smali no ha ido a parar al proyecto: solo hechos en forma de evidencia.
- [ ] Cada hallazgo usa `templates/evidence.md` con las 5 columnas y el cierre Mapa · Límites · Desconocidos.
- [ ] Ninguna conclusión tiene confianza mayor que la que permite su tabla de limitaciones.
- [ ] `extract.py` se ejecutó sin red y su JSON es reproducible (mismo fichero → mismo resultado).

## No hagas

Instalar herramientas, tocar DRM o cifrados, saltarte un login o un paywall, usar credenciales ajenas, copiar código descompilado al proyecto, o presentar una cadena encontrada en un binario como una "función confirmada". Si hay código fuente completo, esta fase sobra: usa las herramientas normales del agente.
