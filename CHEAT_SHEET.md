# 📌 CHEAT SHEET - Banco de Preguntas

## Importar
```python
from banco_preguntas_profesional import BancoPreguntasProfesional
banco = BancoPreguntasProfesional("preguntas.xlsx")
```

## 📖 LECTURA

### Cargar todas
```python
df = banco.obtener_todas_preguntas()
```

### Filtrar
```python
df = banco.obtener_preguntas_filtradas(
    grado="5",
    area="Matemáticas",
    evaluacion="Trimestral"
)
```

### Obtener una
```python
pregunta = banco.obtener_pregunta_por_id("P001")
# Retorna dict o None
```

### Disponibles
```python
grados = banco.obtener_grados_disponibles()
areas = banco.obtener_areas_disponibles(grado="5")
evals = banco.obtener_evaluaciones_disponibles(grado="5", area="Matemáticas")
```

---

## ✏️ EDICIÓN

### Guardar nueva
```python
datos = {
    'id': 'P001',
    'evaluacion': 'Trimestral',
    'area': 'Matemáticas',
    'grado': '5',
    'enunciado': '¿Cuánto es 2+2?',
    'opcion_a': '3',
    'opcion_b': '4',
    'opcion_c': '5',
    'opcion_d': '6',
    'correcta': 'B',
    # Opcional:
    'periodo': '1',
    'id_contexto': 'C001',
    'contexto': 'En una tienda...',
    'imagen': ''
}
exitoso, msg = banco.guardar_pregunta('P001', datos, es_nueva=True)
```

### Editar existente
```python
exitoso, msg = banco.guardar_pregunta('P001', datos, es_nueva=False)
```

### Eliminar
```python
exitoso, msg = banco.eliminar_pregunta("P001")
```

---

## 📦 IMPORTACIÓN

### Importar masivo
```python
resumen = banco.importar_masivo('archivo.xlsx')
# {'exitosas': 45, 'duplicadas_id': 2, 'duplicadas_enunciado': 3, 
#  'rechazadas_validacion': 5, 'total_procesadas': 55, 'detalles': [...]}
```

### Ver reporte
```python
reporte = banco.generar_reporte_importacion(resumen)
print(reporte)
```

---

## ✓ VALIDACIÓN

### Verificar ID
```python
existe = banco.id_existe("P001")  # True/False
```

### Verificar enunciado
```python
existe = banco.enunciado_existe("¿Cuánto es 2+2?")  # True/False
```

### Validación completa
```python
advs = banco.validar_integridad()
# {'ids_duplicados': [], 'enunciados_duplicados': [],
#  'campos_vacios': [], 'opciones_correctas_invalidas': []}
```

---

## 📊 ESTADÍSTICAS

```python
stats = banco.obtener_estadisticas()
# {'total_preguntas': 245,
#  'grados_unicos': 7,
#  'areas_unicas': 5,
#  'evaluaciones_unicas': 3,
#  'preguntas_sin_imagen': 150,
#  'preguntas_con_imagen': 95}
```

---

## 🎯 ESTRUCTURA MÍNIMA DEL EXCEL

```
id | evaluacion | area | grado | enunciado | opcion_a | opcion_b | opcion_c | opcion_d | correcta
```

| Campo | Tipo | Requerido |
|-------|------|-----------|
| id | String | ✓ Único |
| evaluacion | String | ✓ |
| area | String | ✓ |
| grado | String | ✓ |
| enunciado | String | ✓ Único |
| opcion_a | String | ✓ |
| opcion_b | String | ✓ |
| opcion_c | String | ✓ |
| opcion_d | String | ✓ |
| correcta | String | ✓ A/B/C/D |
| periodo | String | □ |
| id_contexto | String | □ |
| contexto | String | □ |
| imagen | String | □ |

---

## ❌ ERRORES COMUNES

```python
# ✗ Campo requerido vacío
# Error: "Campo requerido vacío: enunciado"

# ✗ ID duplicado
# Error: "El ID 'P001' ya existe"

# ✗ Enunciado duplicado
# Error: "Este enunciado ya existe en el banco"

# ✗ Opción correcta inválida
# Error: "La opción correcta debe ser A, B, C o D"

# ✗ Archivo no encontrado
# Error: "ERROR: Archivo no encontrado: importar.xlsx"
```

---

## 🔌 INTEGRACIÓN EN MODULO_SUPERADMIN.PY

```python
# Opción 1: Reemplazo del método (recomendado)
def _build_preguntas_tab(self):
    from interfaz_banco_preguntas import InterfazBancoPreguntasAvanzada
    InterfazBancoPreguntasAvanzada._build_preguntas_tab_mejorada(self)

# Opción 2: Usar el script automático
python integrar_banco_preguntas.py
```

---

## 📝 EJEMPLO COMPLETO

```python
from banco_preguntas_profesional import BancoPreguntasProfesional

# 1. Crear instancia
banco = BancoPreguntasProfesional()

# 2. Obtener disponibles
grados = banco.obtener_grados_disponibles()

# 3. Filtrar
df = banco.obtener_preguntas_filtradas(grado='5')

# 4. Agregar
nuevas = {
    'id': 'NEW001',
    'evaluacion': 'Trimestral',
    'area': 'Matemáticas',
    'grado': '5',
    'enunciado': '¿Cuál es la capital?',
    'opcion_a': 'Bogotá',
    'opcion_b': 'Medellín',
    'opcion_c': 'Cali',
    'opcion_d': 'Barranquilla',
    'correcta': 'A'
}
banco.guardar_pregunta('NEW001', nuevas, es_nueva=True)

# 5. Importar masivo
resumen = banco.importar_masivo('importar.xlsx')
print(f"Importadas: {resumen['exitosas']}")

# 6. Validar
advs = banco.validar_integridad()
if not any(advs.values()):
    print("✓ Banco íntegro")

# 7. Estadísticas
stats = banco.obtener_estadisticas()
print(f"Total: {stats['total_preguntas']}")
```

---

## 🚀 FUNCIONES RÁPIDAS (Sin crear instancia)

```python
from banco_preguntas_profesional import (
    cargar_preguntas_desde_excel,
    guardar_cambios_excel,
    eliminar_pregunta,
    importar_preguntas_masivo
)

# Cargar
df = cargar_preguntas_desde_excel()

# Guardar
guardar_cambios_excel(df)

# Eliminar
exitoso, msg = eliminar_pregunta("P001")

# Importar
resumen = importar_preguntas_masivo("importar.xlsx")
```

---

## 🎨 INTERFAZ TKINTER

### Botones disponibles
- ➕ **Agregar**: Nueva pregunta
- ✏️ **Editar**: Pregunta seleccionada
- 🗑️ **Eliminar**: Pregunta seleccionada
- 📥 **Importar masivo**: Con validación
- 📤 **Exportar**: Preguntas filtradas
- ✓ **Validar integridad**: Chequeo completo

### Filtros
- **Grado**: Automáticamente cargado
- **Área**: Dependiente del grado
- **Evaluación**: Dependiente de grado + área

### TreeView columns
```
ID | EVALUACION | AREA | GRADO | ENUNCIADO | CORRECTA | IMAGEN
```

---

## 💻 LÍNEA DE COMANDOS

```bash
# Test completo
python test_banco_preguntas.py

# Integración automática (modifica modulo_superadmin.py)
python integrar_banco_preguntas.py

# Usar interactivamente
python
>>> from banco_preguntas_profesional import BancoPreguntasProfesional
>>> banco = BancoPreguntasProfesional()
>>> banco.obtener_grados_disponibles()
```

---

## 📚 ARCHIVOS PRINCIPALES

| Archivo | Propósito |
|---------|-----------|
| `banco_preguntas_profesional.py` | Lógica (backend) |
| `interfaz_banco_preguntas.py` | UI (frontend) |
| `test_banco_preguntas.py` | Tests |
| `integrar_banco_preguntas.py` | Setup automático |
| `README_BANCO_PREGUNTAS.md` | Documentación completa |

---

## ⚡ ATAJOS ÚTILES

```python
# Crear archivo como respaldo
import shutil
shutil.copy('preguntas.xlsx', 'preguntas_backup.xlsx')

# Listar todos los ids
ids = banco.obtener_todas_preguntas()['id'].tolist()

# Contar por grado
cuenta = banco.obtener_todas_preguntas().groupby('grado').size()

# Preguntas sin imagen
sin_img = len(banco.obtener_estadisticas()['preguntas_sin_imagen'])

# Buscar palabra en enunciados
df = banco.obtener_todas_preguntas()
df[df['enunciado'].str.contains('palabra', case=False)]
```

---

**Última actualización**: Marzo 2026 | Estado: ✅ Listo
