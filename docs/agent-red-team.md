# Documentación: Agent Red Team

## Descripción
Módulo de auditoría estática y seguridad ofensiva diseñado para evaluar paquetes de instrucciones, carpetas de agentes y scripts auxiliares antes de su ejecución.

## Componentes
- `SKILL.md`: Protocolo de revisión en 4 fases (escaneo estático, revisión adversarial, saneamiento y emisión de veredicto).
- `references/threat-matrix.md`: Matriz de clasificación de vectores (Unicode tags, esteganografía, exfiltración Markdown y tool squatting).
- `scripts/scan_skill.py`: Escáner estático con parser AST para Python, detección de entropía y patrones de inyección.
- `scripts/sanitize_unicode.py`: Herramienta para desinfectar archivos eliminando caracteres no imprimibles.
- `templates/risk-report.md`: Plantilla para informes estructurados de auditoría.

## Modo de uso
```bash
python agent-red-team/scripts/scan_skill.py --target ./ruta-a-inspeccionar
python agent-red-team/scripts/scan_skill.py --target ./ruta-a-inspeccionar --json
```
