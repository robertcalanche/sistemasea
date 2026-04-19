"""
Generador de códigos únicos para certificados.
"""

import sqlite3
from datetime import datetime


def generar_codigo(tipo):
    """
    Genera un código único incremental para el certificado.
    Formato: SEA-TIPO-2026-XXXX
    """
    db_path = "sistema.db"  # Ajustar si es necesario
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS certificados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id INTEGER,
            tipo TEXT,
            codigo TEXT UNIQUE,
            ruta TEXT,
            fecha TEXT,
            libro TEXT,
            folio TEXT,
            numero_diploma TEXT,
            acta TEXT
        )
    """
    )
    cursor.execute("SELECT COUNT(*) FROM certificados WHERE tipo = ?", (tipo,))
    count = cursor.fetchone()[0] + 1
    year = datetime.now().year
    codigo = f"SEA-{tipo}-{year}-{count:04d}"
    conn.close()
    return codigo
