import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "resultados.db"

print(f"DB Path: {DB_FILE}")
print(f"DB existe: {DB_FILE.exists()}")

try:
    conn = sqlite3.connect(str(DB_FILE))
    cursor = conn.cursor()

    # Verificar si existe la tabla config_sistema
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='config_sistema'"
    )
    result = cursor.fetchone()
    print(f"\nTabla config_sistema existe: {result is not None}")

    if result:
        # Ver contenido de config_sistema
        cursor.execute("SELECT * FROM config_sistema")
        rows = cursor.fetchall()
        print(f"Contenido de config_sistema:")
        for row in rows:
            print(f"  {row}")

        # Ver específicamente la clave maestra
        cursor.execute("SELECT valor FROM config_sistema WHERE clave='master_key'")
        master_key = cursor.fetchone()
        if master_key:
            print(f"\nClave maestra encontrada: {master_key[0]}")
        else:
            print("\nClave maestra NO encontrada en la BD")
    else:
        print("\nLa tabla config_sistema no existe aún")

    # Ver todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = cursor.fetchall()
    print(f"\nTodas las tablas en la BD: {all_tables}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
