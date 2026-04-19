from __future__ import annotations

from pathlib import Path

from . import get_connection

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_EXAMENES_API = BASE_DIR / "out_examenes_api"


def _scalar(query, params=None, default=0):
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params or [])
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else default
    except Exception:
        return default


def _recent_files(limit=8):
    if not OUT_EXAMENES_API.exists():
        return []

    files = [item for item in OUT_EXAMENES_API.iterdir() if item.is_file()]
    files.sort(key=lambda item: item.stat().st_mtime, reverse=True)

    rows = []
    for item in files[: max(1, int(limit or 8))]:
        suffix = item.suffix.lower()
        if suffix == ".pdf":
            tipo = "pdf"
        elif suffix == ".zip":
            tipo = "zip"
        else:
            tipo = "archivo"
        rows.append(
            {
                "nombre": item.name,
                "tipo": tipo,
                "tamano_kb": round(item.stat().st_size / 1024, 1),
                "download_url": f"/api/examenes/descargar/{item.name}",
            }
        )
    return rows


def _recent_exams(limit=8):
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT eg.exam_code AS id_examen,
                       TRIM(COALESCE(eg.grado, '')) || ' ' || TRIM(COALESCE(eg.curso, '')) || ' · ' || TRIM(COALESCE(eg.area, '')) AS grupo,
                       COALESCE(COUNT(de.numero_pregunta), 0) AS n_preguntas,
                       eg.fecha_generacion AS fecha
                FROM examenes_generados eg
                LEFT JOIN detalle_examen de ON de.id_examen = eg.exam_code
                GROUP BY eg.exam_code, eg.grado, eg.curso, eg.area, eg.fecha_generacion
                ORDER BY eg.fecha_generacion DESC, eg.id DESC
                LIMIT ?
                """,
                (max(1, int(limit or 8)),),
            )
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception:
        return []


def panel_examenes():
    total_examenes = int(
        _scalar("SELECT COUNT(DISTINCT exam_code) FROM examenes_generados", default=0)
    )
    total_configs = int(_scalar("SELECT COUNT(*) FROM config_examenes", default=0))
    configs_habilitadas = int(
        _scalar(
            "SELECT COUNT(*) FROM config_examenes WHERE COALESCE(habilitado, 0) = 1",
            default=0,
        )
    )
    grupos_configurados = int(
        _scalar(
            "SELECT COUNT(DISTINCT TRIM(CAST(COALESCE(grado, '') AS TEXT)) || '|' || LOWER(TRIM(CAST(COALESCE(area, '') AS TEXT)))) FROM config_examenes WHERE TRIM(CAST(COALESCE(area, '') AS TEXT)) <> ''",
            default=0,
        )
    )

    archivos = _recent_files(limit=10)
    total_pdfs = sum(1 for item in archivos if item.get("tipo") == "pdf")
    cuadernillos = sum(
        1
        for item in archivos
        if str(item.get("nombre") or "").lower().startswith("cuadernillo")
    )
    recientes = _recent_exams(limit=8)

    return {
        "metricas": {
            "examenes_generados": total_examenes,
            "configs_totales": total_configs,
            "configs_habilitadas": configs_habilitadas,
            "grupos_configurados": grupos_configurados,
            "archivos_pdf": total_pdfs,
            "cuadernillos": cuadernillos,
        },
        "recientes": recientes,
        "archivos": archivos,
    }
