# --- Utilidades para nombres y limpieza de campos ---
from core.construir_nombre import construir_nombre


def safe_str(v):
    if v is None:
        return ""
    return str(v).strip()


def get_nombre_estudiante(est):
    return construir_nombre(est)


import pandas as pd
import sqlite3


# --- FUNCIÓN AUXILIAR PARA OBTENER Y VALIDAR PREGUNTAS POR id_evaluacion (multi-área) ---
def obtener_preguntas_multi_area_por_id_evaluacion(
    db_path,
    evaluacion,
    grado,
    periodo,
    areas,
    preguntas_por_area,
):
    """
    Para cada área, obtiene el id_evaluacion y las preguntas asociadas.
    Valida la cantidad mínima requerida. Si alguna área no cumple, lanza ValueError.
    Devuelve: dict {area: DataFrame de preguntas}
    """
    resultado = {}
    with sqlite3.connect(db_path) as conn:
        for area in areas:
            # Paso 1: Obtener id_evaluacion
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id_evaluacion FROM banco_preguntas
                WHERE evaluacion=? AND grado=? AND area=? AND periodo=?
                AND id_evaluacion IS NOT NULL AND id_evaluacion != ''
                LIMIT 1
                """,
                (evaluacion, grado, area, periodo),
            )
            row = cur.fetchone()
            if not row or not row[0]:
                raise ValueError(
                    f"No hay preguntas registradas para el área '{area}' con los filtros dados."
                )
            id_eval = row[0]
            # Paso 2: Validar cantidad de preguntas
            cur.execute(
                "SELECT COUNT(*) FROM banco_preguntas WHERE id_evaluacion=?",
                (id_eval,),
            )
            total = cur.fetchone()[0]
            cantidad_requerida = preguntas_por_area.get(area, 0)
            if total < cantidad_requerida:
                raise ValueError(
                    f"No hay suficientes preguntas en la evaluación del área seleccionada: {area}"
                )
            # Paso 3: Obtener preguntas
            df = pd.read_sql_query(
                "SELECT * FROM banco_preguntas WHERE id_evaluacion=?",
                conn,
                params=(id_eval,),
            )
            resultado[area] = df
    return resultado


"""
Generador de cuadernillos multi-área tipo ICFES para SEA Escritorio
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Frame,
    PageTemplate,
    Table,
    TableStyle,
    Image as RLImage,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
import random


def write_multi_area_exam_pdf(
    areas_preguntas_dict,
    estudiante,
    path,
    evaluacion,
    version,
    config_numeracion,
    preguntas_por_area,
    instrucciones_generales=None,
):
    """
    Genera un cuadernillo multi-área tipo ICFES en un solo PDF.
    - areas_preguntas_dict: dict {area: DataFrame de preguntas}
    - estudiante: dict con datos del estudiante
    - path: ruta de salida del PDF
    - evaluacion: nombre de la evaluación
    - version: etiqueta de versión (A, B, C...)
    - config_numeracion: 'continua' o 'por_area'
    - preguntas_por_area: dict {area: cantidad}
    - instrucciones_generales: str opcional
    """
    # --- Configuración de estilos y documento ---
    styles = getSampleStyleSheet()
    font_family = "Helvetica"
    style_area_title = ParagraphStyle(
        "AreaTitle",
        parent=styles["Heading2"],
        fontName=font_family,
        fontSize=13,
        leading=15,
        alignment=1,
        spaceAfter=10,
    )
    style_normal = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontName=font_family,
        fontSize=10,
        leading=12,
        alignment=4,
    )
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=3 * cm,
        bottomMargin=1.5 * cm,
    )
    flowables = []

    # --- Portada ---
    portada = []
    portada.append(Paragraph(f"<b>{safe_str(evaluacion)}" + "</b>", styles["Title"]))
    portada.append(Spacer(1, 0.5 * cm))
    # Nombre completo dinámico
    portada.append(
        Paragraph(f"Estudiante: {get_nombre_estudiante(estudiante)}", style_normal)
    )
    portada.append(
        Paragraph(f"Grado: {safe_str(estudiante.get('grado'))}", style_normal)
    )
    portada.append(
        Paragraph(f"Curso: {safe_str(estudiante.get('curso'))}", style_normal)
    )
    portada.append(Paragraph(f"Versión: {safe_str(version)}", style_normal))
    if instrucciones_generales:
        portada.append(Spacer(1, 0.5 * cm))
        portada.append(Paragraph(safe_str(instrucciones_generales), style_normal))
    portada.append(PageBreak())
    flowables.extend(portada)

    # --- Secciones por área ---
    pregunta_num_global = 1
    hoja_respuestas = []
    for area, preguntas_df in areas_preguntas_dict.items():
        flowables.append(Paragraph(f"SECCIÓN: {area.upper()}", style_area_title))
        flowables.append(Spacer(1, 0.2 * cm))
        preguntas_area = preguntas_df.sample(
            n=preguntas_por_area[area], random_state=None
        ).reset_index(drop=True)
        pregunta_num_area = 1
        for idx, row in preguntas_area.iterrows():
            if config_numeracion == "continua":
                num = pregunta_num_global
            else:
                num = pregunta_num_area
            enunciado = str(row.get("enunciado", ""))
            flowables.append(Paragraph(f"<b>{num}. {enunciado}</b>", style_normal))
            opciones = [row.get(f"opcion_{x}", "") for x in ["a", "b", "c", "d"]]
            random.shuffle(opciones)
            for i, opt in enumerate(opciones):
                letra = chr(65 + i)
                flowables.append(Paragraph(f"{letra}. {opt}", style_normal))
            flowables.append(Spacer(1, 0.15 * cm))
            if config_numeracion == "continua":
                pregunta_num_global += 1
            else:
                pregunta_num_area += 1
        flowables.append(PageBreak())
    # --- Hoja de respuestas (borrador simple) ---
    total_preguntas = (
        pregunta_num_global - 1
        if config_numeracion == "continua"
        else sum(preguntas_por_area.values())
    )
    hoja_respuestas.append(Paragraph("HOJA DE RESPUESTAS", style_area_title))
    for i in range(1, total_preguntas + 1):
        hoja_respuestas.append(Paragraph(f"{i}. (A) (B) (C) (D)", style_normal))
    flowables.extend(hoja_respuestas)
    # --- Generar PDF ---
    doc.build(flowables)
