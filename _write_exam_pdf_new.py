# Nueva implementación de _write_exam_pdf
def _write_exam_pdf(self, preguntas_df, estudiante, path, cantidad, area, evaluacion):
    """Genera el PDF del examen con formato tipo pruebas ICFES.

    Especificaciones:
    - Arial 10, interlineado sencillo, justificado, mínimo espaciado
    - Márgenes 2 cm, encabezado con tabla (logo + institución + estudiante)
    - Dos columnas, preguntas agrupadas por contexto
    - Pie de página con numeración automática
    """
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Frame,
        PageTemplate,
        Table,
        TableStyle,
        Image as RLImage,
    )
    from reportlab.pdfgen.canvas import Canvas
    from core.construir_nombre import construir_nombre
    import pandas as _pd
    from datetime import datetime
    import os

    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        try:
            pdfmetrics.registerFont(TTFont("Arial", "arial.ttf"))
            font_family = "Arial"
        except Exception:
            font_family = "Helvetica"
    except Exception:
        font_family = "Helvetica"

    class NumberedCanvas(Canvas):
        def __init__(self, *args, **kwargs):
            Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            num_pages = len(self._saved_page_states)
            for i, state in enumerate(self._saved_page_states, 1):
                self.__dict__.update(state)
                self.draw_footer(i, num_pages)
                Canvas.showPage(self)
            Canvas.save(self)

        def draw_footer(self, page_num, total_pages):
            self.setFont(f"{font_family}", 9)
            self.drawCentredString(
                self._pagesize[0] / 2, 0.7 * cm, f"Página {page_num} de {total_pages}"
            )

    def header_callback(canvas, doc):
        canvas.saveState()
        w, h = A4
        margin = 2 * cm

        instit = self._get_config_plantel("nombre_institucion") or "INSTITUCIÓN"
        nit = self._get_config_plantel("nit") or ""
        dane = self._get_config_plantel("codigo_dane") or ""
        corre = self._get_config_plantel("corregimiento_localidad") or ""
        logo_path = self._get_config_plantel("logo_path")

        logo_cell = ""
        if logo_path and os.path.exists(logo_path):
            try:
                logo_cell = RLImage(logo_path, width=2.2 * cm, height=2.2 * cm)
            except Exception:
                logo_cell = ""

        instit_text = f"<b>{instit}</b><br/>NIT: {nit}   DANE: {dane}<br/>{corre}"
        header_data = [[logo_cell, instit_text]]
        header_table = Table(
            header_data, colWidths=[2.5 * cm, w - 2 * margin - 2.5 * cm]
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (0, 0), "CENTER"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONT", (1, 0), (1, 0), f"{font_family}", 8),
                    ("LINEWIDTH", (0, 0), (-1, -1), 0.5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        header_table.wrapOn(canvas, w - 2 * margin, 10 * cm)
        header_table.drawOn(canvas, margin, h - margin - 0.75 * cm)

        est_name = construir_nombre(estudiante)
        est_doc = estudiante.get("id", "")
        est_grado = estudiante.get("grado", "")

        student_data = [
            [f"Nombre: {est_name}", f"Documento: {est_doc}"],
            [
                f"Grado: {est_grado}",
                f"Área: {area}",
                f"Evaluación: {evaluacion or ''}",
                f"Fecha: _______",
            ],
        ]

        student_table = Table(student_data)
        student_table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), f"{font_family}", 8),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEWIDTH", (0, 0), (-1, -1), 0.5),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        student_table.wrapOn(canvas, w - 2 * margin, 10 * cm)
        student_table.drawOn(canvas, margin, h - margin - 1.75 * cm)

        canvas.restoreState()

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=4.2 * cm,
        bottomMargin=1.5 * cm,
        canvasmaker=NumberedCanvas,
    )

    col_width = (doc.width - 0.3 * cm) / 2
    frame1 = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        col_width,
        doc.height,
        leftPadding=0,
        rightPadding=0.15 * cm,
        id="col1",
    )
    frame2 = Frame(
        doc.leftMargin + col_width + 0.3 * cm,
        doc.bottomMargin,
        col_width,
        doc.height,
        leftPadding=0.15 * cm,
        rightPadding=0,
        id="col2",
    )

    template = PageTemplate(
        id="TwoCol", frames=[frame1, frame2], onPage=header_callback
    )
    doc.addPageTemplates([template])

    styles = getSampleStyleSheet()

    style_instruction = ParagraphStyle(
        "Instruction",
        parent=styles["Normal"],
        fontName=font_family,
        fontSize=10,
        leading=10,
        spaceAfter=4,
        alignment=4,
    )

    style_bold = ParagraphStyle(
        "Bold",
        parent=styles["Normal"],
        fontName=f"{font_family}-Bold",
        fontSize=10,
        leading=10,
        spaceAfter=2,
        alignment=4,
    )

    style_normal = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontName=font_family,
        fontSize=10,
        leading=10,
        spaceAfter=1,
        alignment=4,
    )

    style_option = ParagraphStyle(
        "Option",
        parent=styles["Normal"],
        fontName=font_family,
        fontSize=10,
        leading=10,
        spaceAfter=0,
        alignment=0,
        leftIndent=0.2 * cm,
    )

    flowables = []
    flowables.append(
        Paragraph(
            "Lee con atención los siguientes textos y responde las preguntas.",
            style_instruction,
        )
    )
    flowables.append(Spacer(1, 0.15 * cm))

    # --- FILTRADO POR id_evaluacion SI ES POSIBLE ---
    try:
        from core import preguntas as core_preguntas

        id_eval = None
        if area and estudiante.get("grado") and evaluacion:
            id_eval = core_preguntas.obtener_id_evaluacion(
                estudiante.get("grado"), area, evaluacion
            )
        if id_eval:
            preguntas_df = preguntas_df[preguntas_df["id_evaluacion"] == id_eval]
    except Exception:
        pass

    if cantidad < len(preguntas_df):
        preguntas = preguntas_df.sample(n=cantidad, random_state=None)
    else:
        preguntas = preguntas_df.copy()

    preguntas = preguntas.reset_index(drop=True)

    if "id_contexto" in preguntas.columns:
        grupos = [(ctx, grupo) for ctx, grupo in preguntas.groupby("id_contexto")]
    else:
        grupos = [(None, preguntas)]

    pregunta_num = 1
    for context_id, grupo_preg in grupos:
        if context_id and str(context_id).strip() and str(context_id) != "nan":
            flowables.append(Paragraph(f"<b>TEXTO {context_id}</b>", style_bold))

            contexto_texto = grupo_preg.iloc[0].get("contexto", "")
            if (
                contexto_texto
                and str(contexto_texto).strip()
                and str(contexto_texto) != "nan"
            ):
                flowables.append(Paragraph(str(contexto_texto), style_normal))

            imagen_ref = grupo_preg.iloc[0].get("imagen", "")
            if imagen_ref and str(imagen_ref).strip() and str(imagen_ref) != "nan":
                img_path = os.path.join(self.imagenes_dir, str(imagen_ref))
                if os.path.exists(img_path):
                    try:
                        flowables.append(Spacer(1, 0.1 * cm))
                        img = RLImage(img_path, width=3 * cm, height=2 * cm)
                        flowables.append(img)
                        flowables.append(Spacer(1, 0.1 * cm))
                    except Exception:
                        pass

            start_num = pregunta_num
            end_num = pregunta_num + len(grupo_preg) - 1
            flowables.append(
                Paragraph(
                    f"<b>RESPONDE LAS PREGUNTAS {start_num} A {end_num} SEGÚN EL TEXTO {context_id}</b>",
                    style_bold,
                )
            )
            flowables.append(Spacer(1, 0.08 * cm))

        for _, row in grupo_preg.iterrows():
            if pregunta_num > cantidad:
                break

            enunciado = str(row.get("enunciado", ""))
            flowables.append(
                Paragraph(f"<b>{pregunta_num}. {enunciado}</b>", style_bold)
            )

            for i, opt_col in enumerate(
                ["opcion_a", "opcion_b", "opcion_c", "opcion_d"]
            ):
                opt_val = row.get(opt_col, "")
                if (
                    _pd.notna(opt_val)
                    and str(opt_val).strip()
                    and str(opt_val) != "nan"
                ):
                    letra = chr(65 + i)
                    flowables.append(
                        Paragraph(f"{letra}. {str(opt_val)}", style_option)
                    )

            flowables.append(Spacer(1, 0.1 * cm))
            pregunta_num += 1

        if pregunta_num > cantidad:
            break

    doc.build(flowables)
