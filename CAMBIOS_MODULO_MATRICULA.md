# 📋 Cambios Realizados en el Módulo de Matrícula

## Resumen de Cambios

Se ha actualizado completamente el sistema de matrícula para que coincida con el formato Excel utilizado por la institución educativa y se han mejorado significativamente las funcionalidades de gestión académica.

---

## 1️⃣ NUEVO ORDEN DE COLUMNAS DEL EXCEL

El archivo `estudiantes.xlsx` ahora debe tener las columnas en el siguiente orden exacto:

```
sede | jornada | grado | curso | nombre | tipodoc | documento | fechana | telefono | celular | email | genero | tipo_sangre | estado
```

**Descripción de columnas:**
- `sede`: Nombre de la sede educativa
- `jornada`: Jornada académica (M, T, N)
- `grado`: Nivel académico (1, 2, 3, ..., 11)
- `curso`: Identificador del curso (01, 02, 03, etc.)
- `nombre`: Nombre completo del estudiante
- `tipodoc`: Tipo de documento (códigos, ver sección 6)
- `documento`: Número de identificación (alfanumérico)
- `fechana`: Fecha de nacimiento (formato: YYYY-MM-DD)
- `telefono`: Teléfono fijo
- `celular`: Número de celular
- `email`: Correo electrónico
- `genero`: Género (F o M)
- `tipo_sangre`: Tipo de sangre
- `estado`: Estado académico (MA, GR, TR, RE)

### 📎 Archivo Plantilla
Se proporciona `plantilla_estudiantes.xlsx` con el formato correcto para que copies tus datos.

---

## 2️⃣ CAMBIO: GRUPO → CURSO

**Cambio sistemático en toda la aplicación:**

| Componente | Antes | Después |
|-----------|-------|---------|
| Base de datos | `grupo` | `curso` |
| Formulario | "Grupo" | "Curso" |
| TreeView | Columna "grupo" | Columna "curso" |
| Importación Excel | Busca `grupo` | Busca `curso` |
| Validaciones | Valida `grupo` | Valida `curso` |

---

## 3️⃣ CONVERSIÓN AUTOMÁTICA: GÉNERO

| Excel | Sistema |
|-------|---------|
| **F** | Femenino |
| **M** | Masculino |

✅ La conversión ocurre automáticamente al importar del Excel.

---

## 4️⃣ CONVERSIÓN AUTOMÁTICA: JORNADA

| Excel | Sistema |
|-------|---------|
| **M** | Mañana |
| **T** | Tarde |
| **N** | Nocturna |

✅ La conversión ocurre automáticamente al importar del Excel.

---

## 5️⃣ CONVERSIÓN AUTOMÁTICA: ESTADO ACADÉMICO

| Excel | Sistema |
|-------|---------|
| **MA** | Matriculado |
| **GR** | Graduado |
| **TR** | Trasladado |
| **RE** | Retirado |

⚠️ El sistema **ya no usa "Activo"**. Se cambió por "Matriculado".

✅ La conversión ocurre automáticamente al importar del Excel.

---

## 6️⃣ CONVERSIÓN AUTOMÁTICA: TIPO DE DOCUMENTO

El sistema acepta códigos del Excel y los convierte a nombres completos:

| Código | Nombre Completo |
|--------|-----------------|
| RC | Registro civil de nacimiento |
| TI | Tarjeta de identidad |
| NUIP | Número único de identificación personal |
| CC | Cédula de ciudadanía |
| CE | Cédula de extranjería |
| PPT | Permiso de protección temporal |
| PEP | Permiso especial permanencia |
| RUMV | Registro único de migrantes venezolanos |
| PA | Pasaporte |
| PN | Partida de nacimiento |
| NIP | Número de identificación personal |
| NES | Número establecido por la secretaría |
| TMF | Tarjeta movilidad fronteriza |
| CCA | Certificado de cabildo |
| VISA | Visa |

✅ Puedes usar tanto los códigos cortos como los nombres completos en el formulario manual.

---

## 7️⃣ DOCUMENTOS ALFANUMÉRICOS ✅

El campo `documento` ahora permite:
- ✅ Números puros: `1234567890`
- ✅ Letras: `ABCDEF123`
- ✅ Mezcla alfanumérica: `CE-3456789-Z`

❌ Se eliminó la validación estrictamente numérica.

**El sistema convierte automáticamente a texto para mayor flexibilidad.**

---

## 8️⃣ VALIDACIONES MEJORADAS

El sistema valida automáticamente:

### ✅ Campos Obligatorios
- **Documento**: No puede estar vacío
- **Grado**: Debe especificarse (ej: 3, 4, 5)
- **Curso**: Debe especificarse (ej: 01, 02, 03)
- **Jornada**: Debe ser Mañana, Tarde o Nocturna
- **Estado académico**: Debe ser válido (Matriculado, Graduado, Trasladado, Retirado)

### 🚫 Validación de Duplicados
- El campo documento no puede aparecer dos veces

### ⚠️ Mensajes de Error
Si hay problemas al importar un Excel, el sistema mostrará:
- Número de la fila con error
- Qué columnas faltaban
- Qué validación falló

---

## 9️⃣ NUEVO BOTÓN: "CAMBIAR DE CURSO"

### Ubicación
En la pestaña "Gestor Matrícula" del módulo SuperAdmin.

### Funcionalidades
✅ **Seleccionar múltiples estudiantes** a la vez  
✅ **Cambiar grado y curso** simultáneamente  
✅ **Actualizar jornada** (opcional)

### Ejemplo de Uso
1. En la tabla de estudiantes, selecciona uno o más estudiantes
2. Haz clic en el botón **"Cambiar de curso"**
3. Se abre una ventana donde especificas:
   - Nuevo grado (ej: 5)
   - Nuevo curso (ej: 02)
   - Nueva jornada (ej: Tarde) - opcional
4. Haz clic en **"Aplicar"**
5. El sistema actualiza todos los estudiantes seleccionados

### Casos de Uso
- 📚 Promoción de estudiantes (4°01 → 5°01)
- 🔄 Reorganización de grupos
- 📋 Cambios de jornada

---

## 🟡 COMPATIBILIDAD

Se mantienen todas las funciones existentes:
- ✅ **Importar masivo** (mejorado con conversiones y validaciones)
- ✅ **Agregar estudiante** (con nuevo formulario)
- ✅ **Editar estudiante** (con nuevos campos)
- ✅ **Eliminar estudiante**
- ✅ **Cambio de grado** (ahora es "Cambiar de curso" con más opciones)

---

## 📝 FUNCIONES DE CONVERSIÓN DISPONIBLES

En el código, puedes usar estas funciones directamente:

```python
# Conversión de códigos
convertir_genero("M")              # Masculino
convertir_jornada("T")             # Tarde
convertir_estado_academico("MA")   # Matriculado
convertir_tipo_documento("CC")     # Cédula de ciudadanía
```

---

## 🚀 CÓMO USAR

### 1. Preparar el Excel
- Copia `plantilla_estudiantes.xlsx`
- Rellena con tus datos respetando el orden de columnas
- Usa los códigos especificados (M/F para género, MA/GR/TR/RE para estado, etc.)

### 2. Importar Estudiantes
1. Abre el módulo SuperAdmin
2. Ve a la pestaña "Gestor Matrícula"
3. Haz clic en **"Importar masivo"**
4. Selecciona tu archivo Excel
5. El sistema valida automáticamente y convierte los códigos

### 3. Gestionar Estudiantes
- **Agregar**: Llena el formulario con los datos
- **Editar**: Selecciona un estudiante y haz clic en "Editar"
- **Cambiar de curso**: Selecciona uno o varios y haz clic en el botón
- **Eliminar**: Selecciona y confirma la eliminación

---

## 📊 EJEMPLO DE EXCEL CORRECTO

```
sede               | jornada | grado | curso | nombre            | tipodoc | documento      | fechana    | telefono   | celular     | email              | genero | tipo_sangre | estado
Sede Principal     | M       | 1     | 01    | Juan Pérez        | CC      | 1234567890     | 2010-05-15 | 6012345678 | 3001234567  | juan@email.com     | M      | O+          | MA
Sede Principal     | T       | 2     | 02    | María García      | CC      | 0987654321     | 2009-08-20 | 6021234567 | 3101234567  | maria@email.com    | F      | AB-         | MA
Sede Secundaria    | N       | 10    | 01    | Carlos López      | TI      | 987654321      | 2005-03-10 | 6034567890 | 3201234567  | carlos@email.com   | M      | B-          | MA
```

---

## ⚡ CAMBIOS TÉCNICOS

### Archivos Modificados
- `modulo_superadmin.py`: Actualización del gestor de matrícula

### Funciones Nuevas
- `convertir_genero()`
- `convertir_jornada()`
- `convertir_estado_academico()`
- `convertir_tipo_documento()`
- `estudiante_cambiar_curso()` (reemplaza `estudiante_cambiar_grado()`)

### Cambios en BD
Las futuras instancias usan `curso` en lugar de `grupo`.

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [x] Nuevo orden de columnas implementado
- [x] "Grupo" cambiado a "Curso" en toda la app
- [x] Conversión automática de género (F/M)
- [x] Conversión automática de jornada (M/T/N)
- [x] Conversión automática de estado (MA/GR/TR/RE)
- [x] Conversión automática de tipo de documento
- [x] Documentos alfanuméricos permitidos
- [x] Validaciones mejoradas
- [x] Botón "Cambiar de curso" implementado
- [x] Compatibilidad con funciones existentes
- [x] Plantilla de Excel proporcionada

---

## 📞 SOPORTE

Si tienes preguntas o encuentras problemas:
1. Revisa la plantilla Excel (`plantilla_estudiantes.xlsx`)
2. Verifica que las columnas estén en el orden correcto
3. Asegúrate de usar los códigos especificados (M/F, MA/GR/TR/RE, etc.)

---

**Versión**: 2.0  
**Fecha**: 4 de marzo de 2026  
**Estado**: ✅ Implementado completamente
