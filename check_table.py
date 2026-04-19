import sqlite3

conn = sqlite3.connect("sistema.db")
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="docentes"')
result = cursor.fetchone()
print("Tabla docentes existe:", result is not None)
conn.close()
