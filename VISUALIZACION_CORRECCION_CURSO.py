#!/usr/bin/env python3
"""
Comparación ANTES vs DESPUÉS del filtro de curso
"""

ANTES_BUG = """
┌─────────────────────────────────────────────────────────────────┐
│                      ANTES (❌ INCORRECTO)                      │
└─────────────────────────────────────────────────────────────────┘

 Docente selecciona:
 - Grado: 5
 - Curso: 01 ❌ IGNORADO
 - Área: Ciencias Sociales
 - Evaluación: Primera

          │
          ▼
  ┌──────────────────┐
  │  Cargar Preg.    │  Grado 5 ✓
  │   Filtros:       │  Curso 01 ❌ NO TIENE EFECTO
  │  - Grado 5       │  
  │  - Curso 01      │
  └────────┬─────────┘
           │
           ▼
     70 Preguntas (OK)
     
          │
          ▼
  ┌──────────────────────┐
  │  Cargar Estudiantes  │   Carga: TODOS del grado
  │   Filtros:           │   
  │  - Solo Grado 5      │   Esperada: Solo grado 5, curso 01
  │  - Curso: IGNORADO   │   ❌ Pero carga 5-01, 5-02, 5-03
  └────────┬─────────────┘
           │
           ▼
   30 estudiantes (15 de 5-01,
    10 de 5-02, 5 de 5-03)
    
          │
          ▼
    PROBLEMA: Genera exámenes
    para TODOS incluso del
    curso que NO se seleccionó
"""

DESPUES_CORREGIDO = """
┌────────────────────────────────────────────────────────────────┐
│                    DESPUÉS (✅ CORRECTO)                       │
└────────────────────────────────────────────────────────────────┘

 Docente selecciona:
 - Grado: 5
 - Curso: 01 ✅ USADO SOLO PARA ESTUDIANTES
 - Área: Ciencias Sociales
 - Evaluación: Primera

          │
          ▼
  ┌──────────────────────┐
  │  Cargar Preguntas    │  Grado 5 ✓
  │   Filtros:           │  Curso 01 ❌ IGNORADO (correcto)
  │  - Grado 5           │  Las preguntas son para todo el grado
  │  - NO Curso          │
  └────────┬─────────────┘
           │
           ▼
     70 Preguntas (OK)
     Mismo banco para 5-01, 5-02, 5-03
     
          │
          ▼
  ┌──────────────────────────┐
  │  Cargar Estudiantes      │   Filtro: Grado 5 + Curso 01 ✅
  │   Filtros:               │   
  │  - Grado: 5              │   Solo estudiantes de 5-01
  │  - Curso: 01 ✅ APLICADO │
  └────────┬─────────────────┘
           │
           ▼
    15 estudiantes (solo 5-01)
    
          │
          ▼
   Genera 15 exámenes
   (SOLO para el curso 01)
"""

COMPARACION_ESCENARIOS = """
╔════════════════════════════════════════════════════════════════════════════╗
║                          COMPARACIÓN DE ESCENARIOS                         ║
╚════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────┐
│ ESCENARIO 1: Generar para Grado 5, Curso 01                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  PARÁMETRO: curso="01"                                                   │
│                                                                           │
│  ANTES (❌):                          DESPUÉS (✅):                       │
│  ├─ Preguntas: Grado 5                 ├─ Preguntas: Grado 5            │
│  ├─ Estudiantes: 5-01, 5-02, 5-03      ├─ Estudiantes: 5-01 SOLO       │
│  └─ Archivos: 30 generados             └─ Archivos: 15 generados       │
│                                                                           │
│  ❌ RESULTADO: Generó para todos       ✅ RESULTADO: Solo 5-01!         │
│     los cursos aunque pasó 01                                            │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ ESCENARIO 2: Generar para Grado 5, SIN especificar curso                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  PARÁMETRO: curso=None                                                   │
│                                                                           │
│  ANTES (❌):                          DESPUÉS (✅):                       │
│  ├─ Preguntas: Grado 5                 ├─ Preguntas: Grado 5            │
│  ├─ Estudiantes: 5-01, 5-02, 5-03      ├─ Estudiantes: 5-01, 5-02, 5-03 │
│  └─ Archivos: 30 generados             └─ Archivos: 30 generados       │
│                                                                           │
│  ✅ RESULTADO: Igual (ambos generan   ✅ RESULTADO: Correcto!           │
│     para TODOS) pero sin razón                                           │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ ESCENARIO 3: Generar para Grado 5, Cursos diferentes (secuencial)       │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Paso 1: curso="01" → 15 exámenes                                        │
│  Paso 2: curso="02" → 10 exámenes                                        │
│  Paso 3: curso="03" → 5 exámenes                                         │
│  Total: 30 archivos                                                      │
│                                                                           │
│  IMPORTANTE: Todos usan el MISMO banco de preguntas (Grado 5)            │
│  - Solo cambia la LISTA de ESTUDIANTES por curso                         │
│  - El CONTENIDO del examen es idéntico                                   │
└──────────────────────────────────────────────────────────────────────────┘
"""

LOGICA_FILTROS = """
╔════════════════════════════════════════════════════════════════════════════╗
║                        MATRIZ DE FILTROS (LÓGICA)                          ║
╚════════════════════════════════════════════════════════════════════════════╝

PREGUNTAS:
┌─────────────────────────────────────┐
│ Filtro 1: Grado        → ✅ APLICAR  │
│ Filtro 2: Área         → ✅ APLICAR  │
│ Filtro 3: Evaluación   → ✅ APLICAR  │
│ Filtro 4: Curso        → ❌ IGNORAR  │
├─────────────────────────────────────┤
│ Resultado: Un banco de preguntas    │
│ para TODOS los cursos del grado     │
└─────────────────────────────────────┘

ESTUDIANTES:
┌─────────────────────────────────────┐
│ Filtro 1: Grado        → ✅ APLICAR  │
│ Filtro 2: Curso        → ✅ APLICAR  │
│            (si se pasa)              │
├─────────────────────────────────────┤
│ Resultado: Estudiantes del grado    │
│ Y del curso seleccionado (si aplica)│
└─────────────────────────────────────┘

NAMES DE ARCHIVOS:
┌──────────────────────────────────────┐
│ Formato:                             │
│ Examen_GRADO_CURSO_AREA_EVAL_DOC.pdf│
│         ▲     ▲                      │
│    Siempre    Del alumno             │
│              individual              │
└──────────────────────────────────────┘
"""

print(ANTES_BUG)
print("\n" + "=" * 70 + "\n")
print(DESPUES_CORREGIDO)
print("\n" + "=" * 70 + "\n")
print(COMPARACION_ESCENARIOS)
print("\n" + "=" * 70 + "\n")
print(LOGICA_FILTROS)
