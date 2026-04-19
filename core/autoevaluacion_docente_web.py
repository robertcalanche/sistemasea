from __future__ import annotations

import sqlite3
from io import BytesIO

import pandas as pd

from autoevaluacion import (
    DIMENSIONES,
    actualizar_autoevaluacion,
    crear_autoevaluacion,
    crear_tablas_autoevaluacion,
    detalle_resultado_autoevaluacion,
    habilitar_autoevaluacion,
    listar_filtros_resultados_autoevaluacion,
    listar_autoevaluaciones,
    consultar_resultados_autoevaluacion,
    obtener_autoevaluacion,
    obtener_formato_base_autoevaluacion,
    resumir_resultados_autoevaluacion,
)

from . import get_db_path

DB_PATH = str(get_db_path())


def _ensure_tables() -> None:
    crear_tablas_autoevaluacion(db_path=DB_PATH)


def _connect():
    return sqlite3.connect(DB_PATH)


def listar_fuentes_docente(docente_documento: str) -> dict:
    _ensure_tables()
    documento = str(docente_documento or "").strip()
    if not documento:
        return {"areas": [], "grados": [], "cursos_por_grado": {}}

    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT
                TRIM(COALESCE(area, '')) AS area,
                TRIM(COALESCE(grado, '')) AS grado,
                TRIM(COALESCE(curso, '')) AS curso
            FROM carga_academica
            WHERE TRIM(COALESCE(docente_documento, '')) = ?
              AND TRIM(COALESCE(estado, 'Activo')) = 'Activo'
            ORDER BY area, grado, curso
            """,
            (documento,),
        )
        rows = cur.fetchall()

    areas = []
    grados = []
    cursos_por_grado: dict[str, list[str]] = {}
    for area, grado, curso in rows:
        area_txt = str(area or "").strip()
        grado_txt = str(grado or "").strip()
        curso_txt = str(curso or "").strip()
        if area_txt and area_txt not in areas:
            areas.append(area_txt)
        if grado_txt and grado_txt not in grados:
            grados.append(grado_txt)
        if grado_txt and curso_txt:
            cursos_por_grado.setdefault(grado_txt, [])
            if curso_txt not in cursos_por_grado[grado_txt]:
                cursos_por_grado[grado_txt].append(curso_txt)

    return {
        "areas": areas,
        "grados": grados,
        "cursos_por_grado": cursos_por_grado,
        "dimensiones": list(DIMENSIONES),
        "formato_base": obtener_formato_base_autoevaluacion(),
    }


def listar_instrumentos_docente(docente_documento: str) -> list[dict]:
    _ensure_tables()
    return listar_autoevaluaciones(
        docente=str(docente_documento or "").strip(), db_path=DB_PATH
    )


def obtener_instrumento_docente(
    docente_documento: str, instrumento_id: int
) -> dict | None:
    _ensure_tables()
    data = obtener_autoevaluacion(instrumento_id, db_path=DB_PATH)
    if not data:
        return None
    if str(data.get("docente") or "").strip() != str(docente_documento or "").strip():
        return None
    return data


def guardar_instrumento_docente(
    docente_documento: str,
    *,
    instrumento_id: int | None,
    area: str,
    grado: str,
    curso: str,
    periodo: str,
    preguntas: list,
    habilitada: bool,
) -> dict:
    _ensure_tables()
    documento = str(docente_documento or "").strip()
    if not documento:
        raise ValueError("docente_documento_requerido")

    instrumento_actual = None
    if instrumento_id is not None:
        instrumento_actual = obtener_instrumento_docente(documento, instrumento_id)
        if not instrumento_actual:
            raise ValueError("instrumento_no_encontrado")

    if instrumento_id is None:
        instrumento_id = crear_autoevaluacion(
            docente=documento,
            area=str(area or "").strip(),
            grado=str(grado or "").strip(),
            curso=str(curso or "").strip(),
            periodo=str(periodo or "").strip(),
            preguntas=preguntas,
            db_path=DB_PATH,
        )

    actualizado = actualizar_autoevaluacion(
        autoevaluacion_id=instrumento_id,
        docente=documento,
        area=str(area or "").strip(),
        grado=str(grado or "").strip(),
        curso=str(curso or "").strip(),
        periodo=str(periodo or "").strip(),
        preguntas=preguntas,
        habilitada=bool(habilitada),
        db_path=DB_PATH,
    )
    if not actualizado:
        raise ValueError("no_se_pudo_guardar_instrumento")

    instrumento = obtener_instrumento_docente(documento, instrumento_id)
    return {"instrumento_id": instrumento_id, "instrumento": instrumento}


def cambiar_estado_instrumento_docente(
    docente_documento: str,
    instrumento_id: int,
    habilitada: bool,
) -> dict:
    instrumento = obtener_instrumento_docente(docente_documento, instrumento_id)
    if not instrumento:
        raise ValueError("instrumento_no_encontrado")
    habilitar_autoevaluacion(
        instrumento_id, habilitar=bool(habilitada), db_path=DB_PATH
    )
    actualizado = obtener_instrumento_docente(docente_documento, instrumento_id)
    return {"instrumento": actualizado, "habilitada": bool(habilitada)}


def consultar_resultados_docente(
    docente_documento: str,
    *,
    area: str | None = None,
    grado: str | None = None,
    curso: str | None = None,
    periodo: str | None = None,
) -> dict:
    resultados = consultar_resultados_autoevaluacion(
        docente=str(docente_documento or "").strip(),
        area=area,
        grado=grado,
        curso=curso,
        periodo=periodo,
        db_path=DB_PATH,
    )
    resumen = resumir_resultados_autoevaluacion(resultados)
    filtros = listar_filtros_resultados_autoevaluacion(
        docente=str(docente_documento or "").strip(),
        db_path=DB_PATH,
    )
    return {"resultados": resultados, "resumen": resumen, "filtros": filtros}


def exportar_resultados_docente_excel(
    docente_documento: str,
    *,
    area: str | None = None,
    grado: str | None = None,
    curso: str | None = None,
    periodo: str | None = None,
):
    resultados = consultar_resultados_autoevaluacion(
        docente=str(docente_documento or "").strip(),
        area=area,
        grado=grado,
        curso=curso,
        periodo=periodo,
        db_path=DB_PATH,
    )
    rows = []
    for row in resultados:
        rows.append(
            {
                "Documento": row.get("documento", ""),
                "Nombre": row.get("nombre", ""),
                "Area": row.get("area", ""),
                "Grado": row.get("grado", ""),
                "Curso": row.get("curso", ""),
                "Periodo": row.get("periodo", ""),
                "Puntaje total": int(row.get("puntaje_total") or 0),
                "Puntaje maximo": int(row.get("puntaje_maximo") or 0),
                "Nota": float(row.get("nota") or 0),
                "Desempeno": row.get("nivel_calculado") or row.get("nivel") or "",
                "Fecha": row.get("fecha", ""),
            }
        )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name="Resultados")
    buffer.seek(0)
    return buffer


def detalle_resultado_docente(docente_documento: str, respuesta_id: int) -> dict | None:
    resultados = consultar_resultados_autoevaluacion(
        docente=str(docente_documento or "").strip(),
        db_path=DB_PATH,
    )
    if not any(
        int(item.get("respuesta_id") or 0) == int(respuesta_id) for item in resultados
    ):
        return None
    return detalle_resultado_autoevaluacion(respuesta_id, db_path=DB_PATH)
