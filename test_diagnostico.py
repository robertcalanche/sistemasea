#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de diagnóstico para verificar estructura de tabla estudiantes."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "sistema.db"

print("=" * 60)
print("DIAGNOSTICO DE TABLA ESTUDIANTES")
print("=" * 60)

if not DB_FILE.exists():
    print("BASE DE DATOS NO EXISTE")
else:
    print("BASE DE DATOS EXISTE: " + str(DB_FILE))

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Obtener información de las columnas
        cursor.execute("PRAGMA table_info(estudiantes)")
        columns = cursor.fetchall()

        print("\nCOLUMNAS EN TABLA ESTUDIANTES:")
        for col in columns:
            col_id, col_name, col_type, notnull, default_val, pk = col
            print("  %3d | %-20s | %-30s" % (col_id, col_name, col_type))

        # Intentar hacer un SELECT simple
        try:
            cursor.execute("SELECT COUNT(*) FROM estudiantes")
            count = cursor.fetchone()[0]
            print("\nTOTAL DE REGISTROS: " + str(count))
        except Exception as e:
            print("\nERROR AL CONSULTAR: " + str(e))

        conn.close()

    except Exception as e:
        print("ERROR: " + str(e))
