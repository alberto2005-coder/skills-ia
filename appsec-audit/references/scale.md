# Escala: perfiles, coste y proveedores

Consolidar varios repos exige las mismas reglas que auditar uno: alcance escrito, evidencia y límites. Lo que cambia es la unidad de análisis y el precio.

## Perfiles

| Perfil | Cuándo | Qué incluye | Horas base por repo |
|---|---|---|---|
| `quick` | Superficie y semáforo antes de una decisión | Recon, dependencias, CI, informe breve; sin tribunal completo | 6,5 |
| `standard` | Auditoría con informe accionable | Todo lo anterior, threat model, trazado por superficie, tribunal y parches propuestos | 13 |
| `deep` | Sistema crítico o tras un incidente | Añade remediación aplicada, verificación en sandbox y análisis de variantes | 26 |

`scale_report.py` multiplica las horas base por el perfil y por el número de repos, y suma medio punto por tercero a threat model y dependencias.

## Coste

```text
coste_fase = horas_base_fase × multiplicador_perfil × repos × tarifa_horaria
coste_total = Σ coste_fase
```

Con `--cost tarifa.json` (`{"hourly": 95, "currency": "USD"}`) se fija la tarifa; por defecto 80 EUR/h. El informe devuelve horas y coste por fase, no una cifra única: un presupuesto sin desglose no se puede discutir ni recortar con criterio.

Límites: no incluye tiempo del equipo del cliente, ni esperas de acceso, ni remediaciones fuera de alcance; los terceros se estiman por unidad, no por profundidad.

## Inventario multi-repo

- Nombre estable y ruta por repo; sin nombres duplicados.
- Estado explícito: auditado (con artefactos), parcial (artefactos incompletos) o pendiente (sin artefactos).
- Un repo pendiente no aporta hallazgos: aporta superficie y deuda de auditoría.
- Los workflows y dependencias compartidos se auditan una vez y se referencian desde cada repo.

## Checklist de proveedores

| Pregunta | Evidencia aceptable |
|---|---|
| ¿Qué datos trata y para qué? | Contrato de encargo y registro de tratamiento |
| ¿Dónde se alojan y quién accede? | Región, subencargados declarados, control de acceso documentado |
| ¿Qué certificación vigente tiene? | Informe SOC 2 o certificado ISO con fecha y alcance |
| ¿Notifica brechas y en cuánto tiempo? | Cláusula contractual con plazo |
| ¿Qué SLA ofrece y qué pasa si lo incumple? | Contrato con métricas y penalización |
| ¿Puede leer datos sin cifrar o retenerlos? | Arquitectura y política de retención verificables |

Una web comercial no es una certificación. Lo no verificado se escribe como tal en el informe del sistema, y si el proveedor concentra riesgo, se abre una auditoría propia con su autorización.

## Topología

Nodos: `repo:<nombre>` y `vendor:<nombre>`. Aristas: uso declarado de un tercero por un repo, con el dato que cruza. Los terceros sin repo asociado se listan como huérfanos: o falta inventario o sobra dependencia.
