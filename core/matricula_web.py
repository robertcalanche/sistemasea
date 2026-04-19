from __future__ import annotations

from io import BytesIO

import pandas as pd

from . import get_connection
from . import matricula as core_matricula


def _norm(txt):
    return str(txt or "").strip()


def _norm_upper(txt):
    return str(txt or "").strip().upper()


def _estado_ui(estado_db):
    estado = str(estado_db or "").strip().lower()
    if estado in {"", "activo", "ma", "matriculado"}:
        return "Matriculado"
    return str(estado_db or "").strip().title()


def listar_estudiantes(
    grado=None,
    curso=None,
    jornada=None,
    nombre=None,
    limit=200,
    offset=0,
):
    limit = max(1, min(500, int(limit)))
    offset = max(0, int(offset))

    filters = ["1=1"]
    params = []

    if _norm(grado):
        filters.append("TRIM(CAST(grado AS TEXT)) = TRIM(CAST(? AS TEXT))")
        params.append(_norm(grado))
    if _norm(curso):
        filters.append("UPPER(TRIM(CAST(curso AS TEXT))) = ?")
        params.append(_norm_upper(curso))
    if _norm(jornada):
        filters.append(
            "LOWER(TRIM(CAST(jornada AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))"
        )
        params.append(_norm(jornada))
    if _norm(nombre):
        filters.append("LOWER(TRIM(CAST(nombre AS TEXT))) LIKE ?")
        params.append(f"%{_norm(nombre).lower()}%")

    where = " WHERE " + " AND ".join(filters)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM estudiantes {where}", params)
        total = int(cur.fetchone()[0])
        cur.execute(
            f"""
            SELECT documento, nombre, grado, curso, jornada,
                   tipo_documento, fecha_nacimiento, telefono, correo,
                   sexo, sede, estado
            FROM estudiantes
            {where}
            ORDER BY COALESCE(nombre, '') COLLATE NOCASE ASC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    for row in rows:
        row["estado_ui"] = _estado_ui(row.get("estado"))
        row["telefono"] = _norm(row.get("telefono"))
        row["correo"] = _norm(row.get("correo"))
        row["grado"] = _norm(row.get("grado"))
        row["curso"] = _norm(row.get("curso"))
        row["jornada"] = _norm(row.get("jornada"))

    return {"total": total, "estudiantes": rows}


def catalogos():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT grado FROM estudiantes WHERE TRIM(CAST(grado AS TEXT)) <> '' ORDER BY grado"
        )
        grados = [_norm(r[0]) for r in cur.fetchall() if r and _norm(r[0])]

        cur.execute(
            "SELECT DISTINCT UPPER(TRIM(CAST(curso AS TEXT))) FROM estudiantes WHERE TRIM(CAST(curso AS TEXT)) <> '' ORDER BY curso"
        )
        cursos = [_norm_upper(r[0]) for r in cur.fetchall() if r and _norm(r[0])]

        cur.execute(
            "SELECT DISTINCT jornada FROM estudiantes WHERE TRIM(CAST(jornada AS TEXT)) <> '' ORDER BY jornada"
        )
        jornadas = [_norm(r[0]) for r in cur.fetchall() if r and _norm(r[0])]

    return {
        "grados": grados,
        "cursos": cursos,
        "jornadas": jornadas,
    }


def cambiar_curso_masivo(documentos, nuevo_grado, nuevo_curso, nueva_jornada=None):
    docs = [_norm(d) for d in (documentos or []) if _norm(d)]
    if not docs:
        raise ValueError("sin_documentos")
    if not _norm(nuevo_grado) or not _norm(nuevo_curso):
        raise ValueError("grado_y_curso_requeridos")

    count = 0
    for doc in docs:
        core_matricula.cambiar_grado_curso(
            documento=doc,
            nuevo_grado=_norm(nuevo_grado),
            nuevo_curso=_norm_upper(nuevo_curso),
            nueva_jornada=_norm(nueva_jornada) or None,
        )
        count += 1
    return count


_COLUMN_MAP = {
    "sede": "sede",
    "jornada": "jornada",
    "grado": "grado",
    "curso": "curso",
    "nombre": "nombre",
    "tipodoc": "tipodoc",
    "tipo_documento": "tipodoc",
    "documento": "documento",
    "fechana": "fechana",
    "fecha_nacimiento": "fechana",
    "telefono": "telefono",
    "celular": "celular",
    "email": "email",
    "correo": "email",
    "genero": "genero",
    "sexo": "genero",
    "tipo_sangre": "tipo_sangre",
    "estado": "estado",
}


def _normalizar_dataframe(df):
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    renamed = {}
    for c in out.columns:
        if c in _COLUMN_MAP:
            renamed[c] = _COLUMN_MAP[c]
    out = out.rename(columns=renamed)

    required = {
        "sede",
        "jornada",
        "grado",
        "curso",
        "nombre",
        "tipodoc",
        "documento",
        "fechana",
        "telefono",
        "celular",
        "email",
        "genero",
        "tipo_sangre",
        "estado",
    }

    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError("columnas_faltantes:" + ",".join(sorted(missing)))

    out = out[
        [
            "sede",
            "jornada",
            "grado",
            "curso",
            "nombre",
            "tipodoc",
            "documento",
            "fechana",
            "telefono",
            "celular",
            "email",
            "genero",
            "tipo_sangre",
            "estado",
        ]
    ]

    out = out.fillna("")
    for col in out.columns:
        out[col] = out[col].map(lambda x: _norm(x))
    out["curso"] = out["curso"].map(_norm_upper)
    out["documento"] = out["documento"].map(
        lambda x: x[:-2] if x.endswith(".0") and x[:-2].isdigit() else x
    )
    return out


def importar_masivo_desde_archivo(filename, raw_bytes):
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

    normalizado = _normalizar_dataframe(df)
    registros = normalizado.to_dict(orient="records")
    core_matricula.sincronizar_estudiantes(registros)
    return len(registros)
