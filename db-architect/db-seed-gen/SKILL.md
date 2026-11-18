---
name: db-seed-gen
description: Genera datos de siembra deterministas desde un esquema SQL, ordenando las tablas por claves foráneas y repitiendo byte a byte con la misma semilla y el mismo esquema.
license: MIT
metadata:
  package: db-architect
  version: "1.1.0"
---

# DB Seed Gen

## Objetivo

Producir datos de prueba reproducibles para verificar una migración o un cambio de consulta, respetando el orden de las claves foráneas y sin copiar datos reales.

## Instrucciones de ejecución

1. Genera los inserts a partir del esquema:

```bash
py db-architect/scripts/seed_gen.py --schema schema.sql --rows 5 --seed 42
py db-architect/scripts/seed_gen.py --schema schema.sql --rows 5 --seed 42 --format json
```

2. Guarda la semilla junto al fichero generado: sin ella, el resultado no se puede reproducir.
3. Carga los datos en la base de pruebas y ejecuta la verificación con `replica-test` o el runner del proyecto.

## Qué genera

| Tipo de columna | Valor |
|---|---|
| Clave primaria o `id` | Entero secuencial desde 1 |
| Clave foránea | Entero dentro del rango de filas del padre |
| Numérica | Entero 1–100 |
| Booleana | 0 o 1 |
| Fecha u hora | `2024-01-0N` |
| Texto | `<columna>_<n>` |

Las tablas se ordenan topológicamente por sus `REFERENCES`, con orden alfabético estable entre tablas independientes.

## Límites

- Solo entiende `CREATE TABLE` con columnas simples: no procesa vistas, particiones, enums ni `ALTER` posteriores.
- No genera datos válidos para restricciones `CHECK` ni formatos específicos (emails, teléfonos).
- Un ciclo de referencias se rechaza con código 2 en lugar de inventar un orden.

## Gate de salida

- Fichero generado con la semilla y el esquema declarados.
- Los padres se insertan antes que los hijos y las claves foráneas apuntan a filas existentes.
- Dos ejecuciones con la misma semilla producen exactamente el mismo contenido.

## Handoff

Entrega al solicitante el fichero de datos, la semilla y el esquema usado. Si el esquema real tiene restricciones que estos datos no respetan, dilo antes de que se carguen.
