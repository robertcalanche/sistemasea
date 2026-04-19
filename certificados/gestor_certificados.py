"""
Módulo principal para la gestión de certificados académicos oficiales.
- Selección de estudiante y tipo de certificado
- Validación de datos
- Generación de código único
- Generación de PDF
- Registro en base de datos
"""

# Importaciones necesarias (completar en desarrollo)
import os
import sqlite3
from datetime import datetime
from certificados.generador_codigo import generar_codigo

# from certificados.certificado_matricula import generar_certificado_matricula
# from certificados.acta_grado import generar_acta_grado
# from certificados.diploma import generar_diploma

CARPETA_CERTIFICADOS = "certificados_generados"
os.makedirs(CARPETA_CERTIFICADOS, exist_ok=True)


def generar_documento(tipo, estudiante, institucion, ruta_personalizada=None):
    # Validar objeto estudiante
    if not estudiante or not estudiante.get("id"):
        raise Exception("Estudiante no válido")

    # Generar código único incremental
    codigo = generar_codigo(tipo)

    # Generar PDF según tipo

    if ruta_personalizada:
        ruta = ruta_personalizada
    else:
        if tipo == "MATRICULA":
            ruta = os.path.join(CARPETA_CERTIFICADOS, f"matricula_{codigo}.pdf")
        elif tipo == "ACTA":
            ruta = os.path.join(CARPETA_CERTIFICADOS, f"acta_{codigo}.pdf")
        elif tipo == "DIPLOMA":
            ruta = os.path.join(CARPETA_CERTIFICADOS, f"diploma_{codigo}.pdf")
        else:
            raise Exception("Tipo de documento no soportado")

    if tipo == "MATRICULA":
        from certificados.certificado_matricula import generar_certificado_matricula

        datos_cert = {"codigo": codigo}
        generar_certificado_matricula(estudiante, institucion, datos_cert, ruta)
    elif tipo == "ACTA":
        # Si tienes función para acta, llámala aquí y pásale ruta
        pass
    elif tipo == "DIPLOMA":
        from certificados.diploma import generar_diploma

        datos_cert = {"codigo": codigo}
        generar_diploma(estudiante, institucion, datos_cert, ruta)
    else:
        raise Exception("Tipo de documento no soportado")

    # (No crear PDF vacío: el PDF ya fue generado correctamente si corresponde)

    # Guardar registro en base de datos
    guardar_certificado(estudiante, tipo, codigo, ruta)
    return ruta


def guardar_certificado(estudiante, tipo, codigo, ruta):
    db_path = "sistema.db"  # Ajustar si es necesario
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    cursor.execute(
        """
        INSERT INTO certificados (estudiante_id, tipo, codigo, ruta, fecha)
        VALUES (?, ?, ?, ?, ?)
    """,
        (estudiante["id"], tipo, codigo, ruta, fecha),
    )
    conn.commit()
    conn.close()


class GestorCertificados:
    def __init__(self, db_path):
        self.db_path = db_path

    def generar_certificado(self, estudiante_id, tipo, datos_extra):
        """
        Lógica principal para generar y registrar un certificado.
        """
        pass
