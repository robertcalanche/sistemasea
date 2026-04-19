#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verificar estado de la BD después del import."""

import sqlite3
from pathlib import Path

DB_FILE = Path("sistema.db")

print("=" * 60)
print("ESTADO ACTUAL DE LA BASE DE DATOS")
print("=" * 60)

if not DB_FILE.exists():
    print("ERROR: La base de datos sistema.db NO existe")
    exit(1)

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Tablas existentes
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"\nTablas en la BD: {len(tables)}")
for table in tables:
    print(f"  - {table[0]}")

# Datos en estudiantes
print("\n--- TABLA ESTUDIANTES ---")
try:
    cursor.execute("SELECT COUNT(*) FROM estudiantes")
    est_count = cursor.fetchone()[0]
    print(f"Total de registros: {est_count}")

    if est_count > 0:
        cursor.execute("SELECT documento, nombre, grado FROM estudiantes LIMIT 3")
        for row in cursor.fetchall():
            print(f"  {row[0]} | {row[1]} | {row[2]}")
except Exception as e:
    print(f"ERROR consultando: {e}")

# Datos en banco_preguntas
print("\n--- TABLA BANCO_PREGUNTAS ---")
try:
    cursor.execute("SELECT COUNT(*) FROM banco_preguntas")
    preg_count = cursor.fetchone()[0]
    print(f"Total de registros: {preg_count}")

    if preg_count > 0:
        cursor.execute("SELECT evaluacion, area, grado FROM banco_preguntas LIMIT 3")
        for row in cursor.fetchall():
            print(f"  {row[0]} | {row[1]} | {row[2]}")
except Exception as e:
    print(f"ERROR consultando: {e}")

# Tamaño de la BD
db_size = DB_FILE.stat().st_size / (1024 * 1024)
print(f"\nTamaño de la BD: {db_size:.2f} MB")

conn.close()
print("\n" + "=" * 60)
