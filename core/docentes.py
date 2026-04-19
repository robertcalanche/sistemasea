def cambiar_clave_docente(documento, clave_actual, clave_nueva):
    """
    Cambia la clave de un docente/personal si la clave actual es correcta.
    Retorna True si el cambio fue exitoso, False si la clave actual no coincide o el usuario no existe.
    """
    doc = _normalizar_documento(documento)
    if not doc or not clave_nueva:
        return False
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT clave FROM docentes WHERE documento = ? LIMIT 1", (doc,))
        row = cur.fetchone()
        if not row:
            return False
        clave_actual_db = str(row[0] or "")
        if str(clave_actual) != clave_actual_db:
            return False
        cur.execute(
            "UPDATE docentes SET clave = ? WHERE documento = ?", (str(clave_nueva), doc)
        )
        conn.commit()
        return True


from datetime import datetime

from . import get_connection


def _normalizar_documento(documento):
    txt = str(documento or "").strip()
    if not txt:
        return ""
    if txt.endswith(".0") and txt[:-2].isdigit():
        return txt[:-2]
    return txt


def listar_docentes(estado=None, cargo=None, limit=500, offset=0):
    limit = max(1, min(1000, int(limit)))
    offset = max(0, int(offset))

    filtros = []
    params = []

    if estado:
        filtros.append("LOWER(TRIM(estado)) = LOWER(TRIM(?))")
        params.append(str(estado).strip())
    if cargo:
        filtros.append("LOWER(TRIM(cargo)) = LOWER(TRIM(?))")
        params.append(str(cargo).strip())

    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM docentes {where}", params)
        total = int(cur.fetchone()[0])

        cur.execute(
            f"""
            SELECT
                tipo_documento, documento, nombre, sexo, fecha_nacimiento,
                telefono, correo, cargo, jornada, sede, estado
            FROM docentes
            {where}
            ORDER BY COALESCE(nombre, '') COLLATE NOCASE ASC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )
        cols = [d[0] for d in cur.description]
        docentes = [dict(zip(cols, row)) for row in cur.fetchall()]

    return {"total": total, "docentes": docentes}


def buscar_docente(documento):
    doc = _normalizar_documento(documento)
    if not doc:
        return None

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                tipo_documento, documento, nombre, sexo, fecha_nacimiento,
                telefono, correo, cargo, jornada, sede, estado, clave
            FROM docentes
            WHERE documento = ?
            LIMIT 1
            """,
            (doc,),
        )
        row = cur.fetchone()

    if not row:
        return None

    keys = [
        "tipo_documento",
        "documento",
        "nombre",
        "sexo",
        "fecha_nacimiento",
        "telefono",
        "correo",
        "cargo",
        "jornada",
        "sede",
        "estado",
        "clave",
    ]
    return dict(zip(keys, row))


def documento_docente_existe(documento, excluir_documento=None):
    doc = _normalizar_documento(documento)
    if not doc:
        return False

    excluir = _normalizar_documento(excluir_documento)
    with get_connection() as conn:
        cur = conn.cursor()
        if excluir:
            cur.execute(
                "SELECT 1 FROM docentes WHERE documento = ? AND documento <> ? LIMIT 1",
                (doc, excluir),
            )
        else:
            cur.execute("SELECT 1 FROM docentes WHERE documento = ? LIMIT 1", (doc,))
        row = cur.fetchone()
    return row is not None


def crear_o_actualizar_docente(
    tipo_documento,
    documento,
    nombre,
    sexo="",
    fecha_nacimiento="",
    telefono="",
    correo="",
    cargo="Docente",
    jornada="Mañana",
    sede="",
    estado="Activo",
    clave=None,
    documento_original=None,
):
    doc = _normalizar_documento(documento)
    doc_original = _normalizar_documento(documento_original)

    if not doc:
        raise ValueError("El documento es obligatorio.")
    if not str(doc).isdigit():
        raise ValueError("El documento solo debe contener números.")
    if not str(nombre or "").strip():
        raise ValueError("El nombre es obligatorio.")

    with get_connection() as conn:
        cur = conn.cursor()

        # Si no se especifica clave, usar el documento como clave por defecto
        clave_final = str(clave) if clave is not None else str(doc)

        if doc_original:
            cur.execute(
                "SELECT 1 FROM docentes WHERE documento = ? LIMIT 1", (doc_original,)
            )
            existe_original = cur.fetchone() is not None
            if not existe_original:
                return False

            cur.execute(
                "SELECT 1 FROM docentes WHERE documento = ? AND documento <> ? LIMIT 1",
                (doc, doc_original),
            )
            if cur.fetchone():
                raise ValueError("El documento ya está registrado")

            cur.execute(
                """
                UPDATE docentes
                SET
                    tipo_documento = ?,
                    documento = ?,
                    nombre = ?,
                    sexo = ?,
                    fecha_nacimiento = ?,
                    telefono = ?,
                    correo = ?,
                    cargo = ?,
                    jornada = ?,
                    sede = ?,
                    estado = ?,
                    clave = ?
                WHERE documento = ?
                """,
                (
                    str(tipo_documento or "CC").strip(),
                    doc,
                    str(nombre).strip(),
                    str(sexo or "").strip(),
                    str(fecha_nacimiento or "").strip(),
                    str(telefono or "").strip(),
                    str(correo or "").strip(),
                    str(cargo or "Docente").strip(),
                    str(jornada or "Mañana").strip(),
                    str(sede or "").strip(),
                    str(estado or "Activo").strip(),
                    clave_final,
                    doc_original,
                ),
            )
            conn.commit()
            return True

        cur.execute("SELECT 1 FROM docentes WHERE documento = ? LIMIT 1", (doc,))
        existe = cur.fetchone() is not None
        if existe:
            raise ValueError("El documento ya está registrado")

        cur.execute(
            """
            INSERT INTO docentes (
                tipo_documento, documento, nombre, sexo, fecha_nacimiento,
                telefono, correo, cargo, jornada, sede, estado, clave
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(tipo_documento or "CC").strip(),
                doc,
                str(nombre).strip(),
                str(sexo or "").strip(),
                str(fecha_nacimiento or "").strip(),
                str(telefono or "").strip(),
                str(correo or "").strip(),
                str(cargo or "Docente").strip(),
                str(jornada or "Mañana").strip(),
                str(sede or "").strip(),
                str(estado or "Activo").strip(),
                clave_final,
            ),
        )
        conn.commit()
        return True


def eliminar_docente(documento):
    doc = _normalizar_documento(documento)
    if not doc:
        raise ValueError("Documento inválido")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM docentes WHERE documento = ?", (doc,))
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0


def listar_docentes_selector(solo_activos=False):
    filtros = []
    params = []

    if solo_activos:
        filtros.append("LOWER(TRIM(COALESCE(estado, 'Activo'))) = 'activo'")

    where = ("WHERE " + " AND ".join(filtros)) if filtros else ""

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT documento, nombre
            FROM docentes
            {where}
            ORDER BY COALESCE(nombre, '') COLLATE NOCASE ASC
            """,
            params,
        )
        return cur.fetchall()


def listar_docentes_exportacion():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT tipo_documento, documento, nombre, sexo, fecha_nacimiento,
                   telefono, correo, cargo, jornada, sede, estado, fecha_registro
            FROM docentes
            ORDER BY COALESCE(nombre, '') COLLATE NOCASE ASC
            """
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def asegurar_esquema_carga_academica():
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS docente_horas_config (
                docente_documento TEXT PRIMARY KEY,
                horas_normales_max INTEGER NOT NULL DEFAULT 22,
                horas_extras_max INTEGER NOT NULL DEFAULT 0,
                fecha_actualizacion TEXT
            )
            """
        )

        cur.execute("PRAGMA table_info(carga_academica)")
        cols = [str(r[1]).strip().lower() for r in cur.fetchall() if r]
        if "horas_asignadas" not in cols:
            cur.execute(
                "ALTER TABLE carga_academica ADD COLUMN horas_asignadas INTEGER DEFAULT 0"
            )
        if "horas_extras_usadas" not in cols:
            cur.execute(
                "ALTER TABLE carga_academica ADD COLUMN horas_extras_usadas INTEGER DEFAULT 0"
            )
        if "director_grupo_documento" not in cols:
            cur.execute(
                "ALTER TABLE carga_academica ADD COLUMN director_grupo_documento TEXT"
            )

        conn.commit()
        return True


def obtener_limites_docente(docente_documento):
    asegurar_esquema_carga_academica()

    doc = _normalizar_documento(docente_documento)
    if not doc:
        return (22, 0, False)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COALESCE(horas_normales_max, 22), COALESCE(horas_extras_max, 0)
            FROM docente_horas_config
            WHERE TRIM(CAST(docente_documento AS TEXT)) = TRIM(CAST(? AS TEXT))
            LIMIT 1
            """,
            (doc,),
        )
        row = cur.fetchone()

    if not row:
        return (22, 0, False)

    normales = max(0, int(row[0] or 0))
    extras = max(0, int(row[1] or 0))
    return (normales, extras, True)


def guardar_limites_docente(
    docente_documento, horas_normales_max, horas_extras_max, fecha_actualizacion=None
):
    asegurar_esquema_carga_academica()

    doc = _normalizar_documento(docente_documento)
    if not doc:
        raise ValueError("Seleccione un docente válido.")

    horas_normales = int(horas_normales_max)
    horas_extras = int(horas_extras_max)
    if horas_normales < 0 or horas_extras < 0:
        raise ValueError("Las horas no pueden ser negativas.")

    marca_tiempo = str(fecha_actualizacion or "").strip() or datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO docente_horas_config (
                docente_documento, horas_normales_max, horas_extras_max, fecha_actualizacion
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(docente_documento) DO UPDATE SET
                horas_normales_max = excluded.horas_normales_max,
                horas_extras_max = excluded.horas_extras_max,
                fecha_actualizacion = excluded.fecha_actualizacion
            """,
            (doc, horas_normales, horas_extras, marca_tiempo),
        )
        conn.commit()
        return True


def horas_totales_docente(docente_documento, excluir_id=None, excluir_ids=None):
    asegurar_esquema_carga_academica()

    doc = _normalizar_documento(docente_documento)
    if not doc:
        return 0

    query = [
        """
        SELECT COALESCE(SUM(COALESCE(horas_asignadas, 0)), 0)
        FROM carga_academica
        WHERE TRIM(CAST(docente_documento AS TEXT)) = TRIM(CAST(? AS TEXT))
          AND LOWER(TRIM(COALESCE(estado, 'Activo'))) = 'activo'
        """
    ]
    params = [doc]

    if excluir_id is not None:
        query.append(" AND id <> ?")
        params.append(int(excluir_id))

    ids_excluir = [int(valor) for valor in (excluir_ids or []) if valor is not None]
    if ids_excluir:
        marcadores = ", ".join("?" for _ in ids_excluir)
        query.append(f" AND id NOT IN ({marcadores})")
        params.extend(ids_excluir)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("".join(query), params)
        row = cur.fetchone()

    return int((row[0] if row else 0) or 0)


def listar_carga_academica(
    docente_documento=None,
    area=None,
    grado=None,
    curso=None,
    anio_lectivo=None,
):
    asegurar_esquema_carga_academica()

    query = [
        """
        SELECT ca.id,
               ca.docente_documento,
               COALESCE(d.nombre, '') AS docente_nombre,
             ca.director_grupo_documento,
             COALESCE(dd.nombre, '') AS director_grupo_nombre,
               ca.area,
               ca.grado,
               ca.curso,
               COALESCE(ca.horas_asignadas, 0) AS horas_asignadas,
               COALESCE(ca.horas_extras_usadas, 0) AS horas_extras_usadas,
               ca.anio_lectivo,
               ca.estado
        FROM carga_academica ca
        LEFT JOIN docentes d ON d.documento = ca.docente_documento
        LEFT JOIN docentes dd ON dd.documento = ca.director_grupo_documento
        WHERE 1=1
        """
    ]
    params = []

    doc = _normalizar_documento(docente_documento)
    if doc:
        query.append(
            " AND TRIM(CAST(ca.docente_documento AS TEXT)) = TRIM(CAST(? AS TEXT))"
        )
        params.append(doc)

    if str(area or "").strip():
        query.append(
            " AND LOWER(TRIM(CAST(ca.area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))"
        )
        params.append(str(area).strip())

    if str(grado or "").strip():
        query.append(
            " AND LOWER(TRIM(CAST(ca.grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))"
        )
        params.append(str(grado).strip())

    if str(curso or "").strip():
        query.append(
            " AND LOWER(TRIM(CAST(ca.curso AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))"
        )
        params.append(str(curso).strip())

    if str(anio_lectivo or "").strip():
        query.append(
            " AND LOWER(TRIM(CAST(ca.anio_lectivo AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))"
        )
        params.append(str(anio_lectivo).strip())

    query.append(
        " ORDER BY COALESCE(d.nombre, '') COLLATE NOCASE ASC, ca.area, ca.grado, ca.curso"
    )

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("".join(query), params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def obtener_carga_academica(carga_id):
    asegurar_esquema_carga_academica()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
                 SELECT id, docente_documento, director_grupo_documento, area, grado, curso,
                   COALESCE(horas_asignadas, 0) AS horas_asignadas,
                   COALESCE(horas_extras_usadas, 0) AS horas_extras_usadas,
                   anio_lectivo, estado
            FROM carga_academica
            WHERE id = ?
            LIMIT 1
            """,
            (int(carga_id),),
        )
        row = cur.fetchone()

    if not row:
        return None

    keys = [
        "id",
        "docente_documento",
        "director_grupo_documento",
        "area",
        "grado",
        "curso",
        "horas_asignadas",
        "horas_extras_usadas",
        "anio_lectivo",
        "estado",
    ]
    return dict(zip(keys, row))


def carga_academica_duplicada(
    docente_documento, area, grado, curso, excluir_id=None, excluir_ids=None
):
    asegurar_esquema_carga_academica()

    params = [
        _normalizar_documento(docente_documento),
        str(area or "").strip(),
        str(grado or "").strip(),
        str(curso or "").strip(),
    ]
    query = [
        """
        SELECT 1
        FROM carga_academica
        WHERE LOWER(TRIM(CAST(docente_documento AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
          AND LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
          AND LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
          AND LOWER(TRIM(CAST(curso AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
        """
    ]
    if excluir_id is not None:
        query.append(" AND id <> ?")
        params.append(int(excluir_id))
    ids_excluir = [int(valor) for valor in (excluir_ids or []) if valor is not None]
    if ids_excluir:
        marcadores = ", ".join("?" for _ in ids_excluir)
        query.append(f" AND id NOT IN ({marcadores})")
        params.extend(ids_excluir)
    query.append(" LIMIT 1")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("".join(query), params)
        return cur.fetchone() is not None


def preparar_carga_academica(
    docente_documento,
    area,
    grado,
    curso,
    horas_asignadas,
    anio_lectivo,
    estado="Activo",
    director_grupo_documento=None,
    excluir_id=None,
    excluir_ids=None,
    acumulado_previo=0,
):
    asegurar_esquema_carga_academica()

    doc = _normalizar_documento(docente_documento)
    area_txt = str(area or "").strip()
    grado_txt = str(grado or "").strip()
    curso_txt = str(curso or "").strip()
    anio_txt = str(anio_lectivo or "").strip()
    estado_txt = str(estado or "Activo").strip() or "Activo"
    director_txt = _normalizar_documento(director_grupo_documento)

    if not doc:
        raise ValueError("El documento del docente es obligatorio.")
    if not area_txt:
        raise ValueError("El área es obligatoria.")
    if not grado_txt:
        raise ValueError("El grado es obligatorio.")
    if not curso_txt:
        raise ValueError("El curso es obligatorio.")
    if not anio_txt:
        raise ValueError("El año lectivo es obligatorio.")

    horas = int(horas_asignadas or 0)
    if horas <= 0:
        raise ValueError("Las horas asignadas deben ser mayores a cero.")

    if carga_academica_duplicada(
        doc,
        area_txt,
        grado_txt,
        curso_txt,
        excluir_id=excluir_id,
        excluir_ids=excluir_ids,
    ):
        raise ValueError(
            "Ya existe una carga académica con ese docente, área, grado y curso."
        )

    normales_max, extras_max, _cfg = obtener_limites_docente(doc)
    limite_total = max(0, normales_max) + max(0, extras_max)
    horas_base = horas_totales_docente(
        doc, excluir_id=excluir_id, excluir_ids=excluir_ids
    )
    horas_antes = horas_base + max(0, int(acumulado_previo or 0))
    horas_despues = horas_antes + horas

    if horas_despues > limite_total:
        raise ValueError(
            "No es posible asignar más horas. El docente supera el límite máximo permitido."
        )

    extras_antes = max(0, horas_antes - normales_max)
    extras_despues = max(0, horas_despues - normales_max)
    horas_extras_registro = max(0, extras_despues - extras_antes)

    return {
        "docente_documento": doc,
        "area": area_txt,
        "grado": grado_txt,
        "curso": curso_txt,
        "horas_asignadas": horas,
        "horas_extras_usadas": horas_extras_registro,
        "anio_lectivo": anio_txt,
        "estado": estado_txt,
        "director_grupo_documento": director_txt,
        "usa_horas_extras": horas_extras_registro > 0,
    }


def preparar_cargas_academicas(items):
    asegurar_esquema_carga_academica()

    registros = list(items or [])
    if not registros:
        raise ValueError("No se recibieron registros de carga académica.")

    acumulado_por_docente = {}
    preparados = []
    usa_horas_extras = False

    for item in registros:
        doc = _normalizar_documento(item.get("docente_documento"))
        preparado = preparar_carga_academica(
            docente_documento=doc,
            area=item.get("area"),
            grado=item.get("grado"),
            curso=item.get("curso"),
            horas_asignadas=item.get("horas_asignadas"),
            anio_lectivo=item.get("anio_lectivo"),
            estado=item.get("estado", "Activo"),
            director_grupo_documento=item.get("director_grupo_documento"),
            acumulado_previo=acumulado_por_docente.get(doc, 0),
        )
        acumulado_por_docente[doc] = acumulado_por_docente.get(doc, 0) + int(
            preparado["horas_asignadas"]
        )
        usa_horas_extras = usa_horas_extras or bool(preparado["usa_horas_extras"])
        preparados.append(preparado)

    return {"items": preparados, "usa_horas_extras": usa_horas_extras}


def crear_cargas_academicas(items):
    asegurar_esquema_carga_academica()

    registros = list(items or [])
    if not registros:
        return 0

    with get_connection() as conn:
        cur = conn.cursor()
        for item in registros:
            cur.execute(
                """
                INSERT INTO carga_academica (
                    docente_documento, area, grado, curso,
                    horas_asignadas, horas_extras_usadas,
                    anio_lectivo, estado, director_grupo_documento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _normalizar_documento(item.get("docente_documento")),
                    str(item.get("area") or "").strip(),
                    str(item.get("grado") or "").strip(),
                    str(item.get("curso") or "").strip(),
                    int(item.get("horas_asignadas") or 0),
                    int(item.get("horas_extras_usadas") or 0),
                    str(item.get("anio_lectivo") or "").strip(),
                    str(item.get("estado") or "Activo").strip(),
                    _normalizar_documento(item.get("director_grupo_documento")),
                ),
            )
        conn.commit()
        return len(registros)


def obtener_cargas_academicas_grupo(grado, curso, anio_lectivo=None):
    return listar_carga_academica(
        grado=str(grado or "").strip(),
        curso=str(curso or "").strip(),
        anio_lectivo=str(anio_lectivo or "").strip() or None,
    )


def reemplazar_cargas_academicas_grupo(grado, curso, anio_lectivo, items):
    asegurar_esquema_carga_academica()

    grado_txt = str(grado or "").strip()
    curso_txt = str(curso or "").strip()
    anio_txt = str(anio_lectivo or "").strip()
    registros = list(items or [])

    if not grado_txt:
        raise ValueError("El grado es obligatorio.")
    if not curso_txt:
        raise ValueError("El curso es obligatorio.")
    if not anio_txt:
        raise ValueError("El año lectivo es obligatorio.")
    if not registros:
        raise ValueError("No se recibieron registros de carga académica.")

    existentes = obtener_cargas_academicas_grupo(grado_txt, curso_txt, anio_txt)
    ids_existentes = [
        int(row.get("id")) for row in existentes if row.get("id") is not None
    ]

    acumulado_por_docente = {}
    preparados = []
    usa_horas_extras = False

    for item in registros:
        doc = _normalizar_documento(item.get("docente_documento"))
        preparado = preparar_carga_academica(
            docente_documento=doc,
            area=item.get("area"),
            grado=grado_txt,
            curso=curso_txt,
            horas_asignadas=item.get("horas_asignadas"),
            anio_lectivo=anio_txt,
            estado=item.get("estado", "Activo"),
            director_grupo_documento=item.get("director_grupo_documento"),
            excluir_ids=ids_existentes,
            acumulado_previo=acumulado_por_docente.get(doc, 0),
        )
        acumulado_por_docente[doc] = acumulado_por_docente.get(doc, 0) + int(
            preparado["horas_asignadas"]
        )
        usa_horas_extras = usa_horas_extras or bool(preparado["usa_horas_extras"])
        preparados.append(preparado)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM carga_academica
            WHERE LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
              AND LOWER(TRIM(CAST(curso AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
              AND LOWER(TRIM(CAST(anio_lectivo AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
            """,
            (grado_txt, curso_txt, anio_txt),
        )
        for item in preparados:
            cur.execute(
                """
                INSERT INTO carga_academica (
                    docente_documento, area, grado, curso,
                    horas_asignadas, horas_extras_usadas,
                    anio_lectivo, estado, director_grupo_documento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _normalizar_documento(item.get("docente_documento")),
                    str(item.get("area") or "").strip(),
                    grado_txt,
                    curso_txt,
                    int(item.get("horas_asignadas") or 0),
                    int(item.get("horas_extras_usadas") or 0),
                    anio_txt,
                    str(item.get("estado") or "Activo").strip(),
                    _normalizar_documento(item.get("director_grupo_documento")),
                ),
            )
        conn.commit()

    return {
        "guardadas": len(preparados),
        "reemplazadas": len(existentes),
        "usa_horas_extras": usa_horas_extras,
        "items": preparados,
    }


def actualizar_carga_academica(
    carga_id,
    docente_documento,
    area,
    grado,
    curso,
    horas_asignadas,
    horas_extras_usadas,
    anio_lectivo,
    estado,
    director_grupo_documento=None,
):
    asegurar_esquema_carga_academica()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE carga_academica
            SET docente_documento = ?,
                area = ?,
                grado = ?,
                curso = ?,
                horas_asignadas = ?,
                horas_extras_usadas = ?,
                anio_lectivo = ?,
                estado = ?,
                director_grupo_documento = ?
            WHERE id = ?
            """,
            (
                _normalizar_documento(docente_documento),
                str(area or "").strip(),
                str(grado or "").strip(),
                str(curso or "").strip(),
                int(horas_asignadas or 0),
                int(horas_extras_usadas or 0),
                str(anio_lectivo or "").strip(),
                str(estado or "Activo").strip(),
                _normalizar_documento(director_grupo_documento),
                int(carga_id),
            ),
        )
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0


def actualizar_director_grupo(grado, curso, anio_lectivo, director_grupo_documento):
    asegurar_esquema_carga_academica()

    grado_txt = str(grado or "").strip()
    curso_txt = str(curso or "").strip()
    anio_txt = str(anio_lectivo or "").strip()

    if not grado_txt or not curso_txt or not anio_txt:
        return 0

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE carga_academica
            SET director_grupo_documento = ?
            WHERE LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
              AND LOWER(TRIM(CAST(curso AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
              AND LOWER(TRIM(CAST(anio_lectivo AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
            """,
            (
                _normalizar_documento(director_grupo_documento),
                grado_txt,
                curso_txt,
                anio_txt,
            ),
        )
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0


def eliminar_carga_academica(carga_id):
    asegurar_esquema_carga_academica()

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM carga_academica WHERE id = ?", (int(carga_id),))
        conn.commit()
        return cur.rowcount if cur.rowcount is not None else 0
