import sqlite3
import re


def generar_id_evaluacion(area, grado, periodo, n):
    area_norm = re.sub(r"[^A-Za-z]", "", str(area or "")).upper()[:3]
    grado_norm = str(grado or "").strip()
    periodo_norm = str(periodo or "").strip()
    return f"SEA-{area_norm}-{grado_norm}-P{periodo_norm}-F{n:02d}"


def migrar_id_evaluacion(db_path="sistema.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # 1. Detectar grupos sin id_evaluacion
    cur.execute(
        """
        SELECT grado, area, evaluacion, periodo
        FROM banco_preguntas
        WHERE id_evaluacion IS NULL OR id_evaluacion = '' OR id_evaluacion = 'SIN ID'
        GROUP BY grado, area, evaluacion, periodo
    """
    )
    grupos = cur.fetchall()
    print(f"Grupos a migrar: {len(grupos)}")
    for idx, (grado, area, evaluacion, periodo) in enumerate(grupos, 1):
        nuevo_id = generar_id_evaluacion(area, grado, periodo, idx)
        print(
            f"Asignando {nuevo_id} a: grado={grado}, area={area}, evaluacion={evaluacion}, periodo={periodo}"
        )
        cur.execute(
            """
            UPDATE banco_preguntas
            SET id_evaluacion = ?
            WHERE (id_evaluacion IS NULL OR id_evaluacion = '' OR id_evaluacion = 'SIN ID')
              AND grado = ? AND area = ? AND evaluacion = ? AND periodo = ?
        """,
            (nuevo_id, grado, area, evaluacion, periodo),
        )
    conn.commit()
    # Validación final
    cur.execute(
        "SELECT COUNT(*) FROM banco_preguntas WHERE id_evaluacion IS NULL OR id_evaluacion = '' OR id_evaluacion = 'SIN ID'"
    )
    faltantes = cur.fetchone()[0]
    if faltantes == 0:
        print("Migración completada: todos los registros tienen id_evaluacion.")
    else:
        print(f"Advertencia: {faltantes} registros aún sin id_evaluacion.")
    conn.close()


if __name__ == "__main__":
    migrar_id_evaluacion()
