# 📚 BANCO DE PREGUNTAS - GUÍA DE USO

## 🎯 Acceso

Para acceder al módulo SuperAdmin con el Banco de Preguntas:

1. Ejecuta `Admin.py` o `app.py`
2. En el campo de documento, ingresa: `admin`
3. Ingresa la clave maestra: `admin123` (u otra configurada)
4. Haz clic en la pestaña **"Banco de Preguntas"**

---

## 📋 Interfaz Principal

### Panel de Filtros
En la parte superior encontrarás tres desplegables para filtrar:
- **Grado**: Selecciona el grado (4, 5, etc.) o "(Todos)" para verlas todas
- **Área**: Filtra por área (Historia de Colombia, Ciencias Sociales, etc.)
- **Evaluación**: Filtra por tipo de evaluación

### Tabla de Preguntas
Muestra todas las preguntas disponibles con las siguientes columnas:
- **ID**: Identificador único
- **Evaluación**: Nombre de la evaluación
- **Área**: Área de conocimiento
- **Período**: Período o bimestre
- **Grado**: Grado académico
- **Enunciado**: Pregunta
- **Opciones A, B, C, D**: Respuestas posibles
- **Correcta**: Respuesta correcta
- **Imagen**: Si tiene imagen asociada (✓)

---

## ✨ OPERACIONES CON PREGUNTAS

### 1️⃣ VER PREGUNTAS
- Se cargan automáticamente al abrir la pestaña
- Usa los filtros para acotar el listado
- Desplázate horizontalmente para ver todas las columnas

### 2️⃣ EDITAR PREGUNTAS

**Opción A: Doble clic**
- Haz **doble clic** en cualquier pregunta de la tabla
- Se abrirá el formulario de edición
- Modifica los campos que necesites
- Haz clic en **"Guardar"**

**Opción B: Botón Editar**
- Selecciona una pregunta haciendo clic en ella
- Haz clic en el botón ✏️ **"Editar"** en la barra superior
- Se abrirá el formulario de edición

**Opción C: Menú contextual**
- Haz **clic derecho** sobre una pregunta
- Selecciona **"✏️ Editar"**
- Se abrirá el formulario de edición

### 3️⃣ ELIMINAR PREGUNTAS

**Opción A: Botón Eliminar**
- Selecciona una pregunta
- Haz clic en el botón 🗑️ **"Eliminar"**
- Confirma la eliminación

**Opción B: Menú contextual**
- Haz **clic derecho** sobre una pregunta
- Selecciona **"🗑️ Eliminar"**
- Confirma la eliminación

### 4️⃣ AGREGAR NUEVAS PREGUNTAS
- Haz clic en el botón ➕ **"Agregar"**
- Se abrirá un formulario vacío
- Completa todos los campos:
  - Evaluación
  - Área
  - Período
  - Grado
  - ID del contexto (opcional)
  - Contexto (opcional)
  - Enunciado (obligatorio)
  - Opciones A, B, C, D (obligatorias)
  - Respuesta correcta: A, B, C o D
  - Imagen: (puedes seleccionar una imagen)
- Haz clic en **"Guardar"**

---

## 🔧 ACCIONES ADICIONALES

### Importar Preguntas en Masa
- Botón 📥 **"Importar masivo"**
- Selecciona un archivo Excel con preguntas
- Se importarán automáticamente

### Exportar Preguntas
- Botón 📤 **"Exportar"**
- Se descargará un Excel con las preguntas filtradas

### Validar Integridad
- Botón ✓ **"Validar integridad"**
- Verifica que todas las preguntas tengan los campos correctos

### Limpiar Filtros
- Botón **"Limpiar filtros"**
- Vuelve a mostrar todas las preguntas

---

## 📊 INFORMACIÓN ÚTIL

### Estadísticas
En la parte inferior de los filtros verás:
- **Total**: Número total de preguntas
- **Grados**: Cantidad de grados únicos
- **Áreas**: Cantidad de áreas únicas
- **Evaluaciones**: Cantidad de evaluaciones únicas
- **Con imagen**: Preguntas que tienen imagen asociada

### Estado Actual
El banco de preguntas contiene:
- ✅ **48 preguntas** totales
- ✅ **2 grados** (4, 5)
- ✅ **2 áreas** (Historia de Colombia, Ciencias Sociales)
- ✅ **3 evaluaciones** diferentes
- ✅ **16 preguntas** con imagen

---

## ⚠️ RECOMENDACIONES

1. **Hacer copias de seguridad**: Siempre copia `preguntas.xlsx` antes de hacer cambios
2. **Validar datos**: Usa el botón "Validar integridad" regularmente
3. **Usar filtros**: Filtra por grado/área para trabajar con menos preguntas
4. **Revisar imágenes**: Si editas una pregunta con imagen, verifica que siga siendo válida
5. **Actualizar**: Después de agregar/editar, el listado se actualiza automáticamente

---

## 🛠️ SOLUCIÓN DE PROBLEMAS

### No se ven preguntas
- Verifica que `preguntas.xlsx` exista en la carpeta del proyecto
- Limpia los filtros con el botón "Limpiar filtros"
- Reinicia el módulo SuperAdmin

### Error al editar/eliminar
- Revisa que tengas permisos de escritura en la carpeta
- Cierra otras aplicaciones que puedan tener abierto el archivo Excel
- Intenta nuevamente

### Imagen no se carga
- Verifica que la imagen exista en la carpeta `imagenes_preguntas/`
- El nombre del archivo debe coincidir exactamente
- Usa formatos: JPG, PNG, GIF

---

**Para más ayuda, consulta con el administrador del sistema.**
