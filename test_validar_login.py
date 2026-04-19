#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de prueba para validar login de estudiante."""

import sys
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Importar función de validación
from Admin import validar_estudiante, DB_FILE

print("=" * 60)
print("PRUEBA DE VALIDAR_ESTUDIANTE")
print("=" * 60)

# Obtener un documento de prueba
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("SELECT documento FROM estudiantes LIMIT 1")
test_doc = cursor.fetchone()[0]
conn.close()

print(f"\nDocumento de prueba: {test_doc}")

# Probar validación
resultado = validar_estudiante(test_doc)

if resultado:
    print("\nEstudiante validado exitosamente:")
    for key, value in resultado.items():
        print(f"  {key}: {value}")
else:
    print("\nERROR: Estudiante no validado")

print("=" * 60)
