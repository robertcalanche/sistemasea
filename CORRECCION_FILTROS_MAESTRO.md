# Corrección: Filtros en Acceso Maestro - Configuración de Examen

## Problemas Identificados y Corregidos 🔧

### 1. **Tabla `config_examenes` No Se Creaba**
   - **Problema**: El método `_ensure_config()` solo creaba la tabla `config_sistema`, pero no la tabla `config_examenes` necesaria para almacenar la configuración de exámenes (duración, cantidad de preguntas, máximo de intentos, etc.).
   - **Solución**: Se agregó la creación de la tabla `config_examenes` con todas sus columnas necesarias en el método `_ensure_config()`.
   - **Columnas creadas**:
     - `id` (INTEGER PRIMARY KEY)
     - `grado` (TEXT)
     - `area` (TEXT)
     - `evaluacion` (TEXT)
     - `duracion_segundos` (INTEGER)
     - `cantidad_preguntas` (INTEGER)
     - `max_intentos` (INTEGER, default: 1)
     - `permitir_reintentos` (INTEGER, default: 1)
     - `examen_activo` (INTEGER, default: 0)

### 2. **Filtro de Grados Cargaba Datos de Tabla Vacía**
   - **Problema**: El método `_maestro_refresh_grados()` intentaba cargar los grados desde la tabla `resultados` de SQLite, que podría no existir o estar vacía.
   - **Solución**: Se modificó para cargar los grados directamente desde el archivo `preguntas.xlsx` usando la función `cargar_grados_desde_preguntas()`, garantizando que siempre haya grados disponibles.

## Cambios Realizados ✅

### Archivo: `modulo_superadmin.py`

#### Cambio 1: En el método `_ensure_config()` (líneas ~342-365)
```python
# ANTES: Solo creaba config_sistema
# DESPUÉS: Ahora crea tanto config_sistema como config_examenes
```

#### Cambio 2: En el método `_maestro_refresh_grados()` (líneas ~1554-1567)
```python
# ANTES: 
# - Leía grados desde tabla resultados (que podría no existir)
# - Los filtros no funcionaban si no había datos previos

# DESPUÉS:
# - Lee grados desde preguntas.xlsx usando cargar_grados_desde_preguntas()
# - Los filtros funcionan correctamente desde el inicio
```

## Cómo Funciona Ahora 🎯

### En la Pestaña "Acceso Maestro" > "Configuración de Examen":

1. **Seleccionar Grado** 
   - El combo de grado se llena automáticamente con los grados disponibles en `preguntas.xlsx`
   - Al seleccionar un grado, se cargan las áreas disponibles para ese grado

2. **Seleccionar Área**
   - El combo de área se llena dinámicamente basado en el grado seleccionado
   - Al seleccionar un área, se cargan las evaluaciones disponibles

3. **Seleccionar Evaluación**
   - El combo de evaluación muestra las evaluaciones para la combinación grado+área
   - Al seleccionar una evaluación, se cargan los parámetros guardados (si existen)

4. **Guardar Configuración**
   - Ahora guarda correctamente en la tabla `config_examenes` con todos los parámetros:
     - Duración del examen (en minutos)
     - Cantidad de preguntas
     - Máximo de intentos
     - Permitir reintentos
     - Habilitar examen

## Pruebas Realizadas ✓

Se ejecutaron 4 tests de validación:
- ✓ Creación de tablas en la base de datos
- ✓ Carga de grados desde preguntas.xlsx  
- ✓ Carga de áreas por grado
- ✓ Carga de evaluaciones por grado y área

Todos los tests pasaron correctamente.

## Requisitos para Funcionar ✋

Para que los filtros funcionen correctamente:

1. **Archivo `preguntas.xlsx`** debe existir en el directorio de la aplicación
2. **Archivo `preguntas.xlsx`** debe contener las columnas:
   - `grado` (para cargar grados)
   - `area` (para cargar áreas por grado)
   - `evaluacion` (para cargar evaluaciones por grado+área)
3. La base de datos `sistema.db` se crea automáticamente al iniciar

## Notas Importantes 📝

- Los grados, áreas y evaluaciones se cargan **dinámicamente** desde `preguntas.xlsx`
- Si no hay preguntas para un grado/área/evaluación específica, no aparecerán en los filtros
- La configuración se guarda en SQLite (`config_examenes`) para cada combinación grado+área+evaluación
- Los filtros ya no dependen de datos previos en la tabla `resultados`

---

**Fecha de corrección**: 2026-03-01  
**Status**: ✓ Completado y Probado
