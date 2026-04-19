from __future__ import annotations

from datetime import datetime
from io import BytesIO

import pandas as pd

from . import get_connection
from . import examenes as core_examenes
from . import preguntas as core_preguntas


def _normalizar_grado(grado):
    valor = str(grado or "").strip()
    if not valor:
        return None
    if valor.endswith(".0") and valor[:-2].isdigit():
        valor = valor[:-2]
    return valor


def _normalizar_curso(curso):
    valor = str(curso or "").strip().upper()
    return valor or None


def _duracion_texto(hora_inicio, hora_fin):
    try:
        if not hora_inicio or not hora_fin:
            return ""
        inicio = datetime.strptime(str(hora_inicio), "%Y-%m-%d %H:%M:%S")
        fin = datetime.strptime(str(hora_fin), "%Y-%m-%d %H:%M:%S")
        total = max(0, int((fin - inicio).total_seconds()))
        horas = total // 3600
        minutos = (total % 3600) // 60
        segundos = total % 60
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    except Exception:
        return ""


def listar_panel_docente(grado=None, curso=None, area=None, evaluacion=None):
    grado_norm = _normalizar_grado(grado)
    curso_norm = _normalizar_curso(curso)
    area_norm = str(area or "").strip() or None
    evaluacion_norm = str(evaluacion or "").strip() or None

    query_est = [
        """
        SELECT documento, nombre, grado, curso
        FROM estudiantes
        WHERE LOWER(TRIM(COALESCE(estado, 'Activo'))) = 'activo'
        """
    ]
    params_est = []
    if grado_norm:
        query_est.append(" AND TRIM(CAST(grado AS TEXT)) = TRIM(CAST(? AS TEXT))")
        params_est.append(grado_norm)
    if curso_norm:
        query_est.append(" AND UPPER(TRIM(CAST(curso AS TEXT))) = ?")
        params_est.append(curso_norm)
    query_est.append(" ORDER BY grado, curso, nombre")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("".join(query_est), params_est)
        estudiantes = cur.fetchall()

        rows = []
        for documento, nombre, grado_row, curso_row in estudiantes:
            query_res = [
                """
                SELECT id, area, evaluacion, nota, estado_examen, hora_inicio,
                       hora_fin, intento, puede_revisar
                FROM resultados
                WHERE documento = ?
                  AND estado_examen IN ('FINALIZADO', 'PRESENTADO')
                """
            ]
            params_res = [documento]
            if area_norm:
                query_res.append(" AND area = ?")
                params_res.append(area_norm)
            if evaluacion_norm:
                query_res.append(" AND evaluacion = ?")
                params_res.append(evaluacion_norm)
            query_res.append(" ORDER BY id DESC LIMIT 1")

            cur.execute("".join(query_res), params_res)
            resultado = cur.fetchone()

            if resultado:
                (
                    resultado_id,
                    area_row,
                    evaluacion_row,
                    nota,
                    estado_examen,
                    hora_inicio,
                    hora_fin,
                    intento,
                    puede_revisar,
                ) = resultado
                area_out = area_row or area_norm or ""
                evaluacion_out = evaluacion_row or evaluacion_norm or ""
                nota_out = nota
                estado_out = estado_examen or ""
                fecha_out = hora_fin or hora_inicio or ""
                intento_out = intento or 1
                puede_revisar_out = int(puede_revisar or 0)
                resultado_id_out = resultado_id
            else:
                area_out = area_norm or ""
                evaluacion_out = evaluacion_norm or ""
                nota_out = None
                estado_out = "EXAMEN NO PRESENTADO"
                fecha_out = ""
                hora_inicio = ""
                hora_fin = ""
                intento_out = None
                puede_revisar_out = 0
                resultado_id_out = None

            rows.append(
                {
                    "documento": str(documento or "").strip(),
                    "nombre": str(nombre or "").strip(),
                    "grado": str(grado_row or "").strip(),
                    "curso": str(curso_row or "").strip(),
                    "area": str(area_out or "").strip(),
                    "evaluacion": str(evaluacion_out or "").strip(),
                    "nota": nota_out,
                    "estado_examen": estado_out,
                    "fecha": fecha_out,
                    "duracion": _duracion_texto(hora_inicio, hora_fin),
                    "intento": intento_out,
                    "puede_revisar": puede_revisar_out,
                    "resultado_id": resultado_id_out,
                }
            )
    return rows


def listar_cursos_por_grado(grado=None):
    grado_norm = _normalizar_grado(grado)
    query = [
        """
        SELECT DISTINCT UPPER(TRIM(CAST(curso AS TEXT))) AS curso
        FROM estudiantes
        WHERE LOWER(TRIM(COALESCE(estado, 'Activo'))) = 'activo'
          AND curso IS NOT NULL
          AND TRIM(CAST(curso AS TEXT)) <> ''
        """
    ]
    params = []
    if grado_norm:
        query.append(" AND TRIM(CAST(grado AS TEXT)) = TRIM(CAST(? AS TEXT))")
        params.append(grado_norm)
    query.append(" ORDER BY curso")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("".join(query), params)
        return [str(row[0]).strip() for row in cur.fetchall() if row and row[0]]


def obtener_detalle_docente(documento, area=None, intento=None):
    return core_examenes.obtener_respuestas_estudiante(
        documento,
        area=area,
        intento=intento,
    )


def exportar_reporte_excel(grado=None, curso=None, area=None, evaluacion=None):
    rows = listar_panel_docente(
        grado=grado, curso=curso, area=area, evaluacion=evaluacion
    )
    df = pd.DataFrame(
        rows,
        columns=[
            "grado",
            "curso",
            "nombre",
            "documento",
            "area",
            "evaluacion",
            "nota",
            "estado_examen",
            "fecha",
            "duracion",
        ],
    )
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Reporte")
    buffer.seek(0)
    return buffer


def exportar_consolidado_excel(grado, area, curso=None):
    grado_norm = _normalizar_grado(grado)
    area_norm = str(area or "").strip()
    curso_norm = _normalizar_curso(curso)
    if not grado_norm or not area_norm:
        raise ValueError("grado_y_area_requeridos")

    evaluaciones = core_preguntas.cargar_evaluaciones_por_grado_y_area(
        grado_norm, area_norm
    )
    if not evaluaciones:
        raise ValueError("sin_evaluaciones")

    with get_connection() as conn:
        cur = conn.cursor()
        query = [
            """
            SELECT documento, nombre, grado, curso
            FROM estudiantes
            WHERE LOWER(TRIM(COALESCE(estado, 'Activo'))) = 'activo'
              AND TRIM(CAST(grado AS TEXT)) = TRIM(CAST(? AS TEXT))
            """
        ]
        params = [grado_norm]
        if curso_norm:
            query.append(" AND UPPER(TRIM(CAST(curso AS TEXT))) = ?")
            params.append(curso_norm)
        query.append(" ORDER BY curso, nombre")
        cur.execute("".join(query), params)
        estudiantes = cur.fetchall()

        rows = []
        for documento, nombre, grado_row, curso_row in estudiantes:
            row = {
                "grado": str(grado_row or "").strip(),
                "curso": str(curso_row or "").strip(),
                "nombre": str(nombre or "").strip(),
                "documento": str(documento or "").strip(),
                "area": area_norm,
            }
            for evaluacion_nombre in evaluaciones:
                cur.execute(
                    """
                    SELECT nota
                    FROM resultados
                    WHERE documento = ?
                      AND area = ?
                      AND evaluacion = ?
                      AND estado_examen IN ('FINALIZADO', 'PRESENTADO')
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (documento, area_norm, evaluacion_nombre),
                )
                valor = cur.fetchone()
                row[evaluacion_nombre] = (
                    valor[0] if valor and valor[0] is not None else ""
                )
            rows.append(row)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name="Consolidado")
    buffer.seek(0)
    return buffer
