import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "resultados.db"

conn = sqlite3.connect(str(DB_FILE))
cursor = conn.cursor()

# Actualizar clave maestra a admin123
cursor.execute(
    "REPLACE INTO config_sistema(clave,valor) VALUES(?,?)", ("master_key", "admin123")
)
conn.commit()
conn.close()

print("✓ Clave maestra reiniciada a 'admin123'")
