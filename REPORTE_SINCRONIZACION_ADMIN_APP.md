# 📊 REPORTE DETALLADO: SINCRONIZACIÓN ADMIN.PY ↔ APP.PY

**Fecha**: 5 de marzo de 2026  
**Archivos analizados**: Admin.py (~4124 líneas) vs app.py (~1436 líneas)  
**Objetivo**: Identificar diferencias y guiar sincronización

---

## 🎯 RESUMEN EJECUTIVO

El archivo `app.py` actúa como punto de entrada principal que:
1. Importa la mayoría de funciones desde `Admin.py`
2. Redefine y expande `ModuloEstudiante` con funcionalidades de reanudación
3. Añade lógica de autenticación mejorada (clave maestra)
4. Delegación estratégica de responsabilidades

**Estado actual**: Parcialmente sincronizado con problemas de importación

---

## ❌ PROBLEMAS CRÍTICOS DETECTADOS

### 1. IMPORTACIONES QUE FALLAN - CÓDIGO ROTO
```python
# app.py, línea 26
from Admin import (
    ...
    obtener_todas_respuestas_desde_bd,  ❌ NO EXISTE EN ADMIN.PY
    ...
    cargar_grados,                       ❌ NO EXISTE EN ADMIN.PY
    ...
)
```

**Impacto**: 
- ImportError cuando se ejecuta app.py
- Variables `obtener_todas_respuestas_desde_bd` y `cargar_grados` no definidas

---

## 📋 FUNCIÓN 1: `obtener_todas_respuestas_desde_bd()`

### Ubicación donde se usa:
- **app.py, línea 1209**: Utilizada en `ModuloEstudiante._mostrar_examen()`
- Propósito: Recuperar todas las respuestas guardadas cuando se reanuda un examen

### ¿Por qué falta?
Admin.py NO tiene esta función. Debe ser creada o importada desde otro módulo.

### Solución:
**CREAR en Admin.py** esta función:

```python
def obtener_todas_respuestas_desde_bd(documento, area, intento):
    """Obtiene TODAS las respuestas registradas en BD para un examen.
    
    Args:
        documento: Documento del estudiante
        area: Área de evaluación
        intento: Número de intento
        
    Returns:
        Cadena JSON con todas las respuestas o None
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT respuesta_seleccionada, respuesta_correcta, es_correcta, enunciado
            FROM respuestas_estudiantes 
            WHERE documento = ? AND area = ? AND intento = ?
            ORDER BY pregunta_id ASC
            """,
            (documento, area, intento)
        )
        
        respuestas = []
        for row in cursor.fetchall():
            respuestas.append({
                "respuesta_dada": row[0],
                "respuesta_correcta": row[1],
                "correcta": bool(row[2]),
                "enunciado": row[3]
            })
        
        conn.close()
        
        return json.dumps(respuestas) if respuestas else None
    except Exception as e:
        print(f"[ERROR] obtener_todas_respuestas_desde_bd: {e}")
        return None
```

---

## 📋 FUNCIÓN 2: `cargar_grados()`

### Ubicación donde se usa:
- **app.py, línea 40**: Importación directa

### ¿Por qué falta?
Admin.py NO tiene esta función. Debe ser creada.

### Propósito inferido:
Cargar lista de grados únicos desde el archivo `estudiantes.xlsx`

### Solución:
**CREAR en Admin.py** esta función:

```python
def cargar_grados():
    """Carga los grados únicos disponibles desde estudiantes.xlsx.
    
    Returns:
        Lista de grados ordenados alfabéticamente
    """
    try:
        df = pd.read_excel(ESTUDIANTES_FILE)
        df.columns = df.columns.str.strip().str.lower()
        
        if "grado" in df.columns:
            # Normalizar grados
            df["grado"] = df["grado"].apply(normalizar_grado)
            grados = sorted(df["grado"].dropna().unique().tolist())
            return grados if grados else []
        
        return []
    except Exception as e:
        print(f"[DEBUG] Error cargando grados: {e}")
        return []
```

---

## 🔧 IMPORTACIONES FALTANTES EN APP.PY

### Funciones que EXISTEN en Admin.py pero NO se importan

1. **`normalizar_grado(grado)`** (Admin.py, línea 607)
   - **Usada en app.py**: Sí (en ModuloEstudiante)
   - **Importada en app.py**: ❌ NO
   - **Solución**: Agregar a lista de importación

2. **`examen_esta_activo(area)`** (Admin.py, línea 1443)
   - **Usada en app.py**: Posiblemente en futuro
   - **Importada en app.py**: ❌ NO
   - **Solución**: Agregar a lista de importación

---

## 📊 TABLA COMPLETA: FUNCIONES EN ADMIN.PY

| # | Función | Línea | ¿Importada? | ¿Usada? | Estado |
|---|---------|-------|-----------|---------|--------|
| 1 | `crear_base_datos()` | 21 | ✅ | ✅ | OK |
| 2 | `crear_tabla_config()` | 96 | ✅ | ✅ | OK |
| 3 | `registrar_inicio()` | 163 | ✅ | ✅ | OK |
| 4 | `registrar_final()` | 204 | ✅ | ✅ | OK |
| 5 | `ya_presento()` | 338 | ✅ | ✅ | OK |
| 6 | `obtener_estado_area()` | 356 | ✅ | ✅ | OK |
| 7 | `obtener_intento_area()` | 390 | ✅ | ✅ | OK |
| 8 | `autorizar_revision()` | 411 | ✅ | ✅ | OK |
| 9 | `puede_revisar()` | 444 | ✅ | ✅ | OK |
| 10 | `obtener_respuestas_estudiante()` | 465 | ✅ | ✅ | OK |
| 11 | `resetear_examen()` | 573 | ✅ | ✅ | OK |
| 12 | `normalizar_grado()` | 607 | ❌ | ⚠️ | FALTA IMPORTAR |
| 13 | `validar_estudiante()` | 629 | ✅ | ✅ | OK |
| 14 | `validar_docente()` | 677 | ✅ | ✅ | OK |
| 15 | `cargar_preguntas()` | 693 | ✅ | ✅ | OK |
| 16 | `cargar_areas()` | 699 | ✅ | ✅ | OK |
| 17 | `cargar_areas_por_grado()` | 725 | ✅ | ✅ | OK |
| 18 | `cargar_evaluaciones_por_grado_y_area()` | 789 | ✅ | ✅ | OK |
| 19 | `exportar_reporte_por_filtros()` | 870 | ✅ | ✅ | OK |
| 20 | `exportar_consolidado_periodo()` | 998 | ✅ | ✅ | OK |
| 21 | `exportar_reporte_completo()` | 1109 | ✅ | ✅ | OK |
| 22 | `cargar_preguntas_filtradas()` | ~1220 | ✅ | ✅ | OK |
| 23 | `cargar_config_examen()` | 1397 | ⚠️* | ✅ | Asignado |
| 24 | `examen_esta_activo()` | 1443 | ❌ | ⚠️ | FALTA IMPORTAR |
| 25 | `guardar_config_examen()` | 1452 | ⚠️* | ✅ | Asignado |

*Asignadas al final de app.py mediante `Admin.cargar_config_examen = ...`

---

## 🏗️ CLASES EN ADMIN.PY

### 1. `VistaHistorialExamenes` (Admin.py, ~línea 1690)
**Estado en app.py**: ✅ IMPORTADA, ✅ USADA  
**Ubicación**: Componente reutilizable para mostrar historial  
**Cambios necesarios**: NINGUNO

### 2. `ModuloDocente` (Admin.py, ~línea 1800)
**Estado en app.py**: ✅ IMPORTADA  
**Uso**: Panel de control para docentes  
**Cambios necesarios**: NINGUNO

### 3. `ModuloEstudiante` (Admin.py, ~línea 2400)
**Estado en app.py**: Originalmente importada pero **REDEFINIDA** (línea 81)  
**Diferencias principales**:

| Aspecto | Admin.py | app.py |
|---------|----------|--------|
| Métodos básicos | ✅ Todos presentes | ✅ Todos presentes |
| `_obtener_examen_en_proceso()` | ❌ NO | ✅ SÍ (nueva) |
| `_iniciar_examen()` | ⚠️ Básico | ✅ Mejorado con reanudación |
| `_mostrar_examen()` | ⚠️ Simple | ✅ Con recuperación de respuestas |
| Manejo de reanudación | ❌ NO | ✅ SÍ |
| Guardado inmediato de respuestas | ❌ NO | ✅ SÍ |

**Conclusión**: app.py es una **versión mejorada** de ModuloEstudiante

---

## 🔗 VARIABLES GLOBALES Y CONFIGURACIÓN

### Comunes en ambos archivos:
```python
BASE_DIR = Path(__file__).resolve().parent
ESTUDIANTES_FILE = BASE_DIR / "estudiantes.xlsx"
PREGUNTAS_FILE = BASE_DIR / "preguntas.xlsx"
DB_FILE = BASE_DIR / "sistema.db"
```

### Colores (definidos en app.py, línea ~1500):
```python
COLOR_PRIMARIO = "#0066cc"
COLOR_SECUNDARIO = "#f5f7fa"
COLOR_TEXTO = "#1a1a1a"
COLOR_BORDE = "#e0e0e0"
COLOR_EXITO = "#51cf66"
COLOR_ADVERTENCIA = "#ff6b6b"
```

**Ubicación Admin.py**: Las mismas líneas (~últimas 100 líneas)  
**Estado**: ✅ SINCRONIZADAS

---

## 🔐 AUTENTICACIÓN Y DIFERENCIAS EN LOGIN

### Funciones únicas en app.py (NO en Admin.py):
1. `validar_maestra()` - Verifica clave maestra en BD
2. `requerir_clave_maestra()` - Decide si pedir clave
3. `ingresar()` - Flujo mejorado de login con clave maestra

**Impacto**: app.py tiene seguridad mejorada para acceso SuperAdmin

---

## ✅ CHECKLIST DE SINCRONIZACIÓN

### Paso 1: RESOLVER ERRORES CRÍTICOS
- [ ] Crear función `obtener_todas_respuestas_desde_bd()` en Admin.py
- [ ] Crear función `cargar_grados()` en Admin.py
- [ ] Agregar importación de `normalizar_grado` en app.py
- [ ] Agregar importación de `examen_esta_activo` en app.py

### Paso 2: VALIDAR IMPORTACIONES
- [ ] Verificar que todas las funciones importadas en app.py existen en Admin.py
- [ ] Ejecutar app.py y verificar que no hay ImportError

### Paso 3: SINCRONIZAR CLASES
- [ ] Revisar que ModuloEstudiante en app.py tenga todos los métodos de Admin.py
- [ ] Verificar compatibilidad con mejoras de reanudación

### Paso 4: PRUEBAS
- [ ] Ejecutar login con usuario estudiante
- [ ] Ejecutar examen y verificar guardado de respuestas
- [ ] Verificar reanudación de examen interrumpido
- [ ] Login de docente
- [ ] Exportar reportes

---

## 📝 CÓDIGO A COPIAR DE ADMIN.PY HACIA APP.PY (SI NO ESTÁ)

### Función: `normalizar_grado()`
**Ubicación en Admin**: Línea 607  
**Acción**: Verificar que esté en app.py o agregar a importación

### Función: `examen_esta_activo()`
**Ubicación en Admin**: Línea 1443  
**Acción**: Agregar a importación en app.py

---

## 🎯 RECOMENDACIÓN FINAL

### Estrategia de Sincronización Recomendada:

**OPCIÓN A - Consolidar hacia Admin.py (RECOMENDADO)**
1. Mover `obtener_todas_respuestas_desde_bd()` a Admin.py
2. Mover `cargar_grados()` a Admin.py
3. Actualizar ModuloEstudiante en Admin.py con mejoras de app.py
4. Hacer que app.py solo importe de Admin.py (delegación total)

**OPCIÓN B - App.py como versión mejorada**
1. Mantener app.py como reimplementación mejorada
2. Copia selectiva de Admin.py
3. Ambos archivos coexisten con funcionalidades diferentes

**Recomendación**: **OPCIÓN A** - Consolidar hacia Admin.py

---

## 📞 PRÓXIMOS PASOS

1. **Inmediato**: Crear las 2 funciones faltantes en Admin.py
2. **Corto plazo**: Actualizar importaciones en app.py
3. **Mediano plazo**: Integrar mejoras de app.py en Admin.py
4. **Largo plazo**: Mantener single source of truth (Admin.py como módulo principal)

---

**Generado el**: 5 de marzo de 2026  
**Responsable del análisis**: GitHub Copilot
