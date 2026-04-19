from .construir_nombre import construir_nombre


def backup_tabla_estudiantes(db_path):
    import sqlite3

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS estudiantes_backup AS SELECT * FROM estudiantes;"
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR BACKUP]: {e}")
        return False


def obtener_nombre_completo(estudiante):
    """
    Wrapper de compatibilidad para obtener el nombre completo del estudiante
    desde la estructura apellido1/apellido2/nombre1/nombre2.
    """
    return construir_nombre(estudiante)
