# Eliminación de Dependencia de estudiantes.xlsx

## Cambios Realizados

### 1. **Eliminación de Referencias a ESTUDIANTES_FILE**

#### app.py (Línea 54)
```python
# ESTUDIANTES_FILE = BASE_DIR / "estudiantes.xlsx"  # Ahora se valida desde SQLite
```
- Comentada la línea que definía la ruta al archivo Excel

#### Admin.py (Línea 14)
```python
# ESTUDIANTES_FILE = BASE_DIR / "estudiantes.xlsx"  # Ahora se valida desde SQLite
```
- Comentada la línea que definía la ruta al archivo Excel

### 2. **Tabla estudiantes en create_base_datos()**

Añadida la tabla `estudiantes` con la estructura completa:
```sql
CREATE TABLE IF NOT EXISTS estudiantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_documento TEXT,
    documento TEXT UNIQUE,
    nombre TEXT,
    sexo TEXT,
    fecha_nacimiento TEXT,
    telefono TEXT,
    correo TEXT,
    grado TEXT,
    curso TEXT,
    jornada TEXT,
    sede TEXT,
    estado TEXT DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 3. **Función validar_estudiante() - Migrada a SQLite**

**Antes:** Leía estudiantes desde `estudiantes.xlsx`

**Ahora:** Consulta la tabla `estudiantes` en `sistema.db`
```python
def validar_estudiante(documento):
    """Valida estudiante desde la base de datos SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT documento, nombre, grado, curso, jornada, estado
           FROM estudiantes WHERE documento = ?""",
        (documento,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row and str(row[5]).lower() == "activo":
        return {
            "documento": row[0],
            "nombre": row[1],
            "grado": row[2],
            "curso": row[3],
            "jornada": row[4],
            "estado": row[5],
        }
    return None
```

### 4. **Función cargar_grados() - Migrada a SQLite**

**Antes:** Leía grados desde `estudiantes.xlsx`

**Ahora:** Consulta la tabla `estudiantes` en `sistema.db`
```python
def cargar_grados():
    """Carga grados únicos desde la base de datos SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT grado FROM estudiantes WHERE estado = 'Activo'")
    grados = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    return sorted([normalizar_grado(g) for g in grados])
```

### 5. **Funciones de Filtrado - Migradas a SQLite**

#### `_llenar_combo_grados()`
- Reemplazada lectura desde Excel por consultas SQLite
- Obtiene grados y cursos de la tabla `estudiantes`

#### `_on_grado_selected()`
- Reemplazada lectura desde Excel por consultas SQLite
- Filtra cursos por grado desde la tabla `estudiantes`

#### `cargar_datos()`
- Reemplazada lectura desde Excel por consultas SQLite
- Obtiene estudiantes filtrados desde la tabla `estudiantes`

### 6. **Funciones de Exportación - Parcialmente Migradas**

#### `exportar_reporte_por_filtros()`
- Reemplazada lectura de estudiantes desde Excel por SQLite
- Mantiene datos de resultados en SQLite

#### `exportar_consolidado_periodo()`
- Reemplazada lectura de estudiantes desde Excel por SQLite
- Mantiene datos de resultados en SQLite

## Flujo de Validación Actual

```
Usuario ingresa documento
    ↓
Sistema busca en tabla estudiantes de SQLite
    ↓
Valida estado = 'Activo'
    ↓
Retorna diccionario con datos del estudiante
    ↓
Usuario accede al módulo de estudiante
```

## Importación desde Excel

El archivo `estudiantes.xlsx` se mantiene pero **SOLO para importación masiva**.

Para importar estudiantes:
1. Usuario carga el archivo Excel
2. Sistema lee el Excel
3. Sistema inserta/actualiza datos en la tabla `estudiantes` de SQLite

## Compatibilidad

✅ **Red Local:** El sistema funciona totalmente desde SQLite, sin depender del Excel

✅ **Versión Instalable:** El ejecutable puede empaquetar `sistema.db` sin necesidad del Excel

✅ **Exportación:** El Excel se mantiene como destino de exportación

## Cambios Pendientes (si es necesario)

Si deseas implementar la importación desde Excel a SQLite:
- Buscar función de importación (generalmente en ModuloDocente)
- Añadir lógica de lectura de Excel e inserción en tabla `estudiantes`
- Ejemplo:
```python
df = pd.read_excel(archivo)
for _, row in df.iterrows():
    cursor.execute(
        """INSERT OR IGNORE INTO estudiantes
           (documento, nombre, grado, curso, jornada, estado)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (row["documento"], row["nombre"], row["grado"], 
         row["curso"], row["jornada"], "Activo")
    )
```

## Verificación

Para verificar que todo funciona correctamente:

1. Importar estudiantes desde Excel
2. Verificar que aparezcan en la tabla `estudiantes`
3. Login con un documento de estudiante
4. Verificar que el sistema funcione sin acceso al archivo Excel

## Notas

- La tabla `estudiantes` se crea automáticamente al iniciar el sistema
- Los grados y cursos se cargan desde la tabla `estudiantes`, no del Excel
- El login depende únicamente de SQLite, nunca del Excel
- Compatible con base de datos compartida en red local
