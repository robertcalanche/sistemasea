from __future__ import annotations

import re
from pathlib import Path

from . import get_connection
from . import configuracion as core_configuracion

PLANTEL_KEYS = [
    "nombre_institucion",
    "codigo_dane",
    "nit",
    "decreto_funcionamiento",
    "resolucion_aprobacion",
    "departamento",
    "municipio",
    "corregimiento_localidad",
    "direccion",
    "jornadas",
    "rector_nombre",
    "rector_identificacion",
    "rector_cargo",
    "secretaria_nombre",
    "secretaria_identificacion",
    "secretaria_cargo",
    "telefono",
    "correo_institucional",
    "dominio_web",
    "logo_path",
]


DEFAULT_ESCALA = [
    {
        "desde": 4.6,
        "hasta": 5.0,
        "letra": "S",
        "concepto": "Superior",
        "desempeno": "Superior",
        "recomendacion": "",
    },
    {
        "desde": 4.0,
        "hasta": 4.5,
        "letra": "A",
        "concepto": "Alto",
        "desempeno": "Alto",
        "recomendacion": "",
    },
    {
        "desde": 3.0,
        "hasta": 3.9,
        "letra": "B",
        "concepto": "Basico",
        "desempeno": "Basico",
        "recomendacion": "",
    },
    {
        "desde": 1.0,
        "hasta": 2.9,
        "letra": "I",
        "concepto": "Bajo",
        "desempeno": "Bajo",
        "recomendacion": "",
    },
]


def _norm(txt):
    return str(txt or "").strip()


def _ensure_tables():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS configuracion_plantel (
                clave TEXT PRIMARY KEY,
                valor TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS escala_valoracion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                desde REAL NOT NULL,
                hasta REAL NOT NULL,
                letra TEXT,
                concepto TEXT,
                desempeno TEXT,
                recomendacion TEXT
            )
            """
        )
        conn.commit()


def obtener_configuracion_plantel():
    _ensure_tables()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT clave, valor FROM configuracion_plantel")
        data = {str(k): str(v or "") for k, v in cur.fetchall()}

    anio = _norm(core_configuracion.obtener_anio_lectivo())
    if anio:
        data["anio_lectivo"] = anio

    for key in PLANTEL_KEYS:
        data.setdefault(key, "")

    return data


def guardar_configuracion_plantel(payload):
    _ensure_tables()
    data = {k: _norm(v) for k, v in dict(payload or {}).items()}

    nombre = data.get("nombre_institucion", "")
    if not nombre:
        raise ValueError("nombre_institucion_requerido")

    dane = data.get("codigo_dane", "")
    if dane and not re.fullmatch(r"\d{12}", dane):
        raise ValueError("codigo_dane_invalido")

    nit = data.get("nit", "")
    if nit and not re.fullmatch(r"\d+-?\d*|\d+", nit):
        raise ValueError("nit_invalido")

    correo = data.get("correo_institucional", "")
    if correo and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        raise ValueError("correo_institucional_invalido")

    anio = data.get("anio_lectivo", "")
    if anio and not re.fullmatch(r"\d{4}", anio):
        raise ValueError("anio_lectivo_invalido")

    with get_connection() as conn:
        cur = conn.cursor()
        for key in PLANTEL_KEYS:
            if key in data:
                cur.execute(
                    "REPLACE INTO configuracion_plantel(clave, valor) VALUES(?, ?)",
                    (key, data[key]),
                )
        conn.commit()

    if anio:
        core_configuracion.guardar_anio_lectivo(anio)

    return {
        "mensaje": "Configuracion de plantel guardada",
    }


def obtener_escala_valoracion():
    _ensure_tables()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT desde, hasta, letra, concepto, desempeno, recomendacion
            FROM escala_valoracion
            ORDER BY desde DESC
            """
        )
        rows = cur.fetchall()

    if not rows:
        return list(DEFAULT_ESCALA)

    return [
        {
            "desde": float(r[0]),
            "hasta": float(r[1]),
            "letra": _norm(r[2]),
            "concepto": _norm(r[3]),
            "desempeno": _norm(r[4]),
            "recomendacion": _norm(r[5]),
        }
        for r in rows
    ]


def guardar_escala_valoracion(escala):
    rows = list(escala or [])
    if not rows:
        raise ValueError("escala_requerida")

    parsed = []
    for item in rows:
        try:
            desde = float(item.get("desde"))
            hasta = float(item.get("hasta"))
        except Exception as exc:
            raise ValueError("escala_rango_invalido") from exc
        if desde > hasta:
            raise ValueError("escala_desde_mayor_que_hasta")
        parsed.append(
            {
                "desde": desde,
                "hasta": hasta,
                "letra": _norm(item.get("letra")),
                "concepto": _norm(item.get("concepto")),
                "desempeno": _norm(item.get("desempeno")),
                "recomendacion": _norm(item.get("recomendacion")),
            }
        )

    parsed_sorted = sorted(parsed, key=lambda x: x["desde"])
    for i in range(len(parsed_sorted) - 1):
        a = parsed_sorted[i]
        b = parsed_sorted[i + 1]
        if a["hasta"] >= b["desde"]:
            raise ValueError("escala_solapada")

    _ensure_tables()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM escala_valoracion")
        for item in parsed:
            cur.execute(
                """
                INSERT INTO escala_valoracion (
                    desde, hasta, letra, concepto, desempeno, recomendacion
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item["desde"],
                    item["hasta"],
                    item["letra"],
                    item["concepto"],
                    item["desempeno"],
                    item["recomendacion"],
                ),
            )
        conn.commit()

    return {
        "mensaje": "Escala de valoracion guardada",
    }


def guardar_logo_plantel(filename, raw_bytes, base_dir):
    if not raw_bytes:
        raise ValueError("archivo_vacio")

    name = _norm(filename).lower()
    if not (
        name.endswith(".png")
        or name.endswith(".jpg")
        or name.endswith(".jpeg")
        or name.endswith(".bmp")
    ):
        raise ValueError("formato_logo_no_soportado")

    root = Path(base_dir)
    out_dir = root / "static" / "img"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "logo_institucion.png"
    out_path.write_bytes(raw_bytes)

    rel_path = str(Path("static") / "img" / "logo_institucion.png")

    _ensure_tables()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO configuracion_plantel(clave, valor) VALUES(?, ?)",
            ("logo_path", rel_path),
        )
        conn.commit()

    return {
        "logo_path": rel_path,
        "mensaje": "Logo actualizado",
    }
