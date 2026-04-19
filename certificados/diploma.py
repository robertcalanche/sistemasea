"""
Generador de PDF para Diploma (formato visual elegante).
"""

# Importaciones necesarias (completar en desarrollo)


def generar_diploma(estudiante, institucion, datos_cert, path_pdf):
    """
    Genera el PDF del diploma usando el modelo institucional editable.
    """
    import os
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from reportlab.lib.enums import TA_CENTER
    from core.construir_nombre import construir_nombre

    # Cargar el modelo de diploma
    modelo_path = os.path.join(os.path.dirname(__file__), "modelo_diploma.txt")
    try:
        with open(modelo_path, "r", encoding="utf-8") as f:
            texto = f.read()
    except Exception:
        texto = "[No se pudo cargar el modelo institucional de diploma]"

    # Variables para reemplazo
    nombre = construir_nombre(estudiante)
    documento = estudiante.get("documento", "")
    grado = estudiante.get("grado", "")
    curso = estudiante.get("curso", "")
    numero_acta = datos_cert.get("numero_acta", "") if datos_cert else ""
    variables = {
        "nombre": nombre,
        "documento": documento,
        "grado": grado,
        "curso": curso,
        "numero_acta": numero_acta,
    }
    if datos_cert:
        variables.update(datos_cert)

    # Reemplazo de llaves tipo {nombre}, {documento}, etc.
    try:
        texto = texto.format(**variables)
    except Exception:
        pass

    doc = SimpleDocTemplate(
        path_pdf,
        pagesize=letter,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    style_center = ParagraphStyle(
        name="Center",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=13,
        leading=20,
    )
    story = []
    for linea in texto.split("\n"):
        if linea.strip():
            story.append(Paragraph(linea, style_center))
        else:
            story.append(Spacer(1, 0.5 * cm))
    doc.build(story)
