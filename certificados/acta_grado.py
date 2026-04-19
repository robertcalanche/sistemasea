"""
Generador de PDF para Acta de Grado (formato oficial Colombia).
"""

# Importaciones necesarias (completar en desarrollo)


def generar_acta_grado(
    estudiante, institucion, datos_cert, path_pdf, texto_modelo=None
):
    """
    Genera el PDF del acta de grado con el modelo institucional proporcionado o editable.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from reportlab.lib.enums import TA_CENTER
    from core.construir_nombre import construir_nombre

    # Variables para reemplazo
    nombre = construir_nombre(estudiante)
    documento = estudiante.get("documento", "")
    grado = estudiante.get("grado", "")
    curso = estudiante.get("curso", "")
    # Permitir usar datos_cert para compatibilidad futura
    variables = {
        "nombre": nombre,
        "documento": documento,
        "grado": grado,
        "curso": curso,
    }
    if datos_cert:
        variables.update(datos_cert)

    # Usar el texto editable si se proporciona
    texto = texto_modelo or "[No se proporcionó modelo institucional]"
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
        fontSize=12,
        leading=18,
    )
    story = []
    for linea in texto.split("\n"):
        if linea.strip():
            story.append(Paragraph(linea, style_center))
        else:
            story.append(Spacer(1, 0.5 * cm))
    doc.build(story)
