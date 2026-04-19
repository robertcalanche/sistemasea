# IMPLEMENTACIÓN: REANUDACIÓN AUTOMÁTICA DE EXÁMENES

## Resumen Ejecutivo

Se ha implementado un sistema robusto de reanudación automática de exámenes que permite a los estudiantes **continuar exactamente donde dejaron** si existe una interrupción de la conexión, garantizando que **nunca se pierdan respuestas**.

---

## Objetivo Logrado

✅ **Al iniciar un examen**, el sistema verifica automáticamente si existe un registro `EN_PROCESO` para ese documento y área.
✅ **Si existe**: Recupera el intento, las respuestas guardadas, y posiciona el examen en la pregunta correcta.
✅ **Si no existe**: Inicia un nuevo examen normalmente.
✅ **Compatible** con interrupciones de WiFi y fallos de red.

---

## Implementación Técnica

### 1. Función Auxiliar: `_obtener_examen_en_proceso(area)`

**Ubicación**: [modulo_estudiante.py → ModuloEstudiante class](app.py#L2540)

**Funcionalidad**:
- Búsqueda en base de datos: `SELECT intento, id FROM resultados WHERE estado_examen = 'EN_PROCESO'`
- Retorna: `(intento_num, intento_id, respuestas_guardadas)` o `None`
- Cuenta respuestas guardadas para determinar punto de continuación

```python
def _obtener_examen_en_proceso(self, area):
    # Busca si existe EN_PROCESO
    # Retorna (intento_num, intento_id, respuestas_guardadas) o None
```

### 2. Modificación: `_iniciar_examen(area)`

**Cambios**:
- Llamar a `_obtener_examen_en_proceso()` ANTES de registrar inicio
- Si existe EN_PROCESO:
  - Reutilizar `intento_num` e `intento_id`
  - Establecer `es_reanudacion = True`
  - `indice_inicial = respuestas_guardadas`
- Si NO existe:
  - Llamar a `registrar_inicio()` normalmente
  - `es_reanudacion = False`, `indice_inicial = 0`

**Resultado**: Dos flujos posibles sin perder datos.

### 3. Modificación: `_mostrar_pantalla_informativa(area, cantidad_preguntas, duracion_segundos, es_reanudacion=False, indice_inicial=0)`

**Cambios**:
- Parámetros adicionales para reanudación
- Si `es_reanudacion == True`:
  - Mostrar panel azul: "🔄 Se ha detectado un examen incompleto"
  - Información: "Continuarás desde la pregunta X. Tus respuestas han sido guardadas."
- Pasar parámetros al botón "Comenzar Examen"

**Interfaz de Usuario**:
```
╔════════════════════════════════════════╗
║ 🔄 Se ha detectado un examen incompleto║
║                                        │
║ Continuarás desde pregunta 3 de 10    │
║ Tus respuestas han sido guardadas     │
╚════════════════════════════════════════╝
```

### 4. Modificación: `_mostrar_examen(area, cantidad_preguntas, duracion_segundos, es_reanudacion=False, indice_inicial=0)`

**Cambios**:
- Aceptar parámetros de reanudación
- Inicializar `contador["indice"] = indice_inicial` (no siempre 0)
- Si es reanudación:
  - Recuperar contador de correctas previas desde `respuestas_estudiantes`
  - Mostrar alerta: "Se ha reanudado tu examen. Continuarás desde pregunta X."
  - `contador["correctas"]` comienza con el valor correcto (previas + nuevas)

**Datos Recuperados**:
```sql
SELECT COUNT(*) FROM respuestas_estudiantes 
WHERE documento = ? AND area = ? AND intento = ? AND es_correcta = 1
-- Retorna número de respuestas correctas PREVIAS
```

### 5. Función Auxiliar: `obtener_todas_respuestas_desde_bd(documento, area, intento)`

**Ubicación**: [app.py line 310-344](app.py#L310)

**Funcionalidad**:
- Recupera todas las respuestas de `respuestas_estudiantes` ordenadas
- Retorna JSON con formato completo (pregunta_id, enunciado, respuesta_dada, correcta, etc.)
- Útil cuando la reanudación finaliza para tener el JSON COMPLETO

```sql
SELECT pregunta_id, enunciado, respuesta_seleccionada, respuesta_correcta, es_correcta
FROM respuestas_estudiantes
WHERE documento = ? AND area = ? AND intento = ?
ORDER BY rowid ASC
```

### 6. Modificación: `finalizar()` (función interna de _mostrar_examen)

**Cambios**:
- Si es reanudación:
  - Llamar a `obtener_todas_respuestas_desde_bd()` para recuperar TODAS las respuestas
  - Recalcular `contador["correctas"]` basándose en BD (todas, no solo nuevas)
  - Usar ese JSON recuperado en lugar del JSON local incompleto
- Calcular nota FINAL basada en todas las respuestas:
  ```python
  nota = (total_correctas_de_BD / total_preguntas) * 5
  ```
- Llamar a `registrar_final()` con todos los datos correctos

**Resultado**: La nota y el JSON final reflejan el examen COMPLETO, no solo la sesión actual.

---

## Flujo Completo de Reanudación

```
┌─────────────────────────────────┐
│ Estudiante abre la app          │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ _iniciar_examen(area)           │ 
│ ▼ _obtener_examen_en_proceso()  │
└──────────────┬──────────────────┘
               │
        ┌──────┴──────┐
        │             │
    EXISTE        NO EXISTE
        │             │
        ▼             ▼
   REANUDACION    NUEVO EXAMEN
   ┌─────────┐   ┌──────────┐
   │EN_PROCESO│   │registrar │
   │intento=1 │   │_inicio() │
   │resp=2    │   │intento=1 │
   └────┬────┘   │resp=0    │
        │         └────┬─────┘
        └──────┬──────┘
               │
               ▼
   ┌───────────────────────────────┐
   │_mostrar_pantalla_informativa()│
   │ es_reanudacion=True/False     │
   │ indice_inicial=2/0            │
   └────────────────┬──────────────┘
                    │
          "Comenzar Examen" clic
                    │
                    ▼
   ┌───────────────────────────────┐
   │_mostrar_examen(...)           │
   │ contador["indice"]=2 (reanuda)│
   │ contador["correctas"]=1 (BD)   │
   │ "Se ha reanudado tu examen"   │
   └────────────────┬──────────────┘
                    │
        ┌──────────┴──────────┐
        │                     │
  PREGUNTA 3                PREGUNTA 10
  (de reanudacion)          (última)
        │                     │
        ▼                     ▼
   siguiente()  ...      siguiente()
   • Valida respuesta
   • Calcula correcta
   • Guarda en BD INMEDIATAMENTE
   • Avanza
        │                     │
        └──────────┬──────────┘
                   │
                   ▼
            ┌─────────────┐
            │ finalizar() │
            └──────┬──────┘
                   │
        ¿Es reanudacion?
                   │
            ┌──────┴──────┐
            │             │
            SI            NO
            │             │
            ▼             ▼
   obtener_todas_   Usar JSON
   respuestas_     construido
   desde_bd()      durante
   • Recupera 10   sesión
   • Recalcula
   • Nota completa
            │             │
            └──────┬──────┘
                   │
                   ▼
      ┌──────────────────────┐
      │ registrar_final()    │
      │ estado='FINALIZADO'  │
      │ nota=COMPLETA        │
      │ respuestas=JSON FULL │
      └──────────────────────┘
```

---

## Bases de Datos Involucradas

### Tabla: `resultados`
```sql
-- Búsqueda de EN_PROCESO
SELECT intento, id FROM resultados 
WHERE documento = ? AND area = ? AND estado_examen = 'EN_PROCESO'

-- Actualización al finalizar
UPDATE resultados SET estado_examen='FINALIZADO', nota=?, hora_fin=?
WHERE id = ? -- El mismo registro EN_PROCESO
```

### Tabla: `respuestas_estudiantes`
```sql
-- Inserción inmediata cada "Siguiente"
INSERT INTO respuestas_estudiantes (...) ON CONFLICT DO UPDATE ...
-- (UNIQUE constraint: documento, area, intento, pregunta_id)

-- Recuperación al reanudar
SELECT COUNT(*) FROM respuestas_estudiantes
WHERE estado_examen = 'EN_PROCESO'
-- Determina indice_inicial

-- Conteo de correctas previas
SELECT COUNT(*) FROM respuestas_estudiantes
WHERE es_correcta = 1 AND estado_examen = 'EN_PROCESO'
-- Recupera contador["correctas"]

-- Recuperación final al terminar
SELECT * FROM respuestas_estudiantes
WHERE documento = ? AND area = ? AND intento = ?
-- Retorna JSON COMPLETO
```

---

## Protección Contra Fallos de Red

### Estrategia: Guardado Inmediato + Reanudación

**Problema Original**: Si la conexión falla después de responder Pregunta 5, ¿qué pasa?
- Respuesta guardada en `respuestas_estudiantes` ✅ (inmediato)
- Pero estado en `resultados` aún es `EN_PROCESO` ✅
- JSON final no se guardó ❌ (estaba esperando fin del examen)

**Solución Implementada**:
1. **Guardado inmediato** (implementado en sprint anterior)
   - Cada respuesta se guarda en BD al presionar "Siguiente"
   - Se usa UNIQUE + ON CONFLICT para resilencia

2. **Reanudación automática** (este sprint)
   - Si hay EN_PROCESO, se recuperan TODAS las respuestas
   - El examen continúa donde quedó
   - Al finalizar, el JSON recuperado es COMPLETO

**Resultado**: Cero pérdida de datos aunque falle la red múltiples veces.

---

## Estados del Examen

| Estado | Significado | Acción |
|--------|-------------|--------|
| `EN_PROCESO` | Examen iniciado pero no completado | Mostrar opción de reanudación |
| `FINALIZADO` | Examen completado | Mostrar nota y permitir revisión (si autorizado) |
| `PRESENTADO` | Antiguidad: examen marcado como enviado (deprecated) | Compatibilidad hacia atrás |

**Transición en reanudación**:
- Estado EN_PROCESO → permanent hasta llamar a `registrar_final()`
- No se crea nuevo registro, se ACTUALIZA el existente
- `intento` permanece igual (no incrementa)

---

## Variables de Sesión Relevantes

```python
# En ModuloEstudiante.__init__()
self.current_intento_id    # ID del registro en resultados (recuperado o nuevo)
self.current_intento_num   # Número de intento (recuperado o nuevo)

# En _mostrar_examen()
contador["indice"]         # Índice actual (2 si reanuda después de pregunta 2)
contador["correctas"]      # Correctas acumuladas (1 previas + nuevas)
es_reanudacion            # Parámetro: True si es reanudación
indice_inicial            # Parámetro: número de respuestas guardadas
```

---## Test Incluido

**Archivo**: `test_reanudacion_examen.py`

**Verifica**:
1. ✅ Crear examen EN_PROCESO
2. ✅ Guardar respuestas parciales
3. ✅ Detectar examen EN_PROCESO
4. ✅ Calcular índice de continuación correcto
5. ✅ Recuperar respuestas correctas previas
6. ✅ Recuperar TODAS las respuestas desde BD
7. ✅ Verificar integridad de datos

**Ejecución**:
```powershell
python test_reanudacion_examen.py

# Salida esperada:
# ======================================================================
# [EXITO] TEST EXITOSO: Sistema de reanudacion funcionando correctamente
# ======================================================================
```

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `app.py` | Función `_obtener_examen_en_proceso()` (nuevo) |
| `app.py` | Función `obtener_todas_respuestas_desde_bd()` (nuevo) |
| `app.py` | Método `_iniciar_examen()` (modificado) |
| `app.py` | Método `_mostrar_pantalla_informativa()` (modificado) |
| `app.py` | Método `_mostrar_examen()` (modificado) |
| `app.py` | Función interna `finalizar()` (modificado) |
| `test_reanudacion_examen.py` | Test de verificación (nuevo) |

---

## Compatibilidad

✅ Compatible con Python 3.14+  
✅ Funciona en ejecutable (PyInstaller)  
✅ Funciona en WiFi con interrupciones  
✅ No requiere cambios en base de datos existente  
✅ Retrocompatible con exámenes antiguos  
✅ No interfiere con historial de estudiantes  

---

## Próximos Pasos (Opcional)

- [ ] Limpiar registros EN_PROCESO antiguos (> 24 horas)
- [ ] Notify estudiante si hay examen interrumpido al ingresar
- [ ] Dashboard docente mostrando estudiantes con exámenes EN_PROCESO
- [ ] Botón manual para "Abandonar examen" (cambiar EN_PROCESO a ABANDONADO)

---

## Verificación Rápida

Para verificar que funciona en la app principal:

1. Ingresar como estudiante
2. Comenzar examen
3. Responder algunas preguntas (ej: 3 de 10)
4. **Cerrar la aplicación abruptamente** (simular fallo de conexión)
5. Reabrir la app e ingresar nuevamente
6. **Esperar**... la app debería detectar EN_PROCESO
7. Debería mostrarse: "Se ha reanudado tu examen"
8. El examen debería comenzar desde pregunta 4 (la siguiente)
9. Las respuestas previas deberían estar guardadas
10. Al finalizar, la nota debería contar TODAS (previas + nuevas)

