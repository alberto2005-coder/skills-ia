# {{ID}} — {{título}}

| Campo | Valor |
|---|---|
| Severidad | {{crítica / alta / media / baja}} |
| Confianza | {{1-10}} (≥7 para entrar en el informe) |
| CWE | {{CWE-xxx}} |
| OWASP | {{A01-A10 o LLM01-LLM10}} |
| Ubicación | `{{ruta:línea}}` |
| Superficie | {{pública / autenticada / interna / build}} |

## Descripción

{{Qué defecto hay, en dos frases, sin adjetivos.}}

## Trazado

- **Fuente:** `{{ruta:línea}}` — {{qué dato entra}}
- **Transformaciones:** {{validación, parseo, escapado; o «ninguna»}}
- **Sumidero:** `{{ruta:línea}}` — {{qué operación ejecuta}}

## Impacto

{{Qué obtiene un atacante: datos, ejecución, denegación, movimiento lateral.}}

## Vector de explotación

1. {{requisito previo}}
2. {{acción}}
3. {{resultado}}

## Evidencia

```{{lenguaje}}
{{fragmento acotado}}
```

## Mitigación existente

{{Ninguna / parcial / presente pero mal configurada. Si mitiga del todo, este hallazgo no debería existir.}}

## Parche propuesto

```diff
- {{antes}}
+ {{después}}
```

## Verificación tras el parche

{{Cómo se comprueba que queda cerrado: prueba, revisión de código o ambos.}}
