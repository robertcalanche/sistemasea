from __future__ import annotations

from . import get_connection
from . import docentes as core_docentes
from . import plan_estudio_web as core_plan_estudio_web


def _norm(value):
    return str(value or "").strip()


def _norm_upper(value):
    return _norm(value).upper()


def _build_filters(alias: str, grado=None, curso=None):
    conditions = ["1=1"]
    params = []

    if _norm(grado):
        conditions.append(
            f"TRIM(CAST(COALESCE({alias}.grado, '') AS TEXT)) = TRIM(CAST(COALESCE(?, '') AS TEXT))"
        )
        params.append(_norm(grado))

    if _norm(curso):
        conditions.append(
            f"UPPER(TRIM(CAST(COALESCE({alias}.curso, '') AS TEXT))) = UPPER(TRIM(CAST(COALESCE(?, '') AS TEXT)))"
        )
        params.append(_norm_upper(curso))

    return " AND ".join(conditions), params


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
        return row[0] if row else 0


def catalogos_compartidos():
    core_plan_estudio_web.catalogos_plan_estudio()
    core_docentes.asegurar_esquema_carga_academica()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT valor
            FROM (
                SELECT TRIM(CAST(grado AS TEXT)) AS valor FROM estudiantes
                UNION
                SELECT TRIM(CAST(grado AS TEXT)) AS valor FROM plan_estudio
                UNION
                SELECT TRIM(CAST(grado AS TEXT)) AS valor FROM carga_academica
            ) t
            WHERE TRIM(COALESCE(valor, '')) <> ''
            ORDER BY valor
            """
        )
        grados = [_norm(row[0]) for row in cur.fetchall() if _norm(row[0])]

        cur.execute(
            """
            SELECT DISTINCT valor
            FROM (
                SELECT UPPER(TRIM(CAST(curso AS TEXT))) AS valor FROM estudiantes
                UNION
                SELECT UPPER(TRIM(CAST(curso AS TEXT))) AS valor FROM plan_estudio
                UNION
                SELECT UPPER(TRIM(CAST(curso AS TEXT))) AS valor FROM carga_academica
            ) t
            WHERE TRIM(COALESCE(valor, '')) <> ''
            ORDER BY valor
            """
        )
        cursos = [_norm_upper(row[0]) for row in cur.fetchall() if _norm(row[0])]

    return {"grados": grados, "cursos": cursos}


def resumen_gestion_academica(grado=None, curso=None):
    core_plan_estudio_web.catalogos_plan_estudio()
    core_docentes.asegurar_esquema_carga_academica()

    where_est, params_est = _build_filters("e", grado=grado, curso=curso)
    where_plan, params_plan = _build_filters("p", grado=grado, curso=curso)
    where_carga, params_carga = _build_filters("ca", grado=grado, curso=curso)

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(f"SELECT COUNT(*) FROM estudiantes e WHERE {where_est}", params_est)
        total_estudiantes = int(cur.fetchone()[0] or 0)

        cur.execute(f"SELECT COUNT(*) FROM plan_estudio p WHERE {where_plan}", params_plan)
        total_planes = int(cur.fetchone()[0] or 0)

        cur.execute(f"SELECT COUNT(*) FROM carga_academica ca WHERE {where_carga}", params_carga)
        total_cargas = int(cur.fetchone()[0] or 0)

        cur.execute(
            f"""
            SELECT COUNT(DISTINCT TRIM(CAST(COALESCE(ca.docente_documento, '') AS TEXT)))
            FROM carga_academica ca
            WHERE {where_carga}
              AND TRIM(CAST(COALESCE(ca.docente_documento, '') AS TEXT)) <> ''
            """,
            params_carga,
        )
        total_docentes_con_carga = int(cur.fetchone()[0] or 0)

        cur.execute(
            f"""
            SELECT COUNT(DISTINCT TRIM(CAST(COALESCE(e.grado, '') AS TEXT)) || '|' || UPPER(TRIM(CAST(COALESCE(e.curso, '') AS TEXT))))
            FROM estudiantes e
            WHERE {where_est}
              AND TRIM(CAST(COALESCE(e.grado, '') AS TEXT)) <> ''
              AND TRIM(CAST(COALESCE(e.curso, '') AS TEXT)) <> ''
            """,
            params_est,
        )
        total_grupos = int(cur.fetchone()[0] or 0)

        cur.execute(
            f"""
            SELECT COUNT(DISTINCT LOWER(TRIM(CAST(COALESCE(p.area, '') AS TEXT))))
            FROM plan_estudio p
            WHERE {where_plan}
              AND TRIM(CAST(COALESCE(p.area, '') AS TEXT)) <> ''
            """,
            params_plan,
        )
        total_areas_planificadas = int(cur.fetchone()[0] or 0)

    estudiantes_sin_plan = _fetch_rows(
        f"""
        SELECT
            TRIM(CAST(COALESCE(e.grado, '') AS TEXT)) AS grado,
            UPPER(TRIM(CAST(COALESCE(e.curso, '') AS TEXT))) AS curso,
            COUNT(*) AS estudiantes
        FROM estudiantes e
        WHERE {where_est}
          AND TRIM(CAST(COALESCE(e.grado, '') AS TEXT)) <> ''
          AND TRIM(CAST(COALESCE(e.curso, '') AS TEXT)) <> ''
          AND NOT EXISTS (
              SELECT 1
              FROM plan_estudio p
              WHERE TRIM(CAST(COALESCE(p.grado, '') AS TEXT)) = TRIM(CAST(COALESCE(e.grado, '') AS TEXT))
                AND UPPER(TRIM(CAST(COALESCE(p.curso, '') AS TEXT))) = UPPER(TRIM(CAST(COALESCE(e.curso, '') AS TEXT)))
          )
        GROUP BY 1, 2
        ORDER BY estudiantes DESC, grado, curso
        LIMIT 12
        """,
        params_est,
    )
    total_estudiantes_sin_plan = int(
        _fetch_value(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT 1
                FROM estudiantes e
                WHERE {where_est}
                  AND TRIM(CAST(COALESCE(e.grado, '') AS TEXT)) <> ''
                  AND TRIM(CAST(COALESCE(e.curso, '') AS TEXT)) <> ''
                  AND NOT EXISTS (
                      SELECT 1
                      FROM plan_estudio p
                      WHERE TRIM(CAST(COALESCE(p.grado, '') AS TEXT)) = TRIM(CAST(COALESCE(e.grado, '') AS TEXT))
                        AND UPPER(TRIM(CAST(COALESCE(p.curso, '') AS TEXT))) = UPPER(TRIM(CAST(COALESCE(e.curso, '') AS TEXT)))
                  )
                GROUP BY TRIM(CAST(COALESCE(e.grado, '') AS TEXT)), UPPER(TRIM(CAST(COALESCE(e.curso, '') AS TEXT)))
            ) t
            """,
            params_est,
        )
        or 0
    )

    plan_sin_carga = _fetch_rows(
        f"""
        SELECT
            TRIM(CAST(COALESCE(p.grado, '') AS TEXT)) AS grado,
            UPPER(TRIM(CAST(COALESCE(p.curso, '') AS TEXT))) AS curso,
            TRIM(CAST(COALESCE(p.area, '') AS TEXT)) AS area,
            COUNT(*) AS registros_plan,
            COALESCE(SUM(COALESCE(p.horas, 0)), 0) AS horas
        FROM plan_estudio p
        WHERE {where_plan}
          AND TRIM(CAST(COALESCE(p.area, '') AS TEXT)) <> ''
          AND NOT EXISTS (
              SELECT 1
              FROM carga_academica ca
              WHERE TRIM(CAST(COALESCE(ca.grado, '') AS TEXT)) = TRIM(CAST(COALESCE(p.grado, '') AS TEXT))
                AND UPPER(TRIM(CAST(COALESCE(ca.curso, '') AS TEXT))) = UPPER(TRIM(CAST(COALESCE(p.curso, '') AS TEXT)))
                AND LOWER(TRIM(CAST(COALESCE(ca.area, '') AS TEXT))) = LOWER(TRIM(CAST(COALESCE(p.area, '') AS TEXT)))
          )
        GROUP BY 1, 2, 3
        ORDER BY grado, curso, area
        LIMIT 12
        """,
        params_plan,
    )
    total_plan_sin_carga = int(
        _fetch_value(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT 1
                FROM plan_estudio p
                WHERE {where_plan}
                  AND TRIM(CAST(COALESCE(p.area, '') AS TEXT)) <> ''
                  AND NOT EXISTS (
                      SELECT 1
                      FROM carga_academica ca
                      WHERE TRIM(CAST(COALESCE(ca.grado, '') AS TEXT)) = TRIM(CAST(COALESCE(p.grado, '') AS TEXT))
                        AND UPPER(TRIM(CAST(COALESCE(ca.curso, '') AS TEXT))) = UPPER(TRIM(CAST(COALESCE(p.curso, '') AS TEXT)))
                        AND LOWER(TRIM(CAST(COALESCE(ca.area, '') AS TEXT))) = LOWER(TRIM(CAST(COALESCE(p.area, '') AS TEXT)))
                  )
                GROUP BY TRIM(CAST(COALESCE(p.grado, '') AS TEXT)), UPPER(TRIM(CAST(COALESCE(p.curso, '') AS TEXT))), TRIM(CAST(COALESCE(p.area, '') AS TEXT))
            ) t
            """,
            params_plan,
        )
        or 0
    )

    carga_sin_plan = _fetch_rows(
        f"""
        SELECT
            TRIM(CAST(COALESCE(ca.grado, '') AS TEXT)) AS grado,
            UPPER(TRIM(CAST(COALESCE(ca.curso, '') AS TEXT))) AS curso,
            TRIM(CAST(COALESCE(ca.area, '') AS TEXT)) AS area,
            TRIM(CAST(COALESCE(ca.docente_documento, '') AS TEXT)) AS docente_documento,
            COALESCE(d.nombre, '') AS docente_nombre
        FROM carga_academica ca
        LEFT JOIN docentes d ON d.documento = ca.docente_documento
        WHERE {where_carga}
          AND TRIM(CAST(COALESCE(ca.area, '') AS TEXT)) <> ''
          AND NOT EXISTS (
              SELECT 1
              FROM plan_estudio p
                            WHERE TRIM(CAST(COALESCE(p.grado, '') AS TEXT)) = TRIM(CAST(COALESCE(ca.grado, '') AS TEXT))
                AND UPPER(TRIM(CAST(COALESCE(p.curso, '') AS TEXT))) = UPPER(TRIM(CAST(COALESCE(ca.curso, '') AS TEXT)))
                AND LOWER(TRIM(CAST(COALESCE(p.area, '') AS TEXT))) = LOWER(TRIM(CAST(COALESCE(ca.area, '') AS TEXT)))
          )
        ORDER BY grado, curso, area, docente_nombre
        LIMIT 12
        """,
        params_carga,
    )
    total_carga_sin_plan = int(
        _fetch_value(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT 1
                FROM carga_academica ca
                WHERE {where_carga}
                  AND TRIM(CAST(COALESCE(ca.area, '') AS TEXT)) <> ''
                  AND NOT EXISTS (
                      SELECT 1
                      FROM plan_estudio p
                      WHERE TRIM(CAST(COALESCE(p.grado, '') AS TEXT)) = TRIM(CAST(COALESCE(ca.grado, '') AS TEXT))
                        AND UPPER(TRIM(CAST(COALESCE(p.curso, '') AS TEXT))) = UPPER(TRIM(CAST(COALESCE(ca.curso, '') AS TEXT)))
                        AND LOWER(TRIM(CAST(COALESCE(p.area, '') AS TEXT))) = LOWER(TRIM(CAST(COALESCE(ca.area, '') AS TEXT)))
                  )
            ) t
            """,
            params_carga,
        )
        or 0
    )

    cargas_sin_docente = _fetch_rows(
        f"""
        SELECT
            TRIM(CAST(COALESCE(ca.grado, '') AS TEXT)) AS grado,
            UPPER(TRIM(CAST(COALESCE(ca.curso, '') AS TEXT))) AS curso,
            TRIM(CAST(COALESCE(ca.area, '') AS TEXT)) AS area,
            TRIM(CAST(COALESCE(ca.docente_documento, '') AS TEXT)) AS docente_documento
        FROM carga_academica ca
        LEFT JOIN docentes d ON d.documento = ca.docente_documento
        WHERE {where_carga}
          AND (
              TRIM(CAST(COALESCE(ca.docente_documento, '') AS TEXT)) = ''
              OR d.documento IS NULL
          )
        ORDER BY grado, curso, area
        LIMIT 12
        """,
        params_carga,
    )
    total_cargas_sin_docente = int(
        _fetch_value(
            f"""
            SELECT COUNT(*)
            FROM carga_academica ca
            LEFT JOIN docentes d ON d.documento = ca.docente_documento
            WHERE {where_carga}
              AND (
                  TRIM(CAST(COALESCE(ca.docente_documento, '') AS TEXT)) = ''
                  OR d.documento IS NULL
              )
            """,
            params_carga,
        )
        or 0
    )

    auditoria = {
        "sin_plan": {
            "titulo": "Grupos con matricula sin plan",
            "total": total_estudiantes_sin_plan,
            "items": estudiantes_sin_plan,
        },
        "plan_sin_carga": {
            "titulo": "Areas del plan sin docente asignado",
            "total": total_plan_sin_carga,
            "items": plan_sin_carga,
        },
        "carga_sin_plan": {
            "titulo": "Cargas activas fuera del plan",
            "total": total_carga_sin_plan,
            "items": carga_sin_plan,
        },
        "cargas_sin_docente": {
            "titulo": "Cargas sin docente valido",
            "total": total_cargas_sin_docente,
            "items": cargas_sin_docente,
        },
    }

    total_alertas = sum(bloque["total"] for bloque in auditoria.values())

    return {
        "filtros": {"grado": _norm(grado), "curso": _norm_upper(curso)},
        "catalogos": catalogos_compartidos(),
        "resumen": {
            "estudiantes": total_estudiantes,
            "planes": total_planes,
            "cargas": total_cargas,
            "docentes": total_docentes_con_carga,
            "grupos": total_grupos,
            "areas": total_areas_planificadas,
        },
        "auditoria": {
            "total_alertas": total_alertas,
            **auditoria,
        },
    }