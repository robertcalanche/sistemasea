# autoevaluacion.py
# Módulo para la gestión de autoevaluaciones docentes y estudiantiles
# Estructura de datos y lógica base

import json
import sqlite3
from datetime import datetime

DB_PATH = "sistema.db"  # Ajustar si es necesario
AUTOEVALUACION_PLANILLA_PREFIJO = "Autoevaluación - "


# --- Modelo de datos ---
def crear_tablas_autoevaluacion(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS autoevaluacion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            docente TEXT,
            area TEXT,
            grado TEXT,
            curso TEXT,
            periodo TEXT,
            preguntas TEXT, -- JSON serializado
            habilitada INTEGER DEFAULT 0,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS autoevaluacion_respuesta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_autoevaluacion INTEGER,
            estudiante TEXT,
            respuestas TEXT, -- JSON serializado
            puntaje_total INTEGER,
            puntaje_maximo INTEGER,
            nota REAL,
            nivel TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(id_autoevaluacion, estudiante)
        )
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS autoevaluacion_planilla_sync (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            respuesta_id INTEGER UNIQUE,
            docente TEXT,
            documento TEXT,
            nombre TEXT,
            grado TEXT,
            curso TEXT,
            area TEXT,
            evaluacion TEXT,
            periodo TEXT,
            nota REAL,
            nivel TEXT,
            fecha_respuesta TEXT,
            fecha_sincronizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_autoeval_planilla_doc_area_eval ON autoevaluacion_planilla_sync (documento, area, evaluacion)"
    )
    conn.commit()
    conn.close()


def construir_evaluacion_planilla_autoevaluacion(periodo, area=None):
    periodo_txt = str(periodo or "").strip()
    area_txt = str(area or "").strip()
    if not periodo_txt and not area_txt:
        return "Autoevaluación"
    if area_txt and periodo_txt:
        return f"{AUTOEVALUACION_PLANILLA_PREFIJO}{area_txt} - {periodo_txt}"
    if area_txt:
        return f"{AUTOEVALUACION_PLANILLA_PREFIJO}{area_txt}"
    return f"{AUTOEVALUACION_PLANILLA_PREFIJO}{periodo_txt}"


def es_evaluacion_planilla_autoevaluacion(evaluacion):
    texto = str(evaluacion or "").strip().lower()
    return texto.startswith("autoevaluación") or texto.startswith("autoevaluacion")


# --- Utilidades para dimensiones y escalas ---
DIMENSIONES = ["Académica", "Responsabilidad", "Actitudinal"]
ESCALA = [(1, "Nunca"), (2, "Algunas veces"), (3, "Casi siempre"), (4, "Siempre")]
FORMATO_BASE_AUTOEVALUACION = [
    {"dimension": "Académica", "texto": "Comprendo los temas trabajados en clase."},
    {
        "dimension": "Académica",
        "texto": "Realizo mis tareas de manera completa y a tiempo.",
    },
    {
        "dimension": "Académica",
        "texto": "Participo activamente en las actividades de clase.",
    },
    {"dimension": "Académica", "texto": "Pregunto cuando no entiendo un tema."},
    {"dimension": "Responsabilidad", "texto": "Cumplo con mis deberes escolares."},
    {"dimension": "Responsabilidad", "texto": "Soy puntual en la entrega de trabajos."},
    {
        "dimension": "Responsabilidad",
        "texto": "Cuido los materiales y recursos del aula.",
    },
    {"dimension": "Actitudinal", "texto": "Respeto a mis compañeros y docentes."},
    {"dimension": "Actitudinal", "texto": "Trabajo en equipo de manera adecuada."},
    {
        "dimension": "Actitudinal",
        "texto": "Mantengo una actitud positiva frente al aprendizaje.",
    },
]


def obtener_formato_base_autoevaluacion():
    return [dict(item) for item in FORMATO_BASE_AUTOEVALUACION]


def _normalizar_preguntas(preguntas):
    normalizadas = []
    for item in preguntas or []:
        if not isinstance(item, dict):
            continue
        dimension = str(item.get("dimension", "")).strip()
        texto = str(item.get("texto", "")).strip()
        if not dimension or not texto:
            continue
        normalizadas.append({"dimension": dimension, "texto": texto})
    return normalizadas


def _fetchone_dict(cur):
    row = cur.fetchone()
    if row is None:
        return None
    cols = [col[0] for col in cur.description]
    return dict(zip(cols, row))


def _enriquecer_autoevaluacion(item, db_path=DB_PATH):
    data = dict(item or {})
    try:
        preguntas = json.loads(data.get("preguntas") or "[]")
    except Exception:
        preguntas = []
    data["preguntas"] = preguntas
    data["total_preguntas"] = len(preguntas)
    data["docente_nombre"] = obtener_nombre_docente(
        data.get("docente"), db_path=db_path
    )
    return data


def obtener_nombre_docente(docente_documento, db_path=DB_PATH):
    documento = str(docente_documento or "").strip()
    if not documento:
        return ""

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT nombre FROM docentes WHERE TRIM(COALESCE(documento, '')) = ? LIMIT 1",
        (documento,),
    )
    row = cur.fetchone()
    conn.close()
    return str(row[0] or "").strip() if row else ""


def construir_nombre_estudiante(row):
    partes = [
        str((row or {}).get("apellido1") or "").strip(),
        str((row or {}).get("apellido2") or "").strip(),
        str((row or {}).get("nombre1") or "").strip(),
        str((row or {}).get("nombre2") or "").strip(),
    ]
    return " ".join([parte for parte in partes if parte])


# --- Funciones para crear y editar instrumentos ---
def crear_autoevaluacion(
    docente, area, grado, curso, periodo, preguntas, db_path=DB_PATH
):
    preguntas_norm = _normalizar_preguntas(preguntas)
    if not preguntas_norm:
        raise ValueError("Debe registrar al menos una pregunta válida.")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO autoevaluacion (docente, area, grado, curso, periodo, preguntas, habilitada)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """,
        (
            docente,
            area,
            grado,
            curso,
            periodo,
            json.dumps(preguntas_norm, ensure_ascii=True),
        ),
    )
    nuevo_id = cur.lastrowid
    conn.commit()
    conn.close()
    return nuevo_id


def actualizar_autoevaluacion(
    autoevaluacion_id,
    docente,
    area,
    grado,
    curso,
    periodo,
    preguntas,
    habilitada=None,
    db_path=DB_PATH,
):
    preguntas_norm = _normalizar_preguntas(preguntas)
    if not preguntas_norm:
        raise ValueError("Debe registrar al menos una pregunta válida.")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    preguntas_json = json.dumps(preguntas_norm, ensure_ascii=True)
    if habilitada is None:
        cur.execute(
            """
            UPDATE autoevaluacion
            SET docente=?, area=?, grado=?, curso=?, periodo=?, preguntas=?
            WHERE id=?
        """,
            (docente, area, grado, curso, periodo, preguntas_json, autoevaluacion_id),
        )
    else:
        cur.execute(
            """
            UPDATE autoevaluacion
            SET docente=?, area=?, grado=?, curso=?, periodo=?, preguntas=?, habilitada=?
            WHERE id=?
        """,
            (
                docente,
                area,
                grado,
                curso,
                periodo,
                preguntas_json,
                1 if habilitada else 0,
                autoevaluacion_id,
            ),
        )
    conn.commit()
    actualizado = cur.rowcount > 0
    conn.close()
    return actualizado


def obtener_autoevaluacion(autoevaluacion_id, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, docente, area, grado, curso, periodo, preguntas, habilitada, fecha_creacion
        FROM autoevaluacion
        WHERE id=?
    """,
        (autoevaluacion_id,),
    )
    data = _fetchone_dict(cur)
    conn.close()
    if not data:
        return None
    return _enriquecer_autoevaluacion(data, db_path=db_path)


def listar_autoevaluaciones(docente=None, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    params = []
    sql = (
        "SELECT id, docente, area, grado, curso, periodo, preguntas, habilitada, fecha_creacion "
        "FROM autoevaluacion"
    )
    if str(docente or "").strip():
        sql += " WHERE docente = ?"
        params.append(str(docente).strip())
    sql += " ORDER BY id DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    cols = [col[0] for col in cur.description]
    conn.close()

    resultado = []
    for row in rows:
        item = dict(zip(cols, row))
        resultado.append(_enriquecer_autoevaluacion(item, db_path=db_path))
    return resultado


def listar_autoevaluaciones_activas(grado, curso, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, docente, area, grado, curso, periodo, preguntas, habilitada, fecha_creacion
        FROM autoevaluacion
        WHERE habilitada = 1
          AND LOWER(TRIM(COALESCE(grado, ''))) = LOWER(TRIM(COALESCE(?, '')))
          AND UPPER(TRIM(COALESCE(curso, ''))) = UPPER(TRIM(COALESCE(?, '')))
        ORDER BY id DESC
    """,
        (str(grado or "").strip(), str(curso or "").strip()),
    )
    rows = cur.fetchall()
    cols = [col[0] for col in cur.description]
    conn.close()

    resultado = []
    for row in rows:
        resultado.append(
            _enriquecer_autoevaluacion(dict(zip(cols, row)), db_path=db_path)
        )
    return resultado


def listar_filtros_resultados_autoevaluacion(docente, db_path=DB_PATH):
    instrumentos = listar_autoevaluaciones(docente=docente, db_path=db_path)
    filtros = {
        "areas": sorted(
            {
                str(item.get("area") or "").strip()
                for item in instrumentos
                if str(item.get("area") or "").strip()
            }
        ),
        "grados": sorted(
            {
                str(item.get("grado") or "").strip()
                for item in instrumentos
                if str(item.get("grado") or "").strip()
            }
        ),
        "cursos": sorted(
            {
                str(item.get("curso") or "").strip()
                for item in instrumentos
                if str(item.get("curso") or "").strip()
            }
        ),
        "periodos": sorted(
            {
                str(item.get("periodo") or "").strip()
                for item in instrumentos
                if str(item.get("periodo") or "").strip()
            }
        ),
    }
    return filtros


def consultar_resultados_autoevaluacion(
    docente,
    area=None,
    grado=None,
    curso=None,
    periodo=None,
    db_path=DB_PATH,
):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    sql = """
        SELECT
            r.id AS respuesta_id,
            r.id_autoevaluacion,
            r.estudiante AS documento,
            r.respuestas,
            r.puntaje_total,
            r.puntaje_maximo,
            r.nota,
            r.nivel,
            r.fecha,
            a.area,
            a.grado,
            a.curso,
            a.periodo,
            a.preguntas,
            e.apellido1,
            e.apellido2,
            e.nombre1,
            e.nombre2
        FROM autoevaluacion_respuesta r
        INNER JOIN autoevaluacion a ON a.id = r.id_autoevaluacion
        LEFT JOIN estudiantes e ON TRIM(COALESCE(e.documento, '')) = TRIM(COALESCE(r.estudiante, ''))
        WHERE TRIM(COALESCE(a.docente, '')) = ?
    """
    params = [str(docente or "").strip()]

    if str(area or "").strip() and str(area).strip().lower() != "todos":
        sql += " AND LOWER(TRIM(COALESCE(a.area, ''))) = LOWER(TRIM(COALESCE(?, '')))"
        params.append(str(area).strip())
    if str(grado or "").strip() and str(grado).strip().lower() != "todos":
        sql += " AND LOWER(TRIM(COALESCE(a.grado, ''))) = LOWER(TRIM(COALESCE(?, '')))"
        params.append(str(grado).strip())
    if str(curso or "").strip() and str(curso).strip().lower() != "todos":
        sql += " AND UPPER(TRIM(COALESCE(a.curso, ''))) = UPPER(TRIM(COALESCE(?, '')))"
        params.append(str(curso).strip())
    if str(periodo or "").strip() and str(periodo).strip().lower() != "todos":
        sql += (
            " AND LOWER(TRIM(COALESCE(a.periodo, ''))) = LOWER(TRIM(COALESCE(?, '')))"
        )
        params.append(str(periodo).strip())

    sql += " ORDER BY datetime(r.fecha) DESC, r.id DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    cols = [col[0] for col in cur.description]
    conn.close()

    resultados = []
    for row in rows:
        item = dict(zip(cols, row))
        try:
            item["preguntas"] = json.loads(item.get("preguntas") or "[]")
        except Exception:
            item["preguntas"] = []
        try:
            item["respuestas"] = json.loads(item.get("respuestas") or "[]")
        except Exception:
            item["respuestas"] = []
        item["nombre"] = construir_nombre_estudiante(item)
        nota = float(item.get("nota") or 0)
        item["nivel_calculado"] = calcular_nivel_desempeno(nota)
        resultados.append(item)
    return resultados


def listar_evaluaciones_sincronizadas(
    grado=None, area=None, curso=None, docente=None, db_path=DB_PATH
):
    crear_tablas_autoevaluacion(db_path=db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    sql = """
        SELECT DISTINCT evaluacion
        FROM autoevaluacion_planilla_sync
        WHERE TRIM(COALESCE(evaluacion, '')) <> ''
    """
    params = []
    if str(grado or "").strip():
        sql += " AND LOWER(TRIM(COALESCE(grado, ''))) = LOWER(TRIM(COALESCE(?, '')))"
        params.append(str(grado).strip())
    if str(area or "").strip():
        sql += " AND LOWER(TRIM(COALESCE(area, ''))) = LOWER(TRIM(COALESCE(?, '')))"
        params.append(str(area).strip())
    if str(curso or "").strip():
        sql += " AND UPPER(TRIM(COALESCE(curso, ''))) = UPPER(TRIM(COALESCE(?, '')))"
        params.append(str(curso).strip())
    if str(docente or "").strip():
        sql += " AND TRIM(COALESCE(docente, '')) = ?"
        params.append(str(docente).strip())
    sql += " ORDER BY evaluacion"
    cur.execute(sql, params)
    rows = [str(row[0]).strip() for row in cur.fetchall() if row and row[0]]
    conn.close()
    return rows


def listar_calificaciones_sincronizadas_planilla(
    documento=None,
    grado=None,
    area=None,
    curso=None,
    evaluacion=None,
    docente=None,
    db_path=DB_PATH,
):
    crear_tablas_autoevaluacion(db_path=db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    sql = """
        SELECT id, respuesta_id, docente, documento, nombre, grado, curso, area,
               evaluacion, periodo, nota, nivel, fecha_respuesta, fecha_sincronizacion
        FROM autoevaluacion_planilla_sync
        WHERE 1 = 1
    """
    params = []
    if str(documento or "").strip():
        sql += " AND TRIM(COALESCE(documento, '')) = ?"
        params.append(str(documento).strip())
    if str(grado or "").strip():
        sql += " AND LOWER(TRIM(COALESCE(grado, ''))) = LOWER(TRIM(COALESCE(?, '')))"
        params.append(str(grado).strip())
    if str(area or "").strip():
        sql += " AND LOWER(TRIM(COALESCE(area, ''))) = LOWER(TRIM(COALESCE(?, '')))"
        params.append(str(area).strip())
    if str(curso or "").strip():
        sql += " AND UPPER(TRIM(COALESCE(curso, ''))) = UPPER(TRIM(COALESCE(?, '')))"
        params.append(str(curso).strip())
    if str(evaluacion or "").strip():
        sql += (
            " AND LOWER(TRIM(COALESCE(evaluacion, ''))) = LOWER(TRIM(COALESCE(?, '')))"
        )
        params.append(str(evaluacion).strip())
    if str(docente or "").strip():
        sql += " AND TRIM(COALESCE(docente, '')) = ?"
        params.append(str(docente).strip())
    sql += " ORDER BY datetime(fecha_respuesta) DESC, id DESC"
    cur.execute(sql, params)
    cols = [col[0] for col in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows


def obtener_calificacion_sincronizada_planilla(
    documento, area=None, evaluacion=None, grado=None, curso=None, db_path=DB_PATH
):
    rows = listar_calificaciones_sincronizadas_planilla(
        documento=documento,
        grado=grado,
        area=area,
        curso=curso,
        evaluacion=evaluacion,
        db_path=db_path,
    )
    return rows[0] if rows else None


def sincronizar_resultados_autoevaluacion(
    docente, area=None, grado=None, curso=None, periodo=None, db_path=DB_PATH
):
    crear_tablas_autoevaluacion(db_path=db_path)
    resultados = consultar_resultados_autoevaluacion(
        docente=docente,
        area=area,
        grado=grado,
        curso=curso,
        periodo=periodo,
        db_path=db_path,
    )
    if not resultados:
        return {"total": 0, "insertados": 0, "actualizados": 0, "evaluaciones": []}

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    insertados = 0
    actualizados = 0
    evaluaciones = set()
    fecha_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for item in resultados:
        respuesta_id = int(item.get("respuesta_id") or 0)
        if respuesta_id <= 0:
            continue

        evaluacion_planilla = construir_evaluacion_planilla_autoevaluacion(
            item.get("periodo"),
            item.get("area"),
        )
        evaluaciones.add(evaluacion_planilla)
        params = (
            str(docente or "").strip(),
            str(item.get("documento") or "").strip(),
            str(item.get("nombre") or "").strip(),
            str(item.get("grado") or "").strip(),
            str(item.get("curso") or "").strip(),
            str(item.get("area") or "").strip(),
            evaluacion_planilla,
            str(item.get("periodo") or "").strip(),
            float(item.get("nota") or 0),
            str(item.get("nivel_calculado") or item.get("nivel") or "").strip(),
            str(item.get("fecha") or "").strip(),
            fecha_sync,
            respuesta_id,
        )

        cur.execute(
            "SELECT id FROM autoevaluacion_planilla_sync WHERE respuesta_id = ?",
            (respuesta_id,),
        )
        existe = cur.fetchone()

        if existe:
            cur.execute(
                """
                UPDATE autoevaluacion_planilla_sync
                SET docente = ?, documento = ?, nombre = ?, grado = ?, curso = ?,
                    area = ?, evaluacion = ?, periodo = ?, nota = ?, nivel = ?,
                    fecha_respuesta = ?, fecha_sincronizacion = ?
                WHERE respuesta_id = ?
            """,
                params,
            )
            actualizados += 1
        else:
            cur.execute(
                """
                INSERT INTO autoevaluacion_planilla_sync (
                    docente, documento, nombre, grado, curso, area, evaluacion,
                    periodo, nota, nivel, fecha_respuesta, fecha_sincronizacion,
                    respuesta_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                params,
            )
            insertados += 1

    conn.commit()
    conn.close()
    return {
        "total": insertados + actualizados,
        "insertados": insertados,
        "actualizados": actualizados,
        "evaluaciones": sorted(evaluaciones),
    }


def resumir_resultados_autoevaluacion(resultados):
    total = len(resultados or [])
    promedio = 0.0
    conteos = {"Bajo": 0, "Básico": 0, "Alto": 0, "Superior": 0}
    if total:
        promedio = round(
            sum(float(item.get("nota") or 0) for item in resultados) / float(total),
            2,
        )
        for item in resultados:
            conteos[calcular_nivel_desempeno(float(item.get("nota") or 0))] += 1
    return {
        "total_estudiantes": total,
        "promedio_curso": promedio,
        "conteos": conteos,
    }


def detalle_resultado_autoevaluacion(respuesta_id, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            r.id AS respuesta_id,
            r.id_autoevaluacion,
            r.estudiante AS documento,
            r.respuestas,
            r.puntaje_total,
            r.puntaje_maximo,
            r.nota,
            r.nivel,
            r.fecha,
            a.area,
            a.grado,
            a.curso,
            a.periodo,
            a.preguntas,
            e.apellido1,
            e.apellido2,
            e.nombre1,
            e.nombre2
        FROM autoevaluacion_respuesta r
        INNER JOIN autoevaluacion a ON a.id = r.id_autoevaluacion
        LEFT JOIN estudiantes e ON TRIM(COALESCE(e.documento, '')) = TRIM(COALESCE(r.estudiante, ''))
        WHERE r.id = ?
        LIMIT 1
    """,
        (respuesta_id,),
    )
    item = _fetchone_dict(cur)
    conn.close()
    if not item:
        return None

    try:
        preguntas = json.loads(item.get("preguntas") or "[]")
    except Exception:
        preguntas = []
    try:
        respuestas = json.loads(item.get("respuestas") or "[]")
    except Exception:
        respuestas = []

    detalle_preguntas = []
    for idx, pregunta in enumerate(preguntas):
        valor = (
            int(respuestas[idx])
            if idx < len(respuestas) and str(respuestas[idx]).isdigit()
            else 0
        )
        detalle_preguntas.append(
            {
                "dimension": str((pregunta or {}).get("dimension") or "").strip(),
                "texto": str((pregunta or {}).get("texto") or "").strip(),
                "respuesta": valor,
                "puntaje": valor,
            }
        )

    item["nombre"] = construir_nombre_estudiante(item)
    item["nivel_calculado"] = calcular_nivel_desempeno(float(item.get("nota") or 0))
    item["detalle_preguntas"] = detalle_preguntas
    return item


def obtener_respuesta_autoevaluacion(id_autoevaluacion, estudiante, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, id_autoevaluacion, estudiante, respuestas, puntaje_total, puntaje_maximo, nota, nivel, fecha
        FROM autoevaluacion_respuesta
        WHERE id_autoevaluacion = ? AND TRIM(COALESCE(estudiante, '')) = ?
        LIMIT 1
    """,
        (id_autoevaluacion, str(estudiante or "").strip()),
    )
    data = _fetchone_dict(cur)
    conn.close()
    if not data:
        return None
    try:
        data["respuestas"] = json.loads(data.get("respuestas") or "[]")
    except Exception:
        data["respuestas"] = []
    return data


def autoevaluacion_ya_respondida(id_autoevaluacion, estudiante, db_path=DB_PATH):
    return (
        obtener_respuesta_autoevaluacion(
            id_autoevaluacion=id_autoevaluacion,
            estudiante=estudiante,
            db_path=db_path,
        )
        is not None
    )


# --- Función para habilitar/deshabilitar ---
def habilitar_autoevaluacion(id_autoevaluacion, habilitar=True, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE autoevaluacion SET habilitada=? WHERE id=?
    """,
        (1 if habilitar else 0, id_autoevaluacion),
    )
    conn.commit()
    conn.close()


# --- Guardar respuesta de estudiante ---
def guardar_respuesta_autoevaluacion(
    id_autoevaluacion, estudiante, respuestas, db_path=DB_PATH
):
    if autoevaluacion_ya_respondida(id_autoevaluacion, estudiante, db_path=db_path):
        raise ValueError("La autoevaluación ya fue respondida por este estudiante.")

    puntaje_total = sum(respuestas)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT preguntas FROM autoevaluacion WHERE id=?", (id_autoevaluacion,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("Autoevaluación no encontrada")
    preguntas = json.loads(row[0])
    puntaje_maximo = len(preguntas) * 4
    nota = round((puntaje_total / puntaje_maximo) * 5, 2) if puntaje_maximo else 0
    nivel = calcular_nivel_desempeno(nota)
    cur.execute(
        """
        INSERT OR REPLACE INTO autoevaluacion_respuesta
        (id_autoevaluacion, estudiante, respuestas, puntaje_total, puntaje_maximo, nota, nivel, fecha)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            id_autoevaluacion,
            estudiante,
            json.dumps(respuestas),
            puntaje_total,
            puntaje_maximo,
            nota,
            nivel,
            datetime.now(),
        ),
    )
    conn.commit()
    conn.close()
    return nota, nivel


def calcular_nivel_desempeno(nota):
    nota = float(nota or 0)
    if nota < 3.0:
        return "Bajo"
    elif nota < 4.0:
        return "Básico"
    elif nota <= 4.5:
        return "Alto"
    else:
        return "Superior"


# --- Inicialización automática de tablas ---
if __name__ == "__main__":
    crear_tablas_autoevaluacion()
