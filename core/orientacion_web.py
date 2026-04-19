from __future__ import annotations

from . import get_connection
from . import docentes_web as core_docentes_web


def _norm(value):
    return str(value or "").strip()


def _norm_upper(value):
    return _norm(value).upper()


def _build_filters(grado=None, area=None, curso=None):
    filters = ["1=1"]
    params = []

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


def resumen_orientacion(grado=None, area=None, curso=None):
    where, params = _build_filters(grado=grado, area=area, curso=curso)

    estudiantes = int(
        _fetch_value(
            f"""
            SELECT COUNT(DISTINCT TRIM(CAST(COALESCE(r.documento, '') AS TEXT)))
            FROM resultados r
            WHERE {where}
              AND TRIM(CAST(COALESCE(r.documento, '') AS TEXT)) <> ''
            """,
            params,
        )
        or 0
    )
    registros = int(
        _fetch_value(f"SELECT COUNT(*) FROM resultados r WHERE {where}", params) or 0
    )
    areas = int(
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
        SELECT r.grado, r.area, COUNT(*) AS total,
               ROUND(AVG(COALESCE(r.nota, 0)), 2) AS promedio,
               ROUND(MIN(COALESCE(r.nota, 0)), 2) AS minima,
               ROUND(MAX(COALESCE(r.nota, 0)), 2) AS maxima
        FROM resultados r
        WHERE {where}
          AND UPPER(TRIM(CAST(COALESCE(r.estado_examen, '') AS TEXT))) IN ('FINALIZADO', 'PRESENTADO')
        GROUP BY r.grado, r.area
        ORDER BY promedio ASC, r.grado, r.area
        LIMIT 15
        """,
        params,
    )

    priorizadas = _fetch_rows(
        f"""
        SELECT r.documento, r.nombre, r.grado, r.curso, r.area, r.evaluacion,
               ROUND(COALESCE(r.nota, 0), 2) AS nota, r.estado_examen,
               COALESCE(r.hora_fin, r.hora_inicio, '') AS fecha
        FROM resultados r
        WHERE {where}
          AND COALESCE(r.nota, 0) > 0
          AND COALESCE(r.nota, 0) < 3
          AND UPPER(TRIM(CAST(COALESCE(r.estado_examen, '') AS TEXT))) IN ('FINALIZADO', 'PRESENTADO')
        ORDER BY COALESCE(r.nota, 0) ASC, COALESCE(r.hora_fin, r.hora_inicio, '') DESC
        LIMIT 12
        """,
        params,
    )

    cursos = (
        core_docentes_web.listar_cursos_por_grado(grado=grado) if _norm(grado) else []
    )

    return {
        "filtros": {
            "grado": _norm(grado),
            "area": _norm(area),
            "curso": _norm_upper(curso),
        },
        "catalogos": {
            "cursos": [str(item).strip() for item in cursos if str(item or "").strip()],
        },
        "metricas": {
            "estudiantes": estudiantes,
            "registros": registros,
            "areas": areas,
            "alertas": alertas,
        },
        "resumen": resumen,
        "alertas_priorizadas": priorizadas,
    }
