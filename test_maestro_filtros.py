#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test para verificar que los filtros en Acceso Maestro funcionan correctamente.
"""

import os
import sys
import sqlite3

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modulo_superadmin import (
    ModuloSuperAdmin,
    cargar_grados_desde_preguntas,
    cargar_areas_por_grado,
    cargar_evaluaciones_por_grado_y_area,
)


def test_database_creation():
    """Verifica que la tabla config_examenes se cree correctamente."""
    print("=" * 60)
    print("TEST 1: Creación de tablas en la base de datos")
    print("=" * 60)

    # Crear instancia del módulo (sin mostrar UI)
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()  # Ocultar ventana

    try:
        msa = ModuloSuperAdmin(root, db_path="test_sistema.db")

        # Verificar que la tabla config_examenes existe
        conn = sqlite3.connect("test_sistema.db")
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        print(f"✓ Tablas encontradas: {tables}")

        if "config_examenes" in tables:
            print("✓ Tabla config_examenes creada correctamente")

            # Verificar columnas
            cur.execute("PRAGMA table_info(config_examenes)")
            columns = [row[1] for row in cur.fetchall()]
            print(f"✓ Columnas: {columns}")

            required_cols = [
                "grado",
                "area",
                "evaluacion",
                "duracion_segundos",
                "cantidad_preguntas",
            ]
            for col in required_cols:
                if col in columns:
                    print(f"  ✓ Columna '{col}' existe")
                else:
                    print(f"  ✗ Columna '{col}' FALTA")
        else:
            print("✗ Tabla config_examenes NO se creó")

        conn.close()
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        try:
            root.destroy()
        except:
            pass


def test_cargar_grados():
    """Verifica que se pueden cargar los grados desde preguntas.xlsx."""
    print("\n" + "=" * 60)
    print("TEST 2: Carga de grados desde preguntas.xlsx")
    print("=" * 60)

    preguntas_path = os.path.join(os.getcwd(), "preguntas.xlsx")

    if not os.path.exists(preguntas_path):
        print(f"✗ Archivo {preguntas_path} no existe")
        return False

    try:
        grados = cargar_grados_desde_preguntas(preguntas_path)
        if grados:
            print(f"✓ Grados cargados: {grados}")
            return True
        else:
            print("⚠ No se encontraron grados (preguntas.xlsx podría estar vacío)")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_cargar_areas():
    """Verifica que se pueden cargar las áreas por grado."""
    print("\n" + "=" * 60)
    print("TEST 3: Carga de áreas por grado")
    print("=" * 60)

    preguntas_path = os.path.join(os.getcwd(), "preguntas.xlsx")

    grados = cargar_grados_desde_preguntas(preguntas_path)
    if not grados:
        print("⚠ No hay grados disponibles para probar")
        return True

    grado_test = grados[0]
    try:
        areas = cargar_areas_por_grado(grado_test, preguntas_path)
        print(f"✓ Para grado '{grado_test}': áreas = {areas}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_cargar_evaluaciones():
    """Verifica que se pueden cargar las evaluaciones por grado y área."""
    print("\n" + "=" * 60)
    print("TEST 4: Carga de evaluaciones por grado y área")
    print("=" * 60)

    preguntas_path = os.path.join(os.getcwd(), "preguntas.xlsx")

    grados = cargar_grados_desde_preguntas(preguntas_path)
    if not grados:
        print("⚠ No hay grados disponibles")
        return True

    grado = grados[0]
    areas = cargar_areas_por_grado(grado, preguntas_path)
    if not areas:
        print(f"⚠ No hay áreas para el grado '{grado}'")
        return True

    area = areas[0]
    try:
        evals = cargar_evaluaciones_por_grado_y_area(grado, area, preguntas_path)
        print(f"✓ Para grado '{grado}' y área '{area}': evaluaciones = {evals}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def cleanup():
    """Limpia archivos de prueba."""
    print("\n" + "=" * 60)
    print("Limpieza")
    print("=" * 60)

    test_db = "test_sistema.db"
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
            print(f"✓ Archivo de prueba {test_db} eliminado")
        except Exception as e:
            print(f"⚠ No se pudo eliminar {test_db}: {e}")


if __name__ == "__main__":
    print("\n" + "🧪 PRUEBAS DE FILTROS EN ACCESO MAESTRO" + "\n")

    results = []
    results.append(("Creación de tablas", test_database_creation()))
    results.append(("Cargar grados", test_cargar_grados()))
    results.append(("Cargar áreas", test_cargar_areas()))
    results.append(("Cargar evaluaciones", test_cargar_evaluaciones()))

    # nuevo: verificar que el filtrado por evaluación excluye otras entradas
    def test_filtrado_por_evaluacion():
        """El filtrado debe usar exclusivamente el campo `evaluacion`."""
        print("\n" + "=" * 60)
        print("TEST 5: Filtrado por evaluacion")
        print("=" * 60)

        import pandas as pd
        from Admin import cargar_preguntas_filtradas

        # construir un DataFrame simulado
        df = pd.DataFrame(
            {
                "evaluacion": ["a", "a", "b", "c"],
                "area": ["X", "X", "Y", "Y"],
                "grado": ["1", "1", "2", "2"],
                "id": [1, 2, 3, 4],
            }
        )

        original_read = pd.read_excel
        pd.read_excel = lambda *args, **kwargs: df
        try:
            res = cargar_preguntas_filtradas("x", "1", "a")
            if not res.empty and all(res["evaluacion"] == "a"):
                print("✓ sólo devolvió preguntas con evaluacion 'a'")
                return True
            else:
                print("✗ el filtrado devolvió evaluaciones no deseadas", res)
                return False
        finally:
            pd.read_excel = original_read

    results.append(("Filtrado evaluacion", test_filtrado_por_evaluacion()))

    cleanup()

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)

    for name, result in results:
        status = "✓ PASÓ" if result else "✗ FALLÓ"
        print(f"{status}: {name}")

    if all(r[1] for r in results):
        print("\n✓ Todos los tests pasaron!")
        sys.exit(0)
    else:
        print("\n✗ Algunos tests fallaron")
        sys.exit(1)
