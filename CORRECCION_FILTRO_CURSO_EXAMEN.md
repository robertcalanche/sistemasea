# Corrección: Filtro de Curso en Generación de Exámenes

## 🔍 Problema Identificado

El módulo **Super Admin → Generar Examen** no estaba filtrando correctamente por curso:
- ❌ No cargaba la lista de estudiantes cuando se seleccionaba un curso
- ❌ Había confusión entre qué debería filtrar por curso y qué no

## ✅ Solución Implementada

Se aclaró y corrigió el comportamiento del sistema:

### 1. **Banco de Preguntas** (SIN filtro de curso)
- Las preguntas se filtran **solo por GRADO + ÁREA + EVALUACIÓN**
- El mismo conjunto de preguntas se usa para TODOS los cursos del grado
- Motivo: Un grado debe tener el mismo contenido de evaluación sin importar el curso

### 2. **Lista de Estudiantes** (CON filtro de curso)
- Los estudiantes se filtran por **GRADO + CURSO** cuando se selecciona un curso
- Si NO se especifica curso: se generan exámenes para TODOS los estudiantes del grado
- Motivo: Permite generar exámenes específicos para un curso o para todo el grado

### 3. **Generación de Exámenes**
- **Mismo examen** (mismas preguntas) para todos los cursos del mismo grado
- **Archivos diferentes** para cada estudiante (uno por curso si se especifica)
- Los nombres incluyen el curso del estudiante individual

## 📝 Cambios en el Código

### Archivo: `modulo_superadmin.py`

#### Función `_do_generate_exams`

**Antes:**
```python
# Cargaba estudiantes solo por grado, ignoraba curso
alumnos = self.estudiantes_df[
    self.estudiantes_df["grado"].astype(str) == str(grado)
].to_dict(orient="records")
```

**Después:**
```python
# Filtra por grado Y curso (cuando curso se especifica)
df_filtered = self.estudiantes_df[
    self.estudiantes_df["grado"].astype(str) == str(grado)
]
# filtrar también por curso si se proporcionó
if curso_final:
    df_filtered = df_filtered[
        df_filtered["curso"].astype(str) == str(curso_final)
    ]
alumnos = df_filtered.to_dict(orient="records")
```

#### Docstring actualizado:

```python
"""Genera pdfs para los filtros indicados.

Las preguntas se filtran SOLO por grado+área+evaluación. El parámetro
``grado`` determina el banco de preguntas que se utilizará, sin importar
el valor de ``curso``.

El parámetro ``curso`` opcional solo se utiliza para:
- Filtrar la LISTA DE ESTUDIANTES (grado + curso) cuando se genera
  para todos los estudiantes del grado (``estudiante=None``).
- En el nombre del archivo generado.

Es decir: el mismo examen (preguntario) se aplica a todos los cursos
del grado, pero solo se generan archivos para los estudiantes del
curso seleccionado.
"""
```

## 🧪 Comportamiento Verificado

### Caso 1: Generar examen para Grado 5, Curso 01
```python
msa._do_generate_exams(
    out_dir,
    grado="5",
    area="Ciencias Sociales",
    evaluacion="Primera Evaluación",
    curso="01",  # ← FILTRA ESTUDIANTES
    # Preguntas vienen del grado 5 (sin considerar curso)
)
```
**Resultado:** Se generan PDFs **solo para estudiantes de 5-01**

### Caso 2: Generar examen para Grado 5 (SIN especificar curso)
```python
msa._do_generate_exams(
    out_dir,
    grado="5",
    area="Ciencias Sociales",
    evaluacion="Primera Evaluación",
    curso=None,  # ← NO FILTRA POR CURSO
)
```
**Resultado:** Se generan PDFs **para TODOS los estudiantes del grado 5** (5-01, 5-02, 5-03, etc.)

## 📊 Ejemplo de Flujo Correcto

1. **Docente selecciona:** Grado 5 → Curso 01 → Ciencias Sociales → Primera
2. **Sistema carga:**
   - ✅ Preguntas: grado 5 (todas las preguntas de CS Primera del grado 5)
   - ✅ Estudiantes: grado 5 AND curso 01 (solo estudiantes de 5-01)
3. **Genera examen:**
   - Mismo conjunto de preguntas para ambos cursos si lo hace después
   - Archivos `Examen_5_01_...` para estudiantes de 5-01
   - Archivos `Examen_5_02_...` si se ejecuta para curso 02

## ⚙️ Detalles Técnicos

| Componente | Filtra por | Razón |
|-----------|----------|-------|
| **Preguntas** | Grado + Área + Evaluación | Contenido igual para todos los cursos |
| **Estudiantes** | Grado + Curso (si se especifica) | Generar solo para el curso seleccionado |
| **Examen PDF** | Individual por estudiante | Número de documento único |
| **Nombre archivo** | Incluye curso del alumno | Identificación clara del grupo |

## ✨ Beneficios

1. **Consistencia:** Todos los estudiantes del grado reciben el mismo examen
2. **Flexibilidad:** Permite generar para un curso o para todo el grado
3. **Claridad:** Nombres de archivo incluyen el curso del estudiante
4. **Escalabilidad:** Funciona con n cursos por grado

## 🔧 Sincronización en Interfaz

El combobox de curso en la interfaz (`cb_examen_curso`):
- ✅ Se usa para filtrar estudiantes
- ❌ NO afecta la selección de preguntas
- ✅ Se incluye en los nombres de archivo

## 📌 Notas Importantes

- Si el usuario NO selecciona un curso, se generan exámenes para TODOS los estudiantes del grado
- Las preguntas NUNCA varían por curso, solo por grado
- El filtro de curso es **opcional** - si no se especifica, aplica a todo el grado
