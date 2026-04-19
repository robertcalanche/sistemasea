from core.construir_nombre import construir_nombre
import io
import re
import unicodedata

from core import examenes_generacion as core_examenes_generacion


ANSWER_SHEET_MODE_NONE = "none"
ANSWER_SHEET_MODE_APPEND = "append"
ANSWER_SHEET_MODE_INLINE = "inline"

EXAM_FORMAT_STANDARD = "standard"
EXAM_FORMAT_MATH_ICFES = "math_icfes"
EXAM_FORMAT_LANGUAGE_ICFES = "language_icfes"


def _normalizar_texto_sin_tildes(texto):
    txt = str(texto or "").strip().lower()
    if not txt:
        return ""
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _es_area_lenguaje(area):
    area_norm = _normalizar_texto_sin_tildes(area)
    if not area_norm:
        return False

    equivalentes = {
        "lenguaje",
        "lengua castellana",
        "castellano",
        "espanol",
        "comunicacion",
        "humanidades lengua castellana",
        "lectura critica",
    }
    return area_norm in equivalentes


def _extraer_expresiones_latex(texto):
    txt = str(texto or "")
    if "$" not in txt:
        return []
    if txt.count("$") % 2 != 0:
        raise ValueError("Delimitadores '$' desbalanceados.")
    return [frag.strip() for frag in re.findall(r"\$([^$]+)\$", txt) if frag.strip()]


_SUPERSCRIPT_MAP = {
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
    "+": "⁺",
    "-": "⁻",
    "=": "⁼",
    "(": "⁽",
    ")": "⁾",
}


def _to_superscript(token):
    out = []
    for ch in str(token or ""):
        sup = _SUPERSCRIPT_MAP.get(ch)
        if sup is None:
            return f"^{token}"
        out.append(sup)
    return "".join(out)


def _formula_a_texto_legible(expr):
    txt = str(expr or "").strip()
    if not txt:
        return ""

    if txt.startswith("$") and txt.endswith("$") and len(txt) >= 2:
        txt = txt[1:-1].strip()

    txt = txt.replace("**", "^")
    txt = re.sub(r"\\frac\s*\{([^{}]+)\}\{([^{}]+)\}", r"\1/\2", txt)
    txt = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"√\1", txt)
    txt = re.sub(r"sqrt\s*\(([^()]+)\)", r"√\1", txt, flags=re.IGNORECASE)
    txt = re.sub(r"sqrt\s*([A-Za-z0-9]+)", r"√\1", txt, flags=re.IGNORECASE)
    txt = txt.replace("\\cdot", "·").replace("\\times", "x")

    txt = re.sub(r"\^\{([^{}]+)\}", lambda m: _to_superscript(m.group(1)), txt)
    txt = re.sub(r"\^([A-Za-z0-9+\-=()]+)", lambda m: _to_superscript(m.group(1)), txt)

    txt = txt.replace("{", "").replace("}", "")
    txt = txt.replace("\\", "")
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def renderizar_formula(expr, dpi=220):
    expr_txt = str(expr or "").strip()
    if not expr_txt:
        return None

    if expr_txt.startswith("$") and expr_txt.endswith("$") and len(expr_txt) >= 2:
        expr_txt = expr_txt[1:-1].strip()

    if not expr_txt:
        return None

    try:
        import importlib

        mathtext = importlib.import_module("matplotlib.mathtext")
        buf = io.BytesIO()
        mathtext.math_to_image(f"${expr_txt}$", buf, dpi=dpi, format="png")
        buf.seek(0)
        return buf, float(dpi)
    except Exception:
        return None


def normalizar_modo_hoja_respuestas(modo=None, generar=False):
    if isinstance(modo, bool):
        return ANSWER_SHEET_MODE_APPEND if modo else ANSWER_SHEET_MODE_NONE

    modo_txt = str(modo or "").strip().lower()
    if modo_txt in {
        ANSWER_SHEET_MODE_NONE,
        ANSWER_SHEET_MODE_APPEND,
        ANSWER_SHEET_MODE_INLINE,
    }:
        return modo_txt

    return ANSWER_SHEET_MODE_APPEND if generar else ANSWER_SHEET_MODE_NONE


def normalizar_formato_examen(formato=None):
    formato_txt = str(formato or "").strip().lower()
    if formato_txt in {
        EXAM_FORMAT_STANDARD,
        EXAM_FORMAT_MATH_ICFES,
        EXAM_FORMAT_LANGUAGE_ICFES,
    }:
        return formato_txt

    if formato_txt in {
        "estándar",
        "estandar",
        "estándar (actual)",
        "estandar (actual)",
    }:
        return EXAM_FORMAT_STANDARD

    if formato_txt in {
        "matemáticas (tipo icfes)",
        "matematicas (tipo icfes)",
        "matemáticas tipo icfes",
        "matematicas tipo icfes",
        "icfes",
    }:
        return EXAM_FORMAT_MATH_ICFES

    if formato_txt in {
        "lenguaje",
        "lenguaje (lectura y abierta)",
        "lenguaje (lectura + abierta)",
        "lenguaje icfes",
        "lectura y abierta",
    }:
        return EXAM_FORMAT_LANGUAGE_ICFES

    return EXAM_FORMAT_STANDARD


def write_exam_pdf(
    self,
    preguntas_df,
    estudiante,
    path,
    cantidad,
    area,
    evaluacion,
    fecha=None,
    cantidad_textos=0,
    formato_examen=EXAM_FORMAT_STANDARD,
    docente_nombre=None,
    modo_hoja_respuestas=None,
    generar_hoja_respuestas=False,
    version=None,
    exam_id=None,
):
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        PageTemplate,
        NextPageTemplate,
        Paragraph,
        Spacer,
        KeepTogether,
        CondPageBreak,
        FrameBreak,
        PageBreak,
        Image as RLImage,
        Flowable,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
    from reportlab.lib.utils import ImageReader
    import importlib
    import os
    import re

    version_label = str(version or "").strip().upper() or "A"

    modo_hoja_respuestas = normalizar_modo_hoja_respuestas(
        modo_hoja_respuestas,
        generar_hoja_respuestas,
    )
    formato_examen = normalizar_formato_examen(formato_examen)
    if "matem" in str(area or "").strip().lower():
        formato_examen = EXAM_FORMAT_MATH_ICFES
    elif _es_area_lenguaje(area):
        if formato_examen in {
            EXAM_FORMAT_STANDARD,
            EXAM_FORMAT_LANGUAGE_ICFES,
        }:
            formato_examen = EXAM_FORMAT_LANGUAGE_ICFES
    elif formato_examen == EXAM_FORMAT_LANGUAGE_ICFES:
        formato_examen = EXAM_FORMAT_STANDARD
    is_math_icfes = formato_examen == EXAM_FORMAT_MATH_ICFES
    is_language_icfes = formato_examen == EXAM_FORMAT_LANGUAGE_ICFES
    generar_hoja_adicional = modo_hoja_respuestas == ANSWER_SHEET_MODE_APPEND
    integrar_hoja_ultima_pagina = modo_hoja_respuestas == ANSWER_SHEET_MODE_INLINE
    two_col_gap = 0.3 * cm
    qr_render_size = 2.85 * cm
    omr_bubble_diameter = 0.85 * cm
    omr_target_h_gap = 2.5 * cm
    omr_target_v_gap = 1.5 * cm
    omr_corner_mark_size = 1.0 * cm
    omr_qr_min_gap = 1.5 * cm
    omr_frame_margin = 0.7 * cm

    total_preguntas_hoja = max(1, int(cantidad or len(preguntas_df) or 1))

    def _sheet_column_ranges(total_preguntas):
        total = max(1, int(total_preguntas or 1))
        if total <= 30:
            split = max(1, (total + 1) // 2)
            ranges = [(1, split)]
            if split < total:
                ranges.append((split + 1, total))
        else:
            ranges = []
            start = 1
            while start <= total and len(ranges) < 3:
                end = min(total, start + 29)
                ranges.append((start, end))
                start = end + 1
            if start <= total:
                ranges.append((start, total))

        while len(ranges) < 2:
            ranges.append((0, 0))
        if len(ranges) > 4:
            merged = ranges[:3]
            merged.append((ranges[3][0], ranges[-1][1]))
            ranges = merged
        return ranges

    def _embedded_sheet_metrics(total_preguntas):
        ranges = _sheet_column_ranges(total_preguntas)
        filas = max(
            1,
            max(
                ((r[1] - r[0] + 1) for r in ranges if r[0] > 0 and r[1] >= r[0]),
                default=1,
            ),
        )

        safety_gap = 20.0
        title_table_gap = 6.0
        title_font_size = 13
        qr_size = qr_render_size
        block_header_h = 18.0
        row_gap = 13.0
        table_tail = 10.0
        table_height = block_header_h + (filas * row_gap) + table_tail
        bottom_pad = 6.0

        required_from_content = (
            safety_gap + title_font_size + title_table_gap + table_height + bottom_pad
        )
        return {
            "safety_gap": safety_gap,
            "title_table_gap": title_table_gap,
            "title_font_size": title_font_size,
            "qr_size": qr_size,
            "table_height": table_height,
            "required_from_content": required_from_content,
        }

    def _get_last_content_y(page_state):
        if isinstance(page_state, dict):
            direct_y = page_state.get("_last_content_y", None)
            if isinstance(direct_y, (int, float)):
                return float(direct_y)

            anchor_data = page_state.get("_answer_sheet_anchor")
            if isinstance(anchor_data, dict):
                try:
                    return float(anchor_data.get("y", doc.bottomMargin))
                except Exception:
                    return float(doc.bottomMargin)
        return float(doc.bottomMargin)

    def _draw_same_qr(target_canvas, x, y, qr_size):
        """
        Dibuja código QR de ALTA RESOLUCIÓN en el canvas PDF.

        El QR se generó con:
        - box_size=10 (alta resolución)
        - error_correction=ERROR_CORRECT_H (máxima tolerancia a errores)
        - border=4 (márgenes de seguridad)
        - formato PNG (sin compresión con pérdida)

        El dibujo utiliza:
        - preserveAspectRatio=True (mantienen proporción exacta)
        - Sin interpolación para evitar distorsión
        - mask='auto' para manejar transparencia correctamente
        """
        if _qr_img_data is not None:
            try:
                _qr_img_data.seek(0)
                # Dibujar imagen PNG de QR de alta resolución SIN INTERPOLACIÓN
                target_canvas.drawImage(
                    ImageReader(_qr_img_data),
                    x,
                    y,
                    width=qr_size,
                    height=qr_size,
                    preserveAspectRatio=True,
                    mask="auto",
                )
                return
            except Exception as exc:
                # Silenciar excepción para pasar al fallback
                pass

        # Fallback sin dependencia externa: QR vectorial de ReportLab.
        # (Se usa si la generación con qrcode falla)
        if not _qr_content:
            return
        try:
            from reportlab.graphics.barcode import qr as _rl_qr
            from reportlab.graphics.shapes import Drawing
            from reportlab.graphics import renderPDF

            qr_widget = _rl_qr.QrCodeWidget(_qr_content)
            bounds = qr_widget.getBounds()
            bw = max(1.0, float(bounds[2] - bounds[0]))
            bh = max(1.0, float(bounds[3] - bounds[1]))

            drawing = Drawing(
                qr_size,
                qr_size,
                transform=[qr_size / bw, 0, 0, qr_size / bh, 0, 0],
            )
            drawing.add(qr_widget)
            renderPDF.draw(drawing, target_canvas, x, y)
        except Exception as exc:
            # Silenciar excepción silenciosa
            pass

    def _draw_sheet_table(
        target_canvas,
        left_x,
        right_x,
        top_y,
        bottom_y,
        total_preguntas,
        embedded=False,
    ):
        ranges = _sheet_column_ranges(total_preguntas)
        num_columnas = len(ranges)
        filas_por_columna = max(
            1,
            max(
                ((r[1] - r[0] + 1) for r in ranges if r[0] > 0 and r[1] >= r[0]),
                default=1,
            ),
        )

        # Márgenes y separación reforzados
        zone_w = max(1.0, right_x - left_x)
        zone_h = max(1.0, top_y - bottom_y)
        inner_left = left_x + (0.045 * zone_w)  # margen lateral mayor
        inner_right = right_x - (0.045 * zone_w)
        usable_w = max(1.0, inner_right - inner_left)
        col_gap = (0.035 * zone_w) if num_columnas > 1 else 0.0  # separación columnas
        col_width = (usable_w - ((num_columnas - 1) * col_gap)) / max(1, num_columnas)
        block_header_h = max(15.0, 0.09 * zone_h)  # header más alto
        rows_top = top_y - block_header_h
        rows_bottom = bottom_y + (0.045 * zone_h)  # margen inferior mayor
        usable_h = max(1.0, rows_top - rows_bottom)
        row_gap = max(
            omr_bubble_diameter + (0.45 * cm),
            usable_h / max(1, filas_por_columna),
            18.0,
        )
        if (row_gap * filas_por_columna) > usable_h:
            row_gap = usable_h / max(1, filas_por_columna)

        number_w = max(1.45 * cm, 0.22 * col_width)
        left_pad = 0.35 * cm
        right_pad = 0.28 * cm

        bubble_r_target = omr_bubble_diameter / 2.0
        option_font = 11
        number_font = 11 if embedded else 12
        block_font = 9 if embedded else 10

        target_canvas.setFillColor(colors.black)
        target_canvas.setFont(font_family, option_font)

        for col_idx in range(num_columnas):
            x_col = inner_left + (col_idx * (col_width + col_gap))
            r_start, r_end = ranges[col_idx]
            block_label = (
                f"{r_start}-{r_end}" if r_start > 0 and r_end >= r_start else "--"
            )

            max_right = x_col + col_width - right_pad
            opt_start_x = x_col + number_w + left_pad
            available_track = max(1.0, max_right - opt_start_x)
            # Separación horizontal reforzada
            bubble_gap = max(
                omr_target_h_gap, available_track / 3.0, 2.1 * bubble_r_target
            )
            bubble_r = min(
                bubble_r_target,
                max(4.0, (bubble_gap * 0.48)),
            )

            min_center_gap = (2.0 * bubble_r) + (0.28 * cm)
            if bubble_gap < min_center_gap:
                bubble_gap = min_center_gap
            final_track = 3.0 * bubble_gap
            if final_track > available_track:
                bubble_gap = max(1.0, available_track / 3.0)
                bubble_r = min(bubble_r, bubble_gap * 0.45)

            target_canvas.setFont(f"{font_family}-Bold", block_font)
            # Centrado vertical mejorado
            target_canvas.drawCentredString(
                x_col + (col_width / 2.0),
                top_y - (block_header_h * 0.68),
                block_label,
            )

            for row_idx in range(filas_por_columna):
                pregunta = r_start + row_idx
                if r_start <= 0 or r_end < r_start or pregunta > r_end:
                    continue

                y_row = rows_top - ((row_idx + 0.5) * row_gap)
                target_canvas.setFont(f"{font_family}-Bold", number_font)
                num_y = y_row - 3
                target_canvas.drawRightString(
                    x_col + number_w - (0.18 * cm), num_y, f"{pregunta}."
                )

                target_canvas.setFont(font_family, option_font)
                target_canvas.setLineWidth(1.35)
                for opt_idx, opt in enumerate(["A", "B", "C", "D"]):
                    cx = opt_start_x + (opt_idx * bubble_gap)
                    circle_y = y_row
                    # Centrar la letra dentro del círculo
                    target_canvas.circle(cx, circle_y, bubble_r, stroke=1, fill=0)
                    target_canvas.setFont(font_family, option_font + 1)
                    target_canvas.drawCentredString(
                        cx, circle_y - (option_font * 0.38), opt
                    )
                    target_canvas.setFont(font_family, option_font)

    def _draw_alignment_marks(target_canvas, left_x, right_x, top_y, bottom_y):
        mark = omr_corner_mark_size
        target_canvas.setFillColor(colors.black)
        target_canvas.rect(left_x, top_y - mark, mark, mark, stroke=0, fill=1)
        target_canvas.rect(right_x - mark, top_y - mark, mark, mark, stroke=0, fill=1)
        target_canvas.rect(left_x, bottom_y, mark, mark, stroke=0, fill=1)
        target_canvas.rect(right_x - mark, bottom_y, mark, mark, stroke=0, fill=1)

    def _draw_document_frame(target_canvas, page_w, page_h):
        frame_w = page_w - (2 * omr_frame_margin)
        frame_h = page_h - (2 * omr_frame_margin)
        target_canvas.setStrokeColor(colors.black)
        target_canvas.setLineWidth(1.2)
        target_canvas.rect(
            omr_frame_margin,
            omr_frame_margin,
            frame_w,
            frame_h,
            stroke=1,
            fill=0,
        )

        _draw_alignment_marks(
            target_canvas,
            omr_frame_margin,
            page_w - omr_frame_margin,
            page_h - omr_frame_margin,
            omr_frame_margin,
        )

    def _draw_embedded_answer_sheet(
        target_canvas,
        page_num,
        total_pages,
        content_end_y,
    ):
        page_w, page_h = target_canvas._pagesize
        page_left = doc.leftMargin
        page_right = page_w - doc.rightMargin
        # Hoja embebida: en formato Matemáticas ICFES usa toda el área útil (1 columna).
        if is_math_icfes:
            left_x = page_left
            right_x = page_right
        else:
            col_width = (page_w - doc.leftMargin - doc.rightMargin - two_col_gap) / 2.0
            left_x = page_left
            right_x = left_x + col_width
        metrics = _embedded_sheet_metrics(total_preguntas_hoja)

        available_bottom = doc.bottomMargin + (0.25 * cm)
        title_y = content_end_y - metrics["safety_gap"]

        qr_size = metrics["qr_size"]
        min_qr_gap_marks = 34.0
        qr_x_lim = right_x - min_qr_gap_marks - qr_size
        qr_x = min(page_right - qr_size, qr_x_lim)
        title_font_size = metrics["title_font_size"]
        qr_y = title_y - qr_size + title_font_size
        pin_text = f"PIN: {exam_id}"

        title_bottom = title_y - title_font_size
        table_top = min(
            title_bottom - metrics["title_table_gap"],
            qr_y - omr_qr_min_gap,
        )
        table_bottom = table_top - metrics["table_height"]
        bottom_y = max(available_bottom, table_bottom - 4)
        row_top = table_top

        target_canvas.saveState()
        _draw_document_frame(target_canvas, page_w, page_h)
        target_canvas.setStrokeColor(colors.HexColor("#555555"))
        target_canvas.setLineWidth(0.8)
        target_canvas.line(left_x, row_top + 3, right_x, row_top + 3)
        target_canvas.setFillColor(colors.black)
        target_canvas.setFont(f"{font_family}-Bold", title_font_size)
        target_canvas.drawString(left_x, title_y, "HOJA DE RESPUESTAS - SEA")
        _draw_same_qr(target_canvas, qr_x, qr_y, qr_size)
        target_canvas.setFont(f"{font_family}-Bold", 9)
        target_canvas.drawString(qr_x, qr_y - 10, pin_text)
        _draw_sheet_table(
            target_canvas,
            left_x,
            right_x,
            row_top,
            bottom_y,
            total_preguntas_hoja,
            embedded=True,
        )
        target_canvas.draw_footer(page_num, total_pages)
        target_canvas.restoreState()

    def _draw_append_answer_sheet_page(target_canvas, total_pages):
        page_num = total_pages
        page_w, page_h = target_canvas._pagesize
        margin_x = 1.5 * cm
        top_y = page_h - (1.3 * cm)

        target_canvas.saveState()
        _draw_document_frame(target_canvas, page_w, page_h)
        target_canvas.setFont(f"{font_family}-Bold", 14)
        target_canvas.drawCentredString(page_w / 2, top_y, "HOJA DE RESPUESTAS - SEA")

        target_canvas.setFont(font_family, 10)
        target_canvas.drawCentredString(
            page_w / 2,
            top_y - 12,
            "Sistema SEA - Sistema de Evaluación Automatizada",
        )

        estudiante_nombre = (
            str(construir_nombre(estudiante) or "").strip() or est_nombre_marca
        )
        estudiante_documento = (
            str(estudiante.get("documento", estudiante.get("id", "")) or "").strip()
            or est_doc_marca
        )
        estudiante_grado = str(estudiante.get("grado", "") or "").strip()
        estudiante_curso = str(estudiante.get("curso", "") or "").strip()

        info_y = top_y - 30
        line_gap = 11
        target_canvas.drawString(margin_x, info_y, f"Área: {area}")
        target_canvas.drawString(page_w / 2, info_y, f"Grado: {estudiante_grado}")
        target_canvas.drawString(
            margin_x, info_y - line_gap, f"Curso: {estudiante_curso}"
        )
        target_canvas.drawString(
            page_w / 2, info_y - line_gap, f"Evaluación: {evaluacion or ''}"
        )
        target_canvas.drawString(
            page_w / 2,
            info_y - (2 * line_gap),
            f"Versión: {version_label}",
        )
        target_canvas.drawString(
            margin_x,
            info_y - (3 * line_gap),
            f"Nombre del estudiante: {estudiante_nombre}",
        )
        target_canvas.drawString(
            margin_x,
            info_y - (4 * line_gap),
            f"Documento: {estudiante_documento}",
        )

        # QR en alta resolución con tamaño visual contenido.
        qr_size = qr_render_size
        qr_x = page_w - margin_x - qr_size
        qr_y = info_y - (4 * line_gap) - 2
        _draw_same_qr(target_canvas, qr_x, qr_y, qr_size)
        target_canvas.setFont(f"{font_family}-Bold", 10)
        target_canvas.drawString(qr_x, qr_y - 12, f"PIN: {exam_id}")

        inst_y = info_y - (5.5 * line_gap)
        target_canvas.setFont(f"{font_family}-Bold", 11)
        target_canvas.drawString(margin_x, inst_y, "INSTRUCCIONES")
        target_canvas.setFont(font_family, 9)
        instrucciones = [
            "1. Marque completamente el círculo correspondiente a la respuesta correcta.",
            "2. Utilice lápiz o bolígrafo negro.",
            "3. No marque más de una opción por pregunta.",
            "4. No haga marcas fuera de los círculos.",
        ]
        for idx, texto in enumerate(instrucciones, start=1):
            target_canvas.drawString(margin_x + (0.1 * cm), inst_y - (idx * 11), texto)

        table_top = min(inst_y - 66, qr_y - omr_qr_min_gap)
        bottom_y = doc.bottomMargin + (0.35 * cm)
        _draw_sheet_table(
            target_canvas,
            margin_x,
            page_w - margin_x,
            table_top,
            bottom_y,
            total_preguntas_hoja,
            embedded=False,
        )

        target_canvas.draw_footer(page_num, total_pages)
        target_canvas.restoreState()

    # Registrar Arial de forma robusta (ruta local o ruta del sistema).
    try:
        arial_candidates = [
            "arial.ttf",
            os.path.join("C:\\Windows\\Fonts", "arial.ttf"),
        ]
        arial_bold_candidates = [
            "arialbd.ttf",
            os.path.join("C:\\Windows\\Fonts", "arialbd.ttf"),
        ]

        arial_path = next((p for p in arial_candidates if os.path.exists(p)), None)
        arial_bold_path = next(
            (p for p in arial_bold_candidates if os.path.exists(p)), None
        )

        if not arial_path or not arial_bold_path:
            raise FileNotFoundError("No se encontraron archivos de Arial")

        pdfmetrics.registerFont(TTFont("Arial", arial_path))
        pdfmetrics.registerFont(TTFont("Arial-Bold", arial_bold_path))
        font_family = "Arial"
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
            append_sheet_page = generar_hoja_adicional
            content_end_y = float(doc.bottomMargin)
            if integrar_hoja_ultima_pagina and self._saved_page_states:
                content_end_y = _get_last_content_y(self._saved_page_states[-1])
                available_height = max(
                    0,
                    content_end_y - (doc.bottomMargin + (0.25 * cm)),
                )
                required_height = _embedded_sheet_metrics(total_preguntas_hoja)[
                    "required_from_content"
                ]
                inline_sheet_fits = available_height >= required_height
                append_sheet_page = not inline_sheet_fits
            else:
                inline_sheet_fits = False

            extra_pages = 1 if append_sheet_page else 0
            num_pages = len(self._saved_page_states) + extra_pages
            for page_num, state in enumerate(self._saved_page_states, start=1):
                self.__dict__.update(state)
                if (
                    integrar_hoja_ultima_pagina
                    and inline_sheet_fits
                    and page_num == len(self._saved_page_states)
                ):
                    last_content_y = _get_last_content_y(state)
                    _draw_embedded_answer_sheet(
                        self,
                        page_num,
                        num_pages,
                        last_content_y,
                    )
                else:
                    self.draw_footer(page_num, num_pages)
                Canvas.showPage(self)

            if append_sheet_page:
                _draw_append_answer_sheet_page(self, num_pages)
                Canvas.showPage(self)

            Canvas.save(self)

        def draw_footer(self, page_num, total_pages):
            self.setFont(font_family, 8)
            docente_impresion = str(docente_nombre or "").strip() or "N/D"
            footer_text = (
                f"Autor del examen: {docente_impresion} | "
                f"Generado por SEA Sistema de Evaluación Automatizada | "
                f"Página {page_num} de {total_pages}"
            )
            self.drawCentredString(self._pagesize[0] / 2, 1.0 * cm, footer_text)

    # --- Generar QR antes del header para reutilizarlo por closure ---
    import io as _io

    version_token = str(version_label or "A").strip().upper() or "A"
    exam_id = str(
        exam_id or ""
    ).strip().upper() or core_examenes_generacion.crear_codigo_examen(version_token)

    _qr_img_data = None
    _qr_content = ""
    try:
        _qrcode_lib = importlib.import_module("qrcode")

        _est_doc_qr = estudiante.get("documento", estudiante.get("id", ""))
        _est_nombre_qr = construir_nombre(estudiante)
        _est_grado_qr = estudiante.get("grado", "")
        _est_curso_qr = estudiante.get("curso", "")
        _qr_content = core_examenes_generacion.construir_contenido_qr(
            documento=_est_doc_qr,
            nombre=_est_nombre_qr,
            grado=_est_grado_qr,
            curso=_est_curso_qr,
            area=area,
            evaluacion=evaluacion or "",
            exam_id=exam_id,
        )
        # Generar QR en ALTA RESOLUCIÓN con parámetros óptimos para PDF
        _qr = _qrcode_lib.QRCode(
            version=None,
            error_correction=_qrcode_lib.constants.ERROR_CORRECT_H,
            box_size=10,  # IMPORTANTE: mínimo 8, preferible 10
            border=4,  # Mínimo 4 para márgenes seguros
        )
        _qr.add_data(_qr_content)
        _qr.make(fit=True)
        # Crear imagen PNG sin interpolación (formato nativo recomendado)
        _qr_pil = _qr.make_image(fill_color="black", back_color="white")
        _qr_buf = _io.BytesIO()
        # Guardar como PNG en memoria (no usar JPG ni otros formatos)
        _qr_pil.save(_qr_buf, format="PNG", optimize=False)
        _qr_buf.seek(0)
        _qr_img_data = _qr_buf
    except Exception:
        _qr_img_data = None
        try:
            _est_doc_qr = estudiante.get("documento", estudiante.get("id", ""))
            _est_nombre_qr = estudiante.get("nombre", "")
            _est_grado_qr = estudiante.get("grado", "")
            _est_curso_qr = estudiante.get("curso", "")
            _qr_content = core_examenes_generacion.construir_contenido_qr(
                documento=_est_doc_qr,
                nombre=_est_nombre_qr,
                grado=_est_grado_qr,
                curso=_est_curso_qr,
                area=area,
                evaluacion=evaluacion or "",
                exam_id=exam_id,
            )
        except Exception:
            _qr_content = ""

    # Marca de seguridad personalizada del estudiante.
    est_doc_marca = str(
        estudiante.get("documento", estudiante.get("id", "")) or ""
    ).strip()
    est_nombre_marca = str(construir_nombre(estudiante) or "").strip()
    if not est_nombre_marca:
        est_nombre_marca = "N/D"
    if not est_doc_marca:
        est_doc_marca = "N/D"
    marca_estudiante = (
        f"Nombre del estudiante: {est_nombre_marca} | Documento: {est_doc_marca}"
    )

    def header_callback(canvas, doc):
        canvas.saveState()
        w, h = A4
        margin = float(doc.leftMargin)
        canvas._last_content_y = h - doc.topMargin

        # datos de institución
        instit = (self._get_config_plantel("nombre_institucion") or "").upper()
        nit = self._get_config_plantel("nit") or ""
        dane = self._get_config_plantel("codigo_dane") or ""
        departamento = self._get_config_plantel("departamento") or ""
        municipio = self._get_config_plantel("municipio") or ""
        corre = self._get_config_plantel("corregimiento_localidad") or ""
        decreto = self._get_config_plantel("decreto_funcionamiento") or ""
        resolucion = self._get_config_plantel("resolucion_aprobacion") or ""
        logo_path = self._get_config_plantel("logo_path")

        # dibujar logo a la izquierda (más alto para no cabalgar sobre texto)
        logo_w = 2.45 * cm
        logo_h = 2.45 * cm
        logo_x = margin
        if logo_path and os.path.exists(logo_path):
            try:
                canvas.drawImage(
                    logo_path,
                    logo_x,
                    h - margin - logo_h + 0.55 * cm,
                    logo_w,
                    logo_h,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                pass
        y1 = h - margin - 0.1 * cm
        text_x = logo_x + logo_w + 0.05 * cm
        titulo_y = y1 + 8
        info_y = y1 - 9
        canvas.setFont(f"{font_family}-Bold", 10)
        canvas.drawString(text_x, titulo_y, instit)

        canvas.setFont(font_family, 8)
        canvas.drawString(text_x, info_y, f"NIT: {nit}   DANE: {dane}")
        canvas.setFont(font_family, 7)
        canvas.drawString(
            text_x,
            info_y - 8,
            f"Resolución de Funcionamiento: {decreto}",
        )
        canvas.setFont(font_family, 7)
        canvas.drawString(
            text_x,
            info_y - 16,
            f"Resolución de aprobación: {resolucion}",
        )
        canvas.setFont(f"{font_family}-Bold", 11)
        canvas.drawRightString(w - margin, y1, f"VERSION {version_label}")
        # Fila 4: Corregimiento, Municipio y Departamento
        canvas.setFont(font_family, 8)
        canvas.drawString(
            text_x,
            info_y - 24,
            f"Corregimiento: {corre} Municipio: {municipio} Departamento: {departamento}",
        )
        canvas.line(text_x, y1 - 38, w - margin, y1 - 38)

        # líneas del estudiante justo debajo (centradas para evitar que se oculten bajo el logo)
        est_name = construir_nombre(estudiante)
        est_doc = estudiante.get("documento", estudiante.get("id", ""))
        est_grado = estudiante.get("grado", "")
        est_curso = estudiante.get("curso", "")

        extra_gap_docente = 10 if formato_examen == EXAM_FORMAT_STANDARD else 0
        if formato_examen == EXAM_FORMAT_MATH_ICFES:
            extra_gap_docente = 6
        y2 = y1 - 58 - extra_gap_docente
        canvas.setFont(font_family, 10)
        fecha_txt = str(fecha or "").strip() or "________"
        docente_txt = str(docente_nombre or "").strip() or "________"
        # Fila 1: Docente y Área (valor del área en negrita y mayúsculas)
        _prefix_area = f"Docente: {docente_txt}   Área: "
        _area_upper = area.upper()
        docente_x = margin
        canvas.setFont(font_family, 10)
        canvas.drawString(docente_x, y2, _prefix_area)
        _prefix_area_w = canvas.stringWidth(_prefix_area, font_family, 10)
        canvas.setFont(f"{font_family}-Bold", 10)
        canvas.drawString(docente_x + _prefix_area_w, y2, _area_upper)
        canvas.setFont(font_family, 10)
        # Fila 2: Estudiante (nombre en negrita), Grado, Curso, Fecha, Nota
        _label_est = "Estudiante: "
        _rest_est = (
            f"   Grado: {est_grado}  - {est_curso}   Fecha: {fecha_txt}   Nota:_____"
        )
        student_x = margin
        canvas.setFont(font_family, 10)
        canvas.drawString(student_x, y2 - 11, _label_est)
        _label_w = canvas.stringWidth(_label_est, font_family, 10)
        canvas.setFont(f"{font_family}-Bold", 10)
        canvas.drawString(student_x + _label_w, y2 - 11, est_name)
        _name_w = canvas.stringWidth(est_name, f"{font_family}-Bold", 10)
        canvas.setFont(font_family, 10)
        canvas.drawString(student_x + _label_w + _name_w, y2 - 11, _rest_est)

        # QR en esquina superior derecha del encabezado con tamaño visual contenido.
        qr_size = qr_render_size
        if formato_examen == EXAM_FORMAT_MATH_ICFES:
            qr_size = qr_render_size * 0.95
        qr_x = w - margin - qr_size
        qr_y = h - margin - qr_size + 20
        _draw_same_qr(canvas, qr_x, qr_y, qr_size)
        canvas.setFont(font_family, 8)
        canvas.drawCentredString(
            qr_x + (qr_size / 2), qr_y - 6, f"ID Examen: {exam_id}"
        )

        # Marca vertical del sistema en margen derecho, fuera del contenido.
        marca_sistema = (
            "Software y Soporte Tecnológico: Robert Calanche Villa | "
            "SEA | Versión 1.0 | 2026"
        )
        canvas.saveState()
        canvas.setFillColor(colors.Color(0.25, 0.25, 0.25))
        canvas.setFont(font_family, 8)
        canvas.translate(w - 0.45 * cm, h / 2)
        canvas.rotate(90)
        canvas.drawCentredString(0, 0, marca_sistema)
        canvas.restoreState()

        # Marca de seguridad del estudiante en margen izquierdo.
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.setFont(font_family, 8)
        canvas.translate(0.6 * cm, h / 2)
        canvas.rotate(90)
        canvas.drawCentredString(0, 0, marca_estudiante)
        canvas.restoreState()

        canvas.restoreState()

    # Márgenes formato estrecho para maximizar espacio de contenido
    header_height = 2.5 * cm
    math_margin_top = 110.0
    math_margin_bottom = 60.0
    _side_margin = 1.0 * cm
    _bottom_margin = 0.9 * cm
    _top_margin = 3.2 * cm

    doc = BaseDocTemplate(
        path,
        pagesize=A4,
        leftMargin=_side_margin,
        rightMargin=_side_margin,
        topMargin=_top_margin,
        bottomMargin=_bottom_margin,
        canvasmaker=NumberedCanvas,
    )

    width, height = A4

    class TrackingFrame(Frame):
        def _track_y(self, canv, added):
            if not added:
                return
            try:
                y_actual = float(getattr(self, "_y", 0) or 0)
                y_prev = getattr(canv, "_last_content_y", None)
                if y_prev is None:
                    canv._last_content_y = y_actual
                else:
                    canv._last_content_y = min(float(y_prev), y_actual)
            except Exception:
                pass

        def _add(self, flowable, canv, trySplit=0):
            added = Frame._add(self, flowable, canv, trySplit=trySplit)
            self._track_y(canv, added)
            return added

        def add(self, flowable, canv, trySplit=0):
            added = Frame.add(self, flowable, canv, trySplit=trySplit)
            self._track_y(canv, added)
            return added

    # Layout del contenido:
    # - Matemáticas ICFES: una columna.
    # - Lenguaje ICFES: texto (una columna) + preguntas (dos columnas).
    # - Estándar: dos columnas.
    gap = 0.3 * cm
    intro_frame_height = 0.95 * cm
    intro_frame_gap = 0.0 * cm
    if is_math_icfes:
        col_width = doc.width
        frame_main = TrackingFrame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
            id="col1",
        )
        template = PageTemplate(
            id="OneCol", frames=[frame_main], onPage=header_callback
        )
        doc.addPageTemplates([template])
    elif is_language_icfes:
        _lang_col_gap = 20  # pts separación central entre columnas
        _lang_col_w = (doc.width - _lang_col_gap) / 2
        _lang_col_height = max(1.0, doc.height - intro_frame_height - intro_frame_gap)
        frame_lang_intro = TrackingFrame(
            doc.leftMargin,
            doc.bottomMargin + _lang_col_height + intro_frame_gap,
            doc.width,
            intro_frame_height,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
            id="lang_intro",
        )
        frame_lang_left = TrackingFrame(
            doc.leftMargin,
            doc.bottomMargin,
            _lang_col_w,
            _lang_col_height,
            leftPadding=0,
            rightPadding=_lang_col_gap / 2,
            id="lang_left",
        )
        frame_lang_right = TrackingFrame(
            doc.leftMargin + _lang_col_w + _lang_col_gap / 2,
            doc.bottomMargin,
            _lang_col_w,
            _lang_col_height,
            leftPadding=_lang_col_gap / 2,
            rightPadding=0,
            id="lang_right",
        )

        def _lang_header_callback(canvas, doc_obj):
            header_callback(canvas, doc_obj)
            # Separador vertical entre las dos columnas
            x_sep = doc_obj.leftMargin + _lang_col_w + _lang_col_gap / 2
            canvas.saveState()
            canvas.setStrokeColor(colors.HexColor("#aaaaaa"))
            canvas.setLineWidth(0.5)
            canvas.line(
                x_sep,
                doc_obj.bottomMargin,
                x_sep,
                doc_obj.bottomMargin + doc_obj.height,
            )
            canvas.restoreState()

        def _lang_intro_header_callback(canvas, doc_obj):
            header_callback(canvas, doc_obj)
            x_sep = doc_obj.leftMargin + _lang_col_w + _lang_col_gap / 2
            canvas.saveState()
            canvas.setStrokeColor(colors.HexColor("#aaaaaa"))
            canvas.setLineWidth(0.5)
            canvas.line(
                x_sep,
                doc_obj.bottomMargin,
                x_sep,
                doc_obj.bottomMargin + _lang_col_height,
            )
            canvas.restoreState()

        template_lang = PageTemplate(
            id="LangTwoCol",
            frames=[frame_lang_left, frame_lang_right],
            onPage=_lang_header_callback,
        )
        template_lang_intro = PageTemplate(
            id="LangTwoColIntro",
            frames=[frame_lang_intro, frame_lang_left, frame_lang_right],
            onPage=_lang_intro_header_callback,
            autoNextPageTemplate="LangTwoCol",
        )
        doc.addPageTemplates([template_lang_intro, template_lang])
    else:
        col_width = (doc.width - gap) / 2
        col_height = max(1.0, doc.height - intro_frame_height - intro_frame_gap)
        frame_intro = TrackingFrame(
            doc.leftMargin,
            doc.bottomMargin + col_height + intro_frame_gap,
            doc.width,
            intro_frame_height,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
            id="intro",
        )
        frame1 = TrackingFrame(
            doc.leftMargin,
            doc.bottomMargin,
            col_width,
            col_height,
            leftPadding=0,
            rightPadding=gap / 2,
            id="col1",
        )
        frame2 = TrackingFrame(
            doc.leftMargin + col_width + gap / 2,
            doc.bottomMargin,
            col_width,
            col_height,
            leftPadding=gap / 2,
            rightPadding=0,
            id="col2",
        )
        template = PageTemplate(
            id="TwoCol", frames=[frame1, frame2], onPage=header_callback
        )
        template_intro = PageTemplate(
            id="TwoColIntro",
            frames=[frame_intro, frame1, frame2],
            onPage=header_callback,
            autoNextPageTemplate="TwoCol",
        )
        doc.addPageTemplates([template_intro, template])

    def _track_after_flowable(_flowable):
        try:
            canv = getattr(doc, "canv", None)
            frame = getattr(doc, "frame", None)
            if canv is None or frame is None:
                return
            y_actual = float(getattr(frame, "_y", 0) or 0)
            y_prev = getattr(canv, "_last_content_y", None)
            if y_prev is None:
                canv._last_content_y = y_actual
            else:
                canv._last_content_y = min(float(y_prev), y_actual)
        except Exception:
            pass

    doc.afterFlowable = _track_after_flowable

    styles = getSampleStyleSheet()
    exam_font_size = 12 if is_math_icfes else 11
    exam_leading = 13 if is_math_icfes else 12
    style_instruction = ParagraphStyle(
        "Instruction",
        parent=styles["Normal"],
        fontName=font_family,
        fontSize=exam_font_size,
        leading=exam_leading,
        spaceAfter=0,
        alignment=TA_JUSTIFY,
    )
    style_bold = ParagraphStyle(
        "Bold",
        parent=styles["Normal"],
        fontName=f"{font_family}-Bold",
        fontSize=exam_font_size,
        leading=exam_leading,
        spaceAfter=0,
        alignment=TA_JUSTIFY,
    )
    style_normal = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontName=font_family,
        fontSize=exam_font_size,
        leading=exam_leading,
        spaceAfter=0,
        alignment=TA_JUSTIFY,
    )
    style_option = ParagraphStyle(
        "Option",
        parent=styles["Normal"],
        fontName=font_family,
        fontSize=exam_font_size,
        leading=max(exam_font_size + 0.5, exam_leading - 1),
        spaceAfter=0,
        leftIndent=0.2 * cm,
        alignment=TA_LEFT,
    )
    style_option_math = ParagraphStyle(
        "OptionMath",
        parent=style_option,
        leftIndent=0.15 * cm,
        spaceAfter=0,
    )
    style_responde = ParagraphStyle(
        "Responde",
        parent=styles["Normal"],
        fontName=font_family,
        fontSize=exam_font_size,
        leading=exam_leading,
        spaceAfter=0,
        alignment=TA_JUSTIFY,
    )
    style_formula_center = ParagraphStyle(
        "FormulaCenter",
        parent=styles["Normal"],
        fontName=font_family,
        fontSize=exam_font_size,
        leading=exam_leading,
        spaceAfter=0,
        alignment=TA_CENTER,
    )

    flowables = []

    class AnswerSheetAnchorFlowable(Flowable):
        def wrap(self, availWidth, availHeight):
            return (0, 0)

        def draw(self):
            return

        def drawOn(self, canv, x, y, _sW=0):
            canv._answer_sheet_anchor = {
                "page": canv.getPageNumber(),
                "x": x,
                "y": y,
            }
            Flowable.drawOn(self, canv, x, y, _sW)

    class IndivisibleBlockFlowable(Flowable):
        def __init__(self, block_flowables):
            super().__init__()
            self.block_flowables = list(block_flowables or [])
            self._wrapped_items = []

        def wrap(self, availWidth, availHeight):
            self._wrapped_items = []
            total_h = 0.0
            max_w = 0.0
            for item in self.block_flowables:
                w, h = item.wrap(availWidth, availHeight)
                h = max(0.0, float(h or 0.0))
                self._wrapped_items.append((item, float(w or 0.0), h))
                total_h += h
                max_w = max(max_w, float(w or 0.0))
            self.width = max_w
            self.height = total_h
            return availWidth, total_h

        def split(self, availWidth, availHeight):
            return []

        def draw(self):
            y_cursor = float(getattr(self, "height", 0.0) or 0.0)
            for item, _w, h in self._wrapped_items:
                y_cursor -= h
                item.drawOn(self.canv, 0, y_cursor)

    instruccion_lectura = (
        "Lea cada pregunta cuidadosamente y seleccione la respuesta correcta."
        if is_math_icfes
        else "Lee con atención los siguientes textos y responde las preguntas."
    )
    intro_top_spacing = 0.5 * cm

    # --- Depuración: imprimir valores solicitados y forma inicial ---
    try:
        print(f"[DEBUG] cantidad_textos solicitado: {cantidad_textos}")
        print(f"[DEBUG] preguntas_df filas iniciales: {len(preguntas_df)}")
    except Exception:
        pass

    # Agrupar sobre el DataFrame completo para asegurar que la selección
    # de textos (contextos) se realiza antes de truncar por cantidad de
    # preguntas. Esto evita que un .head(cantidad) previo elimine
    # contextos completos.
    preguntas_all = preguntas_df.copy()

    if "id_contexto" in preguntas_all.columns:
        grupos_all = [
            (ctx, grp) for ctx, grp in preguntas_all.groupby("id_contexto", sort=False)
        ]
        total_contextos = len(grupos_all)
        try:
            print(f"[DEBUG] contextos encontrados: {total_contextos}")
        except Exception:
            pass
        # aplicar límite de textos si se solicitó
        if cantidad_textos and cantidad_textos > 0:
            grupos_sel = grupos_all[:cantidad_textos]
        else:
            grupos_sel = grupos_all
        try:
            print(f"[DEBUG] contextos seleccionados (post-slice): {len(grupos_sel)}")
        except Exception:
            pass
        # Usar la lista de grupos seleccionados tal cual para garantizar
        # que la cantidad de textos solicitada se preserve. No recomponemos
        # un DataFrame y luego volvemos a agrupar porque ese head() puede
        # eliminar contextos completos.
        grupos = grupos_sel
        total_filas = sum(len(g) for (_, g) in grupos)
        try:
            print(f"[DEBUG] filas totales en contextos seleccionados: {total_filas}")
            print(f"[DEBUG] grupos finales a procesar (sin truncar): {len(grupos)}")
        except Exception:
            pass
    else:
        # sin contexto definido
        preguntas = preguntas_all.copy()
        if cantidad is not None and cantidad > 0 and cantidad < len(preguntas):
            preguntas = preguntas.head(cantidad).copy()
        grupos = [(None, preguntas)]

    pregunta_num = 1
    contextos_usados = {}
    contador_texto = 1
    _math_buffers = []
    _formula_fallback_notificado = False

    def _texto_valido(valor):
        if valor is None:
            return False
        texto = str(valor).strip()
        return bool(texto) and texto.lower() != "nan"

    def _append_group_image(target_block, imagen_ref):
        if not _texto_valido(imagen_ref):
            return
        img_path = (
            imagen_ref
            if os.path.isabs(imagen_ref)
            else os.path.join(self.imagenes_dir, str(imagen_ref))
        )
        if not os.path.exists(img_path):
            return
        try:
            max_w = 6 * cm
            max_h = 4 * cm
            reader = ImageReader(img_path)
            iw, ih = reader.getSize()
            if iw > 0 and ih > 0:
                scale = min(max_w / iw, max_h / ih, 1)
                img_w = iw * scale
                img_h = ih * scale
            else:
                img_w = max_w
                img_h = max_h

            target_block.append(RLImage(img_path, width=img_w, height=img_h))
        except Exception:
            pass

    def _append_text_with_math(
        target_block,
        texto,
        style,
        prefijo="",
        centrar_formula=False,
    ):
        nonlocal _formula_fallback_notificado
        txt = str(texto or "")
        if not _texto_valido(txt):
            return

        try:
            expresiones = _extraer_expresiones_latex(txt)
        except ValueError:
            expresiones = []

        def _append_formula_as_text(expr_txt, prefijo_local=""):
            texto_formula = _formula_a_texto_legible(expr_txt) or str(expr_txt or "")
            if prefijo_local:
                texto_formula = f"{prefijo_local}{texto_formula}"
            estilo = (
                style_formula_center if (centrar_formula or is_math_icfes) else style
            )
            target_block.append(Paragraph(texto_formula, estilo))

        def _append_formula(expr_txt):
            nonlocal _formula_fallback_notificado
            rendered = renderizar_formula(expr_txt, dpi=220)
            if rendered is None:
                if not _formula_fallback_notificado:
                    try:
                        print(
                            "No se pudo renderizar la fórmula. Se mostrará en formato texto."
                        )
                    except Exception:
                        pass
                    _formula_fallback_notificado = True
                return None

            buf, dpi_math = rendered
            _math_buffers.append(buf)
            try:
                iw, ih = ImageReader(buf).getSize()
                w_pt = (float(iw) * 72.0) / float(dpi_math)
                h_pt = (float(ih) * 72.0) / float(dpi_math)
                max_w = doc.width * (0.94 if is_math_icfes else 0.90)
                scale = min(1.0, (max_w / w_pt)) if w_pt > 0 else 1.0
                img = RLImage(buf, width=w_pt * scale, height=h_pt * scale)
                if centrar_formula and not is_math_icfes:
                    img.hAlign = "CENTER"
                else:
                    img.hAlign = "LEFT"
                target_block.append(img)
                return True
            except Exception:
                return None

        if not expresiones:
            contenido = f"{prefijo}{txt}" if prefijo else txt
            target_block.append(Paragraph(contenido, style))
            return

        partes = re.split(r"(\$[^$]+\$)", txt)
        prefijo_usado = False

        for parte in partes:
            if not parte:
                continue

            es_formula = (
                parte.startswith("$") and parte.endswith("$") and len(parte) >= 2
            )

            if es_formula:
                expr = parte[1:-1].strip()
                if not expr:
                    continue
                appended = _append_formula(expr)
                if appended:
                    if prefijo and not prefijo_usado:
                        target_block.insert(-1, Paragraph(prefijo.strip(), style))
                        prefijo_usado = True
                else:
                    prefijo_local = ""
                    if prefijo and not prefijo_usado:
                        prefijo_local = prefijo
                        prefijo_usado = True
                    _append_formula_as_text(expr, prefijo_local=prefijo_local)
                continue

            chunk = str(parte).strip()
            if not chunk:
                continue
            if prefijo and not prefijo_usado:
                chunk = f"{prefijo}{chunk}"
                prefijo_usado = True
            target_block.append(Paragraph(chunk, style))

        if prefijo and not prefijo_usado:
            target_block.append(Paragraph(prefijo, style))

    def _es_linea_formula_matematica(linea):
        txt_linea = str(linea or "").strip()
        if not txt_linea:
            return False
        return bool(re.fullmatch(r"\$[^$]+\$", txt_linea))

    def _separar_enunciado_formula_matematica(texto):
        txt = str(texto or "").strip()
        if not _texto_valido(txt):
            return "", ""

        try:
            expresiones = _extraer_expresiones_latex(txt)
        except ValueError:
            expresiones = []

        if expresiones:
            enunciado = re.sub(r"\$[^$]+\$", " ", txt)
            enunciado = re.sub(r"\s+", " ", enunciado).strip(" ;:,-")
            formula = " ; ".join(
                [str(e).strip() for e in expresiones if str(e).strip()]
            )
            return enunciado, formula

        return txt, ""

    def _append_formula_centrada(
        target_block,
        expr_txt,
        espacio_antes=8,
        espacio_despues=6,
    ):
        nonlocal _formula_fallback_notificado

        expr_txt = str(expr_txt or "").strip()
        if not expr_txt:
            return

        formula_block = []
        if espacio_antes and float(espacio_antes) > 0:
            formula_block.append(Spacer(1, espacio_antes))

        rendered = renderizar_formula(expr_txt, dpi=240)
        if rendered is not None:
            buf, dpi_math = rendered
            _math_buffers.append(buf)
            try:
                iw, ih = ImageReader(buf).getSize()
                w_pt = (float(iw) * 72.0) / float(dpi_math)
                h_pt = (float(ih) * 72.0) / float(dpi_math)
                max_w = doc.width * 0.65
                scale = min(1.0, (max_w / w_pt)) if w_pt > 0 else 1.0
                img = RLImage(buf, width=w_pt * scale, height=h_pt * scale)
                img.hAlign = "CENTER"
                formula_block.append(img)
            except Exception:
                rendered = None

        if rendered is None:
            if not _formula_fallback_notificado:
                try:
                    print(
                        "No se pudo renderizar la fórmula. Se mostrará en formato texto."
                    )
                except Exception:
                    pass
                _formula_fallback_notificado = True
            texto_formula = _formula_a_texto_legible(expr_txt) or expr_txt
            formula_block.append(Paragraph(texto_formula, style_formula_center))

        if espacio_despues and float(espacio_despues) > 0:
            formula_block.append(Spacer(1, espacio_despues))

        target_block.extend(formula_block)

    def _build_question_block(row, numero_pregunta):
        bloque = []
        _append_text_with_math(
            bloque,
            row.get("enunciado", ""),
            style_bold,
            prefijo=f"{numero_pregunta}. ",
            centrar_formula=False,
        )
        for i, opt_col in enumerate(["opcion_a", "opcion_b", "opcion_c", "opcion_d"]):
            opt_val = row.get(opt_col, "")
            if opt_val is not None and str(opt_val).strip() and str(opt_val) != "nan":
                letra = chr(65 + i)
                _append_text_with_math(
                    bloque,
                    str(opt_val),
                    style_option,
                    prefijo=f"{letra}. ",
                    centrar_formula=False,
                )
        bloque.append(Spacer(1, 0.4 * cm))
        return bloque

    def _build_math_question_block(
        row,
        numero_pregunta,
        incluir_contexto=False,
        contexto_texto="",
        imagen_ref="",
        responde_texto=None,
    ):
        bloque = []
        if responde_texto:
            bloque.append(Paragraph(responde_texto, style_responde))
            bloque.append(Spacer(1, 0.06 * cm))

        bloque.append(Paragraph(f"Pregunta {numero_pregunta}", style_bold))
        bloque.append(Spacer(1, 0.04 * cm))

        if incluir_contexto and _texto_valido(contexto_texto):
            _append_text_with_math(
                bloque,
                str(contexto_texto),
                style_normal,
                centrar_formula=True,
            )
            _append_group_image(bloque, imagen_ref)

        enunciado_raw = str(row.get("enunciado", "") or "")
        enunciado_txt, formula_txt = _separar_enunciado_formula_matematica(
            enunciado_raw
        )

        if _texto_valido(enunciado_txt):
            _append_text_with_math(
                bloque,
                enunciado_txt,
                style_bold,
                centrar_formula=False,
            )

        if _texto_valido(formula_txt):
            _append_formula_centrada(bloque, formula_txt)
        elif not _texto_valido(enunciado_txt):
            _append_text_with_math(
                bloque,
                enunciado_raw,
                style_bold,
                centrar_formula=False,
            )

        opciones_validas = []
        for i, opt_col in enumerate(["opcion_a", "opcion_b", "opcion_c", "opcion_d"]):
            opt_val = row.get(opt_col, "")
            if _texto_valido(opt_val):
                letra = chr(65 + i)
                opciones_validas.append((letra, str(opt_val)))

        for idx_opt, (letra, texto_opt) in enumerate(opciones_validas):
            _append_text_with_math(
                bloque,
                texto_opt,
                style_option_math,
                prefijo=f"{letra}. ",
                centrar_formula=False,
            )
            if idx_opt < (len(opciones_validas) - 1):
                bloque.append(Spacer(1, 1))

        bloque.append(Spacer(1, 10))
        return bloque

    def _normalizar_valor_contexto(valor):
        return re.sub(r"\s+", " ", str(valor or "").strip())

    def _build_math_context_block(
        texto_responde,
        contexto_texto="",
        imagen_ref="",
    ):
        bloque = []
        if _texto_valido(texto_responde):
            bloque.append(Paragraph(str(texto_responde), style_responde))
            bloque.append(Spacer(1, 4))

        if _texto_valido(contexto_texto):
            _append_text_with_math(
                bloque,
                str(contexto_texto),
                style_normal,
                centrar_formula=True,
            )

        if _texto_valido(imagen_ref):
            _append_group_image(bloque, imagen_ref)

        if bloque:
            bloque.append(Spacer(1, 6))
        return bloque

    def _calcular_alto_bloque_pregunta(bloque):
        # Altura total del bloque indivisible: título, enunciado,
        # fórmula (si existe), opciones y márgenes internos.
        return float(_estimate_block_height(bloque, doc.width) or 0.0)

    def _append_math_block_with_paging(target_flowables, bloque, state):
        if not bloque:
            return

        alto_bloque = _calcular_alto_bloque_pregunta(bloque)
        espacio_disponible = max(
            0.0,
            float(state["page_height"])
            - float(state["margin_bottom"])
            - float(state["y_actual"]),
        )

        if alto_bloque > espacio_disponible and state["blocks_on_page"] > 0:
            target_flowables.append(PageBreak())
            state["y_actual"] = float(state["margin_top"])
            state["blocks_on_page"] = 0

        target_flowables.append(IndivisibleBlockFlowable(bloque))
        alto_consumido = min(alto_bloque, float(state["content_height"]))
        state["y_actual"] += alto_consumido
        state["blocks_on_page"] += 1

    def _normalizar_tipo_pregunta(tipo_raw):
        tipo = _normalizar_texto_sin_tildes(tipo_raw)
        tipo = tipo.replace("-", "_").replace(" ", "_")
        tipo = re.sub(r"_+", "_", tipo).strip("_")

        if tipo in {
            "opcion_multiple",
            "seleccion_multiple",
            "multiple",
            "mcq",
            "choice",
        }:
            return "opcion_multiple"

        if tipo in {
            "abierta",
            "pregunta_abierta",
            "respuesta_abierta",
            "texto_libre",
            "desarrollo",
            "open",
            "essay",
        }:
            return "abierta"

        return ""

    def _inferir_tipo_pregunta_lenguaje(row):
        tipo = _normalizar_tipo_pregunta(row.get("tipo_pregunta", ""))
        opciones_ok = all(
            _texto_valido(row.get(col, ""))
            for col in ("opcion_a", "opcion_b", "opcion_c", "opcion_d")
        )

        if not tipo:
            return "opcion_multiple" if opciones_ok else "abierta"

        if tipo == "opcion_multiple" and not opciones_ok:
            return "abierta"

        return tipo

    def _lineas_respuesta_abierta(num_lineas=4):
        lineas = []
        for _ in range(max(3, int(num_lineas))):
            lineas.append(
                Paragraph(
                    "____________________________________________________________",
                    style_normal,
                )
            )
            lineas.append(Spacer(1, 0.08 * cm))
        return lineas

    def _build_language_question_block(row, numero_pregunta):
        bloque = []
        tipo_pregunta = _inferir_tipo_pregunta_lenguaje(row)

        bloque.append(Paragraph(f"Pregunta {numero_pregunta}", style_bold))
        bloque.append(Spacer(1, 0.08 * cm))

        _append_text_with_math(
            bloque,
            row.get("enunciado", ""),
            style_normal,
            centrar_formula=False,
        )
        bloque.append(Spacer(1, 0.12 * cm))

        if tipo_pregunta == "opcion_multiple":
            for i, opt_col in enumerate(
                ["opcion_a", "opcion_b", "opcion_c", "opcion_d"]
            ):
                letra = chr(65 + i)
                _append_text_with_math(
                    bloque,
                    row.get(opt_col, ""),
                    style_option,
                    prefijo=f"{letra}. ",
                    centrar_formula=False,
                )
        else:
            bloque.extend(_lineas_respuesta_abierta(num_lineas=4))

        bloque.append(Spacer(1, 0.28 * cm))
        return bloque

    def _estimate_block_height(block, avail_width):
        total_h = 0.0
        for flowable in block:
            try:
                if flowable.__class__.__name__ == "KeepTogether":
                    inner = getattr(flowable, "_content", None) or getattr(
                        flowable, "_flowables", []
                    )
                    if inner:
                        total_h += _estimate_block_height(inner, avail_width)
                        continue
                _w, h = flowable.wrap(avail_width, doc.height)
                total_h += max(0.0, float(h or 0.0))
            except Exception:
                continue
        return total_h

    def _compose_balanced_math_flowables(question_blocks, intro_height=0.0):
        if not question_blocks:
            return []
        first_page_capacity = max(1.0, float(doc.height) - float(intro_height or 0.0))
        second_page_capacity = float(doc.height)
        heights = [
            float(_estimate_block_height(bloque, doc.width) or 0.0)
            for bloque in question_blocks
        ]

        def _as_flowables(split_index=None):
            result = []
            for idx, bloque in enumerate(question_blocks):
                if split_index is not None and idx == split_index:
                    result.append(PageBreak())
                result.append(KeepTogether(bloque))
            return result

        total_height = sum(heights)
        total_blocks = len(question_blocks)

        # Solo forzamos un reparto cuando realmente es factible que todo el
        # contenido quede en dos hojas. En cualquier otro caso dejamos que
        # Platypus use el espacio real disponible y mueva bloques completos.
        if total_blocks >= 2 and total_height <= (
            first_page_capacity + second_page_capacity
        ):
            acumulado = 0.0
            candidatos = []
            for idx, block_height in enumerate(heights[:-1], start=1):
                acumulado += block_height
                restante = total_height - acumulado
                if (
                    acumulado <= first_page_capacity
                    and restante <= second_page_capacity
                ):
                    diferencia = abs((idx) - (total_blocks - idx))
                    candidatos.append((diferencia, -idx, idx))

            if candidatos:
                candidatos.sort()
                return _as_flowables(split_index=candidatos[0][2])

        return _as_flowables()

    if is_math_icfes:
        math_layout_state = {
            "page_height": float(height),
            "margin_top": float(math_margin_top),
            "margin_bottom": float(math_margin_bottom),
            "content_height": max(
                1.0,
                float(height) - float(math_margin_top) - float(math_margin_bottom),
            ),
            "y_actual": float(math_margin_top),
            "blocks_on_page": 0,
        }

        math_intro_block = [
            Spacer(1, intro_top_spacing),
            Paragraph(instruccion_lectura, style_instruction),
            Spacer(1, 6),
        ]
        _append_math_block_with_paging(flowables, math_intro_block, math_layout_state)

        if "id_contexto" in preguntas_all.columns:
            for _context_id, grupo_preg in grupos:
                if cantidad is not None and pregunta_num > cantidad:
                    break

                filas_grupo = list(grupo_preg.iterrows())
                if cantidad is not None and cantidad > 0:
                    restantes = int(cantidad) - pregunta_num + 1
                    if restantes <= 0:
                        break
                    filas_grupo = filas_grupo[:restantes]

                if not filas_grupo:
                    continue

                contexto_texto = grupo_preg.iloc[0].get("contexto", "")
                imagen_ref = grupo_preg.iloc[0].get("imagen", "")

                contexto_compartido = True
                contexto_base = _normalizar_valor_contexto(contexto_texto)
                imagen_base = _normalizar_valor_contexto(imagen_ref)
                for _idx_row, row_data in filas_grupo:
                    if (
                        _normalizar_valor_contexto(row_data.get("contexto", ""))
                        != contexto_base
                        or _normalizar_valor_contexto(row_data.get("imagen", ""))
                        != imagen_base
                    ):
                        contexto_compartido = False
                        break

                if contexto_compartido and (
                    _texto_valido(contexto_texto) or _texto_valido(imagen_ref)
                ):
                    start_num = pregunta_num
                    end_num = pregunta_num + len(filas_grupo) - 1
                    texto_responde = None
                    if len(filas_grupo) >= 2:
                        texto_responde = (
                            "RESPONDA LAS PREGUNTAS "
                            f"{start_num} A {end_num} "
                            "DE ACUERDO CON LA SIGUIENTE INFORMACIÓN"
                        )

                    bloque_contexto = _build_math_context_block(
                        texto_responde=texto_responde,
                        contexto_texto=contexto_texto,
                        imagen_ref=imagen_ref,
                    )
                    _append_math_block_with_paging(
                        flowables,
                        bloque_contexto,
                        math_layout_state,
                    )

                for idx_fila, (_row_idx, row) in enumerate(filas_grupo):
                    contexto_bloque = row.get("contexto", contexto_texto)
                    imagen_bloque = row.get("imagen", imagen_ref)

                    incluir_contexto = False
                    responde_texto = None
                    if not contexto_compartido:
                        incluir_contexto = _texto_valido(
                            contexto_bloque
                        ) or _texto_valido(imagen_bloque)
                        if incluir_contexto and idx_fila == 0 and len(filas_grupo) >= 2:
                            start_num = pregunta_num
                            end_num = pregunta_num + len(filas_grupo) - 1
                            responde_texto = (
                                "RESPONDA LAS PREGUNTAS "
                                f"{start_num} A {end_num} "
                                "DE ACUERDO CON LA SIGUIENTE INFORMACIÓN"
                            )

                    bloque = _build_math_question_block(
                        row,
                        pregunta_num,
                        incluir_contexto=incluir_contexto,
                        contexto_texto=contexto_bloque,
                        imagen_ref=imagen_bloque,
                        responde_texto=responde_texto,
                    )
                    _append_math_block_with_paging(flowables, bloque, math_layout_state)
                    pregunta_num += 1
        else:
            for _, row in grupos[0][1].iterrows():
                if cantidad is not None and pregunta_num > cantidad:
                    break

                bloque = _build_math_question_block(row, pregunta_num)
                _append_math_block_with_paging(flowables, bloque, math_layout_state)
                pregunta_num += 1
    elif is_language_icfes:
        grupos_lenguaje = grupos
        # Ancho efectivo de una columna del template de Lenguaje.
        lang_col_width = max(1.0, float(doc.width - 20.0) / 2.0)

        # Estilos para Lenguaje (11.5 pt / leading 13)
        _FS = 11.5
        _LD = 13
        style_lang_text = ParagraphStyle(
            "LangText",
            parent=style_normal,
            fontSize=_FS,
            leading=_LD,
            spaceAfter=0,
            alignment=TA_JUSTIFY,
        )
        style_lang_q = ParagraphStyle(
            "LangQ",
            parent=style_normal,
            fontSize=_FS,
            leading=_LD,
            spaceAfter=0,
        )
        style_lang_q_bold = ParagraphStyle(
            "LangQBold",
            parent=style_bold,
            fontSize=_FS,
            leading=_LD,
            spaceAfter=0,
        )
        style_lang_opt = ParagraphStyle(
            "LangOpt",
            parent=style_option,
            fontSize=_FS,
            leading=_LD,
            spaceAfter=0,
            leftIndent=0.1 * cm,
        )
        style_lang_instr_group = ParagraphStyle(
            "LangInstrGroup",
            parent=style_lang_text,
            fontName=f"{font_family}-Bold",
            fontSize=8,
            leading=9,
            spaceAfter=0,
        )

        class _HRuleLang(Flowable):
            def wrap(self, aw, ah):
                return aw, 1

            def draw(self):
                self.canv.setStrokeColor(colors.HexColor("#888888"))
                self.canv.setLineWidth(0.5)
                self.canv.line(0, 0, self._frame._width, 0)

        def _append_lang_guard_page_break(target_flowables, bloque_estimado):
            """Evita iniciar un bloque de texto incompleto al final de columna.

            Si no hay espacio suficiente para el inicio del bloque
            (TEXTO + RESPONDA + contexto), fuerza salto a la siguiente hoja.
            """
            alto_estimado = float(
                _estimate_block_height(bloque_estimado, lang_col_width) or 0.0
            )
            if alto_estimado <= 0.0:
                return

            # Limita la guardia para evitar bucles cuando el contexto es muy extenso.
            alto_guardia = min(alto_estimado, max(80.0, float(doc.height) * 0.92))
            target_flowables.append(CondPageBreak(alto_guardia))

        def _build_lang_q_block(row, numero):
            """Bloque indivisible de pregunta: selección múltiple o abierta."""
            b = []
            b.append(Paragraph(f"<b>Pregunta {numero}.</b>", style_lang_q_bold))
            b.append(Spacer(1, 3))
            enunciado = str(row.get("enunciado", "") or "")
            if _texto_valido(enunciado):
                _append_text_with_math(b, enunciado, style_lang_q)
            tipo_p = _inferir_tipo_pregunta_lenguaje(row)
            if tipo_p == "opcion_multiple":
                b.append(Spacer(1, 4))
                for i, col in enumerate(
                    ["opcion_a", "opcion_b", "opcion_c", "opcion_d"]
                ):
                    val = row.get(col, "")
                    if _texto_valido(val):
                        _append_text_with_math(
                            b,
                            str(val),
                            style_lang_opt,
                            prefijo=f"{chr(65 + i)}. ",
                        )
                        b.append(Spacer(1, 1))
            else:
                # Pregunta abierta: líneas de respuesta visual
                b.append(Spacer(1, 8))
                b.extend(_lineas_respuesta_abierta(num_lineas=4))
            b.append(Spacer(1, 10))
            return b

        # Instrucción inicial del examen
        flowables.append(Spacer(1, intro_top_spacing))
        flowables.append(Paragraph(instruccion_lectura, style_instruction))
        flowables.append(Spacer(1, 2))

        for indice_texto, (_context_id, grupo_preg) in enumerate(grupos_lenguaje):
            if cantidad is not None and pregunta_num > cantidad:
                break

            filas_grupo = list(grupo_preg.iterrows())
            if cantidad is not None and cantidad > 0:
                restantes = int(cantidad) - pregunta_num + 1
                if restantes <= 0:
                    break
                filas_grupo = filas_grupo[:restantes]

            if not filas_grupo:
                continue

            fila_cabecera = grupo_preg.iloc[0]
            contexto_texto = fila_cabecera.get("contexto", "")
            imagen_ref = fila_cabecera.get("imagen", "")

            titulo_texto = ""
            for col_titulo in (
                "titulo_texto",
                "titulo",
                "titulo_lectura",
                "nombre_texto",
            ):
                if col_titulo in grupo_preg.columns and _texto_valido(
                    fila_cabecera.get(col_titulo, "")
                ):
                    titulo_texto = str(fila_cabecera.get(col_titulo, "")).strip()
                    break
            if not titulo_texto:
                titulo_texto = f"TEXTO {indice_texto + 1}"

            start_num = pregunta_num
            end_num = pregunta_num + len(filas_grupo) - 1
            instr_grupo = (
                f"RESPONDA LAS PREGUNTAS {start_num} A {end_num} "
                "DE ACUERDO CON EL SIGUIENTE TEXTO"
            )

            titulo_para = Paragraph(f"<b>{titulo_texto}</b>", style_lang_q_bold)
            instr_para = Paragraph(instr_grupo, style_lang_instr_group)

            # Párrafos del texto de lectura (pueden dividirse entre columnas)
            text_paragraphs = []
            _append_group_image(text_paragraphs, imagen_ref)
            if _texto_valido(contexto_texto):
                partes_ctx = [
                    p.strip() for p in str(contexto_texto).split("\n") if p.strip()
                ]
                for parte_ctx in partes_ctx:
                    text_paragraphs.append(Paragraph(parte_ctx, style_lang_text))
                    text_paragraphs.append(Spacer(1, 3))
            else:
                text_paragraphs.append(
                    Paragraph("Texto de lectura no disponible.", style_lang_text)
                )

            separador_grupo = []
            if indice_texto > 0:
                separador_grupo = [Spacer(1, 6), _HRuleLang(), Spacer(1, 6)]

            bloque_estimado_texto = (
                list(separador_grupo)
                + [
                    titulo_para,
                    Spacer(1, 4),
                    instr_para,
                    Spacer(1, 6),
                ]
                + list(text_paragraphs)
            )
            _append_lang_guard_page_break(flowables, bloque_estimado_texto)

            for item_sep in separador_grupo:
                flowables.append(item_sep)

            # Título + instrucción anclados al primer párrafo del texto
            # para que nunca queden huérfanos al final de una columna
            encabezado_grupo = [
                titulo_para,
                Spacer(1, 4),
                instr_para,
                Spacer(1, 6),
            ]
            if text_paragraphs:
                flowables.append(KeepTogether(encabezado_grupo + [text_paragraphs[0]]))
                for tp in text_paragraphs[1:]:
                    flowables.append(tp)
            else:
                flowables.append(KeepTogether(encabezado_grupo))

            # Preguntas del grupo: cada una como bloque indivisible
            for _idx, row in filas_grupo:
                bloque = _build_lang_q_block(row, pregunta_num)
                flowables.append(IndivisibleBlockFlowable(bloque))
                pregunta_num += 1
    else:
        # Para exactamente 4 textos se conserva una distribución fija de 2 hojas.
        # Para más de 4 textos se usa flujo natural en columnas/páginas.
        if "id_contexto" in preguntas_all.columns:
            total_textos = len(grupos)
            usar_distribucion_fija = total_textos == 4

            if usar_distribucion_fija:
                columnas_por_hoja = {}

            for indice_texto, (context_id, grupo_preg) in enumerate(grupos):
                encabezado_texto = []
                if indice_texto == 0:
                    encabezado_texto.append(Spacer(1, intro_top_spacing))
                    encabezado_texto.append(
                        Paragraph(instruccion_lectura, style_instruction)
                    )
                    encabezado_texto.append(Spacer(1, 0.05 * cm))

                contexto_texto = grupo_preg.iloc[0].get("contexto", "")
                if _texto_valido(contexto_texto):
                    contexto_clave = str(contexto_texto).strip()
                else:
                    # fallback por grupo para conservar estabilidad si falta texto
                    contexto_clave = str(context_id).strip()

                if contexto_clave not in contextos_usados:
                    contextos_usados[contexto_clave] = contador_texto
                    contador_texto += 1

                context_label = contextos_usados[contexto_clave]
                encabezado_texto.append(Paragraph(f"TEXTO {context_label}", style_bold))

                # imagen bajo el encabezado si existe
                imagen_ref = grupo_preg.iloc[0].get("imagen", "")
                _append_group_image(encabezado_texto, imagen_ref)

                # texto de contexto
                if _texto_valido(contexto_texto):
                    _append_text_with_math(
                        encabezado_texto,
                        str(contexto_texto),
                        style_normal,
                        centrar_formula=False,
                    )

                start_num = pregunta_num
                end_num = pregunta_num + len(grupo_preg) - 1
                encabezado_texto.append(Spacer(1, 10))
                encabezado_texto.append(
                    Paragraph(
                        f"RESPONDE LAS PREGUNTAS {start_num} A {end_num} SEGÚN EL TEXTO {context_label}",
                        style_responde,
                    )
                )

                preguntas_bloque = []

                for _, row in grupo_preg.iterrows():
                    preguntas_bloque.append(_build_question_block(row, pregunta_num))
                    pregunta_num += 1

                if usar_distribucion_fija:
                    bloque_texto = list(encabezado_texto)
                    for pregunta_bloque in preguntas_bloque:
                        bloque_texto.extend(pregunta_bloque)
                    flowables.append(KeepTogether(bloque_texto))

                    hoja = indice_texto // 2
                    columna = indice_texto % 2
                    columnas_por_hoja.setdefault(hoja, set()).add(columna)

                    try:
                        col_txt = "izquierda" if columna == 0 else "derecha"
                        print(
                            f"[DEBUG] Texto {indice_texto + 1} -> hoja {hoja + 1}, columna {col_txt}"
                        )
                    except Exception:
                        pass

                    if indice_texto < total_textos - 1:
                        if columna == 0:
                            flowables.append(FrameBreak())
                        else:
                            flowables.append(PageBreak())
                else:
                    # Bloque inicial indivisible: título + contenido + instrucción.
                    # No se agrupa con la primera pregunta para evitar saltos prematuros.
                    bloque_inicial_texto = list(encabezado_texto)
                    flowables.append(KeepTogether(bloque_inicial_texto))

                    # Cada pregunta mantiene su bloque indivisible (pregunta + opciones).
                    for pregunta_bloque in preguntas_bloque:
                        flowables.append(KeepTogether(pregunta_bloque))

            if usar_distribucion_fija:
                total_hojas = (total_textos + 1) // 2
                for hoja in range(total_hojas):
                    textos_disponibles = total_textos - (hoja * 2)
                    esperadas = {0, 1} if textos_disponibles >= 2 else {0}
                    ocupadas = columnas_por_hoja.get(hoja, set())
                    if ocupadas != esperadas:
                        raise ValueError(
                            "Distribución inválida de textos en PDF: "
                            f"hoja {hoja + 1}, columnas esperadas={sorted(esperadas)}, "
                            f"columnas ocupadas={sorted(ocupadas)}"
                        )
        else:
            flowables.append(Spacer(1, intro_top_spacing))
            flowables.append(Paragraph(instruccion_lectura, style_instruction))
            for _, row in grupos[0][1].iterrows():
                if cantidad is not None and pregunta_num > cantidad:
                    break
                flowables.append(KeepTogether(_build_question_block(row, pregunta_num)))
                pregunta_num += 1

    if integrar_hoja_ultima_pagina:
        flowables.append(AnswerSheetAnchorFlowable())

    doc.build(flowables, canvasmaker=NumberedCanvas)
    return exam_id
