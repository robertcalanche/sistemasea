# Configuración de Plantel - Módulo Super Admin

## Descripción
Se ha añadido una nueva pestaña **"Configuración Plantel"** al módulo Super Admin que permite configurar los datos de la institución educativa.

## Ubicación
- **Módulo**: `modulo_superadmin.py`
- **Pestaña**: "Configuración Plantel"
- **Ubicación en interfaz**: Última pestaña después de "Seguridad"

## Campos Obligatorios
La sección requiere completar los siguientes campos:

1. **Nombre de la institución** - Nombre oficial de la escuela/colegio
2. **Código DANE** - Código de identificación del establecimiento educativo
3. **NIT** - Número de Identificación Tributaria
4. **Municipio** - Municipio donde se encuentra la institución
5. **Departamento** - Departamento/Provinicia
6. **Corregimiento / Localidad** - Corregimiento o localidad específica
7. **Año lectivo** - Año académico actual (ej: 2026)
8. **Jornadas** - Jornadas de funcionamiento (ej: Matutina, Vespertina, etc.)
9. **Dirección** - Dirección física completa
10. **Teléfono** - Número de teléfono de contacto
11. **Correo institucional** - Correo electrónico oficial
12. **Logo institucional** - Imagen del logo (PNG, JPG, JPEG, BMP)

## Funcionalidades

### Guardar Configuración
- Valida que todos los campos obligatorios estén completos
- Si falta algún campo, muestra un mensaje indicando cuáles están vacíos
- Una vez completados todos los campos, guarda la configuración en la base de datos SQLite
- Muestra mensaje de confirmación al guardar exitosamente

### Cargar Logo
- Botón "Seleccionar Logo" permite elegir una imagen de la computadora
- El logo se copia automáticamente a la carpeta `imagenes_preguntas/`
- Se guarda con el nombre `logo_institucion.[extensión]`
- Se muestra el nombre del archivo seleccionado en la interfaz

### Cancelar
- El botón "Cancelar" limpia los campos del formulario

## Almacenamiento de Datos
- La configuración se guarda en una tabla SQLite llamada `configuracion_plantel`
- Cada campo se almacena como un par clave-valor
- El logo se guarda como un archivo en la carpeta de imágenes

## Claves Internas de Base de Datos
```
nombre_institucion
codigo_dane
nit
municipio
departamento
corregimiento_localidad
ano_lectivo
jornadas
direccion
telefono
correo_institucional
logo_path
```

## Métodos Disponibles (Para Integración)

### Obtener configuración
```python
valor = modulo.superadmin._get_config_plantel('nombre_institucion')
```

### Establecer configuración
```python
modulo.superadmin._set_config_plantel('nombre_institucion', 'Mi Escuela')
```

## Ejemplos de Uso

### Acceder a la configuración desde otro módulo
```python
from modulo_superadmin import ModuloSuperAdmin

# Dentro de tu código
msa = ModuloSuperAdmin(root)
nombre_institucion = msa._get_config_plantel('nombre_institucion')
logo_path = msa._get_config_plantel('logo_path')
```

## Nota Importante
- La configuración debe completarse antes de usar funcionalidades que dependan de estos datos
- Todos los campos son obligatorios
- El logo es opcional pero recomendado
- Los datos se persisten en la base de datos (resultados.db o sistema.db según configuración)
