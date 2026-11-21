# Plan de pruebas · {{proyecto}}

- **Fecha:** YYYY-MM-DD
- **Alcance:** <rutas o módulos incluidos>
- **Presupuesto:** <número de tests o de horas>
- **Generado con:** `py test-architect/scripts/plan_tests.py --root . --json`

## Resumen

| Métrica | Valor |
|---|---|
| Módulos analizados | |
| Módulos en el plan | |
| Dominios sensibles | |
| Exclusiones motivadas | |

## Plan priorizado

| # | Módulo | Dominio | Riesgo | Cobertura actual | Test a escribir |
|---|---|---|---|---|---|
| 1 | | | high | ninguna | |
| 2 | | | medium | parcial | |

## Ledger de exclusiones

| Módulo | Motivo | Responsable | Revisión |
|---|---|---|---|
| | Código generado en build | | |
| | Tercero: se dobla, no se prueba | | |

## Contratos a fijar

| Contrato | Proveedor | Consumidor | Fixture |
|---|---|---|---|
| | | | |

## Riesgos y supuestos

- La cobertura se ha inferido por nombre de fichero; {{proyecto}} no publica informe de líneas.
- Los módulos de migración se prueban en integración, no en unidad.

## Gate

- [ ] Cada módulo `high` tiene test asignado o exclusión motivada.
- [ ] El ledger está cerrado y firmado.
- [ ] El plan cabe en el presupuesto acordado.
