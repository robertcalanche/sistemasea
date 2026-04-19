# ⚡ GUÍA RÁPIDA: Módulo de Matrícula (v2.0)

## 🎯 Orden de Columnas del Excel (IMPORTANTE)

```
sede | jornada | grado | curso | nombre | tipodoc | documento | fechana | telefono | celular | email | genero | tipo_sangre | estado
```

**Usa el archivo `plantilla_estudiantes.xlsx` como referencia.**

---

## 🔤 Códigos a Usar en el Excel

### Jornada
- `M` = Mañana
- `T` = Tarde  
- `N` = Nocturna

### Género
- `M` = Masculino
- `F` = Femenino

### Estado Académico
- `MA` = Matriculado
- `GR` = Graduado
- `TR` = Trasladado
- `RE` = Retirado

### Tipo de Documento
Usa códigos cortos (se convertirán automáticamente):
- `RC` = Registro civil
- `TI` = Tarjeta identidad
- `CC` = Cédula de ciudadanía
- `CE` = Cédula extranjería
- `PA` = Pasaporte
- [Ver lista completa en CAMBIOS_MODULO_MATRICULA.md]

---

## 📥 Pasos para Importar Estudiantes

1. **Abrir SuperAdmin** → Pestaña "Gestor Matrícula"
2. **Clic en "Importar masivo"**
3. **Seleccionar archivo Excel** con tus datos
4. **Sistema valida automáticamente:**
   - Convierte códigos a valores completos
   - Valida campos obligatorios
   - Detecta duplicados
5. **Mensaje de confirmación** cuando se complete

---

## ➕ Agregar Estudiante Manual

1. **Clic en "Agregar"**
2. **Llenar el formulario:**
   - Sede, Jornada, Grado, Curso (obligatorios)
   - Nombre, Tipo documento, Documento (obligatorios)
   - Fecha nacimiento, Teléfono, Celular, Email
   - Género, Tipo sangre, Estado académico
3. **Clic "OK" para guardar**

---

## ✏️ Editar Estudiante

1. **Seleccionar estudiante en la tabla**
2. **Clic en "Editar"**
3. **Modificar los datos que necesites**
4. **Clic "OK" para guardar**

---

## 🔄 Cambiar de Curso

### ✨ NUEVA FUNCIONALIDAD - Cambiar múltiples estudiantes a la vez

1. **Seleccionar uno o varios estudiantes** en la tabla
2. **Clic en "Cambiar de curso"**
3. **Se abre ventana con campos:**
   - Nuevo Grado (ej: 5)
   - Nuevo Curso (ej: 02)
   - Nueva Jornada (opcional)
4. **Clic "Aplicar"**
5. **Estudiantes actualizados** ✅

### Casos de Uso
- Estudiantes de 4°01 → Promoción a 5°01
- Cambio de turno (Mañana → Tarde)
- Reorganización de grupos

---

## 🗑️ Eliminar Estudiante

1. **Seleccionar estudiante**
2. **Clic en "Eliminar"**
3. **Confirmar eliminación**
4. **Estudiante removido de la base de datos**

---

## ⚠️ Validaciones Automáticas

El sistema valida automáticamente:

| Campo | Validación |
|-------|-----------|
| Documento | No puede estar vacío |
| Grado | Debe especificarse |
| Curso | Debe especificarse |
| Jornada | Mañana / Tarde / Nocturna |
| Estado | Matriculado / Graduado / Trasladado / Retirado |

**Si falta algo o hay error:** El sistema muestra el número de fila problématica.

---

## 📝 Campos Permitidos

- **Documento**: Alfanumérico (ejemplo: `1234567890`, `CE-ABC123`, etc.)
- **Nombre**: Texto completo
- **Fecha de nacimiento**: Formato YYYY-MM-DD (ej: 2010-05-15)
- **Teléfono/Celular**: Números y símbolos de formato

---

## 💾 ¿Dónde se guardan los datos?

- **Archivo Excel principal**: `estudiantes.xlsx`
- **Ubicación**: Raíz del proyecto
- Se guarda automáticamente después de cada operación

---

## 🪛 Troubleshooting

### Problema: "Archivo incompleto - Columnas faltantes"
**Solución:** Verifica que el Excel tenga exactamente estas columnas en este orden:
```
sede, jornada, grado, curso, nombre, tipodoc, documento, fechana, 
telefono, celular, email, genero, tipo_sangre, estado
```

### Problema: "El documento es obligatorio"
**Solución:** Asegúrate de completar el campo "Número de documento" en cada fila.

### Problema: No se ven cambios
**Solución:** Haz clic en el botón **"Actualizar Datos"** en la parte inferior.

---

## 📞 Resumen de Botones

| Botón | Acción |
|-------|--------|
| Importar masivo | Carga múltiples estudiantes desde Excel |
| Agregar | Crea un nuevo estudiante manualmente |
| Editar | Modifica datos de un estudiante seleccionado |
| Cambiar de curso | Actualiza grado/curso/jornada de uno o varios |
| Eliminar | Borra estudiante de la BD |
| Actualizar Datos | Recarga la tabla con datos más recientes |

---

**Documento de referencia rápida v2.0**  
Para detalles completos, consulta: `CAMBIOS_MODULO_MATRICULA.md`
