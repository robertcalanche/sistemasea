def _write_exam_pdf(
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
        Table,
        TableStyle,
        Image,
        FrameBreak,
        KeepTogether,
    )
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfgen import canvas
    from reportlab.platypus import PageBreak
    import os

    # ==============================
    # REGISTRAR ARIAL
    # ==============================
    try:
        pdfmetrics.registerFont(TTFont("Arial", "arial.ttf"))
        pdfmetrics.registerFont(TTFont("Arial-Bold", "arialbd.ttf"))
    except:
        pass

    # ==============================
    # DOCUMENTO
    # ==============================
    doc = BaseDocTemplate(
        path,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    page_width, page_height = A4

    # ==============================
    # FRAME SUPERIOR (ENCABEZADO)
    # ==============================
    altura_encabezado = 5.5 * cm

    frame_superior = Frame(
        doc.leftMargin,
        page_height - doc.topMargin - altura_encabezado,
        doc.width,
        altura_encabezado,
        id="frame_superior",
        showBoundary=0,
    )

    # ==============================
    # FRAMES COLUMNAS
    # ==============================
    altura_columnas = doc.height - altura_encabezado

    frame_izq = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        (doc.width / 2) - 6,
        altura_columnas,
        id="col_izq",
        showBoundary=0,
    )

    frame_der = Frame(
        doc.leftMargin + (doc.width / 2) + 6,
        doc.bottomMargin,
        (doc.width / 2) - 6,
        altura_columnas,
        id="col_der",
        showBoundary=0,
    )

    template = PageTemplate(
        id="plantilla_icfes",
        frames=[frame_superior, frame_izq, frame_der],
    )

    doc.addPageTemplates([template])

    # ==============================
    # ESTILOS
    # ==============================
    styles = getSampleStyleSheet()

    estilo_normal = ParagraphStyle(
        "NormalArial",
        parent=styles["Normal"],
        fontName="Arial",
        fontSize=12,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
    )

    estilo_negrita = ParagraphStyle(
        "BoldArial",
        parent=estilo_normal,
        fontName="Arial-Bold",
    )

    estilo_titulo = ParagraphStyle(
        "TituloTexto",
        parent=estilo_normal,
        fontName="Arial-Bold",
        fontSize=12,
        alignment=TA_LEFT,
    )

    elementos = []

    # ==============================
    # ENCABEZADO
    # ==============================
    nombre_inst = self._get_config_value("institucion", "nombre") or ""
    ciudad = self._get_config_value("institucion", "ciudad") or ""
    logo_path = self._get_config_value("institucion", "logo") or ""

    logo = ""
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path, width=2.5 * cm, preserveAspectRatio=True)

    tabla_header = Table(
        [
            [
                logo,
                Paragraph(
                    f"<b>{nombre_inst}</b><br/>"
                    f"Ciudad: {ciudad}",
                    estilo_negrita,
                ),
            ]
        ],
        colWidths=[3 * cm, doc.width - 3 * cm],
    )

    tabla_header.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    elementos.append(tabla_header)
    elementos.append(Spacer(1, 8))

    tabla_est = Table(
        [
            [
                Paragraph(
                    f"Nombre: {estudiante['nombre']}     Documento: {estudiante['documento']}<br/>"
                    f"Grado: {estudiante['grado']}   Área: {area}   Evaluación: {evaluacion}",
                    estilo_normal,
                )
            ]
        ],
        colWidths=[doc.width],
    )

    tabla_est.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    elementos.append(tabla_est)
    elementos.append(Spacer(1, 12))

    elementos.append(
        Paragraph(
            "Lee con atención los siguientes textos y responde las preguntas",
            estilo_negrita,
        )
    )

    elementos.append(Spacer(1, 18))

    # PASAR A COLUMNA IZQUIERDA
    elementos.append(FrameBreak())

    # ==============================
    # CONTENIDO
    # ==============================
    contador = 1

    for id_contexto, grupo in preguntas_df.groupby("id_contexto"):

        contexto = grupo.iloc[0]["contexto"]

        elementos.append(Paragraph(f"TEXTO {id_contexto}", estilo_titulo))
        elementos.append(Spacer(1, 6))
        elementos.append(Paragraph(contexto, estilo_normal))
        elementos.append(Spacer(1, 6))

        inicio = contador
        fin = contador + len(grupo) - 1

        elementos.append(
            Paragraph(
                f"<b>RESPONDE LAS PREGUNTAS {inicio} A {fin} SEGÚN EL TEXTO {id_contexto}.</b>",
                estilo_negrita,
            )
        )
        elementos.append(Spacer(1, 6))

        for _, row in grupo.iterrows():

            bloque = []

            bloque.append(
                Paragraph(
                    f"<b>{contador}. {row['enunciado']}</b>",
                    estilo_negrita,
                )
            )

            bloque.append(Paragraph(f"A. {row['opcion_a']}", estilo_normal))
            bloque.append(Paragraph(f"B. {row['opcion_b']}", estilo_normal))
            bloque.append(Paragraph(f"C. {row['opcion_c']}", estilo_normal))
            bloque.append(Paragraph(f"D. {row['opcion_d']}", estilo_normal))

            bloque.append(Spacer(1, 12))

            elementos.append(KeepTogether(bloque))

            contador += 1

    # ==============================
    # PIE DE PÁGINA CON TOTAL REAL
    # ==============================
    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_number(total_pages)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

        def draw_page_number(self, total_pages):
            self.setFont("Arial", 9)
            self.drawString(
                1.5 * cm,
                1 * cm,
                f"Nombre: {estudiante['nombre']}   Evaluación: {evaluacion}   Página {self._pageNumber} de {total_pages}",
            )

    doc.build(elementos, canvasmaker=NumberedCanvas)