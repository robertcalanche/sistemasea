"""
core/examenes_web.py
--------------------
Servicios de negocio para el flujo completo de presentación de examen desde la web.
Replica exactamente la lógica del escritorio (ModuloEstudiante en app.py):
  - Resolución de evaluación activa por grado/área/curso
  - Control de intentos y estado (EN_PROCESO / FINALIZADO / PRESENTADO)
  - Reanudación de examen interrumpido
  - Guardado inmediato de respuesta por pregunta (ON CONFLICT … DO UPDATE)
  - Finalización: nota, escala de valoración, registrar_final
  - Historial y detalle de intentos para revisión
"""

from __future__ import annotations

import json
from datetime import datetime

from . import get_connection
from . import examenes as core_examenes
from . import preguntas as core_preguntas
from . import usuarios as core_usuarios


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _tiene_valor(val) -> bool:
    if val is None:
        return False
    if isinstance(val, float) and val != val:
        return False
    return str(val).strip().lower() not in {"", "nan", "none"}


def _limpiar(val) -> str:
    if not _tiene_valor(val):
        return ""
    return str(val).strip()


# ---------------------------------------------------------------------------
# Resolución de evaluación habilitada (igual que _iniciar_examen en app.py)
# ---------------------------------------------------------------------------


def resolver_evaluacion_activa(grado: str, area: str, curso: str | None) -> str | None:
    """Devuelve la evaluación habilitada para grado+área+curso, o None."""
    curso_norm = str(curso or "").strip().upper() or "TODOS"
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT evaluacion FROM config_examenes "
                "WHERE LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT))) "
                "AND LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT))) "
                "AND (UPPER(TRIM(CAST(curso AS TEXT))) = ? OR UPPER(TRIM(CAST(curso AS TEXT))) = 'TODOS') "
                "AND COALESCE(habilitado, 0) = 1 "
                "ORDER BY (UPPER(TRIM(CAST(curso AS TEXT))) = 'TODOS') ASC, id DESC LIMIT 1",
                (grado, area, curso_norm),
            )
            row = cur.fetchone()
        if row and _tiene_valor(row[0]):
            return str(row[0]).strip()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Estado de áreas disponibles para el estudiante
# ---------------------------------------------------------------------------


def listar_areas_con_estado(
    documento: str, grado: str, curso: str | None
) -> list[dict]:
    """Devuelve las áreas del banco con su estado para este estudiante."""
    areas = core_preguntas.cargar_areas_por_grado(grado)
    resultado = []
    for area in areas:
        estado_info = core_examenes.obtener_estado_area(documento, area)
        evaluacion = resolver_evaluacion_activa(grado, area, curso)

        if estado_info is None:
            estado = "disponible"
            nota = None
        elif estado_info[0] == "EN_PROCESO":
            estado = "en_proceso"
            nota = None
        elif estado_info[0] in ("PRESENTADO",):
            estado = "presentado"
            nota = estado_info[1]
        elif estado_info[0] == "REVISION_ACTIVA":
            estado = "revision_activa"
            nota = estado_info[1]
        else:
            estado = "disponible"
            nota = None

        resultado.append(
            {
                "area": area,
                "evaluacion": evaluacion,
                "estado": estado,
                "nota": nota,
                "habilitado": evaluacion is not None,
            }
        )
    return resultado


# ---------------------------------------------------------------------------
# Inicio / reanudación de examen
# ---------------------------------------------------------------------------


def obtener_examen_en_proceso(documento: str, area: str) -> dict | None:
    """Retorna datos del examen EN_PROCESO si existe, o None."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT intento, id, curso, evaluacion
                   FROM resultados
                   WHERE documento = ? AND area = ? AND estado_examen = 'EN_PROCESO'
                   ORDER BY id DESC LIMIT 1""",
                (documento, area),
            )
            row = cur.fetchone()
        if not row:
            return None
        intento_num, intento_id, curso, evaluacion = row

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT MAX(pregunta_id) FROM respuestas_estudiantes "
                "WHERE documento=? AND area=? AND intento=?",
                (documento, area, intento_num),
            )
            r2 = cur.fetchone()
        max_pregunta_id = r2[0] if r2 and r2[0] is not None else 0

        return {
            "intento_num": intento_num,
            "intento_id": intento_id,
            "max_pregunta_id": max_pregunta_id,
            "curso": curso,
            "evaluacion": evaluacion,
        }
    except Exception:
        return None


def iniciar_o_reanudar_examen(
    documento: str,
    nombre: str,
    grado: str,
    area: str,
    curso: str | None,
    preflight: bool = False,
) -> dict:
    """
    Punto de entrada para el estudiante al seleccionar un área.
    Replica el flujo de _iniciar_examen() del escritorio.

    Retorna un dict con:
        ok (bool)
        error (str | None)   – mensaje de error si ok=False
        reanudacion (bool)
        intento_num, intento_id
        evaluacion, duracion, cantidad, max_intentos, permitir_reintentos
        preguntas (list[dict])  – ordenada, sin respuesta_correcta
        correctas_previas (int)  – para restaurar contador si es reanudación
        indice_inicial (int)
        respuestas_previas (dict pregunta_id → letra)
    """
    curso_norm = str(curso or "").strip() or "TODOS"

    # 1. Obtener evaluación habilitada
    evaluacion = resolver_evaluacion_activa(grado, area, curso_norm)
    if not evaluacion:
        return {
            "ok": False,
            "error": "El examen de esta área no ha sido habilitado por el docente.",
        }

    # 2. Cargar config
    duracion, cantidad, max_intentos, permitir_reintentos, habilitado = (
        core_examenes.cargar_config_examen(area, grado, evaluacion, curso_norm)
    )

    if not habilitado:
        return {
            "ok": False,
            "error": "El examen de esta área no ha sido habilitado por el docente.",
        }

    # 3. Verificar intentos previos finalizados
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM resultados "
            "WHERE documento=? AND area=? AND estado_examen IN ('FINALIZADO','PRESENTADO')",
            (documento, area),
        )
        intentos_finalizados = cur.fetchone()[0]

    estado_info = core_examenes.obtener_estado_area(documento, area)
    if estado_info and estado_info[0] in ("PRESENTADO", "REVISION_ACTIVA"):
        if not permitir_reintentos or intentos_finalizados >= max_intentos:
            return {
                "ok": False,
                "error": "Ya alcanzaste el límite de intentos para esta área.",
            }

    # 4. Verificar reanudación
    en_proceso = obtener_examen_en_proceso(documento, area)
    if preflight and not en_proceso:
        return {
            "ok": True,
            "error": None,
            "preview": True,
            "reanudacion": False,
            "intento_num": 0,
            "intento_id": 0,
            "evaluacion": evaluacion,
            "duracion": int(duracion),
            "cantidad": int(cantidad),
            "max_intentos": int(max_intentos),
            "permitir_reintentos": bool(permitir_reintentos),
            "indice_inicial": 0,
            "correctas_previas": 0,
            "respuestas_previas": {},
            "preguntas": [],
        }

    if en_proceso:
        intento_num = en_proceso["intento_num"]
        intento_id = en_proceso["intento_id"]
        curso_guardado = en_proceso["curso"] or curso_norm
        es_reanudacion = True
    else:
        intento_num, intento_id = core_examenes.registrar_inicio(
            documento, nombre, grado, area, evaluacion, curso_norm
        )
        curso_guardado = curso_norm
        es_reanudacion = False

    # 5. Cargar preguntas
    df = core_preguntas.cargar_preguntas_filtradas(
        area=area, grado=grado, evaluacion=evaluacion
    )
    if df is None or df.empty:
        return {
            "ok": False,
            "error": "No hay preguntas disponibles para esta evaluación.",
        }

    preguntas_df = df.head(int(cantidad)).reset_index(drop=True)

    # 6. Calcular índice inicial y respuestas previas
    respuestas_previas: dict[str, str] = {}
    correctas_previas = 0
    indice_inicial = 0

    if es_reanudacion:
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT pregunta_id, respuesta_seleccionada, es_correcta "
                    "FROM respuestas_estudiantes "
                    "WHERE documento=? AND area=? AND intento=?",
                    (documento, area, intento_num),
                )
                for pid, sel, corr in cur.fetchall():
                    if pid is not None:
                        respuestas_previas[str(pid)] = str(sel or "").strip().upper()
                        if corr:
                            correctas_previas += 1
        except Exception:
            pass

        max_pid = en_proceso["max_pregunta_id"]
        for idx, row in preguntas_df.iterrows():
            pid = row.get("id")
            if _tiene_valor(pid) and int(pid) <= max_pid:
                indice_inicial = idx + 1

    # 7. Serializar preguntas (ocultar respuesta_correcta)
    cols_ocultas = {"correcta", "respuesta_correcta"}
    preguntas_out = []
    for _, row in preguntas_df.iterrows():
        p: dict = {}
        for col in preguntas_df.columns:
            if col in cols_ocultas:
                continue
            val = row.get(col)
            p[col] = (
                None
                if not _tiene_valor(val)
                else (str(val).strip() if not isinstance(val, (int, float)) else val)
            )
        preguntas_out.append(p)

    return {
        "ok": True,
        "error": None,
        "reanudacion": es_reanudacion,
        "intento_num": intento_num,
        "intento_id": intento_id,
        "evaluacion": evaluacion,
        "duracion": int(duracion),
        "cantidad": int(cantidad),
        "max_intentos": int(max_intentos),
        "permitir_reintentos": bool(permitir_reintentos),
        "indice_inicial": indice_inicial,
        "correctas_previas": correctas_previas,
        "respuestas_previas": respuestas_previas,
        "preguntas": preguntas_out,
    }


# ---------------------------------------------------------------------------
# Guardar una respuesta (llamada por cada pregunta respondida)
# ---------------------------------------------------------------------------


def guardar_respuesta(
    documento: str,
    nombre: str,
    grado: str,
    curso: str,
    area: str,
    evaluacion: str,
    intento_num: int,
    pregunta_id: int,
    enunciado: str,
    seleccion: str,
) -> dict:
    """
    Persiste una respuesta individual. Usa ON CONFLICT … DO UPDATE igual que
    el escritorio para soportar reanudación.

    Retorna: {ok, es_correcta, correcta_letra}
    """
    seleccion = str(seleccion or "").strip().upper()
    if seleccion not in {"A", "B", "C", "D"}:
        return {"ok": False, "error": "Respuesta inválida"}

    # Obtener la respuesta correcta desde el banco
    correcta = ""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT correcta FROM banco_preguntas WHERE id=? LIMIT 1",
                (int(pregunta_id),),
            )
            row = cur.fetchone()
        if row and _tiene_valor(row[0]):
            correcta = str(row[0]).strip().upper()
    except Exception:
        pass

    es_correcta = 1 if seleccion == correcta and correcta else 0

    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO respuestas_estudiantes
                   (documento, nombre, grado, curso, area, evaluacion,
                    intento, pregunta_id, enunciado,
                    respuesta_seleccionada, respuesta_correcta, es_correcta)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(documento, area, intento, pregunta_id)
                   DO UPDATE SET
                       respuesta_seleccionada = EXCLUDED.respuesta_seleccionada,
                       es_correcta = EXCLUDED.es_correcta""",
                (
                    documento,
                    nombre,
                    grado,
                    curso,
                    area,
                    evaluacion,
                    intento_num,
                    int(pregunta_id),
                    enunciado,
                    seleccion,
                    correcta,
                    es_correcta,
                ),
            )
            conn.commit()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    return {"ok": True, "es_correcta": bool(es_correcta), "correcta_letra": correcta}


# ---------------------------------------------------------------------------
# Finalizar examen
# ---------------------------------------------------------------------------


def finalizar_examen(
    documento: str,
    area: str,
    intento_num: int,
    intento_id: int,
) -> dict:
    """
    Calcula nota final, consulta escala de valoración, llama a registrar_final.
    Réplica exacta de la función finalizar() interna del escritorio.
    """
    # Recuperar TODAS las respuestas guardadas en BD (incluye reanudación)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT pregunta_id, enunciado, respuesta_seleccionada, "
            "respuesta_correcta, es_correcta "
            "FROM respuestas_estudiantes "
            "WHERE documento=? AND area=? AND intento=? "
            "ORDER BY pregunta_id ASC",
            (documento, area, intento_num),
        )
        filas = cur.fetchall()

        # Total de preguntas del intento (del registro en resultados)
        cur.execute(
            "SELECT COUNT(*) FROM resultados "
            "WHERE documento=? AND area=? AND intento=?",
            (documento, area, intento_num),
        )

    respuestas_list = []
    total_respondidas = len(filas)
    correctas = 0
    for pid, enun, sel, corr, es_corr in filas:
        if es_corr:
            correctas += 1
        respuestas_list.append(
            {
                "pregunta_id": pid,
                "enunciado": enun,
                "respuesta_dada": sel,
                "respuesta_correcta": corr,
                "correcta": bool(es_corr),
            }
        )

    # Cantidad configurada en el intento (puede diferir de respondidas si finalizó por tiempo)
    total = total_respondidas if total_respondidas > 0 else 1
    nota = round((correctas / total) * 5, 2)

    # Escala de valoración
    nivel_desempeno = "Sin clasificación"
    recomendacion = "Consulte al docente."
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT
                     COALESCE(NULLIF(TRIM(desempeno),''), NULLIF(TRIM(concepto),''), 'Sin clasificación') AS nivel,
                     COALESCE(NULLIF(TRIM(recomendacion),''), 'Consulte al docente.') AS recomendacion
                   FROM escala_valoracion
                   WHERE ? BETWEEN
                       MIN(CAST(REPLACE(CAST(desde AS TEXT),',','.') AS REAL),
                           CAST(REPLACE(CAST(hasta AS TEXT),',','.') AS REAL))
                       AND
                       MAX(CAST(REPLACE(CAST(desde AS TEXT),',','.') AS REAL),
                           CAST(REPLACE(CAST(hasta AS TEXT),',','.') AS REAL))
                   LIMIT 1""",
                (float(nota),),
            )
            fila_escala = cur.fetchone()
        if fila_escala:
            nivel_desempeno = fila_escala[0] or nivel_desempeno
            recomendacion = fila_escala[1] or recomendacion
    except Exception:
        pass

    # Registrar final
    try:
        core_examenes.registrar_final(
            documento,
            nota,
            respuestas=json.dumps(respuestas_list),
            area=area,
            intento_id=intento_id,
        )
    except Exception:
        pass

    return {
        "ok": True,
        "correctas": correctas,
        "total": total,
        "nota": nota,
        "nivel_desempeno": nivel_desempeno,
        "recomendacion": recomendacion,
    }


# ---------------------------------------------------------------------------
# Historial de intentos (para la pantalla "Mi historial")
# ---------------------------------------------------------------------------


def historial_estudiante(documento: str) -> list[dict]:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT id, area, intento, nota, estado_examen,
                          hora_inicio, hora_fin, puede_revisar, evaluacion
                   FROM resultados
                   WHERE documento=?
                   ORDER BY id DESC""",
                (documento,),
            )
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return rows
    except Exception:
        return []
