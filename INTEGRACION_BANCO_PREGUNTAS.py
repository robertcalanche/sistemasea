# -*- coding: utf-8 -*-
"""
GUÍA DE INTEGRACIÓN - Banco de Preguntas Profesional
=====================================================

Archivos creados:
1. banco_preguntas_profesional.py - Backend profesional
2. interfaz_banco_preguntas.py - Frontend mejorado (Tkinter)
3. integracion_ejemplo.py - Este archivo (ejemplo de integración)

"""

# ============================================================
# OPCIÓN 1: INTEGRACIÓN MÍNIMA (Recomendado)
# ============================================================
"""
Pasos:

1. En modulo_superadmin.py, busca la línea:
   def _build_preguntas_tab(self):

2. Reemplázala con:
   def _build_preguntas_tab(self):
       from interfaz_banco_preguntas import InterfazBancoPreguntasAvanzada
       InterfazBancoPreguntasAvanzada._build_preguntas_tab_mejorada(self)

3. Mantén los métodos existentes de pregunta_agregar, _dialog_pregunta, etc.
   o reemplázalos con los de interfaz_banco_preguntas.py

Eso es todo. El sistema seguirá funcionando como antes pero con capacidades mejoradas.
"""

# ============================================================
# OPCIÓN 2: USO INDEPENDIENTE (Para testing)
# ============================================================

from banco_preguntas_profesional import BancoPreguntasProfesional

# Crear instancia del banco
banco = BancoPreguntasProfesional(path="preguntas.xlsx")

# ---- CARGAR PREGUNTAS ----
print("1. CARGAR TODAS LAS PREGUNTAS")
todas = banco.obtener_todas_preguntas()
print(f"Total de preguntas: {len(todas)}\n")

# ---- OBTENER DISPONIBLES ----
print("2. GRADOS DISPONIBLES")
grados = banco.obtener_grados_disponibles()
print(f"Grados: {grados}\n")

print("3. ÁREAS DISPONIBLES")
areas = banco.obtener_areas_disponibles()
print(f"Áreas: {areas}\n")

print("4. EVALUACIONES DISPONIBLES")
evals = banco.obtener_evaluaciones_disponibles()
print(f"Evaluaciones: {evals}\n")

# ---- FILTRAR PREGUNTAS ----
print("5. PREGUNTAS FILTRADAS (Grado 5, Área Matemáticas)")
filtradas = banco.obtener_preguntas_filtradas(grado="5", area="matemáticas")
print(f"Encontradas: {len(filtradas)} preguntas\n")

# ---- AGREGAR UNA PREGUNTA ----
print("6. AGREGAR NUEVA PREGUNTA")
nueva_pregunta = {
    "id": "P001",
    "evaluacion": "Trimestral",
    "area": "Matemáticas",
    "periodo": "1",
    "grado": "5",
    "id_contexto": "C001",
    "contexto": "En una tienda...",
    "enunciado": "¿Cuánto es 2+2?",
    "opcion_a": "3",
    "opcion_b": "4",
    "opcion_c": "5",
    "opcion_d": "6",
    "correcta": "B",
    "imagen": "",
}

exitoso, mensaje = banco.guardar_pregunta(
    id_pregunta="P001", datos_pregunta=nueva_pregunta, es_nueva=True
)
print(f"Resultado: {mensaje}\n")

# ---- EDITAR UNA PREGUNTA ----
print("7. EDITAR PREGUNTA")
pregunta_existente = banco.obtener_pregunta_por_id("P001")
if pregunta_existente:
    pregunta_existente["enunciado"] = "¿Cuánto es 2+3?"
    exitoso, mensaje = banco.guardar_pregunta(
        id_pregunta="P001", datos_pregunta=pregunta_existente, es_nueva=False
    )
    print(f"Resultado: {mensaje}\n")

# ---- ELIMINAR UNA PREGUNTA ----
print("8. ELIMINAR PREGUNTA")
exitoso, mensaje = banco.eliminar_pregunta("P001")
print(f"Resultado: {mensaje}\n")

# ---- IMPORTAR MASIVAMENTE ----
print("9. IMPORTACIÓN MASIVA")
# Crear un archivo de prueba primero:
import pandas as pd

df_importar = pd.DataFrame(
    [
        {
            "id": "IMP001",
            "evaluacion": "Diagnóstica",
            "area": "Lenguaje",
            "periodo": "1",
            "grado": "6",
            "id_contexto": "C002",
            "contexto": "Lee el siguiente texto...",
            "enunciado": "¿Cuál es el tema principal?",
            "opcion_a": "Tema A",
            "opcion_b": "Tema B",
            "opcion_c": "Tema C",
            "opcion_d": "Tema D",
            "correcta": "A",
            "imagen": "",
        },
        {
            "id": "IMP002",
            "evaluacion": "Diagnóstica",
            "area": "Lenguaje",
            "periodo": "1",
            "grado": "6",
            "id_contexto": "C003",
            "contexto": "Lee el siguiente texto...",
            "enunciado": "¿Quién es el personaje principal?",
            "opcion_a": "Juan",
            "opcion_b": "María",
            "opcion_c": "Pedro",
            "opcion_d": "Ana",
            "correcta": "B",
            "imagen": "",
        },
    ]
)

# Guardar a Excel temporal
df_importar.to_excel("importar_temp.xlsx", index=False)

# Importar
resumen = banco.importar_masivo("importar_temp.xlsx")
print(f"Importadas: {resumen['exitosas']}")
print(f"Duplicadas ID: {resumen['duplicadas_id']}")
print(f"Duplicadas Enunciado: {resumen['duplicadas_enunciado']}")
print(f"Rechazadas: {resumen['rechazadas_validacion']}\n")

# Mostrar reporte
reporte = banco.generar_reporte_importacion(resumen)
print(reporte)

# ---- VALIDAR INTEGRIDAD ----
print("10. VALIDACIÓN DE INTEGRIDAD")
advertencias = banco.validar_integridad()
if any(advertencias.values()):
    print("Advertencias encontradas:")
    for tipo, items in advertencias.items():
        if items:
            print(f"  - {tipo}: {len(items) if isinstance(items, list) else items}")
else:
    print("No hay problemas de integridad")

# ---- OBTENER ESTADÍSTICAS ----
print("\n11. ESTADÍSTICAS DEL BANCO")
stats = banco.obtener_estadisticas()
for clave, valor in stats.items():
    print(f"  {clave}: {valor}")


# ============================================================
# OPCIÓN 3: INTERFAZ TKINTER COMPLETA
# ============================================================

"""
Para usar la interfaz Tkinter completa:

import tkinter as tk
from modulo_superadmin import ModuloSuperAdmin

root = tk.Tk()
root.withdraw()

# Crear instancia del módulo mejorado
msa = ModuloSuperAdmin(root)

# Autenticarse
if msa.authenticate():
    # Usar la interfaz mejorada
    msa.open_interface()
    root.mainloop()
"""


# ============================================================
# FUNCIONES RÁPIDAS (Standalone)
# ============================================================

"""
Si solo necesitas funciones rápidas sin la clase completa:

from banco_preguntas_profesional import (
    cargar_preguntas_desde_excel,
    guardar_cambios_excel,
    eliminar_pregunta,
    importar_preguntas_masivo
)

# Cargar preguntas
df = cargar_preguntas_desde_excel()

# Guardar cambios
guardar_cambios_excel(df)

# Eliminar
exitoso, mensaje = eliminar_pregunta("ID123")

# Importar masivo
resumen = importar_preguntas_masivo("importar.xlsx")
"""


# ============================================================
# ESTRUCTURA DEL EXCEL ESPERADO
# ============================================================

"""
El archivo preguntas.xlsx debe tener estas columnas:

id                 | evaluacion    | area        | periodo | grado | id_contexto | contexto              | enunciado             | opcion_a | opcion_b | opcion_c | opcion_d | correcta | imagen
P001              | Trimestral     | Matemática  | 1       | 5     | C001        | En una tienda...      | ¿Cuánto es 2+2?      | 3        | 4        | 5        | 6        | B        | 
P002              | Trimestral     | Lenguaje    | 1       | 5     | C002        | Lee el texto...       | ¿Cuál es el tema?     | A        | B        | C        | D        | A        | imagen.png

Notas:
- 'id' debe ser único
- 'enunciado' debe ser único (para evitar duplicados)
- 'correcta' debe ser A, B, C o D
- Los campos 'id_contexto', 'contexto', 'periodo' e 'imagen' son opcionales pero recomendados
"""


# ============================================================
# CARACTERES ESPECIALES EN ETIQUETAS (Emojis)
# ============================================================

"""
En la interfaz mejorada, los botones usan iconos:
➕ Agregar
✏️  Editar
🗑️  Eliminar
📥 Importar
📤 Exportar
✓ Validar

Si tu sistema no soporta emojis, reemplaza en interfaz_banco_preguntas.py:
btn_agregar = ttk.Button(toolbar, text="➕ Agregar", ...) 
por:
btn_agregar = ttk.Button(toolbar, text="[ + ] Agregar", ...)
"""


print("\n" + "=" * 60)
print("GUÍA DE INTEGRACIÓN COMPLETADA")
print("=" * 60)
print("\nPróximos pasos:")
print("1. Copiar banco_preguntas_profesional.py a tu proyecto")
print("2. Copiar interfaz_banco_preguntas.py a tu proyecto")
print("3. Importar en modulo_superadmin.py")
print("4. Ejecutar y probar")
print("\nDocumentación disponible en cada archivo.")
