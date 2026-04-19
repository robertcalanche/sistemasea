from __future__ import annotations

from io import BytesIO

import pandas as pd

from . import get_connection
from . import docentes_web as core_docentes_web
from . import examenes as core_examenes
from . import preguntas as core_preguntas


def _norm(value):
    return str(value or "").strip()


def _norm_upper(value):
    return _norm(value).upper()


def _to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)


def _build_filters(documento=None, grado=None, area=None, curso=None, evaluacion=None):
    filters = ["1=1"]
    params = []

    if _norm(documento):
        filters.append(
            "TRIM(CAST(COALESCE(r.documento, '') AS TEXT)) = TRIM(CAST(COALESCE(?, '') AS TEXT))"
        )
        params.append(_norm(documento))
    if _norm(grado):
        filters.append(
            "TRIM(CAST(COALESCE(r.grado, '') AS TEXT)) = TRIM(CAST(COALESCE(?, '') AS TEXT))"
        )
        params.append(_norm(grado))
    if _norm(area):
        filters.append(
            "LOWER(TRIM(CAST(COALESCE(r.area, '') AS TEXT))) = LOWER(TRIM(CAST(COALESCE(?, '') AS TEXT)))"
        )
        params.append(_norm(area))
    if _norm(curso):
        filters.append(
            "UPPER(TRIM(CAST(COALESCE(r.curso, '') AS TEXT))) = UPPER(TRIM(CAST(COALESCE(?, '') AS TEXT)))"
        )
        params.append(_norm_upper(curso))
    if _norm(evaluacion):
        filters.append(
            "LOWER(TRIM(CAST(COALESCE(r.evaluacion, '') AS TEXT))) = LOWER(TRIM(CAST(COALESCE(?, '') AS TEXT)))"
        )
        params.append(_norm(evaluacion))

    return " AND ".join(filters), params


def _fetch_rows(query, params=None):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params or [])
        cols = [desc[0] for desc in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetch_value(query, params=None):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params or [])
        row = cur.fetchone()
        return row[0] if row else None


def _catalogos_resultados(grado=None, area=None):
    cursos = (
        core_docentes_web.listar_cursos_por_grado(grado=grado) if _norm(grado) else []
    )
    evaluaciones = []
    if _norm(grado) and _norm(area):
        try:
            evaluaciones = core_preguntas.cargar_evaluaciones_por_grado_y_area(
                _norm(grado), _norm(area)
            )
        except Exception:
            evaluaciones = []
    return {
        "cursos": [str(item).strip() for item in cursos if str(item or "").strip()],
        "evaluaciones": [
            str(item).strip() for item in evaluaciones if str(item or "").strip()
        ],
    }


def panel_resultados(
    documento=None,
    grado=None,
    area=None,
    curso=None,
    evaluacion=None,
    limit=50,
    offset=0,
):
    limit = max(1, min(200, int(limit or 50)))
    offset = max(0, int(offset or 0))

    where, params = _build_filters(
        documento=documento,
        grado=grado,
        area=area,
        curso=curso,
        evaluacion=evaluacion,
    )

    total = int(
        _fetch_value(
            f"SELECT COUNT(*) FROM resultados r WHERE {where}",
            params,
        )
        or 0
    )

    promedio_general = _to_float(
        _fetch_value(
            f"""
            SELECT ROUND(AVG(CASE WHEN COALESCE(r.nota, 0) > 0 THEN r.nota END), 2)
            FROM resultados r
            WHERE {where}
              AND UPPER(TRIM(CAST(COALESCE(r.estado_examen, '') AS TEXT))) IN ('FINALIZADO', 'PRESENTADO')
            """,
            params,
        ),
        default=0,
    )

    areas_activas = int(
        _fetch_value(
            f"""
            SELECT COUNT(DISTINCT LOWER(TRIM(CAST(COALESCE(r.area, '') AS TEXT))))
            FROM resultados r
            WHERE {where}
              AND TRIM(CAST(COALESCE(r.area, '') AS TEXT)) <> ''
            """,
            params,
        )
        or 0
    )

    alertas = int(
        _fetch_value(
            f"""
            SELECT COUNT(*)
            FROM resultados r
            WHERE {where}
              AND COALESCE(r.nota, 0) > 0
              AND COALESCE(r.nota, 0) < 3
              AND UPPER(TRIM(CAST(COALESCE(r.estado_examen, '') AS TEXT))) IN ('FINALIZADO', 'PRESENTADO')
            """,
            params,
        )
        or 0
    )

    resumen = _fetch_rows(
        f"""
        SELECT r.grado, r.area,
               COUNT(*) AS total,
               ROUND(AVG(COALESCE(r.nota, 0)), 2) AS promedio,
               ROUND(MIN(COALESCE(r.nota, 0)), 2) AS minima,
               ROUND(MAX(COALESCE(r.nota, 0)), 2) AS maxima
        FROM resultados r
        WHERE {where}
          AND UPPER(TRIM(CAST(COALESCE(r.estado_examen, '') AS TEXT))) IN ('FINALIZADO', 'PRESENTADO')
        GROUP BY r.grado, r.area
        ORDER BY r.grado, r.area
        LIMIT 20
        """,
        params,
    )

    resultados = _fetch_rows(
        f"""
        SELECT r.documento, r.nombre, r.grado, r.curso, r.area, r.evaluacion,
               r.nota, r.estado_examen, r.hora_inicio, r.hora_fin, r.intento
        FROM resultados r
        WHERE {where}
        ORDER BY COALESCE(r.hora_fin, r.hora_inicio, '') DESC, r.id DESC
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset],
    )

    return {
        "filtros": {
            "documento": _norm(documento),
            "grado": _norm(grado),
            "area": _norm(area),
            "curso": _norm_upper(curso),
            "evaluacion": _norm(evaluacion),
        },
        "catalogos": _catalogos_resultados(grado=grado, area=area),
        "metricas": {
            "registros": total,
            "promedio_general": round(promedio_general, 2) if total else 0,
            "areas_activas": areas_activas,
            "alertas": alertas,
        },
        "resumen": resumen,
        "resultados": resultados,
        "total": total,
    }


def detalle_resultado(documento, area=None, intento=None):
    respuestas = core_examenes.obtener_respuestas_estudiante(
        documento,
        area=area,
        intento=intento,
    )
    return {"respuestas": respuestas}


def exportar_resultados_excel(
    documento=None,
    grado=None,
    area=None,
    curso=None,
    evaluacion=None,
):
    payload = panel_resultados(
        documento=documento,
        grado=grado,
        area=area,
        curso=curso,
        evaluacion=evaluacion,
        limit=500,
        offset=0,
    )
    rows = payload["resultados"]
    df = pd.DataFrame(
        rows,
        columns=[
            "documento",
            "nombre",
            "grado",
            "curso",
            "area",
            "evaluacion",
            "nota",
            "estado_examen",
            "hora_inicio",
            "hora_fin",
            "intento",
        ],
    )
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultados")
    buffer.seek(0)
    return buffer


def exportar_consolidado_excel(grado, area, curso=None):
    return core_docentes_web.exportar_consolidado_excel(
        grado=grado, area=area, curso=curso
    )
