#!/usr/bin/env python3
import sqlite3

DB_FILE = "sistema.db"

# Ver estructura de tabla de configuración
with sqlite3.connect(DB_FILE) as conn:
    cur = conn.cursor()

    # Listar tablas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tablas = cur.fetchall()
    print("=== TABLAS EN BD ===")
    for tabla in tablas:
        print(f"  {tabla[0]}")

    # Buscar tabla de configuración
    for tabla_name in [
        "configuracion",
        "config",
        "plantel",
        "configuracion_plantel",
        "instituciones",
    ]:
        try:
            cur.execute(f"PRAGMA table_info({tabla_name})")
            cols = cur.fetchall()
            if cols:
                print(f"\n=== TABLA {tabla_name} ===")
                for col in cols:
                    print(f"  {col[1]} ({col[2]})")
        except:
            pass
