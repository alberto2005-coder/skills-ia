---
name: appsec-scale
description: >
  Auditoría a escala: varios repositorios en una sola pasada, inventario y
  auditoría de proveedores, topología del sistema con sus terceros, perfiles
  quick, standard y deep, y estimación de coste por fase con horas y tarifa.
  Consolida los artefactos de cada repo en un informe de sistema. Úsala cuando
  pidan auditar una organización, comparar varios repos, revisar proveedores o
  presupuestar una auditoría.
  English: multi-repo audit with vendor inventory, system topology, profiles
  and a per-phase cost estimate.
license: MIT
metadata:
  package: appsec-audit
  version: "2.1.1"
  author: "Alberto Ortiz"
---

# AppSec · Escala: multi-repo, proveedores y coste

Auditar diez repos como diez auditorías sueltas produce diez informes incompatibles y ninguna vista del sistema. Esta fase consolida y pone precio antes de empezar.

## Precondiciones

- Artefactos por repo: `.appsec-audit/findings.json` y `coverage-ledger.json` de cada auditoría individual.
- Inventario de terceros con qué servicio prestan y qué datos tratan.
- Perfil acordado y tarifa horaria, o el coste será una cifra inventada.

## Método

1. **Inventario.** Un nombre y una ruta por repo; el informe marca cuáles tienen artefactos y cuáles solo superficie pendiente.
2. **Topología.** Cada tercero se enlaza a los repos que lo usan; los que no aparecen en ningún repo quedan como huérfanos y se revisan aparte.
3. **Proveedores.** Por tercero: certificaciones, datos tratados, subencargados, notificación de brecha y SLA. Lo que no se pueda verificar se declara.
4. **Perfil.** `quick` para una pasada de superficie, `standard` para auditoría con tribunal, `deep` para sistemas críticos con remediación y variantes.
5. **Coste.** Horas base por fase multiplicadas por el perfil y el número de repos; los terceros añaden coste a threat model y dependencias.

```bash
py appsec-audit/scripts/scale_report.py --repos api=./api,web=./web --vendor terceros.json --profile deep --cost tarifa.json --output sistema.json
```

El detalle de perfiles, fórmula de coste y checklist de proveedores está en [`../references/scale.md`](../references/scale.md).

## Reglas duras

- Un repo sin `findings.json` no cuenta como auditado: cuenta como pendiente, y así aparece en el informe.
- El coste es una estimación por fase con fórmula publicada, nunca un presupuesto cerrado ni una promesa.
- Los proveedores se auditan con evidencia documental; una web comercial no es una certificación.
- La topología solo incluye relaciones declaradas: si un servicio aparece en el código y no en el inventario, es un hallazgo de inventario.
- Nada de credenciales compartidas entre repos para «simplificar»: cada repo conserva su alcance y autorización.

## Gate de salida

- Todos los repos con estado explícito: auditado, parcial o pendiente.
- Topología con nodos, aristas y terceros huérfanos.
- Proveedores con evidencia o con el dato declarado como no verificado.
- Perfil y tarifa escritos, con horas y coste por fase.
- Límites del informe: lo que la consolidación no puede demostrar.

## Handoff

Entrega el informe de sistema a dirección y a cada equipo su parte. Los hallazgos por repo vuelven a `appsec-report` para el tribunal; las variantes y parches van a `appsec-fix`, y los workflows compartidos a `appsec-ci`. Si un tercero concentra riesgo, se abre una auditoría propia con su autorización.
