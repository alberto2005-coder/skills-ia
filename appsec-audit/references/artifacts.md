# Artefactos de una auditoría

Una auditoría sin artefactos no se puede revisar ni repetir. Este paquete escribe tres ficheros en `<target>/.appsec-audit/` y los valida con scripts deterministas.

## Qué se crea

| Fichero | Para qué sirve | Dueño |
|---|---|---|
| `findings.json` | Hallazgos con veredicto, confianza, `CWE`, evidencia y fingerprint | `appsec-report` |
| `coverage-ledger.json` | Unidades superficie × subsistema × clase de ataque y su estado | `appsec-recon` lo abre y `appsec-report` lo cierra |
| `architecture.md` | Límites de confianza, superficies, almacenes y terceros | `appsec-recon` |

```bash
py appsec-audit/scripts/init_audit.py <target> --id audit-<nombre>
```

`init_audit.py` no sobrescribe nada sin `--force` y deja los tres ficheros válidos para sus validadores.

## Veredictos

| Veredicto | Exige | Prohíbe |
|---|---|---|
| `confirmed` | severidad, confianza ≥ 7, al menos dos pasos de `exploit` y `patch` | — |
| `needs_validation` | `unresolved` con el dato exacto que falta | severidad |
| `rejected` | `reason` con lo que refutó el candidato | severidad |

Un hallazgo confirmado sin vector no es un hallazgo: es una sospecha, y va como `needs_validation`.

## Fingerprint

```text
sha256(cwe | fichero | causa raíz normalizada)[:32]  →  "sha256:ab12…"
```

La causa raíz se normaliza a minúsculas y espacios simples; si falta, se usa el título. **No incluye el número de línea**, así que la huella sobrevive a cualquier refactor y sirve para re-ejecuciones y para deduplicar entre pasadas.

`validate_findings.py` recalcula la huella y rechaza el fichero si no coincide: un fingerprint editado a mano es un error, no una comodidad.

## Unidades de cobertura

```bash
py appsec-audit/scripts/ledger.py add <ledger.json> \
  --surface "POST /login" --subsystem auth --class auth --owner appsec-code
```

| Estado | Significado | Regla |
|---|---|---|
| `planned` | Identificada, sin revisar | Cuenta como hueco |
| `hunting` | En revisión | Cuenta como hueco |
| `covered` | Revisada | Exige al menos una comprobación en `checks` |
| `skipped` | Descartada | Exige `skip_reason` |

```bash
py appsec-audit/scripts/ledger.py gaps <ledger.json> --strict
```

`--strict` sale con código 1 mientras queden huecos: es la puerta que impide cerrar una auditoría con la mitad de la superficie sin mirar.

## Validación

```bash
py appsec-audit/scripts/validate_findings.py <findings.json> --ledger <coverage-ledger.json>
```

Comprueba estructura, campos permitidos contra el esquema, coherencia veredicto↔severidad, pasos de explotación, parche y que cada `source_unit` exista en el ledger. Exit 0 válido, 1 inválido, 2 fichero ilegible.

## Re-ejecución

Una pasada nueva no borra la anterior: se conserva el `findings.json`, se comparan fingerprints y solo se revalida lo que cambió de código. Lo que ya estaba `confirmed` y sigue igual no se vuelve a cazar; lo que cambió de causa raíz entra como hallazgo nuevo.

## Reglas

- Nada de severidad sin veredicto `confirmed`.
- Nada de `confirmed` con confianza menor que 7.
- Nada de `U-` inventada: el validador la cruza con el ledger.
- Nada de cerrar la auditoría con unidades `planned` o `hunting`.
