# Mejoras en la Visualización del TreeView - Banco de Preguntas

## Problema Original
Las columnas del TreeView en el módulo SUPER ADMIN → Banco de Preguntas tenían una distribución desigual:
- Las columnas de texto **corto** (id, evaluacion, area, periodo, grado, id_contexto, correcta, imagen) ocupaban **demasiado espacio**
- Las columnas de texto **largo** (contexto, enunciado, opcion_a, opcion_b, opcion_c, opcion_d) quedaban **muy pequeñas**
- Solo se mostraban **7 columnas** de las **14 disponibles**
- Faltaban scrollbars tanto vertical como horizontal

## Cambios Realizados

### Archivo: `interfaz_banco_preguntas.py`

#### 1. ✅ Ampliación de Columnas
Se agregaron todas las **14 columnas** necesarias:

```python
cols = (
    "id",                 # Columna muy corta
    "evaluacion",         # Columna mediana
    "area",              # Columna mediana
    "periodo",           # Columna corta
    "grado",             # Columna corta
    "id_contexto",       # Columna mediana
    "contexto",          # Columna LARGA
    "enunciado",         # Columna LARGA
    "opcion_a",          # Columna LARGA
    "opcion_b",          # Columna LARGA
    "opcion_c",          # Columna LARGA
    "opcion_d",          # Columna LARGA
    "correcta",          # Columna muy corta
    "imagen",            # Columna corta
)
```

#### 2. ✅ Ajuste Inteligente de Anchos
Clasificación por categoría de tamaño:

| Categoría | Columnas | Ancho | Propósito |
|-----------|----------|-------|---------|
| **Muy Cortas** | id, correcta | 35-40px | Identificadores y valores simples |
| **Cortas** | periodo, grado, imagen | 50px | Valores de clasificación pequeños |
| **Medianas** | evaluacion, area, id_contexto | 80-90px | Clasificaciones intermedias |
| **Largas** | contexto, enunciado, opciones | 180-220px | Texto descriptivo completo |

#### 3. ✅ Sistema de Scrollbars Mejorado

**Scroll Vertical:**
```python
scrollbar_v = ttk.Scrollbar(
    tree_frame, orient="vertical", 
    command=self.tree_preg.yview
)
self.tree_preg.configure(yscroll=scrollbar_v.set)
```

**Scroll Horizontal (NUEVO):**
```python
scrollbar_h = ttk.Scrollbar(
    tree_frame, orient="horizontal", 
    command=self.tree_preg.xview
)
self.tree_preg.configure(xscroll=scrollbar_h.set)
```

#### 4. ✅ Redimensionamiento Manual de Columnas
Habilitado con `stretch=True` en cada columna:
```python
self.tree_preg.column(
    col,
    width=config.get("width", 100),
    anchor=config.get("anchor", "w"),
    stretch=True,  # Permite redimensionamiento manual del usuario
)
```

#### 5. ✅ Layout Mejorado con Grid
Se utiliza `grid` en lugar de `pack` para mejor control de los scrollbars:
```python
self.tree_preg.grid(row=0, column=0, sticky="nsew", in_=tree_frame)
scrollbar_v.grid(row=0, column=1, sticky="ns", in_=tree_frame)
scrollbar_h.grid(row=1, column=0, sticky="ew", in_=tree_frame)
```

#### 6. ✅ Datos Completos en la Vista
El método `_preg_cargar_datos_filtrados()` ahora inserta **todas las 14 columnas**:
```python
valores = (
    row.get("id", ""),
    row.get("evaluacion", ""),
    row.get("area", ""),
    row.get("periodo", ""),
    row.get("grado", ""),
    row.get("id_contexto", ""),
    row.get("contexto", ""),
    row.get("enunciado", ""),
    row.get("opcion_a", ""),
    row.get("opcion_b", ""),
    row.get("opcion_c", ""),
    row.get("opcion_d", ""),
    row.get("correcta", ""),
    imagen_str,  # "✓" si existe, "" si no
)
```

## Compatibilidad

✅ **Mantiene la lógica funcional intacta:**
- Los métodos `pregunta_editar()` y `pregunta_eliminar()` siguen usando `values[0]` para obtener el ID (sin cambios)
- `_load_preguntas()` en `modulo_superadmin.py` completa el llenado (sin conflictos)
- Importación desde Excel sigue siendo compatible
- Todos los datos se cargan correctamente desde la base de datos Excel

✅ **Sin cambios en:**
- Funcionalidad de agregar/editar/eliminar preguntas
- Sistema de filtros (grado, área, evaluación)
- Importación masiva de preguntas
- Exportación de datos
- Validación de integridad

## Mejora Visual

### Antes:
- 7 columnas visibles con anchos desproporcionados
- Sin scroll horizontal (contenido cortado)
- Difícil lectura del enunciado y opciones

### Después:
- 14 columnas visibles con anchos optimizados
- Scroll horizontal para desplazarse por todas las columnas
- Scroll vertical optimizado para la altura disponible
- Redimensionamiento manual de columnas por el usuario
- Mejor separación visual entre columnas cortas y largas
- Enunciados y opciones completamente visibles

## Notas Técnicas

1. **Grid Layout:** Se usa grid en lugar de pack para mejor control de scrollbars con disposición de 2x2
2. **Stretch:** El parámetro `stretch=True` permite que las columnas se redimensionen manualmente
3. **Anclajes:** Columnas numéricas centradas (`center`), textuales alineadas a izquierda (`w`)
4. **Compatibilidad Pandas:** El código sigue siendo compatible tanto con pandas como sin él

## Instrucciones de Uso

Para aprovechar las mejoras:

1. **Scroll Horizontal:** Use la barra de scroll inferior para desplazarse horizontalmente
2. **Scroll Vertical:** Use la barra de scroll derecha para desplazarse verticalmente
3. **Redimensionar Columnas:** Coloque el cursor en el borde de un encabezado (entre dos etiquetas) y arrastre
4. **Ordenar:** Haga clic en el encabezado de una columna para ordenar (cuando se implemente)

## Validación

✅ Sintaxis verificada sin errores
✅ Compatible con estructura de datos existente
✅ Mantiene todas las funcionalidades originales
