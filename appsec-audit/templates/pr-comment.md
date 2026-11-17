## Auditoría de seguridad — {{PR o commit}}

**Resultado:** {{bloquea / no bloquea}} · **Perfil:** {{quick / standard / deep}} · **Nota:** {{A–F}} ({{puntuación}}/100)

{{Una frase: qué cambia en riesgo con este PR y qué hay que hacer antes de fusionar.}}

### Nuevos en este PR

| # | Severidad | Hallazgo | CWE | Ubicación | Confianza |
|---|---|---|---|---|---|
| F-00x | {{crítica}} | {{título}} | CWE-{{xxx}} | `{{ruta:línea}}` | {{7-10}}/10 |

### Frente al baseline

| Estado | Nº | Detalle |
|---|---|---|
| Nuevos | {{n}} | {{ids}} |
| Corregidos | {{n}} | {{ids}} |
| Persistentes | {{n}} | {{ids}} |

### Workflow y herramientas

- Herramientas detectadas: {{semgrep, trivy, …}} · Ausentes: {{…}}
- Hallazgos del workflow: {{n}} ({{crítica}} crítico(s)) — {{regla y línea}}
- SARIF: {{subido a cloud scanning con upload-sarif / no aplica}} · Normalizados: {{n}} como `needs_validation`

### Límites

- {{qué no se pudo revisar: herramienta ausente, superficie fuera del diff, entorno no reproducible}}

### Cómo reproducirlo

```bash
py appsec-audit/scripts/normalize_sarif.py {{sarif}} --fail-on {{high}}
py appsec-audit/scripts/scale_report.py --repos {{nombre}}={{ruta}} --profile {{perfil}}
```

{{Si bloquea: qué parche lo cierra y quién lo aprueba. Si no bloquea: qué queda pendiente y para cuándo.}}
