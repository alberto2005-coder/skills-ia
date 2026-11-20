---
name: replica-diff
description: >
  Fase 7 de replica — mide paridad funcional (parity.py) y visual (imgdiff.py) entre el original y el clon: contraste de features por severidad, diff de layout por regiones y evidencia por hallazgo. Úsala para saber si un clon ya iguala a la app original, cerrar un gate de paridad o documentar diferencias aceptadas. English: measure functional and visual parity between the original and the clone, and compare the screenshots with imgdiff.
license: MIT
metadata:
  package: replica
  version: "2.0.1"
  author: "Alberto Ortiz"
---

# Replica · Paridad (fase 7)

Responde una sola pregunta con evidencia: **¿el clon hace lo mismo?** Sin adornos y sin aprobar por impresión.

Assets compartidos: `../references/`, `../scripts/`, `../templates/`. **Todos los comandos se ejecutan desde la raíz del repositorio**.

## Precondiciones

- `features.csv` actualizado por la fase 4.
- Suite de pruebas verde (fase 6).
- Capturas propias de original y clon con el mismo viewport y estado.

## Método

1. Lee `../references/07-diff.md` entero.
2. **Paridad funcional**:

```bash
py replica/scripts/parity.py replica/features.csv --markdown --out replica/parity.md
```

   Pondera must 3 / should 2 / could 1, `partial` = 0.5 y excluye `out_of_scope`. Falla si algún `must` no está `done`.

3. **Paridad visual**:

```bash
py replica/scripts/imgdiff.py original.png clon.png --out replica/diff/home.png --min-similarity 85
```

   Compara layout por mapa de bordes y rejilla, ignorando el color: el rebrand no debe penalizar.

4. Cada diferencia que importe lleva fila de `../templates/evidence.md` con **Fuente · Observación · Inferencia · Confianza · Límites**. Una diferencia no explicada no es «parecido razonable»: es un hallazgo abierto.
5. Clasifica cada diferencia en: **corregir** (rompe función), **aceptar** (decisión con motivo) o **fuera de alcance** (con enlace a `scope.md`).
6. Escribe `replica/parity.md` con la tabla, el resultado del gate y las diferencias aceptadas.

## Gate de salida

- `parity.py` sin `must` pendientes y con al menos un `must` declarado (código de salida 0). Un manifiesto sin `must` no es un gate: sale 1 y hay que asignar prioridades antes de dar la fase por buena.
- `imgdiff.py` sobre el flujo principal con similitud ≥ umbral acordado o diferencia explicada región por región.
- Toda diferencia aceptada tiene motivo y responsable.
- Cero filas de evidencia con confianza `THIN` usadas como argumento.

## Handoff

`parity.md` cierra la parte funcional. `replica-entrepreneur` (fase 8) usa el producto ya construido para escuchar a usuarios reales.
