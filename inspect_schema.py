#!/usr/bin/env python3
import sqlite3
import json

DB_FILE = "sistema.db"

# Ver estructuras de tablas principales
with sqlite3.connect(DB_FILE) as conn:
    cur = conn.cursor()

    # Tabla respuestas_estudiantes
    print("=== ESTRUCTURA respuestas_estudiantes ===")
    cur.execute("PRAGMA table_info(respuestas_estudiantes)")
    for row in cur.fetchall():
        print(f"  {row[1]} ({row[2]})")

    # Tabla resultados
    print("\n=== ESTRUCTURA resultados ===")
    cur.execute("PRAGMA table_info(resultados)")
    for row in cur.fetchall():
        print(f"  {row[1]} ({row[2]})")

    # Tabla evaluaciones
    print("\n=== ESTRUCTURA evaluaciones ===")
    cur.execute("PRAGMA table_info(evaluaciones)")
    for row in cur.fetchall():
        print(f"  {row[1]} ({row[2]})")

    # Ejemplo de datos
    print("\n=== EJEMPLO: respuesta de estudiante ===")
    cur.execute("SELECT * FROM respuestas_estudiantes LIMIT 1")
    cols = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    if row:
        for col, val in zip(cols, row):
            print(f"  {col}: {val}")

    print("\n=== EJEMPLO: resultado ===")
    cur.execute("SELECT * FROM resultados LIMIT 1")
    cols = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    if row:
        for col, val in zip(cols, row):
            print(f"  {col}: {val}")

    print("\n=== EJEMPLO: evaluación ===")
    cur.execute("SELECT * FROM evaluaciones LIMIT 1")
    cols = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    if row:
        for col, val in zip(cols, row):
            print(f"  {col}: {val}")
