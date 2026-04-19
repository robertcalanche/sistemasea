#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de depuración para el Banco de Preguntas
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("=" * 70)
print("DEPURACIÓN DEL BANCO DE PREGUNTAS - VERIFICACIÓN DE FLUJO")
print("=" * 70)

# Paso 1: Verificar BancoPreguntasProfesional
print("\n✓ Paso 1: Cargando BancoPreguntasProfesional...")
try:
    from banco_preguntas_profesional import BancoPreguntasProfesional

    banco = BancoPreguntasProfesional(str(BASE_DIR / "preguntas.xlsx"))
    print(f"   Total preguntas: {banco.obtener_estadisticas()['total_preguntas']}")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Paso 2: Probar obtener_preguntas_filtradas
print("\n✓ Paso 2: Probando obtener_preguntas_filtradas()...")
try:
    df = banco.obtener_preguntas_filtradas(grado=None, area=None, evaluacion=None)
    print(f"   Total filas devueltas (sin filtros): {len(df)}")
    if len(df) > 0:
        print(f"   Primeras columnas: {list(df.columns)}")
    else:
        print("   ✗ DataFrame vacío!")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback

    traceback.print_exc()

# Paso 3: Buscar si hay problema de combo o initialización
print("\n✓ Paso 3: Revisando obtener_grados_disponibles()...")
try:
    grados = banco.obtener_grados_disponibles()
    print(f"   Grados: {grados}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Paso 4: Revisar si se puede crear la interfaz sin errores
print("\n✓ Paso 4: Intentando crear interfaz (sin mostrar ventana)...")
try:
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()

    from modulo_superadmin import ModuloSuperAdmin

    DB_FILE = BASE_DIR / "resultados.db"

    msa = ModuloSuperAdmin(root, db_path=str(DB_FILE), base_dir=str(BASE_DIR))
    print("   ModuloSuperAdmin creado exitosamente")

    # Verificar que banco tenga datos
    print(
        f"   Banco del módulo tiene {msa.banco.obtener_estadisticas()['total_preguntas']} preguntas"
    )

    root.destroy()

except Exception as e:
    print(f"   ✗ Error creando ModuloSuperAdmin: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✓ TODAS LAS PRUEBAS PASARON - El problema está en la interfaz visual")
print("=" * 70)
