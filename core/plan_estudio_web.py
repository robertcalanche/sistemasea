from __future__ import annotations

import re
from io import BytesIO

import pandas as pd

from . import get_connection


def _norm(txt):
    return str(txt or "").strip()


def _norm_upper(txt):
    return _norm(txt).upper()


def _normalizar_grado(valor):
    raw = _norm_upper(valor)
    if not raw:
        raise ValueError("grado_requerido")
    if raw in {"JA", "JARDIN", "JARDIN"}:
        return "JA"
    if raw in {"PREJ", "PREJARDIN", "PREJARDIN"}:
        return "PREJ"
    if raw in {"0", "TRANSICION", "TRANSICION PREESCOLAR"}:
        return "0"
    if re.fullmatch(r"C[1-6]", raw):
        return raw
    if re.fullmatch(r"\d+", raw):
        return str(int(raw))
    raise ValueError("grado_invalido")


def _normalizar_curso(valor):
    raw = _norm_upper(valor)
    if not raw:
        raise ValueError("curso_requerido")
    if re.fullmatch(r"C[1-6]", raw):
        return raw
    if re.fullmatch(r"\d+", raw):
        return str(int(raw))
    raise ValueError("curso_invalido")


def _ensure_tables():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS plan_estudio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nivel TEXT,
                grado TEXT,
                curso TEXT,
                area TEXT,
                horas INTEGER,
                estado INTEGER DEFAULT 1
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE,
                estado INTEGER DEFAULT 1
            )
            """
        )

        cur.execute("PRAGMA table_info(plan_estudio)")
        cols_plan = {str(r[1]).lower() for r in cur.fetchall()}
        if "idarea" not in cols_plan:
            cur.execute("ALTER TABLE plan_estudio ADD COLUMN IdArea INTEGER")

        cur.execute(
            """
            UPDATE plan_estudio
            SET IdArea = (
                SELECT a.id
                FROM areas a
                WHERE LOWER(TRIM(COALESCE(a.nombre, ''))) =
                      LOWER(TRIM(COALESCE(plan_estudio.area, '')))
                LIMIT 1
            )
            WHERE (IdArea IS NULL OR TRIM(CAST(IdArea AS TEXT)) = '')
              AND area IS NOT NULL
              AND TRIM(COALESCE(area, '')) <> ''
            """
        )

        try:
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_plan_estudio_unica_idarea
                ON plan_estudio (grado, curso, IdArea)
                """
            )
        except Exception:
            pass

        conn.commit()


def listar_areas(only_active=True):
    _ensure_tables()
    with get_connection() as conn:
        cur = conn.cursor()
        sql = "SELECT id, nombre, estado FROM areas"
        if only_active:
            sql += " WHERE estado=1"
        sql += " ORDER BY nombre"
        cur.execute(sql)
        return [
            {"id": int(r[0]), "nombre": _norm(r[1]), "estado": int(r[2] or 0)}
            for r in cur.fetchall()
            if r and _norm(r[1])
        ]


def catalogos_plan_estudio():
    _ensure_tables()
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            "SELECT DISTINCT nivel FROM plan_estudio WHERE TRIM(COALESCE(nivel,''))<>'' ORDER BY nivel"
        )
        niveles = [_norm(r[0]) for r in cur.fetchall() if r and _norm(r[0])]

        cur.execute(
            "SELECT DISTINCT grado FROM plan_estudio WHERE TRIM(CAST(COALESCE(grado,'') AS TEXT))<>'' ORDER BY grado"
        )
        grados = [_norm(r[0]) for r in cur.fetchall() if r and _norm(r[0])]

        cur.execute(
            "SELECT DISTINCT curso FROM plan_estudio WHERE TRIM(CAST(COALESCE(curso,'') AS TEXT))<>'' ORDER BY curso"
        )
        cursos = [_norm(r[0]) for r in cur.fetchall() if r and _norm(r[0])]

    return {
        "niveles": niveles,
        "grados": grados,
        "cursos": cursos,
        "areas": listar_areas(only_active=True),
    }


def listar_plan_estudio(
    nivel=None,
    grado=None,
    curso=None,
    area=None,
    limit=200,
    offset=0,
):
    _ensure_tables()
    limit = max(1, min(500, int(limit)))
    offset = max(0, int(offset))

    conditions = ["1=1"]
    params = []

    if _norm(nivel):
        conditions.append(
            "LOWER(TRIM(COALESCE(p.nivel,''))) = LOWER(TRIM(COALESCE(?,'')))"
        )
        params.append(_norm(nivel))
    if _norm(grado):
        conditions.append(
            "TRIM(CAST(COALESCE(p.grado,'') AS TEXT)) = TRIM(CAST(COALESCE(?,'') AS TEXT))"
        )
        params.append(_norm(grado))
    if _norm(curso):
        conditions.append(
            "UPPER(TRIM(CAST(COALESCE(p.curso,'') AS TEXT))) = UPPER(TRIM(CAST(COALESCE(?,'') AS TEXT)))"
        )
        params.append(_norm(curso))
    if _norm(area):
        conditions.append("LOWER(TRIM(COALESCE(a.nombre, p.area, ''))) LIKE ?")
        params.append(f"%{_norm(area).lower()}%")

    where = " WHERE " + " AND ".join(conditions)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT COUNT(*)
            FROM plan_estudio p
            LEFT JOIN areas a ON a.id = p.IdArea
            {where}
            """,
            params,
        )
        total = int(cur.fetchone()[0])

        cur.execute(
            f"""
            SELECT p.id, p.nivel, p.grado, p.curso,
                   COALESCE(a.nombre, p.area) AS area,
                   p.horas, p.estado, p.IdArea
            FROM plan_estudio p
            LEFT JOIN areas a ON a.id = p.IdArea
            {where}
            ORDER BY p.grado, p.curso, COALESCE(a.nombre, p.area)
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )

        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    for row in rows:
        row["id"] = int(row.get("id") or 0)
        row["horas"] = int(row.get("horas") or 0)
        row["estado"] = int(row.get("estado") or 0)
        if row.get("IdArea") is not None:
            try:
                row["IdArea"] = int(row.get("IdArea"))
            except Exception:
                row["IdArea"] = None

    return {"total": total, "items": rows}


def _resolver_area(cur, area_id=None, area_nombre=None):
    if area_id is not None and str(area_id).strip() != "":
        cur.execute(
            "SELECT id, nombre FROM areas WHERE id=? AND estado=1 LIMIT 1",
            (int(area_id),),
        )
        row = cur.fetchone()
        if row:
            return int(row[0]), _norm(row[1])

    nombre = _norm(area_nombre)
    if not nombre:
        raise ValueError("area_requerida")

    cur.execute(
        "SELECT id, nombre FROM areas WHERE LOWER(TRIM(nombre))=LOWER(TRIM(?)) LIMIT 1",
        (nombre,),
    )
    row = cur.fetchone()
    if not row:
        raise ValueError("area_no_encontrada")
    return int(row[0]), _norm(row[1])


def crear_registro(payload):
    _ensure_tables()
    data = dict(payload or {})

    nivel = _norm(data.get("nivel"))
    grado = _normalizar_grado(data.get("grado"))
    curso = _normalizar_curso(data.get("curso"))

    try:
        horas = int(float(data.get("horas") or 0))
    except Exception as exc:
        raise ValueError("horas_invalidas") from exc

    with get_connection() as conn:
        cur = conn.cursor()
        area_id, area_nombre = _resolver_area(
            cur,
            area_id=data.get("IdArea"),
            area_nombre=data.get("area"),
        )

        cur.execute(
            """
            SELECT id FROM plan_estudio
            WHERE grado=? AND curso=? AND CAST(COALESCE(IdArea,'') AS TEXT)=CAST(? AS TEXT)
            LIMIT 1
            """,
            (grado, curso, area_id),
        )
        if cur.fetchone():
            raise ValueError("registro_duplicado")

        cur.execute(
            """
            INSERT INTO plan_estudio (nivel, grado, curso, IdArea, area, horas, estado)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (nivel, grado, curso, area_id, area_nombre, horas),
        )
        new_id = int(cur.lastrowid)
        conn.commit()

    return new_id


def actualizar_registro(registro_id, payload):
    _ensure_tables()
    rid = int(registro_id)
    data = dict(payload or {})

    nivel = _norm(data.get("nivel"))
    grado = _normalizar_grado(data.get("grado"))
    curso = _normalizar_curso(data.get("curso"))

    try:
        horas = int(float(data.get("horas") or 0))
    except Exception as exc:
        raise ValueError("horas_invalidas") from exc

    with get_connection() as conn:
        cur = conn.cursor()
        area_id, area_nombre = _resolver_area(
            cur,
            area_id=data.get("IdArea"),
            area_nombre=data.get("area"),
        )

        cur.execute("SELECT id FROM plan_estudio WHERE id=? LIMIT 1", (rid,))
        if not cur.fetchone():
            raise ValueError("registro_no_encontrado")

        cur.execute(
            """
            SELECT id FROM plan_estudio
            WHERE grado=? AND curso=? AND CAST(COALESCE(IdArea,'') AS TEXT)=CAST(? AS TEXT)
              AND id<>?
            LIMIT 1
            """,
            (grado, curso, area_id, rid),
        )
        if cur.fetchone():
            raise ValueError("registro_duplicado")

        cur.execute(
            """
            UPDATE plan_estudio
            SET nivel=?, grado=?, curso=?, IdArea=?, area=?, horas=?
            WHERE id=?
            """,
            (nivel, grado, curso, area_id, area_nombre, horas, rid),
        )
        conn.commit()


def eliminar_registro(registro_id):
    _ensure_tables()
    rid = int(registro_id)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM plan_estudio WHERE id=?", (rid,))
        deleted = int(cur.rowcount or 0)
        conn.commit()
    return deleted


def copiar_plan(
    origen_grado, origen_curso, destino_grado, destino_curso, reemplazar=False
):
    _ensure_tables()
    g_origen = _normalizar_grado(origen_grado)
    c_origen = _normalizar_curso(origen_curso)
    g_destino = _normalizar_grado(destino_grado)
    c_destino = _normalizar_curso(destino_curso)

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT nivel, area, IdArea, horas
            FROM plan_estudio
            WHERE grado=? AND curso=?
            ORDER BY area
            """,
            (g_origen, c_origen),
        )
        origen_rows = cur.fetchall()
        if not origen_rows:
            raise ValueError("origen_sin_registros")

        cur.execute(
            "SELECT COUNT(*) FROM plan_estudio WHERE grado=? AND curso=?",
            (g_destino, c_destino),
        )
        destino_count = int(cur.fetchone()[0] or 0)

        if destino_count > 0 and not bool(reemplazar):
            raise ValueError("destino_tiene_registros")

        if destino_count > 0 and bool(reemplazar):
            cur.execute(
                "DELETE FROM plan_estudio WHERE grado=? AND curso=?",
                (g_destino, c_destino),
            )

        insertados = 0
        for nivel, area, id_area, horas in origen_rows:
            id_area_val = id_area
            if id_area_val is None and _norm(area):
                cur.execute(
                    "SELECT id FROM areas WHERE LOWER(TRIM(nombre))=LOWER(TRIM(?)) LIMIT 1",
                    (_norm(area),),
                )
                found = cur.fetchone()
                if found:
                    id_area_val = int(found[0])

            cur.execute(
                """
                INSERT INTO plan_estudio (nivel, grado, curso, IdArea, area, horas)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    _norm(nivel),
                    g_destino,
                    c_destino,
                    id_area_val,
                    _norm(area),
                    int(horas or 0),
                ),
            )
            insertados += 1

        conn.commit()

    return {
        "insertados": insertados,
        "destino_previo": destino_count,
        "origen": {"grado": g_origen, "curso": c_origen},
        "destino": {"grado": g_destino, "curso": c_destino},
    }


def importar_plan_estudio_desde_archivo(filename, raw_bytes):
    _ensure_tables()
    nombre = _norm(filename).lower()
    if not nombre:
        raise ValueError("archivo_invalido")

    if nombre.endswith(".csv"):
        df = pd.read_csv(BytesIO(raw_bytes))
    elif nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        df = pd.read_excel(BytesIO(raw_bytes))
    else:
        raise ValueError("formato_no_soportado")

    if df is None or df.empty:
        raise ValueError("archivo_vacio")

    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    alias = {
        "nivel": ["nivel", "level"],
        "curso": ["curso", "course", "grado_curso"],
        "idarea": ["idarea", "id_area", "idarea_", "id_area_"],
        "horas": ["horas", "hours", "intensidad", "intensidad_horaria"],
    }

    def _pick(row, keys):
        for k in keys:
            if k in row and row[k] is not None and str(row[k]).strip() != "":
                return row[k]
        return None

    inserted = 0
    skipped = 0

    with get_connection() as conn:
        cur = conn.cursor()
        for _, raw in df.fillna("").iterrows():
            row = raw.to_dict()
            nivel = _norm(_pick(row, alias["nivel"]))
            curso_compuesto = _norm(_pick(row, alias["curso"]))
            idarea_raw = _pick(row, alias["idarea"])
            horas_raw = _pick(row, alias["horas"]) or 0

            if not curso_compuesto or idarea_raw in (None, ""):
                skipped += 1
                continue

            curso_text = _norm_upper(curso_compuesto)
            if "-" not in curso_text:
                skipped += 1
                continue

            grado_txt, curso_txt = curso_text.split("-", 1)
            try:
                grado = _normalizar_grado(grado_txt)
                curso = _normalizar_curso(curso_txt)
                id_area = int(str(idarea_raw).strip())
                horas = int(float(horas_raw)) if str(horas_raw).strip() else 0
            except Exception:
                skipped += 1
                continue

            cur.execute("SELECT nombre FROM areas WHERE id=? AND estado=1", (id_area,))
            row_area = cur.fetchone()
            if not row_area:
                skipped += 1
                continue
            area_nombre = _norm(row_area[0])

            cur.execute(
                """
                SELECT id FROM plan_estudio
                WHERE grado=? AND curso=? AND CAST(COALESCE(IdArea,'') AS TEXT)=CAST(? AS TEXT)
                LIMIT 1
                """,
                (grado, curso, id_area),
            )
            if cur.fetchone():
                skipped += 1
                continue

            cur.execute(
                """
                INSERT INTO plan_estudio (nivel, grado, curso, IdArea, area, horas)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (nivel, grado, curso, id_area, area_nombre, horas),
            )
            inserted += 1

        conn.commit()

    return {"insertados": inserted, "omitidos": skipped}
