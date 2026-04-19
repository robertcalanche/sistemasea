#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test cargar_preguntas y funciones relacionadas."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Suprimir GUI de Tkinter
import os

os.environ["DISPLAY"] = ""

import sqlite3
import pandas as pd
from Admin import (
    cargar_preguntas,
    cargar_preguntas_filtradas,
    cargar_areas,
    cargar_areas_por_grado,
    cargar_evaluaciones_por_grado_y_area,
    DB_FILE,
)

print("=" * 70)
print("TEST: FUNCIONES DE CARGA DE PREGUNTAS")
print("=" * 70)

# 1. cargar_preguntas()
print("\n1. Testing cargar_preguntas()...")
try:
    preguntas = cargar_preguntas()
    print(f"   ✓ Cargadas {len(preguntas)} preguntas")
    print(f"   Columnas: {list(preguntas.columns[:5])}...")
    if len(preguntas) > 0:
        print(f"   Primer registro (área): {preguntas.iloc[0].get('area', 'N/A')}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# 2. cargar_areas()
print("\n2. Testing cargar_areas()...")
try:
    areas = cargar_areas()
    print(f"   ✓ Áreas encontradas: {len(areas)}")
    if len(areas) > 0:
        print(f"   Áreas: {areas[:3]}...")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# 3. cargar_areas_por_grado()
print("\n3. Testing cargar_areas_por_grado()...")
try:
    areas_5 = cargar_areas_por_grado("5")
    print(f"   ✓ Áreas para grado 5: {len(areas_5)}")
    if len(areas_5) > 0:
        print(f"   Áreas: {areas_5}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# 4. cargar_evaluaciones_por_grado_y_area()
print("\n4. Testing cargar_evaluaciones_por_grado_y_area()...")
try:
    # Usar el primer grado y área disponibles
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT grado, area FROM banco_preguntas LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        grado, area = row
        evals = cargar_evaluaciones_por_grado_y_area(grado, area)
        print(f"   ✓ Evaluaciones para grado {grado}, área {area}: {len(evals)}")
        if len(evals) > 0:
            print(f"   Evaluaciones: {evals}")
    else:
        print("   ⚠ No hay datos para probar")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# 5. cargar_preguntas_filtradas()
print("\n5. Testing cargar_preguntas_filtradas()...")
try:
    # Obtener primer grado y área
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT area, grado FROM banco_preguntas LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        area, grado = row
        filtradas = cargar_preguntas_filtradas(area=area, grado=grado)
        print(
            f"   ✓ Preguntas filtradas (área={area}, grado={grado}): {len(filtradas)}"
        )
        if len(filtradas) > 0:
            print(
                f"   Primera pregunta enunciado: {filtradas.iloc[0]['enunciado'][:50]}..."
            )
    else:
        print("   ⚠ No hay datos para probar")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

# 6. Evaluar por evaluación
print("\n6. Testing cargar_preguntas_filtradas(evaluacion=...)...")
try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT evaluacion FROM banco_preguntas LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        evaluacion = row[0]
        filtradas = cargar_preguntas_filtradas(evaluacion=evaluacion)
        print(f"   ✓ Preguntas para evaluación '{evaluacion}': {len(filtradas)}")
    else:
        print("   ⚠ No hay datos para probar")
except Exception as e:
    print(f"   ✗ ERROR: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETADO")
print("=" * 70)
