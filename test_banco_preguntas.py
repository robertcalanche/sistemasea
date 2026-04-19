# -*- coding: utf-8 -*-
"""
PRUEBAS Y EJEMPLOS - Banco de Preguntas Profesional
====================================================

Este archivo contiene ejemplos ejecutables que demuestran
todas las funcionalidades del Banco de Preguntas.

Uso:
    python test_banco_preguntas.py
"""

import os
import sys
import pandas as pd
from banco_preguntas_profesional import BancoPreguntasProfesional


def crear_archivo_prueba():
    """Crea un archivo de prueba con algunas preguntas."""
    print("Creando archivo de prueba...")

    df = pd.DataFrame(
        [
            {
                "id": "TEST001",
                "evaluacion": "Diagnóstica",
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
            },
            {
                "id": "TEST002",
                "evaluacion": "Diagnóstica",
                "area": "Matemáticas",
                "periodo": "1",
                "grado": "5",
                "id_contexto": "C001",
                "contexto": "En una tienda...",
                "enunciado": "¿Cuánto es 3+4?",
                "opcion_a": "6",
                "opcion_b": "7",
                "opcion_c": "8",
                "opcion_d": "9",
                "correcta": "B",
                "imagen": "",
            },
            {
                "id": "TEST003",
                "evaluacion": "Trimestral",
                "area": "Lenguaje",
                "periodo": "1",
                "grado": "5",
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
                "id": "TEST004",
                "evaluacion": "Trimestral",
                "area": "Lenguaje",
                "periodo": "1",
                "grado": "6",
                "id_contexto": "C003",
                "contexto": "Lee el siguiente cuento...",
                "enunciado": "¿Quién es el protagonista?",
                "opcion_a": "Juan",
                "opcion_b": "María",
                "opcion_c": "Pedro",
                "opcion_d": "Ana",
                "correcta": "B",
                "imagen": "",
            },
            {
                "id": "TEST005",
                "evaluacion": "Semestral",
                "area": "Ciencias",
                "periodo": "2",
                "grado": "5",
                "id_contexto": "C004",
                "contexto": "Observa la imagen del ecosistema...",
                "enunciado": "¿Cuál es el productor en esta cadena?",
                "opcion_a": "Depredador",
                "opcion_b": "Herbívoro",
                "opcion_c": "Planta",
                "opcion_d": "Descomponedor",
                "correcta": "C",
                "imagen": "",
            },
        ]
    )

    path = "preguntas_test.xlsx"
    df.to_excel(path, index=False)
    print(f"✓ Archivo creado: {path}\n")
    return path


def test_cargar_preguntas():
    """Test 1: Cargar preguntas desde Excel"""
    print("=" * 60)
    print("TEST 1: CARGAR PREGUNTAS DESDE EXCEL")
    print("=" * 60)

    banco = BancoPreguntasProfesional("preguntas_test.xlsx")

    todas = banco.obtener_todas_preguntas()
    print(f"✓ Total de preguntas cargadas: {len(todas)}")
    print(f"✓ Primeras columnas: {list(todas.columns)[:5]}\n")

    return banco


def test_obtener_disponibles(banco):
    """Test 2: Obtener grados, áreas y evaluaciones disponibles"""
    print("=" * 60)
    print("TEST 2: OBTENER DISPONIBLES (Grados, Áreas, Evaluaciones)")
    print("=" * 60)

    grados = banco.obtener_grados_disponibles()
    print(f"✓ Grados disponibles: {grados}")

    areas = banco.obtener_areas_disponibles()
    print(f"✓ Áreas disponibles: {areas}")

    evals = banco.obtener_evaluaciones_disponibles()
    print(f"✓ Evaluaciones disponibles: {evals}")

    # Por grado
    areas_g5 = banco.obtener_areas_disponibles(grado="5")
    print(f"✓ Áreas en Grado 5: {areas_g5}")

    evals_mat = banco.obtener_evaluaciones_disponibles(area="Matemáticas")
    print(f"✓ Evaluaciones en Matemáticas: {evals_mat}\n")


def test_filtrar_preguntas(banco):
    """Test 3: Filtrar preguntas"""
    print("=" * 60)
    print("TEST 3: FILTRAR PREGUNTAS")
    print("=" * 60)

    # Filtro 1: Solo grado 5
    df1 = banco.obtener_preguntas_filtradas(grado="5")
    print(f"✓ Preguntas de Grado 5: {len(df1)}")

    # Filtro 2: Grado 5, Matemáticas
    df2 = banco.obtener_preguntas_filtradas(grado="5", area="Matemáticas")
    print(f"✓ Preguntas Grado 5 + Matemáticas: {len(df2)}")
    print(f"  Preguntas: {list(df2['id'].values)}")

    # Filtro 3: Grado 5, Matemáticas, Diagnóstica
    df3 = banco.obtener_preguntas_filtradas(
        grado="5", area="Matemáticas", evaluacion="Diagnóstica"
    )
    print(f"✓ Preguntas Grado 5 + Matemáticas + Diagnóstica: {len(df3)}")
    print(f"  Enunciados: {list(df3['enunciado'].values)}\n")


def test_agregar_pregunta(banco):
    """Test 4: Agregar nueva pregunta"""
    print("=" * 60)
    print("TEST 4: AGREGAR NUEVA PREGUNTA")
    print("=" * 60)

    nueva_pregunta = {
        "id": "NEW001",
        "evaluacion": "Diagnóstica",
        "area": "Matemáticas",
        "periodo": "1",
        "grado": "5",
        "id_contexto": "C005",
        "contexto": "En una panadería...",
        "enunciado": "¿Cuánto es 5+5?",
        "opcion_a": "9",
        "opcion_b": "10",
        "opcion_c": "11",
        "opcion_d": "12",
        "correcta": "B",
        "imagen": "",
    }

    exitoso, mensaje = banco.guardar_pregunta(
        id_pregunta="NEW001", datos_pregunta=nueva_pregunta, es_nueva=True
    )
    print(f"{'✓' if exitoso else '✗'} {mensaje}")

    # Verificar que se guardó
    pregunta_guardada = banco.obtener_pregunta_por_id("NEW001")
    if pregunta_guardada:
        print(f"✓ Pregunta recuperada: {pregunta_guardada['enunciado']}\n")
    else:
        print("✗ No se pudo recuperar\n")


def test_editar_pregunta(banco):
    """Test 5: Editar pregunta existente"""
    print("=" * 60)
    print("TEST 5: EDITAR PREGUNTA EXISTENTE")
    print("=" * 60)

    # Obtener pregunta original
    pregunta_original = banco.obtener_pregunta_por_id("TEST001")
    print(f"Original: {pregunta_original['enunciado']}")

    # Modificar
    pregunta_original["enunciado"] = "¿Cuánto es el doble de 2?"
    pregunta_original["correcta"] = "B"

    exitoso, mensaje = banco.guardar_pregunta(
        id_pregunta="TEST001", datos_pregunta=pregunta_original, es_nueva=False
    )
    print(f"{'✓' if exitoso else '✗'} {mensaje}")

    # Verificar cambio
    pregunta_actualizada = banco.obtener_pregunta_por_id("TEST001")
    print(f"Actualizada: {pregunta_actualizada['enunciado']}\n")


def test_eliminar_pregunta(banco):
    """Test 6: Eliminar pregunta"""
    print("=" * 60)
    print("TEST 6: ELIMINAR PREGUNTA")
    print("=" * 60)

    exitoso, mensaje = banco.eliminar_pregunta("NEW001")
    print(f"{'✓' if exitoso else '✗'} {mensaje}")

    # Verificar que se eliminó
    pregunta = banco.obtener_pregunta_por_id("NEW001")
    if pregunta is None:
        print("✓ Confirmado: Pregunta eliminada\n")
    else:
        print("✗ La pregunta aún existe\n")


def test_importacion_masiva(banco):
    """Test 7: Importación masiva"""
    print("=" * 60)
    print("TEST 7: IMPORTACIÓN MASIVA")
    print("=" * 60)

    # Crear archivo para importar
    df_importar = pd.DataFrame(
        [
            {
                "id": "IMP001",
                "evaluacion": "Diagnóstica",
                "area": "Inglés",
                "periodo": "1",
                "grado": "7",
                "id_contexto": "C100",
                "contexto": "Listen to the dialogue...",
                "enunciado": "What is the man's name?",
                "opcion_a": "John",
                "opcion_b": "James",
                "opcion_c": "Jack",
                "opcion_d": "Joseph",
                "correcta": "A",
                "imagen": "",
            },
            {
                "id": "IMP002",
                "evaluacion": "Diagnóstica",
                "area": "Inglés",
                "periodo": "1",
                "grado": "7",
                "id_contexto": "C100",
                "contexto": "Listen to the dialogue...",
                "enunciado": "Where does he work?",
                "opcion_a": "School",
                "opcion_b": "Hospital",
                "opcion_c": "Office",
                "opcion_d": "Factory",
                "correcta": "C",
                "imagen": "",
            },
            # Este será rechazado (duplicado por ID)
            {
                "id": "TEST001",  # Ya existe
                "evaluacion": "Diagnóstica",
                "area": "Inglés",
                "periodo": "1",
                "grado": "7",
                "id_contexto": "C101",
                "contexto": "",
                "enunciado": "Different question",
                "opcion_a": "A",
                "opcion_b": "B",
                "opcion_c": "C",
                "opcion_d": "D",
                "correcta": "A",
                "imagen": "",
            },
            # Este será rechazado (sin enunciado)
            {
                "id": "IMP003",
                "evaluacion": "Diagnóstica",
                "area": "Inglés",
                "periodo": "1",
                "grado": "7",
                "id_contexto": "C102",
                "contexto": "",
                "enunciado": "",  # Falta
                "opcion_a": "A",
                "opcion_b": "B",
                "opcion_c": "C",
                "opcion_d": "D",
                "correcta": "A",
                "imagen": "",
            },
        ]
    )

    df_importar.to_excel("importar_test.xlsx", index=False)
    print("✓ Archivo de importación creado\n")

    # Hacer la importación
    resumen = banco.importar_masivo("importar_test.xlsx")

    print(f"Resultados:")
    print(f"  Exitosas: {resumen['exitosas']}")
    print(f"  Duplicadas por ID: {resumen['duplicadas_id']}")
    print(f"  Duplicadas por enunciado: {resumen['duplicadas_enunciado']}")
    print(f"  Rechazadas por validación: {resumen['rechazadas_validacion']}")
    print(f"  Total procesadas: {resumen['total_procesadas']}\n")

    # Mostrar reporte
    print("Reporte detallado:")
    reporte = banco.generar_reporte_importacion(resumen)
    print(reporte)


def test_validacion_integridad(banco):
    """Test 8: Validación de integridad"""
    print("=" * 60)
    print("TEST 8: VALIDACIÓN DE INTEGRIDAD")
    print("=" * 60)

    advertencias = banco.validar_integridad()

    encontro_problemas = any(advertencias.values())

    if not encontro_problemas:
        print("✓ No se encontraron problemas de integridad\n")
    else:
        print("Advertencias encontradas:")

        if advertencias["ids_duplicados"]:
            print(f"  IDs duplicados: {advertencias['ids_duplicados']}")

        if advertencias["enunciados_duplicados"]:
            print(
                f"  Enunciados duplicados: {len(advertencias['enunciados_duplicados'])}"
            )

        if advertencias["campos_vacios"]:
            for campo in advertencias["campos_vacios"][:3]:
                print(f"  Campos vacíos: {campo}")

        if advertencias["opciones_correctas_invalidas"]:
            print(
                f"  Opciones correctas inválidas: {advertencias['opciones_correctas_invalidas']}\n"
            )


def test_estadisticas(banco):
    """Test 9: Estadísticas del banco"""
    print("=" * 60)
    print("TEST 9: ESTADÍSTICAS DEL BANCO")
    print("=" * 60)

    stats = banco.obtener_estadisticas()

    for clave, valor in stats.items():
        print(f"  {clave}: {valor}")
    print()


def test_casos_especiales(banco):
    """Test 10: Casos especiales de validación"""
    print("=" * 60)
    print("TEST 10: CASOS ESPECIALES DE VALIDACIÓN")
    print("=" * 60)

    # Intento 1: Agregar con ID vacío
    print("1. Intento de guardar con ID vacío:")
    datos = {
        "id": "",  # Vacío
        "evaluacion": "Test",
        "area": "Test",
        "enunciado": "Test",
        "opcion_a": "A",
        "opcion_b": "B",
        "opcion_c": "C",
        "opcion_d": "D",
        "correcta": "A",
        "imagen": "",
        "periodo": "",
        "grado": "",
        "id_contexto": "",
        "contexto": "",
    }
    exitoso, mensaje = banco.guardar_pregunta("", datos, es_nueva=True)
    print(f"   {'✗ Rechazado' if not exitoso else '✓ Aceptado'}: {mensaje}")

    # Intento 2: Opción correcta inválida
    print("\n2. Intento con opción correcta inválida (Z):")
    datos["id"] = "SPECIAL001"
    datos["correcta"] = "Z"
    exitoso, mensaje = banco.guardar_pregunta("SPECIAL001", datos, es_nueva=True)
    print(f"   {'✗ Rechazado' if not exitoso else '✓ Aceptado'}: {mensaje}")

    # Intento 3: ID duplicado en edición
    print("\n3. Intento de cambiar ID a uno existente:")
    existente = banco.obtener_pregunta_por_id("TEST002")
    existente["id"] = "TEST001"  # Cambiar a ID que ya existe
    exitoso, mensaje = banco.guardar_pregunta("TEST002", existente, es_nueva=False)
    print(f"   {'✗ Rechazado' if not exitoso else '✓ Aceptado'}: {mensaje}\n")


def main():
    """Función principal de pruebas."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║  PRUEBAS COMPLETAS - BANCO DE PREGUNTAS PROFESIONAL  ║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    # Crear archivo de prueba
    path = crear_archivo_prueba()

    # Ejecutar tests
    try:
        banco = test_cargar_preguntas()
        test_obtener_disponibles(banco)
        test_filtrar_preguntas(banco)
        test_agregar_pregunta(banco)
        test_editar_pregunta(banco)
        test_eliminar_pregunta(banco)
        test_importacion_masiva(banco)
        test_validacion_integridad(banco)
        test_estadisticas(banco)
        test_casos_especiales(banco)

        print("=" * 60)
        print("✓ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("=" * 60)

        # Realizar limpieza
        print("\nLimpieza de archivos de prueba...")
        if os.path.exists("preguntas_test.xlsx"):
            os.remove("preguntas_test.xlsx")
            print("✓ preguntas_test.xlsx eliminado")

        if os.path.exists("importar_test.xlsx"):
            os.remove("importar_test.xlsx")
            print("✓ importar_test.xlsx eliminado")

        print("\n✓ Test suite completado correctamente")

    except Exception as e:
        print(f"\n✗ ERROR durante los tests: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    exito = main()
    sys.exit(0 if exito else 1)
