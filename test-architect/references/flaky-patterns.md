# Patrones de tests inestables

Un fallo intermitente tiene causa mecánica. Estas son las que aparecen una y otra vez, con la señal que busca `flaky_scan.py` y el arreglo que se pide.

## Espera fija

```python
time.sleep(0.5)
assert cola.vacia()
```

El test asume que medio segundo basta. En una máquina cargada no basta; en una rápida sobra. **Arreglo:** sondear con plazo máximo (`esperar_hasta(condicion, timeout=2)`) o esperar el evento real.

## Reloj de pared

```python
assert registro.creado == datetime.now()
```

El instante cambia entre la escritura y la lectura, y la zona horaria del runner no es la del autor. **Arreglo:** inyectar un reloj, congelarlo (`freezegun`) o comparar rangos explícitos.

## Azar sin semilla

```python
assert generar_codigo() != generar_codigo()
```

Con `random` global, el caso cambia en cada ejecución y un fallo no se reproduce. **Arreglo:** `random.seed(7)` en el test o un generador determinista inyectado.

## Red real

```python
respuesta = requests.get("https://api.ejemplo.com/salud")
```

El test depende de DNS, cuota y latencia de un tercero. **Arreglo:** doble de red (`responses`, `respx`, servidor local) o excepción declarada con `--allow-network` y su motivo.

## Ruta compartida

```python
ruta = "/tmp/informe.csv"
```

Dos ejecuciones en paralelo escriben el mismo fichero. **Arreglo:** `tempfile.TemporaryDirectory()` por test, o un `tmp_path` del runner.

## Estado global

```python
global CONTADOR
CONTADOR += 1
```

El orden de ejecución pasa a ser parte del resultado. **Arreglo:** reiniciar el estado en `setUp`/`tearDown` o inyectar el colaborador.

## Bucle sin salida

```python
while True:
    if servicio.listo():
        break
```

Si la condición nunca llega, el test cuelga hasta el timeout del job. **Arreglo:** plazo máximo y fallo explícito con el último estado observado.

## Skip permanente

```python
@unittest.skip("flaky hasta que se arregle")
```

El test ya no protege nada y nadie recuerda por qué. **Arreglo:** arreglar la causa o borrar el test; si se mantiene, con fecha de revisión y enlace al issue.

## Orden de diagnóstico

1. Reproducir con la semilla y el reloj fijados.
2. Aislar el test: ejecutarlo solo, luego con la suite completa.
3. Comparar con `-p no:randomly` o el orden por defecto.
4. Solo entonces tocar el código: un reintento es el último recurso, nunca el primero.
