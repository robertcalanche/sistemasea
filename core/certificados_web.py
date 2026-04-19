from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from certificados.acta_grado import generar_acta_grado
from certificados.certificado_matricula import generar_certificado_matricula

from . import get_connection, get_db_path
from .construir_nombre import construir_nombre
from . import matricula as core_matricula
from . import plantel_web as core_plantel_web


TIPO_MATRICULA = "MATRICULA"
TIPO_CALIFICACIONES = "CALIFICACIONES"
TIPO_ACTA = "ACTA"
TIPO_DIPLOMA = "DIPLOMA"

ACTA_MODELO_DEFAULT = """LA INSTITUCION EDUCATIVA {institucion}\n\nCERTIFICA QUE\n\n{nombre}, identificado(a) con documento No. {documento}, culmino satisfactoriamente el grado {grado} curso {curso}.\n\nSe expide la presente acta de grado con numero {numero_acta} el dia {fecha_grado}.\n\nResolucion de aprobacion: {resolucion}.\n\nRector(a): {rector_nombre}\nSecretaria: {secretaria_nombre}"""


def _norm(value):
    return str(value or "").strip()


def _slug(value):
    text = _norm(value)
    if not text:
        return "documento"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_") or "documento"


def _to_int(value, default=20):
    try:
        return int(value)
    except Exception:
        return int(default)


def _certificados_dir() -> Path:
    target = get_db_path().parent / "certificados_generados"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _ensure_certificados_table():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS certificados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estudiante_id INTEGER,
                tipo TEXT,
                codigo TEXT UNIQUE,
                ruta TEXT,
                fecha TEXT,
                libro TEXT,
                folio TEXT,
                numero_diploma TEXT,
                acta TEXT
            )
            """
        )
        conn.commit()


def _generar_codigo(tipo: str) -> str:
    _ensure_certificados_table()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM certificados WHERE tipo = ?", (tipo,))
        consecutivo = int(cur.fetchone()[0] or 0) + 1
    return f"SEA-{tipo}-{datetime.now().year}-{consecutivo:04d}"


def _obtener_institucion() -> dict:
    data = core_plantel_web.obtener_configuracion_plantel()
    return {
        "nombre": _norm(data.get("nombre_institucion")) or "Institucion Educativa",
        "institucion": _norm(data.get("nombre_institucion")) or "Institucion Educativa",
        "codigo_dane": _norm(data.get("codigo_dane")),
        "resolucion": _norm(data.get("resolucion_aprobacion")),
        "rector_nombre": _norm(data.get("rector_nombre")) or "Rectoria",
        "secretaria_nombre": _norm(data.get("secretaria_nombre"))
        or "Secretaria Academica",
        "correo": _norm(data.get("correo_institucional")),
        "telefono": _norm(data.get("telefono")),
        "anio_lectivo": _norm(data.get("anio_lectivo")) or str(datetime.now().year),
    }


def _modelo_acta() -> str:
    model_path = get_db_path().parent / "certificados" / "modelo_acta_grado.txt"
    if model_path.exists():
        try:
            return model_path.read_text(encoding="utf-8").strip() or ACTA_MODELO_DEFAULT
        except Exception:
            return ACTA_MODELO_DEFAULT
    return ACTA_MODELO_DEFAULT


def _registrar_documento(
    estudiante: dict,
    tipo: str,
    codigo: str,
    ruta: Path,
    *,
    libro: str = "",
    folio: str = "",
    numero_diploma: str = "",
    acta: str = "",
):
    _ensure_certificados_table()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO certificados (
                estudiante_id, tipo, codigo, ruta, fecha, libro, folio, numero_diploma, acta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                estudiante.get("id"),
                tipo,
                codigo,
                str(ruta),
                datetime.now().isoformat(timespec="seconds"),
                _norm(libro),
                _norm(folio),
                _norm(numero_diploma),
                _norm(acta),
            ),
        )
        conn.commit()


def _nombre_estudiante(estudiante: dict) -> str:
    return _norm(estudiante.get("nombre")) or construir_nombre(estudiante)


def obtener_estudiante(documento):
    documento = _norm(documento)
    if not documento:
        raise ValueError("documento_requerido")

    estudiante = core_matricula.buscar_estudiante(documento)
    if not estudiante:
        raise ValueError("estudiante_no_encontrado")

    return {
        "id": estudiante.get("id"),
        "documento": _norm(estudiante.get("documento")),
        "nombre": _nombre_estudiante(estudiante),
        "grado": _norm(estudiante.get("grado")),
        "curso": _norm(estudiante.get("curso")),
        "estado": _norm(estudiante.get("estado_academico")) or "Activo",
        "jornada": _norm(estudiante.get("jornada")),
        "sede": _norm(estudiante.get("sede")),
    }


def listar_documentos(documento=None, limit=20):
    _ensure_certificados_table()
    limit = max(1, min(100, _to_int(limit, 20)))
    documento = _norm(documento)

    where = []
    params = []
    if documento:
        where.append("TRIM(CAST(COALESCE(e.documento, '') AS TEXT)) = ?")
        params.append(documento)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT c.tipo, c.codigo, c.ruta, c.fecha, c.libro, c.folio,
                   c.numero_diploma, c.acta, e.documento, e.grado, e.curso,
                   e.nombre1, e.nombre2, e.apellido1, e.apellido2, e.nombre
            FROM certificados c
            LEFT JOIN estudiantes e ON e.id = c.estudiante_id
            {where_sql}
            ORDER BY COALESCE(c.fecha, '') DESC, c.id DESC
            LIMIT ?
            """,
            params + [limit],
        )
        cols = [desc[0] for desc in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    historial = []
    for row in rows:
        referencia = _norm(row.get("acta"))
        if not referencia:
            referencia = _norm(row.get("numero_diploma"))
        if not referencia:
            libro = _norm(row.get("libro"))
            folio = _norm(row.get("folio"))
            referencia = " / ".join([value for value in (libro, folio) if value])

        historial.append(
            {
                "tipo": _norm(row.get("tipo")),
                "codigo": _norm(row.get("codigo")),
                "ruta": _norm(row.get("ruta")),
                "fecha": _norm(row.get("fecha")),
                "documento": _norm(row.get("documento")),
                "referencia": referencia,
            }
        )
    return historial


def _resultados_estudiante(documento: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT area, evaluacion, nota, estado_examen, hora_fin, hora_inicio, intento
            FROM resultados
            WHERE TRIM(CAST(COALESCE(documento, '') AS TEXT)) = ?
              AND UPPER(TRIM(CAST(COALESCE(estado_examen, '') AS TEXT))) IN ('FINALIZADO', 'PRESENTADO')
            ORDER BY COALESCE(hora_fin, hora_inicio, '') DESC, id DESC
            """,
            (documento,),
        )
        cols = [desc[0] for desc in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _resumen_calificaciones(documento: str):
    rows = _resultados_estudiante(documento)
    resumen = {}
    for row in rows:
        area = _norm(row.get("area")) or "General"
        nota = row.get("nota")
        try:
            nota_float = float(nota)
        except Exception:
            continue
        bucket = resumen.setdefault(area, {"notas": [], "evaluaciones": set()})
        bucket["notas"].append(nota_float)
        evaluacion = _norm(row.get("evaluacion"))
        if evaluacion:
            bucket["evaluaciones"].add(evaluacion)

    areas = []
    for area, payload in sorted(resumen.items()):
        notas = payload["notas"]
        promedio = round(sum(notas) / len(notas), 2) if notas else 0.0
        areas.append(
            {
                "area": area,
                "promedio": promedio,
                "registros": len(notas),
                "evaluaciones": ", ".join(sorted(payload["evaluaciones"])),
            }
        )

    promedio_general = (
        round(sum(item["promedio"] for item in areas) / len(areas), 2)
        if areas
        else None
    )
    return rows, areas, promedio_general


def _build_doc(path_pdf: Path):
    return SimpleDocTemplate(
        str(path_pdf),
        pagesize=letter,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )


def _pdf_calificaciones(
    estudiante: dict, institucion: dict, codigo: str, path_pdf: Path
):
    _, areas, promedio_general = _resumen_calificaciones(estudiante["documento"])
    nombre = _nombre_estudiante(estudiante)
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        name="Body", parent=styles["BodyText"], fontSize=10, leading=14
    )
    title = ParagraphStyle(
        name="TitleSea", parent=styles["Heading1"], fontSize=15, leading=18, alignment=1
    )

    story = [
        Paragraph(institucion.get("institucion") or "Institucion Educativa", title),
        Spacer(1, 0.2 * cm),
        Paragraph("CERTIFICADO DE CALIFICACIONES", title),
        Spacer(1, 0.4 * cm),
        Paragraph(f"Estudiante: <b>{nombre}</b>", body),
        Paragraph(f"Documento: <b>{estudiante.get('documento')}</b>", body),
        Paragraph(
            f"Grado/Curso: <b>{_norm(estudiante.get('grado'))} - {_norm(estudiante.get('curso'))}</b>",
            body,
        ),
        Paragraph(f"Codigo de certificacion: <b>{codigo}</b>", body),
        Spacer(1, 0.35 * cm),
    ]

    if areas:
        table_data = [["Area", "Promedio", "Registros", "Evaluaciones"]]
        for item in areas:
            table_data.append(
                [
                    item["area"],
                    f"{item['promedio']:.2f}",
                    str(item["registros"]),
                    item["evaluaciones"] or "-",
                ]
            )
        table = Table(
            table_data, repeatRows=1, colWidths=[4.5 * cm, 2.2 * cm, 2.4 * cm, 7.2 * cm]
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a4f8c")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9dee8")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.whitesmoke, colors.HexColor("#eef4fb")],
                    ),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.35 * cm))
        promedio_texto = (
            f"{promedio_general:.2f}"
            if promedio_general is not None
            else "Sin registros"
        )
        story.append(
            Paragraph(f"Promedio general consolidado: <b>{promedio_texto}</b>", body)
        )
    else:
        story.append(
            Paragraph(
                "No se encontraron calificaciones finales registradas para este estudiante.",
                body,
            )
        )

    story.extend(
        [
            Spacer(1, 0.6 * cm),
            Paragraph(
                f"Se expide en fecha {datetime.now().strftime('%d/%m/%Y')} a solicitud del interesado.",
                body,
            ),
            Spacer(1, 1.0 * cm),
            Paragraph(
                f"Rector(a): {institucion.get('rector_nombre') or 'Rectoria'}", body
            ),
            Paragraph(
                f"Secretaria Academica: {institucion.get('secretaria_nombre') or 'Secretaria Academica'}",
                body,
            ),
        ]
    )

    _build_doc(path_pdf).build(story)


def _pdf_diploma(
    estudiante: dict,
    institucion: dict,
    codigo: str,
    path_pdf: Path,
    *,
    numero_diploma: str = "",
    fecha_grado: str = "",
):
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        name="DiplomaTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        alignment=1,
    )
    subtitle = ParagraphStyle(
        name="DiplomaSub",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16,
        alignment=1,
    )
    body = ParagraphStyle(
        name="DiplomaBody",
        parent=styles["BodyText"],
        fontSize=12,
        leading=18,
        alignment=1,
    )

    fecha_legible = _norm(fecha_grado) or datetime.now().strftime("%Y-%m-%d")
    nombre = _nombre_estudiante(estudiante)
    story = [
        Spacer(1, 1.3 * cm),
        Paragraph(institucion.get("institucion") or "Institucion Educativa", title),
        Spacer(1, 0.4 * cm),
        Paragraph("DIPLOMA DE BACHILLER", title),
        Spacer(1, 0.8 * cm),
        Paragraph("Otorga el presente diploma a", subtitle),
        Spacer(1, 0.4 * cm),
        Paragraph(f"<b>{nombre}</b>", title),
        Spacer(1, 0.5 * cm),
        Paragraph(
            f"identificado(a) con documento No. <b>{estudiante.get('documento')}</b>, por haber culminado satisfactoriamente el grado <b>{_norm(estudiante.get('grado'))}</b> curso <b>{_norm(estudiante.get('curso'))}</b>.",
            body,
        ),
        Spacer(1, 0.5 * cm),
        Paragraph(
            f"Numero de diploma: <b>{_norm(numero_diploma) or codigo}</b>", subtitle
        ),
        Paragraph(f"Fecha de grado: <b>{fecha_legible}</b>", subtitle),
        Paragraph(f"Codigo institucional: <b>{codigo}</b>", subtitle),
        Spacer(1, 1.4 * cm),
        Paragraph(
            f"Rector(a): {institucion.get('rector_nombre') or 'Rectoria'}", subtitle
        ),
        Spacer(1, 0.3 * cm),
        Paragraph(
            f"Secretaria Academica: {institucion.get('secretaria_nombre') or 'Secretaria Academica'}",
            subtitle,
        ),
    ]
    _build_doc(path_pdf).build(story)


def generar_certificado_matricula_web(documento):
    estudiante = obtener_estudiante(documento)
    institucion = _obtener_institucion()
    codigo = _generar_codigo(TIPO_MATRICULA)
    filename = f"certificado_matricula_{_slug(estudiante['documento'])}_{codigo}.pdf"
    path_pdf = _certificados_dir() / filename

    generar_certificado_matricula(
        estudiante, institucion, {"codigo": codigo}, str(path_pdf)
    )
    _registrar_documento(estudiante, TIPO_MATRICULA, codigo, path_pdf)
    return {"ruta": path_pdf, "nombre_archivo": filename, "codigo": codigo}


def generar_acta_grado_web(documento, numero_acta=None, fecha_grado=None):
    estudiante = obtener_estudiante(documento)
    institucion = _obtener_institucion()
    codigo = _generar_codigo(TIPO_ACTA)
    numero_acta = _norm(numero_acta) or codigo
    fecha_grado = _norm(fecha_grado) or datetime.now().strftime("%Y-%m-%d")
    filename = f"acta_grado_{_slug(estudiante['documento'])}_{codigo}.pdf"
    path_pdf = _certificados_dir() / filename

    generar_acta_grado(
        estudiante,
        institucion,
        {
            "codigo": codigo,
            "numero_acta": numero_acta,
            "fecha_grado": fecha_grado,
            "institucion": institucion.get("institucion"),
            "resolucion": institucion.get("resolucion"),
            "rector_nombre": institucion.get("rector_nombre"),
            "secretaria_nombre": institucion.get("secretaria_nombre"),
        },
        str(path_pdf),
        _modelo_acta(),
    )
    _registrar_documento(estudiante, TIPO_ACTA, codigo, path_pdf, acta=numero_acta)
    return {"ruta": path_pdf, "nombre_archivo": filename, "codigo": codigo}


def generar_certificado_calificaciones_web(documento):
    estudiante = obtener_estudiante(documento)
    institucion = _obtener_institucion()
    codigo = _generar_codigo(TIPO_CALIFICACIONES)
    filename = (
        f"certificado_calificaciones_{_slug(estudiante['documento'])}_{codigo}.pdf"
    )
    path_pdf = _certificados_dir() / filename

    _pdf_calificaciones(estudiante, institucion, codigo, path_pdf)
    _registrar_documento(estudiante, TIPO_CALIFICACIONES, codigo, path_pdf)
    return {"ruta": path_pdf, "nombre_archivo": filename, "codigo": codigo}


def generar_diploma_web(documento, numero_diploma=None, fecha_grado=None):
    estudiante = obtener_estudiante(documento)
    institucion = _obtener_institucion()
    codigo = _generar_codigo(TIPO_DIPLOMA)
    numero_diploma = _norm(numero_diploma) or codigo
    fecha_grado = _norm(fecha_grado) or datetime.now().strftime("%Y-%m-%d")
    filename = f"diploma_{_slug(estudiante['documento'])}_{codigo}.pdf"
    path_pdf = _certificados_dir() / filename

    _pdf_diploma(
        estudiante,
        institucion,
        codigo,
        path_pdf,
        numero_diploma=numero_diploma,
        fecha_grado=fecha_grado,
    )
    _registrar_documento(
        estudiante,
        TIPO_DIPLOMA,
        codigo,
        path_pdf,
        numero_diploma=numero_diploma,
    )
    return {"ruta": path_pdf, "nombre_archivo": filename, "codigo": codigo}
