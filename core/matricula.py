"""
Servicios de matrícula — desacoplados de UI.
Permite operaciones CRUD de estudiantes desde escritorio y web.
"""

from . import get_connection
from .construir_nombre import construir_nombre
from .preguntas import normalizar_grado


def _asegurar_columna_nombre(cur):
    cur.execute("PRAGMA table_info(estudiantes)")
    columnas = {str(row[1]).strip().lower() for row in cur.fetchall()}
    if "nombre" not in columnas:
        cur.execute("ALTER TABLE estudiantes ADD COLUMN nombre TEXT")


def cargar_todos_estudiantes_dataframe():
    """Carga todos los estudiantes como lista de dicts (para Pandas o UI)."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    sede,
                    jornada,
                    grado,
                    curso,
                    codigo,
                    apellido1,
                    apellido2,
                    nombre1,
                    nombre2,
                    tipodoc,
                    documento,
                    lugar_expedicion,
                    fecha_expedicion,
                    fecha_nacimiento,
                    lugar_nacimiento,
                    telefono,
                    celular,
                    correo,
                    genero,
                    tipo_sangre,
                    estado_academico
                FROM estudiantes
                ORDER BY COALESCE(nombre1, '') COLLATE NOCASE ASC
                """
            )
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        return rows
    except Exception:
        return []


def crear_o_actualizar_estudiante(
    documento,
    sede="",
    jornada="",
    grado="",
    curso="",
    codigo="",
    apellido1="",
    apellido2="",
    nombre1="",
    nombre2="",
    tipodoc="",
    lugar_expedicion="",
    fecha_expedicion="",
    fecha_nacimiento="",
    lugar_nacimiento="",
    telefono="",
    celular="",
    correo="",
    genero="",
    tipo_sangre="",
    estado_academico="Activo",
    anio_lectivo=None,
):
    """UPSERT de estudiante por documento."""
    if not documento or not str(documento).strip():
        raise ValueError("documento requerido")

    documento = str(documento).strip()

    with get_connection() as conn:
        cur = conn.cursor()
        # Crear tabla con todos los campos requeridos si no existen
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS estudiantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sede TEXT,
                jornada TEXT,
                grado TEXT,
                curso TEXT,
                codigo TEXT,
                apellido1 TEXT,
                apellido2 TEXT,
                nombre1 TEXT,
                nombre2 TEXT,
                tipodoc TEXT,
                documento TEXT UNIQUE,
                lugar_expedicion TEXT,
                fecha_expedicion TEXT,
                fecha_nacimiento TEXT,
                lugar_nacimiento TEXT,
                telefono TEXT,
                celular TEXT,
                correo TEXT,
                nombre TEXT,
                genero TEXT,
                tipo_sangre TEXT,
                estado_academico TEXT DEFAULT 'Activo',
                anio_lectivo TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        _asegurar_columna_nombre(cur)

        nombre = construir_nombre(
            {
                "apellido1": apellido1,
                "apellido2": apellido2,
                "nombre1": nombre1,
                "nombre2": nombre2,
            }
        )

        sql_upsert = """
            INSERT INTO estudiantes (
                sede, jornada, grado, curso, codigo, apellido1, apellido2, nombre1, nombre2, tipodoc, documento,
                lugar_expedicion, fecha_expedicion, fecha_nacimiento, lugar_nacimiento, telefono, celular, correo, nombre, genero, tipo_sangre, estado_academico, anio_lectivo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(documento) DO UPDATE SET
                sede=excluded.sede,
                jornada=excluded.jornada,
                grado=excluded.grado,
                curso=excluded.curso,
                codigo=excluded.codigo,
                apellido1=excluded.apellido1,
                apellido2=excluded.apellido2,
                nombre1=excluded.nombre1,
                nombre2=excluded.nombre2,
                tipodoc=excluded.tipodoc,
                lugar_expedicion=excluded.lugar_expedicion,
                fecha_expedicion=excluded.fecha_expedicion,
                fecha_nacimiento=excluded.fecha_nacimiento,
                lugar_nacimiento=excluded.lugar_nacimiento,
                telefono=excluded.telefono,
                celular=excluded.celular,
                correo=excluded.correo,
                nombre=excluded.nombre,
                genero=excluded.genero,
                tipo_sangre=excluded.tipo_sangre,
                estado_academico=excluded.estado_academico,
                anio_lectivo=excluded.anio_lectivo
        """

        cur.execute(
            sql_upsert,
            (
                str(sede or "").strip(),
                str(jornada or "").strip(),
                str(grado or "").strip(),
                str(curso or "").strip(),
                str(codigo or "").strip(),
                str(apellido1 or "").strip(),
                str(apellido2 or "").strip(),
                str(nombre1 or "").strip(),
                str(nombre2 or "").strip(),
                str(tipodoc or "").strip(),
                str(documento or "").strip(),
                str(lugar_expedicion or "").strip(),
                str(fecha_expedicion or "").strip(),
                str(fecha_nacimiento or "").strip(),
                str(lugar_nacimiento or "").strip(),
                str(telefono or "").strip(),
                str(celular or "").strip(),
                str(correo or "").strip(),
                nombre,
                str(genero or "").strip(),
                str(tipo_sangre or "").strip(),
                str(estado_academico or "").strip(),
                str(anio_lectivo or "").strip(),
            ),
        )
        conn.commit()


def eliminar_estudiante(documento):
    """Elimina estudiante por documento."""
    documento = str(documento).strip()
    with get_connection() as conn:
        conn.execute("DELETE FROM estudiantes WHERE documento = ?", (documento,))
        conn.commit()


def buscar_estudiante(documento):
    """Busca un estudiante por documento."""
    documento = str(documento).strip()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM estudiantes WHERE documento = ?", (documento,))
        col_names = [desc[0] for desc in cur.description]
        row = cur.fetchone()
    if row:
        estudiante = dict(zip(col_names, row))
        estudiante["nombre"] = str(
            estudiante.get("nombre") or ""
        ).strip() or construir_nombre(estudiante)
        return estudiante
    return None


def sincronizar_estudiantes(registros, anio_lectivo=None):
    """UPSERT masivo: actualiza estudiantes en BD según una lista de dicts.
    Elimina los que no estén en la lista.
    """
    if not registros:
        registros = []

    documentos_validos = set()

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS estudiantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sede TEXT,
                jornada TEXT,
                grado TEXT,
                curso TEXT,
                codigo TEXT,
                apellido1 TEXT,
                apellido2 TEXT,
                nombre1 TEXT,
                nombre2 TEXT,
                tipodoc TEXT,
                documento TEXT UNIQUE,
                lugar_expedicion TEXT,
                fecha_expedicion TEXT,
                fecha_nacimiento TEXT,
                lugar_nacimiento TEXT,
                telefono TEXT,
                celular TEXT,
                correo TEXT,
                nombre TEXT,
                genero TEXT,
                tipo_sangre TEXT,
                estado_academico TEXT DEFAULT 'Activo',
                anio_lectivo TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        _asegurar_columna_nombre(cur)

        sql_upsert = """
            INSERT INTO estudiantes (
                sede, jornada, grado, curso, codigo, apellido1, apellido2, nombre1, nombre2, tipodoc, documento,
                lugar_expedicion, fecha_expedicion, fecha_nacimiento, lugar_nacimiento, telefono, celular, correo, nombre, genero, tipo_sangre, estado_academico, anio_lectivo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(documento) DO UPDATE SET
                sede=excluded.sede,
                jornada=excluded.jornada,
                grado=excluded.grado,
                curso=excluded.curso,
                codigo=excluded.codigo,
                apellido1=excluded.apellido1,
                apellido2=excluded.apellido2,
                nombre1=excluded.nombre1,
                nombre2=excluded.nombre2,
                tipodoc=excluded.tipodoc,
                lugar_expedicion=excluded.lugar_expedicion,
                fecha_expedicion=excluded.fecha_expedicion,
                fecha_nacimiento=excluded.fecha_nacimiento,
                lugar_nacimiento=excluded.lugar_nacimiento,
                telefono=excluded.telefono,
                celular=excluded.celular,
                correo=excluded.correo,
                nombre=excluded.nombre,
                genero=excluded.genero,
                tipo_sangre=excluded.tipo_sangre,
                estado_academico=excluded.estado_academico,
                anio_lectivo=excluded.anio_lectivo
        """

        for row in registros:
            # Unificar claves a minúsculas y limpiar valores
            clean_row = {
                k.lower(): (
                    "" if v is None or str(v).lower() == "nan" else str(v).strip()
                )
                for k, v in row.items()
            }
            documento = clean_row.get("documento", "")
            if not documento:
                continue
            documentos_validos.add(documento)

            # Estado académico
            estado_ui = clean_row.get("estado_academico", "")
            if estado_ui.lower() in ("matriculado", "activo", "ma", ""):
                estado_db = "Activo"
            else:
                estado_db = estado_ui

            nombre = construir_nombre(clean_row)

            cur.execute(
                sql_upsert,
                (
                    clean_row.get("sede", ""),
                    clean_row.get("jornada", ""),
                    clean_row.get("grado", ""),
                    clean_row.get("curso", ""),
                    clean_row.get("codigo", ""),
                    clean_row.get("apellido1", ""),
                    clean_row.get("apellido2", ""),
                    clean_row.get("nombre1", ""),
                    clean_row.get("nombre2", ""),
                    clean_row.get("tipodoc", ""),
                    documento,
                    clean_row.get("lugar_expedicion", ""),
                    clean_row.get("fecha_expedicion", ""),
                    clean_row.get("fecha_nacimiento", ""),
                    clean_row.get("lugar_nacimiento", ""),
                    clean_row.get("telefono", ""),
                    clean_row.get("celular", ""),
                    clean_row.get("correo", ""),
                    nombre,
                    clean_row.get("genero", ""),
                    clean_row.get("tipo_sangre", ""),
                    estado_db,
                    anio_lectivo or clean_row.get("anio_lectivo", ""),
                ),
            )

        # Eliminar estudiantes no en la lista
        if not registros:
            cur.execute("DELETE FROM estudiantes")
        elif documentos_validos:
            placeholders = ",".join(["?"] * len(documentos_validos))
            cur.execute(
                f"DELETE FROM estudiantes WHERE documento NOT IN ({placeholders})",
                tuple(documentos_validos),
            )

        conn.commit()


def cambiar_grado_curso(documento, nuevo_grado, nuevo_curso, nueva_jornada=None):
    """Cambia grado y/o curso de un estudiante."""
    documento = str(documento).strip()

    with get_connection() as conn:
        cur = conn.cursor()
        if nueva_jornada:
            cur.execute(
                "UPDATE estudiantes SET grado = ?, curso = ?, jornada = ? WHERE documento = ?",
                (
                    str(nuevo_grado).strip(),
                    str(nuevo_curso).strip(),
                    str(nueva_jornada).strip(),
                    documento,
                ),
            )
        else:
            cur.execute(
                "UPDATE estudiantes SET grado = ?, curso = ? WHERE documento = ?",
                (str(nuevo_grado).strip(), str(nuevo_curso).strip(), documento),
            )
        conn.commit()


def cambiar_estado_estudiante(documento, nuevo_estado):
    """Cambia estado de un estudiante (Activo, Inactivo, etc.)."""
    documento = str(documento).strip()
    nuevo_estado = str(nuevo_estado).strip()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE estudiantes SET estado_academico = ? WHERE documento = ?",
            (nuevo_estado, documento),
        )
        conn.commit()


def _normalizar_grado_comparable(valor):
    try:
        return int(float(str(valor).strip()))
    except Exception:
        return normalizar_grado(valor)


def listar_estudiantes_por_grado(grado, curso=None, solo_activos=False):
    """Retorna estudiantes por grado y curso opcional como lista de dicts."""
    grado_ref = _normalizar_grado_comparable(grado)
    curso_ref = str(curso).strip() if curso is not None else ""

    with get_connection() as conn:
        cur = conn.cursor()
        if solo_activos:
            cur.execute("SELECT * FROM estudiantes WHERE estado_academico = 'Activo'")
        else:
            cur.execute("SELECT * FROM estudiantes")

        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    out = []
    for reg in rows:
        reg["nombre"] = str(reg.get("nombre") or "").strip() or construir_nombre(reg)
        grado_reg = _normalizar_grado_comparable(reg.get("grado"))
        if grado_reg != grado_ref:
            continue
        if curso_ref and str(reg.get("curso", "")).strip() != curso_ref:
            continue
        out.append(reg)
    return out


def listar_grados_distintos(solo_activos=False):
    """Lista grados únicos de estudiantes, ordenados de forma natural."""
    with get_connection() as conn:
        cur = conn.cursor()
        if solo_activos:
            cur.execute(
                "SELECT DISTINCT grado FROM estudiantes WHERE estado_academico = 'Activo'"
            )
        else:
            cur.execute("SELECT DISTINCT grado FROM estudiantes")
        rows = [r[0] for r in cur.fetchall() if r and r[0] is not None]

    normalizados = []
    vistos = set()
    for raw in rows:
        valor = _normalizar_grado_comparable(raw)
        key = str(valor)
        if not key or key in vistos:
            continue
        vistos.add(key)
        normalizados.append(valor)

    return sorted(
        normalizados,
        key=lambda x: (0, x) if isinstance(x, int) else (1, str(x)),
    )


def listar_cursos_distintos(grado=None, solo_activos=False):
    """Lista cursos únicos. Si se pasa grado, filtra por grado."""
    grado_ref = _normalizar_grado_comparable(grado) if grado not in (None, "") else None

    with get_connection() as conn:
        cur = conn.cursor()
        if solo_activos:
            cur.execute(
                "SELECT grado, curso FROM estudiantes WHERE estado_academico = 'Activo'"
            )
        else:
            cur.execute("SELECT grado, curso FROM estudiantes")
        rows = cur.fetchall()

    cursos = []
    vistos = set()
    for grado_raw, curso_raw in rows:
        curso_txt = str(curso_raw or "").strip().upper()
        if not curso_txt:
            continue

        if grado_ref is not None:
            grado_reg = _normalizar_grado_comparable(grado_raw)
            if grado_reg != grado_ref:
                continue

        if curso_txt in vistos:
            continue
        vistos.add(curso_txt)
        cursos.append(curso_txt)

    return sorted(cursos)


def listar_estudiantes_activos_basico(grado=None, curso=None):
    """Retorna (documento, nombre, grado, curso) de estudiantes activos."""
    rows = (
        listar_estudiantes_por_grado(grado, curso=curso, solo_activos=True)
        if grado not in (None, "")
        else None
    )
    if rows is None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT documento, nombre, grado, curso
                FROM estudiantes
                WHERE estado_academico = 'Activo'
                ORDER BY grado, curso, nombre
                """
            )
            data = cur.fetchall()
    else:
        data = [
            (
                r.get("documento", ""),
                str(r.get("nombre") or "").strip() or construir_nombre(r),
                r.get("grado", ""),
                r.get("curso", ""),
            )
            for r in rows
        ]
        data.sort(key=lambda t: (str(t[2]), str(t[3]), str(t[1]).lower()))

    curso_ref = str(curso).strip().upper() if curso is not None else ""
    if curso_ref:
        data = [row for row in data if str(row[3] or "").strip().upper() == curso_ref]
    return data


def listar_sedes(solo_activos=False):
    """Lista sedes únicas de estudiantes."""
    with get_connection() as conn:
        cur = conn.cursor()
        if solo_activos:
            cur.execute(
                "SELECT DISTINCT sede FROM estudiantes WHERE estado_academico = 'Activo'"
            )
        else:
            cur.execute("SELECT DISTINCT sede FROM estudiantes")
        rows = cur.fetchall()

    sedes = []
    vistos = set()
    for row in rows:
        sede = str((row or [""])[0] or "").strip()
        key = sede.lower()
        if not sede or key in vistos:
            continue
        vistos.add(key)
        sedes.append(sede)
    return sorted(sedes, key=lambda x: x.lower())


def listar_jornadas(solo_activos=False):
    """Lista jornadas únicas de estudiantes."""
    with get_connection() as conn:
        cur = conn.cursor()
        if solo_activos:
            cur.execute(
                "SELECT DISTINCT jornada FROM estudiantes WHERE estado_academico = 'Activo'"
            )
        else:
            cur.execute("SELECT DISTINCT jornada FROM estudiantes")
        rows = cur.fetchall()

    jornadas = []
    vistos = set()
    for row in rows:
        jornada = str((row or [""])[0] or "").strip()
        key = jornada.lower()
        if not jornada or key in vistos:
            continue
        vistos.add(key)
        jornadas.append(jornada)
    return sorted(jornadas, key=lambda x: x.lower())


def listar_cursos_por_grado(grado=None, solo_activos=False):
    """Alias de compatibilidad para escritorio."""
    return listar_cursos_distintos(grado=grado, solo_activos=solo_activos)


def listar_estudiantes(
    sede=None,
    jornada=None,
    grado=None,
    curso=None,
    solo_activos=True,
):
    """Retorna estudiantes como tuplas para componentes de escritorio heredados.

    Formato: (id, codigo, apellido1, apellido2, nombre1, nombre2, documento)
    """
    filters = []
    params = []

    if solo_activos:
        filters.append("COALESCE(estado_academico, 'Activo') = 'Activo'")
    if str(sede or "").strip():
        filters.append("TRIM(COALESCE(sede, '')) = TRIM(?)")
        params.append(str(sede).strip())
    if str(jornada or "").strip():
        filters.append("LOWER(TRIM(COALESCE(jornada, ''))) = LOWER(TRIM(?))")
        params.append(str(jornada).strip())
    if grado not in (None, ""):
        filters.append("TRIM(CAST(grado AS TEXT)) = TRIM(CAST(? AS TEXT))")
        params.append(str(grado).strip())
    if str(curso or "").strip():
        filters.append("UPPER(TRIM(COALESCE(curso, ''))) = UPPER(TRIM(?))")
        params.append(str(curso).strip())

    where = f"WHERE {' AND '.join(filters)}" if filters else ""

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT id, codigo, apellido1, apellido2, nombre1, nombre2, documento
            FROM estudiantes
            {where}
            ORDER BY COALESCE(apellido1, '') COLLATE NOCASE,
                     COALESCE(apellido2, '') COLLATE NOCASE,
                     COALESCE(nombre1, '') COLLATE NOCASE,
                     COALESCE(nombre2, '') COLLATE NOCASE
            """,
            params,
        )
        return cur.fetchall()
