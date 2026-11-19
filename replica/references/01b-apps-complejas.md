# 01b · Replicación de Software de Alta Complejidad y Motores Interactivos

## Caso de referencia: Suites de Productividad y Editores (Ej. Microsoft Word, Google Docs, Figma, Notion)

Cuando la aplicación a replicar no es un simple CRUD o SaaS con formularios web, sino un **software de alta complejidad interactiva** (procesador de textos como Microsoft Word, editor visual como Figma, hoja de cálculo como Excel o canvas como Miro), el enfoque ingenuo de "hacer unas pantallas y una API REST" fracasa en minutos.

Este documento establece el protocolo estricto para descomponer y replicar con **exactitud funcional (1:1 en comportamiento)** cualquier software complejo en modo clean-room.

---

## 1. El Principio Fundamental: Motor de Estado vs. Shell Visual

Un software como Microsoft Word consta de dos mundos separados:

1. **El Motor Central (In-Memory Engine & AST):** Totalmente desacoplado de la interfaz. Maneja el árbol del documento, las coordenadas de selección, los comandos reversibles y las reglas matemáticas de formateo y paginación.
2. **El Shell de UI (Ribbon & Canvas):** Dibuja el estado del motor y captura eventos del teclado y ratón para transformarlos en comandos del motor.

> **Regla de oro:** Nunca almacenes el contenido de un editor complejo como HTML plano o cadenas de texto sueltas. Si es un procesador de documentos, se modela como un **Árbol de Sintaxis Abstracta (Document AST)**; si es un editor visual, como un **Grafo de Nodos (Scene Graph)**.

---

## 2. Los 8 Subsistemas Esenciales de una App de Productividad (Ejemplo: Word)

Para duplicar con exactitud lo que hace Microsoft Word, el sistema se descompone en estos 8 subsistemas obligatorios:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        UI Shell (Ribbon & Viewport)                   │
├───────────────┬──────────────────────────┬─────────────────────────────┤
│ 1. Document   │ 2. Selection & Cursor    │ 3. Command & History        │
│    AST Model  │    Range Model           │    (Undo/Redo Transactions) │
├───────────────┼──────────────────────────┼─────────────────────────────┤
│ 4. Style &    │ 5. Layout & Pagination   │ 6. Embedded Elements        │
│    Formatting │    (Breaking & Geometry) │    (Tables, Images, Shapes) │
├───────────────┴──────────────────────────┴─────────────────────────────┤
│ 7. File I/O & Interoperability (DOCX, PDF, JSON AST)                   │
│ 8. Ergonomics, Shortcuts & Realtime Metrics (Word Count, Status Bar)   │
└────────────────────────────────────────────────────────────────────────┘
```

### Subsistema 1: Modelo de Documento (Document AST)

- Estructura jerárquica estricta:
  - `Document` -> `Section` (márgenes, orientación vertical/horizontal, columnas, encabezado/pie).
  - `Section` -> `BlockNode` (`Paragraph`, `Table`, `PageBreak`).
  - `Paragraph` -> `InlineNode` (`Run`, `InlineImage`, `Field`, `TabChar`).
  - `Run` -> `Text` + Diccionario de propiedades tipográficas (`bold`, `italic`, `size`, `color`, etc.).
- **Invariante:** Cada cambio al árbol genera una versión inmutable o pasa a través de una transacción atómica.

### Subsistema 2: Motor de Selección y Cursor (Caret & Range)

- Coordenadas universales: `anchor = { nodeId, offset }`, `focus = { nodeId, offset }`.
- Comportamientos exactos:
  - Cursor colapsado (`anchor == focus`): parpadeo rítmico (500 ms), medición vertical coincidente con la altura del glifo actual.
  - Selección de rango: `Shift + Flechas` expande/contrae; `Ctrl + Flechas` salta palabras completas; `Home` y `End` se mueven al inicio/fin de la línea visual (no del párrafo).
  - Triple clic: selecciona el párrafo completo. Doble clic: selecciona la palabra.

### Subsistema 3: Patrón Command e Historial Transaccional (Undo / Redo)

- Cada mutación es un objeto con dos métodos: `execute()` y `undo()`.
- **Agrupación inteligente de eventos (Batching):** Escribir caracteres continuos se agrupa en una sola transacción en el historial de `Ctrl + Z`. Un cambio de estilo, una inserción de tabla o una pausa de más de 1 segundo inicia un nuevo lote de deshacer.
- Invariante: Ejecutar `undo()` y luego `redo()` devuelve el AST exactamente al mismo checksum inicial.

### Subsistema 4: Cascada de Estilos y Formateo

- Jerarquía de 4 niveles idéntica a Word:
  1. *Estilo por defecto del documento* (Normal: Calibri / Aptos 11pt, interlineado 1.08).
  2. *Estilo de párrafo* (Título 1, Título 2, Cita, Lista).
  3. *Estilo de carácter* (Énfasis, Enlace).
  4. *Sobrescritura directa (Direct Formatting)*: El usuario pulsa `Ctrl + B` sobre una palabra seleccionada.
- **Herencia e inversión:** Si una selección abarca texto mixto (parte en negrita y parte normal), pulsar `Ctrl + B` convierte TODO a negrita; pulsarla de nuevo quita la negrita de todo.

### Subsistema 5: Motor de Layout y Paginación (Canvas Geometry)

- **Cálculo geométrico de saltos de línea (Line-Breaking):** Ajuste por ancho disponible `(PageWidth - LeftMargin - RightMargin)`.
- **Control de líneas huérfanas y viudas:** Una página nunca puede terminar con la primera línea solitaria de un párrafo, ni empezar con la última línea aislada.
- **Saltos de página dinámicos vs. duros:**
  - Salto dinámico: calculado en tiempo real cuando el texto excede la altura útil de página `(PageHeight - TopMargin - BottomMargin)`.
  - Salto duro (`Ctrl + Enter`): inserta un nodo explícito `PageBreak` en el AST.
- **Encabezados y Pies de página:** Páginas pares/impares diferenciadas y campo dinámico de paginación (`Página {PAGE} de {NUMPAGES}`).

### Subsistema 6: Estructuras Complejas (Tablas e Imágenes)

- **Tablas:** Matriz bidimensional de celdas. Soporte de combinación de celdas (`colspan`, `rowspan`), anchos relativos o fijos de columna, y saltos de fila entre páginas.
- **Imágenes:**
  - Modo *En línea con el texto (Inline):* se comporta como un carácter gigante dentro de un párrafo.
  - Modo *Ajuste de texto (Floating / Wrap):* Cuadrado, Estrecho, Detrás del texto o Delante del texto con coordenadas `(x, y)` relativas a la página o párrafo.

### Subsistema 7: Ergonomía de UI y Ribbon (Barra de Comandos)

- Pestañas funcionales organizadas:
  - **Inicio:** Portapapeles (Copiar/Pegar con retención de formato), Fuente, Párrafo (alineación, listas, interlineado), Estilos.
  - **Insertar:** Salto de página, Tablas, Imágenes, Encabezado/Pie, Número de página, Vínculos.
  - **Disposición:** Márgenes (Normal, Estrecho, Personalizado), Orientación, Tamaño de papel (A4, Carta).
  - **Revisar / Vista:** Conteo de palabras, Zoom (50% a 200%), Modo lectura vs. Vista de impresión.
- Regla horizontal superior con marcadores interactivos de sangría izquierda, sangría de primera línea y sangría derecha.

### Subsistema 8: Persistencia e Interoperabilidad

- Formato primario en disco: JSON nativo que serializa el AST al 100% sin pérdida.
- Importación y exportación DOCX: Mapeo del AST hacia el estándar OOXML (`word/document.xml`, `word/styles.xml`).
- Exportación fiel a PDF usando el mismo motor de geometría y paginación.

---

## 3. Matriz de Atajos de Teclado Universales Obligatorios

Para garantizar paridad 1:1, la réplica debe responder a la totalidad de estos atajos:

| Atajo | Acción Exacta en el Motor |
|---|---|
| `Ctrl + B` / `Ctrl + N` | Alternar Negrita en selección o activar en el cursor para el próximo carácter |
| `Ctrl + I` / `Ctrl + K` | Alternar Cursiva |
| `Ctrl + U` / `Ctrl + S` | Alternar Subrayado |
| `Ctrl + Z` | Deshacer la última transacción atómica del Command Stack |
| `Ctrl + Y` / `Ctrl + Shift + Z` | Rehacer la última transacción descartada |
| `Ctrl + A` | Seleccionar el documento completo (establece rango de inicio a fin) |
| `Ctrl + F` | Abrir panel de búsqueda de texto con resaltado en vivo |
| `Ctrl + H` | Abrir diálogo de Reemplazo (Buscar y Reemplazar uno o todos) |
| `Ctrl + S` | Guardar archivo en formato nativo / exportar estado |
| `Ctrl + Enter` | Insertar salto de página duro |
| `Ctrl + Backspace` | Borrar palabra anterior completa |
| `Ctrl + Delete` | Borrar palabra siguiente completa |
| `Ctrl + Shift + C` / `Ctrl + Shift + V` | Copiar y pegar formato tipográfico (Format Painter) |

---

## 4. Estrategia de Construcción por Rebanadas Verticales para Word

No construyas "todas las pantallas vacías". Construye por rebanadas que funcionen de principio a fin:

1. **Rebanada 1 (El Núcleo):** Editor de texto plano con cursor parpadeante, navegación por flechas, selección de texto, tipeo, borrado y Undo/Redo funcional.
2. **Rebanada 2 (El Formato y AST):** Transformación de texto plano en Document AST. Soporte de Runs, negrita, cursiva, tamaño, color y atajos `Ctrl+B`, `Ctrl+I`, `Ctrl+Z`.
3. **Rebanada 3 (Párrafos y Estilos):** Alineación (izquierda, centro, derecha, justificado), interlineado, estilos de encabezado (H1, H2, H3) y regla de sangrías.
4. **Rebanada 4 (Motor de Paginación y Geometría):** Visualización en hojas A4/Carta con sombras y márgenes, cálculo de saltos de página dinámicos y saltos duros.
5. **Rebanada 5 (Tablas y Multimedia):** Inserción de tablas con edición de celdas, imágenes redimensionables y selector de color.
6. **Rebanada 6 (Shell Ribbon y Utilidades):** Ribbon con pestañas, barra de estado con conteo de palabras en vivo, diálogo de Buscar/Reemplazar e importación/exportación DOCX y PDF.

Siguiendo esta descomposición sistemática, cualquier aplicación de grado industrial o de escritorio puede ser reconstruida con fidelidad matemática, sin improvisar y con 100% de paridad funcional.
