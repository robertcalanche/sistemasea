import pandas as pd

from . import get_connection


def _obtener_columnas_banco_preguntas(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(banco_preguntas)")
    return {str(row[1]).strip() for row in cur.fetchall() if row and len(row) > 1}


def _normalizar_pregunta_id(pregunta_id):
    txt = str(pregunta_id or "").strip()
    if not txt:
        return ""
    try:
        return str(int(float(txt)))
    except Exception:
        return txt


def _normalizar_payload_pregunta(datos, columnas_validas):
    payload = {}
    for clave, valor in (datos or {}).items():
        if clave in {"id_area"} or clave not in columnas_validas:
            continue
        if clave == "id":
            normalizado = _normalizar_pregunta_id(valor)
            if normalizado:
                payload[clave] = normalizado
            continue
        if valor is None:
            payload[clave] = None
            continue
        if isinstance(valor, str):
            payload[clave] = valor.strip()
            continue
        payload[clave] = valor
    return payload


def _asegurar_tabla_area_map(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS banco_preguntas_area_map (
            pregunta_id TEXT PRIMARY KEY,
            id_area INTEGER,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def guardar_area_id_pregunta(pregunta_id, id_area, conn=None):
    pregunta_id_norm = _normalizar_pregunta_id(pregunta_id)
    if not pregunta_id_norm or id_area in (None, ""):
        return

    def _guardar(conexion):
        _asegurar_tabla_area_map(conexion)
        conexion.execute(
            """
            INSERT INTO banco_preguntas_area_map (pregunta_id, id_area, fecha_actualizacion)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(pregunta_id) DO UPDATE SET
                id_area=excluded.id_area,
                fecha_actualizacion=CURRENT_TIMESTAMP
            """,
            (pregunta_id_norm, int(id_area)),
        )

    if conn is not None:
        _guardar(conn)
        return

    with get_connection() as conn_local:
        _guardar(conn_local)
        conn_local.commit()


def obtener_area_id_pregunta(pregunta_id):
    pregunta_id_norm = _normalizar_pregunta_id(pregunta_id)
    if not pregunta_id_norm:
        return None

    with get_connection() as conn:
        _asegurar_tabla_area_map(conn)
        cur = conn.cursor()
        cur.execute(
            "SELECT id_area FROM banco_preguntas_area_map WHERE pregunta_id=?",
            (pregunta_id_norm,),
        )
        row = cur.fetchone()
    if row and row[0] is not None:
        return int(row[0])
    return None


def eliminar_area_id_pregunta(pregunta_id, conn=None):
    pregunta_id_norm = _normalizar_pregunta_id(pregunta_id)
    if not pregunta_id_norm:
        return

    def _eliminar(conexion):
        _asegurar_tabla_area_map(conexion)
        conexion.execute(
            "DELETE FROM banco_preguntas_area_map WHERE pregunta_id=?",
            (pregunta_id_norm,),
        )

    if conn is not None:
        _eliminar(conn)
        return

    with get_connection() as conn_local:
        _eliminar(conn_local)
        conn_local.commit()


def asegurar_tabla_area_pregunta():
    with get_connection() as conn:
        _asegurar_tabla_area_map(conn)
        conn.commit()


def crear_pregunta_banco(**datos):
    id_area = datos.pop("id_area", None)
    with get_connection() as conn:
        columnas_validas = _obtener_columnas_banco_preguntas(conn)
        payload = _normalizar_payload_pregunta(datos, columnas_validas)
        if not payload:
            raise ValueError("No hay datos válidos para crear la pregunta.")

        columnas = list(payload.keys())
        placeholders = ", ".join(["?"] * len(columnas))
        sql = (
            f"INSERT INTO banco_preguntas ({', '.join(columnas)}) "
            f"VALUES ({placeholders})"
        )
        cur = conn.cursor()
        cur.execute(sql, [payload[c] for c in columnas])

        pregunta_id = payload.get("id") or _normalizar_pregunta_id(cur.lastrowid)
        if id_area not in (None, ""):
            guardar_area_id_pregunta(pregunta_id, id_area, conn=conn)
        conn.commit()
    return pregunta_id


def actualizar_pregunta_banco(pregunta_id, **datos):
    pregunta_id_actual = _normalizar_pregunta_id(pregunta_id)
    if not pregunta_id_actual:
        raise ValueError("El identificador de la pregunta es obligatorio.")

    id_area = datos.pop("id_area", None)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM banco_preguntas WHERE CAST(id AS TEXT)=? LIMIT 1",
            (pregunta_id_actual,),
        )
        if not cur.fetchone():
            return False

        columnas_validas = _obtener_columnas_banco_preguntas(conn)
        payload = _normalizar_payload_pregunta(datos, columnas_validas)
        nuevo_id = _normalizar_pregunta_id(payload.get("id", pregunta_id_actual))

        if nuevo_id != pregunta_id_actual:
            cur.execute(
                "SELECT 1 FROM banco_preguntas WHERE CAST(id AS TEXT)=? LIMIT 1",
                (nuevo_id,),
            )
            if cur.fetchone():
                raise ValueError(f"El id '{nuevo_id}' ya existe.")

        if payload:
            asignaciones = ", ".join(f"{columna} = ?" for columna in payload)
            cur.execute(
                f"UPDATE banco_preguntas SET {asignaciones} WHERE CAST(id AS TEXT)=?",
                [payload[columna] for columna in payload] + [pregunta_id_actual],
            )

        if nuevo_id != pregunta_id_actual:
            eliminar_area_id_pregunta(pregunta_id_actual, conn=conn)
        if id_area not in (None, ""):
            guardar_area_id_pregunta(nuevo_id, id_area, conn=conn)

        conn.commit()
    return True


def eliminar_preguntas_banco(grado=None, curso=None, area=None, evaluacion=None):
    filtros = []
    params = []

    if grado is not None:
        filtros.append("LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(?))")
        params.append(str(grado).strip())
    if curso is not None:
        filtros.append("LOWER(TRIM(CAST(curso AS TEXT))) = LOWER(TRIM(?))")
        params.append(str(curso).strip())
    if area is not None:
        filtros.append("LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(?))")
        params.append(str(area).strip())
    if evaluacion is not None:
        filtros.append("LOWER(TRIM(CAST(evaluacion AS TEXT))) = LOWER(TRIM(?))")
        params.append(str(evaluacion).strip())

    sql = "DELETE FROM banco_preguntas"
    if filtros:
        sql += " WHERE " + " AND ".join(filtros)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, tuple(params))
        eliminadas = cur.rowcount if cur.rowcount is not None else 0
        _asegurar_tabla_area_map(conn)
        conn.execute(
            """
            DELETE FROM banco_preguntas_area_map
            WHERE pregunta_id NOT IN (
                SELECT CAST(id AS TEXT) FROM banco_preguntas
            )
            """
        )
        conn.commit()
    return eliminadas


def vaciar_banco_preguntas():
    return eliminar_preguntas_banco()


def normalizar_grado(grado):
    if grado is None:
        return ""
    result = str(grado).strip().lower()
    result = result.replace("grado", "").strip()
    result = result.replace("°", "").strip()
    result = " ".join(result.split())
    return result


def cargar_preguntas():
    try:
        with get_connection() as conn:
            df = pd.read_sql_query(
                "SELECT * FROM banco_preguntas ORDER BY id DESC", conn
            )
        return df.sample(frac=1).reset_index(drop=True) if not df.empty else df
    except Exception:
        return pd.DataFrame()


def cargar_areas():
    try:
        with get_connection() as conn:
            df = pd.read_sql_query(
                "SELECT DISTINCT area FROM banco_preguntas WHERE area IS NOT NULL",
                conn,
            )
        if df.empty:
            return []
        return sorted(
            [
                str(a).strip().lower()
                for a in df["area"].dropna().unique()
                if a and str(a).strip().lower() not in {"none", "nan", ""}
            ]
        )
    except Exception:
        return []


def cargar_areas_por_grado(grado):
    try:
        grado_norm = normalizar_grado(grado)
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT DISTINCT area FROM banco_preguntas WHERE grado = ? AND area IS NOT NULL",
                (grado_norm,),
            )
            rows = cur.fetchall()
        return sorted(
            [
                str(r[0]).strip().lower()
                for r in rows
                if r and r[0] and str(r[0]).strip().lower() not in {"none", "nan", ""}
            ]
        )
    except Exception:
        return []


def cargar_evaluaciones_por_grado_y_area(grado, area):
    try:
        grado_norm = normalizar_grado(grado)
        area_norm = str(area).strip().lower() if area is not None else ""
        if not grado_norm or not area_norm:
            return []
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT DISTINCT evaluacion
                FROM banco_preguntas
                WHERE grado = ?
                  AND LOWER(TRIM(area)) = ?
                  AND evaluacion IS NOT NULL
                  AND TRIM(evaluacion) <> ''
                ORDER BY evaluacion
                """,
                (grado_norm, area_norm),
            )
            rows = cur.fetchall()
        return [
            r[0]
            for r in rows
            if r and r[0] and str(r[0]).strip().lower() not in {"none", "nan", ""}
        ]
    except Exception:
        return []


def cargar_grados_banco():
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT DISTINCT grado FROM banco_preguntas WHERE grado IS NOT NULL ORDER BY grado"
            )
            rows = cur.fetchall()
        return [r[0] for r in rows if r and r[0]]
    except Exception:
        return []


def listar_banco_preguntas(
    grado=None,
    area=None,
    evaluacion=None,
    curso=None,
    limit=50,
    offset=0,
):
    limit = max(1, min(200, int(limit)))
    offset = max(0, int(offset))

    with get_connection() as conn:
        filters = []
        params = []
        if grado:
            filters.append("grado = ?")
            params.append(grado)
        if area:
            filters.append("LOWER(TRIM(area)) = LOWER(TRIM(?))")
            params.append(area)
        if evaluacion:
            filters.append("LOWER(TRIM(evaluacion)) = LOWER(TRIM(?))")
            params.append(evaluacion)
        if curso:
            filters.append("LOWER(TRIM(curso)) = LOWER(TRIM(?))")
            params.append(curso)

        where = ("WHERE " + " AND ".join(filters)) if filters else ""
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM banco_preguntas {where}", params)
        total = int(cur.fetchone()[0])
        cur.execute(
            f"SELECT * FROM banco_preguntas {where} ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "preguntas": rows,
    }


def eliminar_pregunta_banco(pregunta_id):
    with get_connection() as conn:
        pregunta_id_norm = _normalizar_pregunta_id(pregunta_id)
        conn.execute(
            "DELETE FROM banco_preguntas WHERE CAST(id AS TEXT)=?",
            (pregunta_id_norm,),
        )
        eliminar_area_id_pregunta(pregunta_id_norm, conn=conn)
        conn.commit()


def obtener_pregunta_banco(pregunta_id):
    pregunta_id_norm = _normalizar_pregunta_id(pregunta_id)
    if not pregunta_id_norm:
        return None

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM banco_preguntas WHERE CAST(id AS TEXT)=? LIMIT 1",
            (pregunta_id_norm,),
        )
        row = cur.fetchone()
        if not row:
            return None
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))


def cargar_preguntas_filtradas(
    area=None, grado=None, evaluacion=None, curso=None, id_evaluacion=None
):
    try:
        with get_connection() as conn:
            # Si se proporciona id_evaluacion, priorizarlo
            if id_evaluacion is not None and str(id_evaluacion).strip():
                id_eval_norm = str(id_evaluacion).strip()
                df = pd.read_sql_query(
                    "SELECT * FROM banco_preguntas WHERE id_evaluacion = ?",
                    conn,
                    params=[id_eval_norm],
                )
                if "id_contexto" in df.columns and "id" in df.columns:
                    return df.sort_values(by=["id_contexto", "id"]).reset_index(
                        drop=True
                    )
                return df.reset_index(drop=True)

            # Lógica anterior (por evaluación)
            if evaluacion is not None and str(evaluacion).strip():
                evaluacion_norm = str(evaluacion).strip().lower()
                if evaluacion_norm not in {"none", "nan", ""}:
                    df = pd.read_sql_query(
                        "SELECT * FROM banco_preguntas WHERE evaluacion = ?",
                        conn,
                        params=[evaluacion_norm],
                    )
                    if "id_contexto" in df.columns and "id" in df.columns:
                        return df.sort_values(by=["id_contexto", "id"]).reset_index(
                            drop=True
                        )
                    return df.reset_index(drop=True)

            if area is None or grado is None:
                return pd.DataFrame()

            area_norm = str(area).strip().lower()
            grado_norm = normalizar_grado(grado)

            query = "SELECT * FROM banco_preguntas WHERE area = ? AND grado = ?"
            params = [area_norm, grado_norm]
            if curso and str(curso).strip().upper() != "TODOS":
                query += " AND curso = ?"
                params.append(str(curso).strip())

            df = pd.read_sql_query(query, conn, params=params)
            if "id_contexto" in df.columns and "id" in df.columns:
                return df.sort_values(by=["id_contexto", "id"]).reset_index(drop=True)
            return df.reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


# Utilidad para obtener el id_evaluacion único para los filtros dados
def obtener_id_evaluacion(grado, area, evaluacion, periodo=None):
    """Obtiene el id_evaluacion único para los filtros dados."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            query = """
                SELECT id_evaluacion FROM banco_preguntas
                WHERE grado = ? AND area = ? AND evaluacion = ?
            """
            params = [str(grado).strip(), str(area).strip(), str(evaluacion).strip()]
            if periodo is not None:
                query += " AND periodo = ?"
                params.append(str(periodo).strip())
            query += " LIMIT 1"
            cur.execute(query, params)
            row = cur.fetchone()
            if row and row[0]:
                return row[0]
    except Exception:
        pass
    return None
