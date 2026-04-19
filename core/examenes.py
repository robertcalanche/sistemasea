import importlib
import json
from datetime import datetime

from . import get_connection
from .preguntas import normalizar_grado


def _admin():
    return importlib.import_module("Admin")


def registrar_inicio(
    documento, nombre, grado, area="General", evaluacion=None, curso=None
):
    hora_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    anio_lectivo = str(datetime.now().year)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT MAX(intento) FROM resultados WHERE documento = ? AND area = ?",
            (documento, area),
        )
        row = cur.fetchone()
        intento = (row[0] or 0) + 1

        cur.execute(
            """
            INSERT INTO resultados (documento, nombre, grado, area, nota, estado_examen, hora_inicio, hora_fin, intento, evaluacion, curso, anio_lectivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                documento,
                nombre,
                grado,
                area,
                None,
                "EN_PROCESO",
                hora_inicio,
                None,
                intento,
                evaluacion,
                curso,
                anio_lectivo,
            ),
        )
        intento_id = cur.lastrowid
        conn.commit()

    return intento, intento_id


def registrar_final(documento, nota, respuestas=None, area="General", intento_id=None):
    # Mantiene el flujo histórico de SEA para detalle de respuestas y consistencia.
    return _admin().registrar_final(
        documento, nota, respuestas=respuestas, area=area, intento_id=intento_id
    )


def ya_presento(documento):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT estado_examen FROM resultados
            WHERE documento = ? AND estado_examen = 'FINALIZADO'
            """,
            (documento,),
        )
        row = cur.fetchone()
    return row is not None


def obtener_estado_area(documento, area):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT estado_examen, nota, puede_revisar FROM resultados
            WHERE documento = ? AND area = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (documento, area),
        )
        row = cur.fetchone()

    if not row:
        return None

    estado_examen, nota, puede_revisar = row
    if estado_examen == "FINALIZADO" and puede_revisar == 1:
        return ("REVISION_ACTIVA", nota)
    if estado_examen == "FINALIZADO":
        return ("PRESENTADO", nota)
    return (estado_examen, nota)


def obtener_intento_area(documento, area):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, nota, estado_examen, puede_revisar, respuestas FROM resultados
            WHERE documento = ? AND area = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (documento, area),
        )
        return cur.fetchone()


def autorizar_revision(documento, area=None):
    with get_connection() as conn:
        cur = conn.cursor()
        if area:
            cur.execute(
                "SELECT id FROM resultados WHERE documento = ? AND area = ? AND estado_examen = 'FINALIZADO' ORDER BY id DESC LIMIT 1",
                (documento, area),
            )
            row = cur.fetchone()
            if row:
                cur.execute(
                    "UPDATE resultados SET puede_revisar = 1 WHERE id = ?", (row[0],)
                )
        else:
            cur.execute(
                """
                UPDATE resultados
                SET puede_revisar = 1
                WHERE documento = ? AND estado_examen = 'FINALIZADO'
                """,
                (documento,),
            )
        conn.commit()


def puede_revisar(documento):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1 FROM resultados
            WHERE documento = ?
              AND estado_examen = 'FINALIZADO'
              AND puede_revisar = 1
            ORDER BY id DESC
            LIMIT 1
            """,
            (documento,),
        )
        return cur.fetchone() is not None


def cargar_config_examen(area, grado=None, evaluacion=None, curso=None):
    try:
        area_param = str(area).strip().lower() if area is not None else None
        grado_param = normalizar_grado(grado) if grado is not None else None
        evaluacion_param = str(evaluacion).strip() if evaluacion is not None else None
        if evaluacion_param == "":
            evaluacion_param = None

        with get_connection() as conn:
            cur = conn.cursor()
            if grado_param is not None and evaluacion_param is not None:
                curso_param = str(curso).strip().upper() if curso is not None else ""
                if curso_param == "":
                    curso_param = "TODOS"
                cur.execute(
                    """
                    SELECT duracion_segundos, cantidad_preguntas, COALESCE(max_intentos, 1), COALESCE(permitir_reintentos, 1), COALESCE(habilitado, 0)
                    FROM config_examenes
                    WHERE LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
                      AND LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
                      AND LOWER(TRIM(CAST(evaluacion AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
                      AND (UPPER(TRIM(curso)) = ? OR UPPER(TRIM(curso)) = 'TODOS')
                    ORDER BY (curso = 'TODOS') ASC
                    LIMIT 1
                    """,
                    (grado_param, area_param, evaluacion_param, curso_param),
                )
                row = cur.fetchone()
                if not row:
                    cur.execute(
                        """
                        SELECT duracion_segundos, cantidad_preguntas, COALESCE(max_intentos, 1), COALESCE(permitir_reintentos, 1), COALESCE(habilitado, 0)
                        FROM config_examenes
                        WHERE LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
                          AND LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
                          AND LOWER(TRIM(CAST(evaluacion AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
                        """,
                        (grado_param, area_param, evaluacion_param),
                    )
                    row = cur.fetchone()
            elif grado_param is not None:
                cur.execute(
                    """
                    SELECT duracion_segundos, cantidad_preguntas, COALESCE(max_intentos, 1), COALESCE(permitir_reintentos, 1), COALESCE(habilitado, 0)
                    FROM config_examenes
                    WHERE LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
                      AND LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
                    """,
                    (grado_param, area_param),
                )
                row = cur.fetchone()
            else:
                cur.execute(
                    """
                    SELECT duracion_segundos, cantidad_preguntas, COALESCE(max_intentos, 1), COALESCE(permitir_reintentos, 1), COALESCE(habilitado, 0)
                    FROM config_examenes
                    WHERE LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
                    """,
                    (area_param,),
                )
                row = cur.fetchone()

        if row:
            return (row[0], row[1], row[2], row[3], row[4])
        return 120, 10, 1, 1, 0
    except Exception:
        return 120, 10, 1, 1, 0


def guardar_config_examen(
    grado,
    area,
    evaluacion,
    duracion_segundos,
    cantidad_preguntas,
    max_intentos=1,
    permitir_reintentos=1,
    habilitado=0,
    curso=None,
):
    # Se delega en Admin para respetar validaciones y migraciones históricas.
    return _admin().guardar_config_examen(
        grado,
        area,
        evaluacion,
        duracion_segundos,
        cantidad_preguntas,
        max_intentos=max_intentos,
        permitir_reintentos=permitir_reintentos,
        habilitado=habilitado,
        curso=curso,
    )


def examen_esta_activo(area):
    try:
        _, _, _, _, habilitado = cargar_config_examen(area)
        return bool(habilitado)
    except Exception:
        return False


def obtener_respuestas_estudiante(documento, area=None, intento=None):
    return _admin().obtener_respuestas_estudiante(documento, area=area, intento=intento)


def obtener_todas_respuestas_desde_bd(documento, area, intento):
    return _admin().obtener_todas_respuestas_desde_bd(documento, area, intento)


def resetear_examen(documento, area):
    return _admin().resetear_examen(documento, area)


def listar_calificaciones(
    documento=None,
    grado=None,
    area=None,
    curso=None,
    evaluacion=None,
    limit=100,
    offset=0,
):
    limit = max(1, min(500, int(limit)))
    offset = max(0, int(offset))

    with get_connection() as conn:
        filters = []
        params = []
        if documento:
            filters.append("documento = ?")
            params.append(documento)
        if grado:
            filters.append("grado = ?")
            params.append(grado)
        if area:
            filters.append("area = ?")
            params.append(area)
        if curso:
            filters.append("curso = ?")
            params.append(curso)
        if evaluacion:
            filters.append("evaluacion = ?")
            params.append(evaluacion)

        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM resultados {where}", params)
        total = int(cur.fetchone()[0])
        cur.execute(
            f"""SELECT documento, nombre, grado, curso, area, evaluacion,
                       nota, estado_examen, hora_inicio, hora_fin, intento
                  FROM resultados {where}
                 ORDER BY hora_inicio DESC
                 LIMIT ? OFFSET ?""",
            params + [limit, offset],
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    return {"total": total, "calificaciones": rows}


def listar_calificaciones_camara(
    documento=None,
    grado=None,
    area=None,
    limit=100,
    offset=0,
):
    limit = max(1, min(500, int(limit)))
    offset = max(0, int(offset))

    with get_connection() as conn:
        filters = []
        params = []
        if documento:
            filters.append("documento = ?")
            params.append(documento)
        if grado:
            filters.append("grado = ?")
            params.append(grado)
        if area:
            filters.append("area = ?")
            params.append(area)

        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(calificaciones_camara)")
        cols_tabla = {str(row[1]).strip().lower() for row in cur.fetchall()}
        if "fecha_registro" in cols_tabla:
            fecha_expr = "fecha_registro"
            order_expr = "fecha_registro DESC"
        elif "fecha" in cols_tabla:
            fecha_expr = "fecha AS fecha_registro"
            order_expr = "fecha DESC"
        else:
            fecha_expr = "'' AS fecha_registro"
            order_expr = "id DESC"

        cur.execute(f"SELECT COUNT(*) FROM calificaciones_camara {where}", params)
        total = int(cur.fetchone()[0])
        cur.execute(
            f"""SELECT id_examen, documento, estudiante_nombre, grado, curso,
                       area, evaluacion, total_preguntas, correctas, nota, {fecha_expr}
                  FROM calificaciones_camara {where}
                 ORDER BY {order_expr}
                 LIMIT ? OFFSET ?""",
            params + [limit, offset],
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    return {"total": total, "calificaciones": rows}


def resumen_calificaciones_por_grado_area():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT grado, area, COUNT(*) as total,
                      ROUND(AVG(nota), 2) as promedio,
                      ROUND(MIN(nota), 2) as minima,
                      ROUND(MAX(nota), 2) as maxima
                 FROM resultados
                WHERE estado_examen = 'FINALIZADO'
                GROUP BY grado, area
                ORDER BY grado, area"""
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    return rows


def listar_examenes_generados(limit=50, offset=0):
    limit = max(1, min(500, int(limit)))
    offset = max(0, int(offset))

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """SELECT id_examen, grupo, COUNT(*) as n_preguntas,
                      MIN(fecha_generacion) as fecha
                 FROM detalle_examen
                GROUP BY id_examen, grupo
                ORDER BY fecha DESC
                LIMIT ? OFFSET ?""",
            (limit, offset),
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    return rows
