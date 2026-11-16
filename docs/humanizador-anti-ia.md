# Documentación: Humanizador Anti-IA

## Descripción
Módulo para transformar borradores planos o generados por inteligencia artificial en prosa orgánica, fluida y con variabilidad rítmica natural en español.

## Métricas evaluadas
- **Burstiness (Coeficiente de Variación):** Mide la alternancia entre frases cortas (4 a 8 palabras) y oraciones largas subordinadas (22+ palabras).
- **Diversidad léxica (TTR):** Ratio entre palabras únicas y totales.
- **Legibilidad Fernández-Huerta:** Índice cuantitativo adaptado a la fonética y sintaxis del español.
- **Detección de patrones:** Erradicación de guiones largos (—), pasiva analítica innecesaria y muletillas robóticas.

## Componentes
- `SKILL.md`: Directrices obligatorias de edición y reglas de estilo.
- `references/lista-negra.md`: Catálogo de términos sobreutilizados y sus alternativas naturales.
- `references/01-patrones-sintacticos.md`: Explicación de firmas estadísticas y perplejidad.
- `references/02-tecnicas-reescritura.md`: Técnicas de staccato, inversión sintáctica y corte en seco.
- `scripts/audit_style.py`: Script de evaluación con soporte de salida en texto, JSON y Markdown.
- `templates/informe-auditoria.md`: Plantilla de análisis comparativo antes/después.

## Modo de uso
```bash
python humanizador-anti-ia/scripts/audit_style.py --text "Texto a evaluar..."
python humanizador-anti-ia/scripts/audit_style.py --file documento.md --markdown
```
