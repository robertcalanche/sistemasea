# 🔄 Funciones de Conversión Implementadas

Estas funciones se agregaron al archivo `modulo_superadmin.py` para automatizar la conversión de códigos del Excel al formato completo del sistema.

## 📍 Ubicación en el Código
Las funciones están definidas en las líneas 327-411 de `modulo_superadmin.py`, justo antes de la importación de `InterfazBancoPreguntasAvanzada`.

---

## 1️⃣ `convertir_genero(codigo)`

### Descripción
Convierte códigos de género del Excel al formato completo.

### Parámetros
- `codigo` (str): Valor del Excel ("F", "M", o similar)

### Retorna
- `"Femenino"` si código es "F"
- `"Masculino"` si código es "M"
- El valor original si no coincide

### Ejemplo
```python
convertir_genero("F")  # → "Femenino"
convertir_genero("M")  # → "Masculino"
convertir_genero("O")  # → "O" (no coincide)
```

---

## 2️⃣ `convertir_jornada(codigo)`

### Descripción
Convierte códigos de jornada del Excel al formato completo.

### Parámetros
- `codigo` (str): Valor del Excel ("M", "T", "N", o similar)

### Retorna
- `"Mañana"` si código es "M"
- `"Tarde"` si código es "T"
- `"Nocturna"` si código es "N"
- El valor original si no coincide

### Ejemplo
```python
convertir_jornada("M")  # → "Mañana"
convertir_jornada("T")  # → "Tarde"
convertir_jornada("N")  # → "Nocturna"
convertir_jornada("X")  # → "X" (no coincide)
```

---

## 3️⃣ `convertir_estado_academico(codigo)`

### Descripción
Convierte códigos de estado académico del Excel al formato completo.

### Parámetros
- `codigo` (str): Valor del Excel ("MA", "GR", "TR", "RE", o similar)

### Retorna
- `"Matriculado"` si código es "MA"
- `"Graduado"` si código es "GR"
- `"Trasladado"` si código es "TR"
- `"Retirado"` si código es "RE"
- El valor original si no coincide

### Ejemplo
```python
convertir_estado_academico("MA")  # → "Matriculado"
convertir_estado_academico("GR")  # → "Graduado"
convertir_estado_academico("TR")  # → "Trasladado"
convertir_estado_academico("RE")  # → "Retirado"
convertir_estado_academico("AC")  # → "AC" (no coincide)
```

---

## 4️⃣ `convertir_tipo_documento(codigo)`

### Descripción
Convierte códigos de tipo de documento del Excel al nombre completo.

### Parámetros
- `codigo` (str): Código abreviado del tipo de documento

### Retorna
- Nombre completo del tipo de documento si el código existe
- El código original si no encuentra coincidencia

### Mapeo de Códigos

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

### Ejemplo
```python
convertir_tipo_documento("CC")    # → "Cédula de ciudadanía"
convertir_tipo_documento("PA")    # → "Pasaporte"
convertir_tipo_documento("TI")    # → "Tarjeta de identidad"
convertir_tipo_documento("XYZ")   # → "XYZ" (no existe)
```

---

## ⚙️ Cómo se Usan en la Importación

Cuando importas un Excel masivo, estas funciones se aplican automáticamente:

```python
# En estudiantes_importar() - líneas 992-1003
if "genero" in incoming.columns:
    incoming["genero"] = incoming["genero"].apply(convertir_genero)
if "jornada" in incoming.columns:
    incoming["jornada"] = incoming["jornada"].apply(convertir_jornada)
if "estado" in incoming.columns:
    incoming["estado"] = incoming["estado"].apply(convertir_estado_academico)
if "tipodoc" in incoming.columns:
    incoming["tipodoc"] = incoming["tipodoc"].apply(convertir_tipo_documento)
```

---

## 📋 Tabla de Conversiones Rápidas

### Género
| Excel | Sistema |
|-------|---------|
| F | Femenino |
| M | Masculino |

### Jornada
| Excel | Sistema |
|-------|---------|
| M | Mañana |
| T | Tarde |
| N | Nocturna |

### Estado Académico
| Excel | Sistema |
|-------|---------|
| MA | Matriculado |
| GR | Graduado |
| TR | Trasladado |
| RE | Retirado |

### Tipo Documento (ejemplos)
| Excel | Sistema |
|-------|---------|
| CC | Cédula de ciudadanía |
| PA | Pasaporte |
| TI | Tarjeta de identidad |
| CE | Cédula de extranjería |

---

## 🔧 Seguridad de Conversión

⚠️ **Importante**: Las funciones son **seguras ante valores nulos o vacíos**:

```python
convertir_genero(None)       # → None
convertir_genero("")         # → ""
convertir_genero("  ")       # → "" (espacios)
```

Las funciones usan `.strip()` y `.upper()` para normalizar antes de convertir, asegurando:
- Insensibilidad a mayúsculas/minúsculas
- Tolerancia a espacios en blanco
- No generan errores si el dato está vacío

---

## 📊 Rendimiento

Todas las funciones usan búsqueda en diccionario (`dict.get()`), lo que garantiza:
- ⚡ Rendimiento O(1) - muy rápido
- 🔄 Apto para importación masiva (1000+ registros)
- 💾 Bajo uso de memoria

---

## 🎯 Flujo Completo de Importación

1. **Usuario selecciona archivo Excel**
2. **Sistema lee el Excel**
3. **Valida que existan todas las columnas requeridas**
4. **Normaliza nombres de columnas a minúsculas**
5. **Aplica funciones de conversión:**
   - `convertir_genero()` en columna `genero`
   - `convertir_jornada()` en columna `jornada`
   - `convertir_estado_academico()` en columna `estado`
   - `convertir_tipo_documento()` en columna `tipodoc`
6. **Valida que campos obligatorios no estén vacíos**
7. **Guarda en la base de datos**
8. **Muestra confirmación al usuario**

---

## 💡 Ventajas del Sistema

✅ Automatización total - sin intervención manual  
✅ Conversión transparente - usuario no ve detalles  
✅ Tolerancia a fallos - no cancela por espacios o mayúsculas  
✅ Flexibilidad - acepta códigos cortos o nombres largos  
✅ Integridad - valida valores antes de guardar  

---

**Versión**: 2.0  
**Últimas modificaciones**: 4 de marzo de 2026
