# Medición en navegador

Para los gates que no se pueden leer en el código: composición real, líneas de titular, objetivos táctiles y solapes.

## Snippet de medición

Pégalo en la consola del navegador (o en la herramienta de evaluación del entorno) **después** de fijar el ancho. Devuelve un objeto por ancho; anota el resultado.

```javascript
(() => {
  const q = (s) => document.querySelector(s);
  const box = (s) => {
    const r = q(s).getBoundingClientRect();
    return Math.round(r.width) + "x" + Math.round(r.height);
  };
  const lines = (s) => {
    const r = document.createRange();
    r.selectNodeContents(q(s));
    return r.getClientRects().length;
  };
  const doc = document.documentElement;

  return {
    ancho: innerWidth,
    overflowX: doc.scrollWidth - doc.clientWidth,
    h1: box("h1"),
    lineasH1: lines("h1"),
    primario: box("button, .btn, [type=submit]"),
    enlacesNav: [...document.querySelectorAll("nav a")].map((a) => box("nav a")),
    cabecera: box("header"),
    solapes: [...document.querySelectorAll("main *")]
      .filter((el) => {
        const s = getComputedStyle(el);
        return s.position === "absolute" && el.getBoundingClientRect().height > innerHeight;
      }).length,
  };
})()
```

## Comprobaciones que este snippet resuelve

| Dato | Lectura | Defecto típico |
|---|---|---|
| `overflowX` | Debe ser `0` | Una columna o un `min-width` empuja el documento |
| `lineasH1` | `≤ 3` | Titular en la columna estrecha de una rejilla o `max-width` demasiado corto |
| `box("button")` | Alto `≥ 44` | Botones de 28–39 px en móvil |
| `box("nav a")` | Alto `≥ 44` si es táctil | Enlaces de navegación diminutos |
| `solapes` | `0` | Elemento decorativo gigante que tapa contenido |

## Anclas bajo cabecera fija

Con la cabecera en `position: sticky`, un salto a `#seccion` deja el título debajo de ella si falta compensación. Mide así:

```javascript
(() => {
  const header = document.querySelector("header").getBoundingClientRect();
  document.querySelector('a[href^="#"]').click();
  const target = document.querySelector(":target").getBoundingClientRect();
  return {
    cabeceraAbajo: Math.round(header.bottom),
    objetivoArriba: Math.round(target.top),
    visible: Math.round(target.top) >= Math.round(header.bottom),
  };
})()
```

Arreglo: `html { scroll-padding-top: <alto de cabecera + aire> }`.

## Caché que sirve CSS viejo

Si tras editar una hoja los estilos no cambian, el navegador está sirviendo una copia. Comprueba la URL del recurso y fuerza versión:

```html
<link rel="stylesheet" href="styles.css?v=3">
<script src="app.js?v=3"></script>
```

Vuelve a medir después de recargar; un resultado idéntico al anterior suele significar caché, no que el arreglo no funcione.

## Orden de trabajo

1. Fija el ancho (360, 390, 768, 1024, 1440) y recarga.
2. Ejecuta el snippet, guarda números.
3. Corrige una causa por iteración; vuelve a medir solo lo afectado.
4. Cierra con la tabla de antes/después en el informe.
