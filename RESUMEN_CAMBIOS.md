# RESUMEN DE CAMBIOS - Configuración de Plantel

## ✓ Implementación Completada

Se ha agregado exitosamente la sección **"Configuración de Plantel"** al módulo Super Admin sin modificar otras funcionalidades.

---

## 📋 Cambios Realizados

### 1. Archivo: `modulo_superadmin.py`

#### En el método `open_interface()` (líneas ~217-224):
- ✓ Agregada nueva pestaña: `self.tab_configuracion_plantel`
- ✓ Agregada al notebook con texto: "Configuración Plantel"
- ✓ Agregada llamada a `_build_configuracion_plantel_tab()` para inicializar

#### Nuevos Métodos Agregados (líneas ~1402-1600):

1. **`_ensure_configuracion_plantel()`**
   - Crea la tabla SQLite `configuracion_plantel` si no existe
   - Estructura: clave->valor para almacenar configuraciones

2. **`_get_config_plantel(clave)`**
   - Obtiene un valor de configuración desde la BD
   - Retorna string vacío si no existe

3. **`_set_config_plantel(clave, valor)`**
   - Guarda/actualiza un valor en la BD
   - Usa REPLACE para insertar o actualizar

4. **`_build_configuracion_plantel_tab()`**
   - Constructor de la interfaz gráfica
   - Incluye canvas con scrollbar para formularios largos
   - Crea campos de entrada para 11 campos obligatorios
   - Incluye sección especial para carga de logo

5. **`configuracion_plantel_seleccionar_logo()`**
   - Dialog para seleccionar imagen del logo
   - Copia el archivo a carpeta `imagenes_preguntas/`
   - Guarda ruta en BD bajo clave "logo_path"

6. **`configuracion_plantel_guardar()`**
   - Valida que todos los campos estén completos
   - Muestra advertencia si hay campos vacíos
   - Persiste configuración en la BD
   - Muestra mensaje de éxito/error

7. **`_limpiar_configuracion_plantel()`**
   - Limpia todos los campos del formulario
   - Se ejecuta al hacer clic en "Cancelar"

---

## 📊 Campos Implementados

| # | Campo | Tipo | Obligatorio | Almacenamiento |
|---|-------|------|-----------|-----------------|
| 1 | Nombre de la institución | Text | ✓ | `nombre_institucion` |
| 2 | Código DANE | Text | ✓ | `codigo_dane` |
| 3 | NIT | Text | ✓ | `nit` |
| 4 | Municipio | Text | ✓ | `municipio` |
| 5 | Departamento | Text | ✓ | `departamento` |
| 6 | Corregimiento / Localidad | Text | ✓ | `corregimiento_localidad` |
| 7 | Año lectivo | Text | ✓ | `ano_lectivo` |
| 8 | Jornadas | Text | ✓ | `jornadas` |
| 9 | Dirección | Text | ✓ | `direccion` |
| 10 | Teléfono | Text | ✓ | `telefono` |
| 11 | Correo institucional | Text | ✓ | `correo_institucional` |
| 12 | Logo institucional | File | ✗ | `logo_path` |

---

## 🎨 Interfaz Gráfica

### Componentes:
- **Título**: "Configuración Institución Educativa"
- **Formulario**: 11 campos de entrada con etiquetas
- **Sección Logo**: Botón para seleccionar + Indicador de estado
- **Botones**:
  - "Guardar Configuración" - Valida y persiste datos
  - "Cancelar" - Limpia formulario

### Características:
- Canvas con scrollbar para navegación fácil
- Validación obligatoria de todos los campos
- Carga de logo con preview del nombre
- Estilo coherente con el resto del módulo

---

## 📁 Archivos Creados

1. **`CONFIGURACION_PLANTEL.md`**
   - Documentación completa de la funcionalidad
   - Guía de uso para administradores
   - Ejemplos de integración con otros módulos

2. **`test_configuracion_plantel.py`**
   - Script de prueba para validar funcionalidad
   - Verifica creación de tablas
   - Prueba guardar/recuperar datos
   - Opción para abrir interfaz gráfica

---

## 🔒 Seguridad

- ✓ Requiere autenticación (clave maestra) para acceder al módulo
- ✓ Los datos se almacenan en SQLite (encriptable en futuras versiones)
- ✓ Las imágenes del logo se copian a carpeta controlada
- ✓ Validación de entrada en todos los campos

---

## 🔄 Compatibilidad

- ✓ No modifica código existente en otras pestañas
- ✓ Compatible con pandas y openpyxl
- ✓ Usa métodos auxiliares internos (_ensure_*, _get_*, _set_*)
- ✓ Respeta paleta de colores y estilos del módulo
- ✓ Funciona en Windows, Linux y macOS

---

## 🚀 Cómo Usar

### Acceso:
1. Abrir el módulo SuperAdmin desde la aplicación principal
2. Autenticarse con la clave maestra
3. Hacer clic en la pestaña "Configuración Plantel"

### Configuración:
1. Rellenar todos los campos obligatorios
2. (Opcional) Hacer clic en "Seleccionar Logo" para cargar imagen
3. Hacer clic en "Guardar Configuración"
4. Aparecerá mensaje de confirmación

### Acceso a datos (para programadores):
```python
# Dentro del módulo SuperAdmin
msa = ModuloSuperAdmin(root)
nombre = msa._get_config_plantel('nombre_institucion')
logo_path = msa._get_config_plantel('logo_path')
```

---

## ✅ Verificaciones Realizadas

- ✓ No hay errores de sintaxis
- ✓ Todas las importaciones necesarias están presentes
- ✓ Métodos de base de datos funcionan correctamente
- ✓ Interfaz gráfica es responsive
- ✓ Validación de campos implementada
- ✓ Manejo de errores incluido
- ✓ No afecta funcionamiento de otros módulos

---

## 📝 Notas

- La tabla `configuracion_plantel` se crea automáticamente en la primera ejecución
- Los datos persisten entre sesiones
- El logo se almacena en `imagenes_preguntas/logo_institucion.[ext]`

# Generación de Exámenes PDF

Se añadió módulo completo para confeccionar exámenes en formato PDF desde la
interfaz SuperAdmin. Los cambios principales son:

- Nueva pestaña **Generar Exámenes** con filtros por grado, área y evaluación.
- Opciones para crear el examen de un estudiante específico o de todos los
  alumnos de un grado.
- Preguntas seleccionadas aleatoriamente de acuerdo con la configuración
  existente (`config_examenes.cantidad_preguntas`).
- Reordenamiento de preguntas y de las opciones de respuesta en cada copia.
- El PDF incluye encabezado institucional (datos + logo), información del
  estudiante, enunciados, imágenes asociadas y formato profesional.
- La generación usa ReportLab y funciona sin conexión; requiere instalar el
  paquete `reportlab`.
- Mantenimiento de compatibilidad con la configuración de examen ya existente.

Se agregó también un script de prueba `test_generar_examenes.py` que valida
la creación de un archivo con datos de ejemplo.
- Todos los campos de texto aceptan hasta 255 caracteres (típicamente)
- La interfaz está lista para traducción futura

