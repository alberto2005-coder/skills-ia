# Estrategia de pruebas por riesgo

## Qué decide un plan

Un plan de pruebas responde a tres preguntas, en este orden: qué puede fallar caro, qué se comprueba hoy y qué se deja fuera con motivo. El número de tests no es una respuesta.

## Matriz de riesgo

| Señal | Peso | Por qué |
|---|---|---|
| Dominio sensible (sesión, cobro, permisos, secretos) | Alto | El fallo cuesta dinero, datos o acceso |
| Módulo sin test reconocible | Alto si es sensible, medio si no | Nadie detecta la regresión |
| Superficie pública grande | Medio | Más entradas, más combinaciones |
| Errores y excepciones capturadas | Medio | El camino de error suele estar sin probar |
| Módulo solo de datos o constantes | Bajo | Un test de humo basta |

La puntuación de `plan_tests.py` suma estas señales; el orden importa más que el valor exacto.

## Cartera, no pirámide

| Nivel | Qué cubre | Cuándo |
|---|---|---|
| Contrato | Forma del payload entre módulos | Frontera que comparten dos equipos o dos capas |
| Unidad | Decisión y límite de una función | Lógica con ramas y casos límite |
| Integración | Colaboración entre dos piezas reales | Base de datos, cola, fichero |
| Extremo a extremo | Un flujo de usuario | Solo los caminos que sostienen el negocio |

La pirámide dice «muchas unidades y pocas de extremo a extremo»; la cartera añade que un contrato mal fijado no lo arregla ninguna unidad.

## Cobertura declarada y cobertura real

La heurística de nombres (`test_<módulo>.py`) es un suelo, no una medida: detecta lo obvio y falla con tests agrupados. Si el proyecto publica cobertura de líneas o de ramas, se usa como entrada y manda sobre el nombre.

## Qué no se prueba

- Código generado que se regenera en cada build.
- Configuración que el propio framework valida al arrancar.
- Terceros: se doblan, no se prueban.
- Ramas imposibles por contrato: se documentan como equivalentes.

## Fronteras del paquete

| Asunto | Dueño |
|---|---|
| Rutas, OpenAPI y SemVer | `api-contract-guard` |
| Activación y calidad de una skill | `skill-evals` |
| Ejecución de la suite o de mutantes | El proyecto auditado |
| Corrección de seguridad del código | `appsec-audit` |

## Entregables

1. Plan ordenado con puntuación y motivo.
2. Ledger de exclusiones con fecha y responsable.
3. Lista de contratos que hay que fijar antes de tocar la frontera.
4. Presupuesto de mutación, si se pide campaña.
