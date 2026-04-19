#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de prueba para importar estudiantes desde Excel a SQLite."""

import sys
from pathlib import Path

# Agregar el directorio actual al path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Importar las funciones necesarias
from Admin import crear_base_datos, importar_estudiantes_desde_excel
import sqlite3

DB_FILE = BASE_DIR / "sistema.db"

print("=" * 60)
print("INICIALIZANDO BASE DE DATOS E IMPORTANDO ESTUDIANTES")
print("=" * 60)

# Crear base de datos e importar estudiantes
print("\n1. Creando tablas...")
crear_base_datos()

print("\n2. Importando estudiantes desde Excel (explícito)...")
importar_estudiantes_desde_excel()

# Verificar estudiantes importados
print("\n3. Verificando estudiantes en la BD...")
try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM estudiantes")
    count = cursor.fetchone()[0]

    print(f"   ✓ Total de estudiantes: {count}")

    if count > 0:
        print("\n4. Primeros 5 estudiantes:")
        cursor.execute(
            "SELECT documento, nombre, grado, curso, estado FROM estudiantes LIMIT 5"
        )
        for row in cursor.fetchall():
            print(f"   - {row[0]} | {row[1]} | Grado {row[2]} | {row[3]} | {row[4]}")

    conn.close()
    print("\n✓ IMPORTACIÓN COMPLETADA EXITOSAMENTE")

except Exception as e:
    print(f"   ✗ Error: {e}")

print("=" * 60)
