# Especificación de Motor y Subsistemas para App Compleja: {{app_nombre_propio}}
## App de Referencia: {{app_original}} (Ej. Microsoft Word, Figma, Excel)

---

## 1. Descomposición del Modelo de Datos (Document AST / Graph)

```text
// Diagrama de jerarquía de nodos del motor
Root
└── Section (propiedades de página, márgenes, orientación)
    └── BlockNode (Párrafo, Tabla, Salto, Contenedor)
        └── InlineNode (Run de texto, Imagen en línea, Campo dinámico)
```

### Invariantes del Modelo:
1. {{invariante_1}} (ej. Todo bloque de texto termina con un delimitador de párrafo válido).
2. {{invariante_2}} (ej. Toda celda de tabla pertenece a una fila y columna válidas dentro de la matriz).
3. {{invariante_3}} (ej. Toda mutación pasa por una transacción invertible en el historial).

---

## 2. Subsistema de Selección, Cursor y Coordenadas

- **Estructura del Rango:** `{ anchor: { nodeId, offset }, focus: { nodeId, offset }, isCollapsed: boolean }`
- **Comportamientos de Teclado:**
  - `ArrowLeft / ArrowRight`: {{comportamiento_paso}}
  - `Ctrl + ArrowLeft / ArrowRight`: {{salto_palabra}}
  - `Shift + Arrows`: {{expansion_seleccion}}
  - `Home / End`: {{movimiento_linea_visual}}
  - `Ctrl + Home / Ctrl + End`: {{movimiento_inicio_fin_documento}}

---

## 3. Matriz de Comandos y Pila Transaccional (Command Stack)

| Comando | Parámetros | Operación `execute()` | Operación inversa `undo()` | Política de Batching |
|---|---|---|---|---|
| `InsertTextCommand` | text, range | Inserta texto en el rango | Borra texto insertado y restaura rango | Agrupa pulsaciones continuas (< 1s) |
| `ApplyStyleCommand` | styleKey, value, range | Aplica propiedad tipográfica | Restaura propiedades previas | Inmediato (1 comando por clic/atajo) |
| `InsertTableCommand` | rows, cols, position | Inserta nodo tabla | Elimina nodo tabla | Inmediato |
| `SplitParagraphCommand`| position | Divide bloque en dos | Une los dos bloques | Inmediato (tecla Enter) |

---

## 4. Motor de Layout, Medición y Geometría

- **Unidades de Medida:** Pixels / Points (1 pt = 1.333 px) / Milímetros (A4 = 210mm x 297mm).
- **Algoritmo de Salto de Línea (Line-Breaking):** {{algoritmo_greedy_o_knuth_plass}}
- **Reglas de Paginación:**
  - Márgenes configurables: Superior, Inferior, Izquierdo, Derecho.
  - Altura útil = `Alto_Página - Margen_Sup - Margen_Inf`.
  - Tratamiento de líneas huérfanas y viudas (Orphan/Widow control activo).
  - Cálculo de saltos de página dinámicos y saltos forzados (`Ctrl + Enter`).

---

## 5. Matriz de Atajos de Teclado (Keyboard Shortcuts)

| Atajo | Función Asociada | Estado de UI Afectado |
|---|---|---|
| `Ctrl + B` | Alternar Negrita | Botón en Ribbon se activa/desactiva + Texto |
| `Ctrl + I` | Alternar Cursiva | Botón en Ribbon se activa/desactiva + Texto |
| `Ctrl + U` | Alternar Subrayado | Botón en Ribbon se activa/desactiva + Texto |
| `Ctrl + Z` | Deshacer transacción | Estado del documento retrocede un paso |
| `Ctrl + Y` | Rehacer transacción | Estado del documento avanza un paso |
| `Ctrl + F` | Buscar | Abre panel lateral de búsqueda |
| `Ctrl + H` | Reemplazar | Abre modal de reemplazo |
| `Ctrl + S` | Guardar / Exportar | Serializa AST a JSON / DOCX |

---

## 6. Shell de Interfaz y Controles de Usuario

- **Ribbon / Barra de Herramientas:**
  - Pestaña Inicio: Fuente, Párrafo, Estilos, Portapapeles.
  - Pestaña Insertar: Páginas, Tablas, Ilustraciones, Vínculos, Encabezado/Pie.
  - Pestaña Disposición: Márgenes, Orientación, Tamaño, Columnas.
- **Regla Superior:** Marcadores arrastrables de sangría izquierda, sangría francesa y sangría derecha.
- **Barra de Estado Inferior:** Conteo de palabras en tiempo real, número de página actual (`Pág. 1 de 3`), selector de zoom (`100%`).
- **Interoperabilidad de Archivos:** Exportación/Importación DOCX, PDF y JSON nativo.
