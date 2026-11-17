# Informe de auditoría de seguridad — {{proyecto}}

- **Fecha:** {{fecha}}
- **Alcance:** {{rutas, servicios y entornos revisados}}
- **Fuera de alcance:** {{exclusiones explícitas}}
- **Autorización:** {{referencia a la autorización}}
- **Revisor:** {{rol o agente}}
- **Nota global:** **{{A-F}}** ({{puntuación}}/100)
- **Hallazgos:** {{críticos}} críticos · {{altos}} altos · {{medios}} medios · {{bajos}} bajos · {{descartados}} descartados

## Resumen ejecutivo

{{Cinco líneas en lenguaje de negocio: qué se puede perder, qué está expuesto hoy y qué tres acciones van primero. Sin jerga, sin CVE en esta sección.}}

## Hallazgos

| # | Severidad | Hallazgo | CWE | OWASP | Confianza | Ubicación |
|---|---|---|---|---|---|---|
| F1 | Crítica | {{título corto}} | CWE-89 | A03 | 9/10 | `{{ruta:línea}}` |
| F2 | Alta | {{título corto}} | CWE-639 | A01 | 8/10 | `{{ruta:línea}}` |

## Detalle

### F1 — {{título}}

- **Severidad:** crítica · **Confianza:** 9/10 · **CWE-89** · **OWASP A03**
- **Dónde:** `{{ruta:línea}}`
- **Qué pasa:** {{descripción en dos frases, con el dato concreto que se traza}}
- **Impacto:** {{qué consigue un atacante y sobre qué datos}}
- **Vector:**
  1. {{paso 1}}
  2. {{paso 2}}
  3. {{resultado}}
- **Evidencia:** {{fragmento de código o salida de comando, acotado}}
- **Mitigación comprobada:** {{ninguna / parcial: por qué no basta}}
- **Parche:**

```diff
- {{línea vulnerable}}
+ {{línea corregida}}
```

## Descartes

{{N}} candidatos descartados en el tribunal. Motivo dominante: {{mitigación del framework / no alcanzable / no explotable}}. Registro completo en el anexo.

## Límites

- {{qué no se pudo revisar y con qué consecuencia}}
- Análisis estático: no sustituye a prueba dinámica ni a revisión de lógica sin especificación.
