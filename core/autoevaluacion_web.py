from __future__ import annotations

from autoevaluacion import (
    ESCALA,
    autoevaluacion_ya_respondida,
    crear_tablas_autoevaluacion,
    guardar_respuesta_autoevaluacion,
    listar_autoevaluaciones_activas,
    obtener_autoevaluacion,
    obtener_respuesta_autoevaluacion,
)

from . import get_db_path

DB_PATH = str(get_db_path())


def _ensure_tables() -> None:
    crear_tablas_autoevaluacion(db_path=DB_PATH)


def _sanitize_instrumento(instrumento: dict, documento: str) -> dict:
    item = dict(instrumento or {})
    respuesta = obtener_respuesta_autoevaluacion(
        item.get("id"),
        documento,
        db_path=DB_PATH,
    )
    item["respondida"] = respuesta is not None
    item["respuesta"] = respuesta
    item["escala"] = [{"valor": valor, "texto": texto} for valor, texto in ESCALA]
    return item


def listar_instrumentos_estudiante(
    documento: str, grado: str, curso: str
) -> list[dict]:
    _ensure_tables()
    instrumentos = listar_autoevaluaciones_activas(
        grado=grado, curso=curso, db_path=DB_PATH
    )
    return [_sanitize_instrumento(item, documento) for item in instrumentos]


def obtener_instrumento_estudiante(
    documento: str,
    grado: str,
    curso: str,
    instrumento_id: int,
) -> dict | None:
    _ensure_tables()
    instrumento = obtener_autoevaluacion(instrumento_id, db_path=DB_PATH)
    if not instrumento:
        return None

    if int(instrumento.get("habilitada") or 0) != 1:
        return None

    if (
        str(instrumento.get("grado") or "").strip().lower()
        != str(grado or "").strip().lower()
    ):
        return None

    if (
        str(instrumento.get("curso") or "").strip().upper()
        != str(curso or "").strip().upper()
    ):
        return None

    return _sanitize_instrumento(instrumento, documento)


def responder_instrumento_estudiante(
    documento: str,
    grado: str,
    curso: str,
    instrumento_id: int,
    respuestas: list,
) -> dict:
    instrumento = obtener_instrumento_estudiante(
        documento=documento,
        grado=grado,
        curso=curso,
        instrumento_id=instrumento_id,
    )
    if not instrumento:
        raise ValueError("autoevaluacion_no_encontrada")

    if autoevaluacion_ya_respondida(instrumento_id, documento, db_path=DB_PATH):
        raise ValueError("autoevaluacion_ya_respondida")

    respuestas_norm = [int(item or 0) for item in list(respuestas or [])]
    preguntas = list(instrumento.get("preguntas") or [])
    if not respuestas_norm or len(respuestas_norm) != len(preguntas):
        raise ValueError("respuestas_incompletas")
    if any(valor not in {1, 2, 3, 4} for valor in respuestas_norm):
        raise ValueError("respuesta_fuera_de_rango")

    nota, nivel = guardar_respuesta_autoevaluacion(
        instrumento_id,
        documento,
        respuestas_norm,
        db_path=DB_PATH,
    )
    puntaje_total = sum(respuestas_norm)
    puntaje_maximo = len(preguntas) * 4
    respuesta = obtener_respuesta_autoevaluacion(
        instrumento_id, documento, db_path=DB_PATH
    )

    return {
        "instrumento": _sanitize_instrumento(instrumento, documento),
        "respuesta": respuesta,
        "nota": nota,
        "nivel": nivel,
        "puntaje_total": puntaje_total,
        "puntaje_maximo": puntaje_maximo,
    }


def resumir_historial_estudiante(documento: str, grado: str, curso: str) -> list[dict]:
    instrumentos = listar_instrumentos_estudiante(documento, grado, curso)
    historial = []
    for item in instrumentos:
        respuesta = item.get("respuesta")
        if not respuesta:
            continue
        historial.append(
            {
                "id": item.get("id"),
                "area": item.get("area"),
                "periodo": item.get("periodo"),
                "curso": item.get("curso"),
                "grado": item.get("grado"),
                "preguntas": item.get("total_preguntas", 0),
                "nota": respuesta.get("nota"),
                "nivel": respuesta.get("nivel"),
                "puntaje_total": respuesta.get("puntaje_total"),
                "puntaje_maximo": respuesta.get("puntaje_maximo"),
                "fecha": respuesta.get("fecha"),
            }
        )
    return historial
