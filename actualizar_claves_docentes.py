import sqlite3
import os

# Bases de datos a actualizar
db_files = [
    "sistema.db",
    "sistema_test_examen.db",
    "dist/sistema.db",
    "DatosCompartidos/sistema.db",
]

for db_path in db_files:
    print()
    print("=" * 60)
    print("Base de datos:", db_path)
    print("=" * 60)

    if not os.path.exists(db_path):
        print("  ARCHIVO NO ENCONTRADO - Saltando...")
        continue

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verificar si existe la tabla docentes
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='docentes'"
        )
        if not cursor.fetchone():
            print("  La tabla docentes NO EXISTE en esta base de datos.")
            conn.close()
            continue

        # Actualizar clave solo si está vacía o NULL y estado es Activo
        cursor.execute(
            """
            UPDATE docentes
            SET clave = documento
            WHERE (clave IS NULL OR clave = '') AND (estado IS NULL OR LOWER(estado) = 'activo')
        """
        )
        conn.commit()
        print("  Claves actualizadas para docentes activos con clave vacía.")

        # Mostrar los docentes afectados
        cursor.execute(
            "SELECT documento, nombre, cargo, clave, estado FROM docentes WHERE clave = documento AND (estado IS NULL OR LOWER(estado) = 'activo')"
        )
        for row in cursor.fetchall():
            print(
                f"    Documento: {row[0]}, Nombre: {row[1]}, Cargo: {row[2]}, Clave: {row[3]}, Estado: {row[4]}"
            )

        conn.close()
    except Exception as e:
        print("  ERROR:", e)
