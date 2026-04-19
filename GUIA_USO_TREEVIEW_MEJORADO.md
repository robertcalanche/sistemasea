# GUÍA COMPLETA - TreeView Mejorado Banco de Preguntas

## 📋 Tabla de Contenidos
1. [Cambios Implementados](#cambios-implementados)
2. [Instrucciones de Uso](#instrucciones-de-uso)
3. [Distribución de Columnas](#distribución-de-columnas)
4. [Características de Interacción](#características-de-interacción)
5. [Resolución de Problemas](#resolución-de-problemas)

---

## Cambios Implementados

### ✅ 1. Todas las 14 Columnas Visibles

Anteriormente el TreeView solo mostraba 7 columnas. Ahora muestra todas:

```
ID | EVALUACION | AREA | PERIODO | GRADO | ID_CONTEXTO | CONTEXTO | 
ENUNCIADO | OPCION_A | OPCION_B | OPCION_C | OPCION_D | CORRECTA | IMAGEN
```

### ✅ 2. Scroll Horizontal

Se agregó barra de desplazamiento horizontal en la parte inferior para ver todas las columnas:

```
┌─────────────────────────────────────────┐
│  [...contenido del treeview...]         │
├─────────────────────────────────────────┤
└──────────┬────────►[═══════════════════]│
           └─ Scroll Horizontal para desplazarse
```

### ✅ 3. Scroll Vertical Mejorado

El scroll vertical se optimizó y se reposiciona correctamente:

```
┌──────────────────────────────────────┬──┐
│                                      │║ │
│     ... contenido del treeview ...   │║ │ ◄─ Scroll Vertical
│                                      │║ │
└──────────────────────────────────────┴──┘
```

### ✅ 4. Redimensionamiento Manual

Cada columna se puede redimensionar manualmente arrastrando su borde:

```
Paso a paso:
1. Posicione el cursor en el borde superior entre dos encabezados
2. El cursor cambiará a una línea vertical con flechas ↔
3. Haga clic y arrastre hacia izquierda (reducir) o derecha (ampliar)
4. El cambio se aplica inmediatamente
```

---

## Instrucciones de Uso

### 🖱️ Navegación Horizontal

**Problema:** No puedo ver todas las columnas a la vez  
**Solución:** Use la barra de scroll horizontal en la parte inferior

```
Opción 1: Arrastra la barra de scroll
├─ Haz clic en el control ▬ de la barra horizontal
└─ Arrastra hacia izquierda o derecha

Opción 2: Rueda del ratón + Shift
├─ Mantén presionada la tecla Shift
└─ Gira la rueda hacia arriba (izquierda) o abajo (derecha)

Opción 3: Flechas de teclado
├─ Haz clic en el treeview primero
└─ Usa ← y → para desplazarte
```

### 🖱️ Navegación Vertical

```
Opción 1: Arrastra la barra de scroll
├─ Haz clic en el control ▬ de la barra vertical
└─ Arrastra hacia arriba o abajo

Opción 2: Rueda del ratón
├─ Gira la rueda para desplazarte arriba/abajo

Opción 3: Flechas de teclado
├─ Haz clic en una fila del treeview
└─ Usa ↑ y ↓ para seleccionar filas
```

### 📏 Redimensionar Columnas

```
Paso 1: Posicionamiento
├─ Mueva el cursor al borde del encabezado de columna (línea vertical)
└─ El cursor debe cambiar a ↔

Paso 2: Arrastrar
├─ Haga clic y mantenga presionado
├─ Arrastre hacia la derecha para ampliar
├─ Arrastre hacia la izquierda para reducir
└─ Suelte el botón del ratón

Ejemplo:
   Antes:        Después (más ancho):
   ┌──────┐      ┌──────────────┐
   │ ID   │      │ ID           │
   └──────┘      └──────────────┘
```

### 🔍 Buscar Información Específica

```
Para encontrar el enunciado completo:
1. Desplácese horizontalmente hasta ver la columna ENUNCIADO
2. Busque la fila deseada
3. Si el texto está truncado, puede:
   a. Ampliar la columna arrastrando su borde
   b. Hacer doble clic sobre la celda para expandir (si aplica)

Para ver todas las opciones de respuesta:
1. Desplácese horizontalmente para ver OPCION_A, OPCION_B, OPCION_C, OPCION_D
2. Amplíe las columnas si es necesario
3. Compare las opciones con CORRECTA
```

---

## Distribución de Columnas

### Vista General (Ancho Total: 1625px)

```
┌─────┬───────────┬──────────┬─────────┬───────┬──────────┬────────────┐
│ ID  │ EVALUACION│ AREA     │PERIODO  │GRADO  │ID_CONTX  │ CONTEXTO   │
├─────┼───────────┼──────────┼─────────┼───────┼──────────┼────────────┤
│ 40px│    90px   │   90px   │  50px   │ 50px  │   80px   │   200px    │
└─────┴───────────┴──────────┴─────────┴───────┴──────────┴────────────┘
        MEDIANAS                CORTAS              MEDIANAS    LARGA

[scroll horizontal →]

┌──────────────┬─────────────┬─────────────┬─────────────┬──────────┬────────┐
│  ENUNCIADO   │  OPCION_A   │  OPCION_B   │  OPCION_C   │OPCION_D  │CORRECTA│IMAGEN │
├──────────────┼─────────────┼─────────────┼─────────────┼──────────┼────────┤
│    220px     │    180px    │    180px    │    180px    │ 180px    │ 35px   │50px   │
└──────────────┴─────────────┴─────────────┴─────────────┴──────────┴────────┘
       LARGA        LARGA        LARGA        LARGA        LARGA    CORTA
```

### Ancho de Cada Columna

| Columna | Tamaño | Ancho | Contenido Típico |
|---------|--------|-------|------------------|
| **ID** | Muy corta | 40px | 1-3 caracteres (ej: "1", "42", "123") |
| **EVALUACION** | Mediana | 90px | Nombres moderados (ej: "Diagnóstica") |
| **AREA** | Mediana | 90px | Áreas de estudio (ej: "Lenguaje") |
| **PERIODO** | Corta | 50px | Datos cortos (ej: "1", "2023-I") |
| **GRADO** | Corta | 50px | Números (ej: "1", "11") |
| **ID_CONTEXTO** | Mediana | 80px | Identificadores (ej: "CTX-001") |
| **CONTEXTO** | Larga | 200px | Textos descriptivos medianos |
| **ENUNCIADO** | Larga | 220px | Pregunta completa |
| **OPCION_A** | Larga | 180px | Texto de opción |
| **OPCION_B** | Larga | 180px | Texto de opción |
| **OPCION_C** | Larga | 180px | Texto de opción |
| **OPCION_D** | Larga | 180px | Texto de opción |
| **CORRECTA** | Muy corta | 35px | Letra (A, B, C o D) |
| **IMAGEN** | Corta | 50px | Símbolo (✓ o vacío) |

---

## Características de Interacción

### 🎯 Seleccionar Preguntas

```
Seleccionar una fila:
├─ Haga clic en cualquier celda de la fila
└─ La fila se resaltará (fondo gris)

Seleccionar múltiples filas (si aplica):
├─ Haga clic en la primera fila
├─ Mantenga Ctrl presionado
└─ Haga clic en filas adicionales

Seleccionar rango continuo:
├─ Haga clic en la primera fila
├─ Mantenga Shift presionado
└─ Haga clic en la última fila del rango
```

### 🔧 Operaciones Disponibles

Con una pregunta seleccionada puede:

| Botón | Acción | Atajo |
|-------|--------|-------|
| ➕ Agregar | Añade nueva pregunta | (Sin atajo) |
| ✏️ Editar | Modifica pregunta seleccionada | (Sin atajo) |
| 🗑️ Eliminar | Elimina pregunta seleccionada | (Requiere confirmación) |
| 📥 Importar | Carga múltiples preguntas de Excel | (Sin atajo) |
| 📤 Exportar | Descarga todas las preguntas | (Sin atajo) |
| ✓ Validar | Revisa integridad de datos | (Sin atajo) |

---

## Resolución de Problemas

### 🚨 Problema: No veo scroll horizontal

**Causa:** Es probable que todas las columnas quepan en la pantalla (resolución muy grande)  
**Solución:**
- Reduce el ancho de la ventana
- Amplía algunas columnas manualmente
- Verifica que tu monitor tenga una resolución estándar

### 🚨 Problema: El texto está cortado en algunas columnas

**Causa:** El ancho de la columna es menor que el contenido  
**Solución:**
1. Posiciona el cursor en el borde de la columna
2. Arrastra hacia la derecha para ampliar
3. O puedes usar el scroll horizontal para desplazarte

### 🚨 Problema: El scroll horizontal no aparece 

**Causa:** Todas las columnas caben en la pantalla actual  
**Solución:**
- Amplía manualmente el ancho de las columnas largas
- O reduce el ancho de la ventana
- El scroll aparecerá automáticamente cuando sea necesario

### 🚨 Problema: He redimensionado las columnas y se ve raro

**Causa:** Los cambios se aplican solo durante la sesión actual  
**Solución:**
- Recargue la aplicación para volver a los anchos por defecto
- O ajuste nuevamente manualmente según sus preferencias

### 🚨 Problema: Los datos no se ven completos en el enunciado

**Causa:** El ancho por defecto de ENUNCIADO (220px) puede no ser suficiente para textos muy largos  
**Solución:**
1. Amplíe la columna ENUNCIADO arrastrando su borde derecho
2. O use el scroll horizontal para ver el contenido completo
3. Puede cambiar el ancho de columna cada vez que lo necesite

---

## Consejos Útiles

### 💡 Trabajar Eficientemente con Gran Número de Preguntas

```
1. Usa los filtros (Grado, Área, Evaluación)
   └─ Reduce el número de filas visibles

2. Optimiza el tamaño de las columnas
   ├─ Reduce el ancho de columnas que no necesitas ver
   └─ Amplía el ancho de columnas importantes

3. Usa scroll horizontal cuando sea necesario
   ├─ No intentes ampliar todas las columnas
   └─ Desplázate según necesites

4. Guarda tu configuración mentalmente
   └─ Los ajustes de columna se pierden al cerrar
```

### 💡 Mejores Prácticas para Importación

```
1. Antes de importar, valida tu archivo Excel
   └─ Asegurate de tener todas las 14 columnas

2. Después de importar, usa "✓ Validar integridad"
   └─ Revisa que todo se cargó correctamente

3. Si hay errores, usa los filtros para encontrarlos
   └─ Busca por grado, área o evaluación
```

---

## Especificaciones Técnicas

### Configuración del TreeView

```python
Columnas totales:        14
Altura predeterminada:   15 filas visibles
Scroll Vertical:         Habilitado
Scroll Horizontal:       Habilitado
Redimensionamiento:      Permitido por el usuario
```

### Compatibilidad

✅ Windows 10/11  
✅ Python 3.7+  
✅ Tkinter (incluido en Python)  
✅ Pandas (opcional, compatible)  
✅ Excel (.xlsx, .xls)  

---

## Soporte

Si encuentras problemas:

1. **Verifica los filtros:** Asegúrate de que no hay filtros activos
2. **Recarga los datos:** Usa "Limpiar filtros" en la interfaz
3. **Exporta y revisa:** Descarga los datos para inspeccionar manualmente
4. **Revisa el archivo:** Asegúrate de que el Excel está bien formado

---

**Última actualización:** 1 de marzo de 2026  
**Versión:** 1.0 - Mejoras TreeView Banco de Preguntas
