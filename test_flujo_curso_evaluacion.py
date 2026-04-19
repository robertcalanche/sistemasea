#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para probar las funciones de carga de cursos y evaluaciones"""

import sqlite3
from pathlib import Path
from Admin import (
    cargar_cursos_disponibles,
    cargar_evaluaciones_por_grado_area_curso,
    normalizar_grado,
    cargar_areas_por_grado,
)

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "sistema.db"


def test_flow():
    """Prueba el flujo completo"""

    print("=" * 60)
    print("TEST: Flujo de Carga de Cursos y Evaluaciones")
    print("=" * 60)

    # 1. Obtener grados disponibles
    print("\n1. Obteniendo grados disponibles...")
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT DISTINCT grado FROM estudiantes 
               WHERE estado = 'Activo' AND grado IS NOT NULL 
               ORDER BY grado"""
        )
        grados = [r[0] for r in cursor.fetchall() if r[0]]
        grados = sorted([normalizar_grado(g) for g in grados])
        conn.close()

        print(f"   Grados encontrados: {grados}")
    except Exception as e:
        print(f"   ERROR: {e}")
        return

    if not grados:
        print("   ⚠️ No hay grados disponibles")
        return

    # 2. Probar con cada grado
    for grado in grados:
        print(f"\n2. Testando con Grado: {grado}")
        print("-" * 40)

        # 2a. Cargar cursos
        print(f"   Cargando cursos para grado {grado}...")
        cursos = cargar_cursos_disponibles(grado)
        print(f"   Cursos: {cursos}")

        # 2b. Cargar áreas para el grado
        print(f"   Cargando áreas para grado {grado}...")
        areas = cargar_areas_por_grado(grado)
        print(f"   Áreas: {areas}")

        if not areas:
            print(f"   ⚠️ Sin áreas para grado {grado}, saltando...")
            continue

        # 2c. Para cada área, probar cargar evaluaciones
        for area in areas[:2]:  # Solo probar las 2 primeras áreas
            print(f"\n   Probando con Área: {area}")
            area_lower = str(area).strip().lower()

            # Sin filtro de curso
            print(f"      Cargando evaluaciones (sin filtro de curso)...")
            evals = cargar_evaluaciones_por_grado_area_curso(grado, area_lower, None)
            print(f"      Evaluaciones: {evals}")

            # Con filtro de curso = "TODOS"
            print(f"      Cargando evaluaciones (curso=TODOS)...")
            evals2 = cargar_evaluaciones_por_grado_area_curso(
                grado, area_lower, "TODOS"
            )
            print(f"      Evaluaciones: {evals2}")

            # Con filtro de curso específico (si existe alguno)
            if cursos:
                curso_test = cursos[0]
                print(f"      Cargando evaluaciones (curso={curso_test})...")
                evals3 = cargar_evaluaciones_por_grado_area_curso(
                    grado, area_lower, curso_test
                )
                print(f"      Evaluaciones: {evals3}")

    print("\n" + "=" * 60)
    print("✅ Test completado")
    print("=" * 60)


if __name__ == "__main__":
    test_flow()
