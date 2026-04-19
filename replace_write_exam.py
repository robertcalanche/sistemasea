import re

file = r"c:\Users\rober\Documents\Proyecto_Evaluacion\modulo_superadmin.py"

new = """    def _write_exam_pdf(
    self,
    preguntas_df,
    estudiante,
    path,
    cantidad,
    area,
    evaluacion,
):

    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        PageTemplate,
        Paragraph,
        Spacer,
        KeepTogether,
    )
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfgen import canvas

    import os

    # ==========================
    # REGISTRAR ARIAL
    # ==========================
    try:
        pdfmetrics.registerFont(TTFont("Arial", "arial.ttf"))
        pdfmetrics.registerFont(TTFont("Arial-Bold", "arialbd.ttf"))
    except:
        pass

    # ==========================
    # CONFIGURACIÓN DOCUMENTO
    # ==========================
    altura_header = 4.5 * cm  # espacio fijo arriba

    doc = BaseDocTemplate(
        path,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm + altura_header,
        bottomMargin=1.5 * cm,
    )

    width, height = A4

    # ==========================
    # COLUMNAS
    # ==========================
    frame_izq = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        (doc.width / 2) - 6,
        doc.height,
        id="col1",
    )

    frame_der = Frame(
        doc.leftMargin + (doc.width / 2) + 6,
        doc.bottomMargin,
        (doc.width / 2) - 6,
        doc.height,
        id="col2",
    )

    # ==========================
    # ENCABEZADO EN CANVAS
    # ==========================
    def header_footer(canvas_obj, doc_obj):

        canvas_obj.setFont("Arial-Bold", 12)
        canvas_obj.drawCentredString(
            width / 2,
            height - 1.5 * cm,
            self._get_config_value("institucion", "nombre") or "",
        )

        canvas_obj.setFont("Arial", 10)
        canvas_obj.drawCentredString(
            width / 2,
            height - 2.1 * cm,
            f"Ciudad: {self._get_config_value('institucion','ciudad') or ''}",
        )

        canvas_obj.setFont("Arial", 10)
        canvas_obj.drawString(
            1.5 * cm,
            height - 3 * cm,
            f"Nombre: {estudiante['nombre']}    Documento: {estudiante['documento']}",
        )

        canvas_obj.drawString(
            1.5 * cm,
            height - 3.6 * cm,
            f"Grado: {estudiante['grado']}   Área: {area}   Evaluación: {evaluacion}",
        )

        # PIE
        canvas_obj.setFont("Arial", 9)
        canvas_obj.drawString(
            1.5 * cm,
            1 * cm,
            f"Nombre: {estudiante['nombre']}   Evaluación: {evaluacion}   Página {doc_obj.page}",
        )

    template = PageTemplate(
        id="dos_columnas",
        frames=[frame_izq, frame_der],
        onPage=header_footer,
    )

    doc.addPageTemplates([template])

    # ==========================
    # ESTILOS
    # ==========================
    styles = getSampleStyleSheet()

    estilo_normal = ParagraphStyle(
        "normal",
        parent=styles["Normal"],
        fontName="Arial",
        fontSize=12,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
    )

    estilo_negrita = ParagraphStyle(
        "bold",
        parent=estilo_normal,
        fontName="Arial-Bold",
    )

    elementos = []

    # ==========================
    # TEXTO INICIAL
    # ==========================
    elementos.append(
        Paragraph(
            "Lee con atención los siguientes textos y responde las preguntas",
            estilo_negrita,
        )
    )

    elementos.append(Spacer(1, 18))

    # ==========================
    # CONTENIDO
    # ==========================
    contador = 1

    for id_contexto, grupo in preguntas_df.groupby("id_contexto"):

        elementos.append(Paragraph(f"TEXTO {id_contexto}", estilo_negrita))
        elementos.append(Spacer(1, 6))

        contexto = grupo.iloc[0]["contexto"]
        elementos.append(Paragraph(contexto, estilo_normal))
        elementos.append(Spacer(1, 6))

        inicio = contador
        fin = contador + len(grupo) - 1

        elementos.append(
            Paragraph(
                f"RESPONDE LAS PREGUNTAS {inicio} A {fin} SEGÚN EL TEXTO {id_contexto}.",
                estilo_negrita,
            )
        )

        elementos.append(Spacer(1, 6))

        for _, row in grupo.iterrows():

            bloque = []

            bloque.append(
                Paragraph(f"{contador}. {row['enunciado']}", estilo_negrita)
            )

            bloque.append(Paragraph(f"A. {row['opcion_a']}", estilo_normal))
            bloque.append(Paragraph(f"B. {row['opcion_b']}", estilo_normal))
            bloque.append(Paragraph(f"C. {row['opcion_c']}", estilo_normal))
            bloque.append(Paragraph(f"D. {row['opcion_d']}", estilo_normal))

            bloque.append(Spacer(1, 12))

            elementos.append(KeepTogether(bloque))

            contador += 1

    doc.build(elementos)
"""

# read and replace
with open(file, "r", encoding="utf-8") as f:
    text = f.read()
pattern = re.compile(
    r"    def _write_exam_pdf[\s\S]*?(?=\n    def maestro_modificar_nota)", re.MULTILINE
)
new_text = pattern.sub(new, text)
with open(file, "w", encoding="utf-8") as f:
    f.write(new_text)
print("replaced")
