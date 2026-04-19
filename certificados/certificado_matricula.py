from core.construir_nombre import construir_nombre

"""
Generador de PDF para Certificado de Matrícula.
"""

# Importaciones necesarias (completar en desarrollo)


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generar_certificado_matricula(estudiante, institucion, datos_cert, path_pdf):
    """
    Genera el PDF del certificado de matrícula.
    """
    c = canvas.Canvas(path_pdf, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "CERTIFICADO DE MATRÍCULA")
    c.setFont("Helvetica", 12)
    c.drawString(72, height - 110, f"Nombre: {construir_nombre(estudiante)}")
    c.drawString(72, height - 130, f"Documento: {estudiante.get('documento','')}")
    c.drawString(72, height - 150, f"Grado: {estudiante.get('grado','')}")
    c.drawString(72, height - 170, f"Curso: {estudiante.get('curso','')}")
    c.drawString(72, height - 190, f"Institución: {institucion.get('nombre','')}")
    c.drawString(72, height - 210, f"Código: {datos_cert.get('codigo','')}")
    c.drawString(
        72,
        height - 250,
        "Este documento certifica que el estudiante está matriculado para el año lectivo.",
    )
    c.showPage()
    c.save()
