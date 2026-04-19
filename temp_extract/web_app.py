# --- IMPORTS Y FLASK APP (debe ir antes de los decoradores) ---
print("==[DEBUG]== Inicio de web_app.py")
import os
from flask import (
    Flask,
    render_template,
    session,
    send_from_directory,
    jsonify,
    send_file,
    request,
)
from werkzeug.utils import secure_filename
import Admin

# Instancia de Flask y configuración (debe ir antes de los decoradores)
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SEA_WEB_SECRET_KEY", "sea-web-dev-secret-change-this")


# --- API: Detalle de respuestas de un estudiante (para resultados) ---
@app.get("/api/resultados/detalle/<documento>/<area>/<evaluacion>/<int:intento>")
def api_resultados_detalle(documento, area, evaluacion, intento):
    """Devuelve el detalle de respuestas de un estudiante para un área, evaluación e intento específico."""
    try:
        # Se asume que existe un core_resultados_web con función obtener_respuestas_estudiante_web
        from core import resultados_web as core_resultados_web

        respuestas = core_resultados_web.obtener_respuestas_estudiante_web(
            documento=documento, area=area, evaluacion=evaluacion, intento=int(intento)
        )
        # Formato: lista de dicts con pregunta, respuesta_estudiante, respuesta_correcta, estado, etc.
        return jsonify({"ok": True, "respuestas": respuestas})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# --- Rutas base para nuevas pestañas SuperAdmin migradas ---
@app.get("/certificados")
def web_certificados():
    return render_template("certificados.html", web_user=session.get("web_user"))


@app.get("/actas")
def web_actas():
    return render_template("actas.html", web_user=session.get("web_user"))


@app.get("/diplomas")
def web_diplomas():
    return render_template("diplomas.html", web_user=session.get("web_user"))


@app.get("/planillas")
def web_planillas():
    return render_template("planillas.html", web_user=session.get("web_user"))


@app.get("/plan-aula")
def web_plan_aula():
    return render_template("plan_aula.html", web_user=session.get("web_user"))


@app.get("/planeador-clase")
def web_planeador_clase():
    return render_template("planeador_clase.html", web_user=session.get("web_user"))


@app.get("/calendario-academico")
def web_calendario_academico():
    return render_template(
        "calendario_academico.html", web_user=session.get("web_user")
    )


# --- ENDPOINT: Exámenes disponibles para el estudiante autenticado ---
@app.get("/api/examenes/estudiante")
def api_examenes_estudiante():
    """Devuelve los exámenes activos para el estudiante autenticado (grado y curso)."""
    user = session.get("web_user")
    if not user or user.get("rol") != "estudiante":
        return _api_error("no_autorizado", status=401)
    grado = user.get("grado")
    curso = user.get("curso")
    if not grado or not curso:
        return _api_error("grado_o_curso_faltante", status=400)
    # Buscar exámenes activos para ese grado y curso
    import sqlite3
    from pathlib import Path

    DB_FILE = str((Path(__file__).parent / "sea.db").resolve())
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, grado, curso, area, evaluacion, duracion_segundos, cantidad_preguntas, max_intentos, permitir_reintentos
        FROM config_examenes
        WHERE estado = 'activo'
          AND habilitado = 1
          AND LOWER(TRIM(grado)) = LOWER(TRIM(?))
          AND UPPER(TRIM(curso)) = UPPER(TRIM(?))
        ORDER BY area, evaluacion
        """,
        (grado, curso),
    )
    rows = cur.fetchall()
    conn.close()
    ex_list = [
        {
            "id": row[0],
            "grado": row[1],
            "curso": row[2],
            "area": row[3],
            "evaluacion": row[4],
            "duracion_segundos": row[5],
            "cantidad_preguntas": row[6],
            "max_intentos": row[7],
            "permitir_reintentos": row[8],
        }
        for row in rows
    ]
    return _api_ok(examenes=ex_list)


# --- Endpoint para importar preguntas desde Excel (banco de preguntas) ---
@app.route("/api/v1/banco-preguntas/importar_excel", methods=["POST"])
def api_importar_preguntas_excel():
    """Importa preguntas desde un archivo Excel subido por el usuario."""
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No se envió archivo."}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"ok": False, "error": "Nombre de archivo vacío."}), 400
    filename = secure_filename(file.filename)
    temp_path = os.path.join("/tmp", filename)
    file.save(temp_path)
    try:
        # Reutiliza la lógica de Admin.py
        Admin.importar_preguntas_desde_excel.__globals__["EXCEL_PATH"] = temp_path
        Admin.importar_preguntas_desde_excel()
        os.remove(temp_path)
        return jsonify({"ok": True, "msg": "Preguntas importadas correctamente."})
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"ok": False, "error": str(e)}), 500


# --- Endpoint para unir y descargar todos los PDFs generados en un solo PDF ---

import os
from flask import Flask, send_from_directory, jsonify, send_file
import yaml
import glob
from PyPDF2 import PdfMerger
import io


@app.get("/api/v1/examenes/descargar_todos")
def api_descargar_todos_los_pdfs():
    """Une todos los PDFs generados en out_examenes_api y los descarga como un solo PDF."""
    output_dir = (BASE_DIR / "out_examenes_api").resolve()
    pdf_files = sorted([str(p) for p in output_dir.glob("*.pdf")])
    if not pdf_files:
        return _api_error("No hay PDFs para unir", status=404)
    merger = PdfMerger()
    for pdf_path in pdf_files:
        merger.append(pdf_path)
    merged_pdf = io.BytesIO()
    merger.write(merged_pdf)
    merger.close()
    merged_pdf.seek(0)
    return send_file(
        merged_pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="examenes_unidos.pdf",
    )


# --- Endpoint para datos de gráficas del dashboard ---
@app.get("/api/v1/dashboard/charts")
def api_dashboard_charts():
    """Devuelve datos para las gráficas del dashboard: exámenes por área y estudiantes por grado."""
    try:
        # Exámenes por área
        examenes = core_examenes.listar_examenes_generados(limit=10000)
        area_count = {}
        for ex in examenes:
            area = ex.get("grupo") or "Sin área"
            area_count[area] = area_count.get(area, 0) + 1
        labels_area = list(area_count.keys())
        data_area = [area_count[a] for a in labels_area]

        # Estudiantes por grado
        grados = core_preguntas.cargar_grados_banco()
        labels_grado = [str(g) for g in grados]
        data_grado = []
        for grado in grados:
            try:
                total = core_usuarios.listar_estudiantes(grado=grado, limit=1).get(
                    "total", 0
                )
            except Exception:
                total = 0
            data_grado.append(total)

        return _api_ok(
            examenes_por_area={"labels": labels_area, "data": data_area},
            estudiantes_por_grado={"labels": labels_grado, "data": data_grado},
        )
    except Exception as exc:
        return _api_error(str(exc), status=500)


# --- Endpoint para servir OpenAPI y Swagger UI ---
import os
from flask import Flask, send_from_directory, jsonify
import yaml
import glob

# ...existing code...


# =================== CONFIGURACIÓN DE MÓDULOS ===================


### --- Endpoint de métricas dashboard (después de instanciar app) ---
@app.get("/api/v1/dashboard/metrics")
def api_dashboard_metrics():
    """Devuelve métricas agregadas para el dashboard principal."""
    try:
        # Total de estudiantes
        try:
            total_estudiantes = core_usuarios.listar_estudiantes().get("total", 0)
        except Exception:
            total_estudiantes = 0
        # Total de docentes
        try:
            total_docentes = core_docentes.listar_docentes().get("total", 0)
        except Exception:
            total_docentes = 0
        # Total de preguntas
        try:
            total_preguntas = core_preguntas.listar_banco_preguntas().get("total", 0)
        except Exception:
            total_preguntas = 0
        # Total de exámenes generados
        try:
            total_examenes = len(core_examenes.listar_examenes_generados(limit=10000))
        except Exception:
            total_examenes = 0
        # Total de áreas
        try:
            total_areas = len(core_preguntas.cargar_areas())
        except Exception:
            total_areas = 0
        # Total de evaluaciones (únicas)
        try:
            grados = core_preguntas.cargar_grados_banco()
            areas = core_preguntas.cargar_areas()
            evaluaciones_set = set()
            for grado in grados:
                for area in areas:
                    evals = core_preguntas.cargar_evaluaciones_por_grado_y_area(
                        grado, area
                    )
                    evaluaciones_set.update(evals)
            total_evaluaciones = len(evaluaciones_set)
        except Exception:
            total_evaluaciones = 0
        return _api_ok(
            metrics={
                "estudiantes": total_estudiantes,
                "docentes": total_docentes,
                "preguntas": total_preguntas,
                "examenes": total_examenes,
                "areas": total_areas,
                "evaluaciones": total_evaluaciones,
            }
        )
    except Exception as exc:
        return _api_error(str(exc), status=500)


# Instancia de Flask y configuración

# =================== CONFIGURACIÓN DE MÓDULOS ===================
MODULOS = [
    {
        "nombre": "Banco de Preguntas",
        "ruta": "/banco-preguntas",
        "estado": "completo",  # completo | parcial | pendiente
        "roles": [
            "docente",
            "admin",
            "rector",
            "coordinador",
            "orientador",
            "secretaria academica",
        ],
        "icono": "fa-database",
    },
    {
        "nombre": "Generar Exámenes",
        "ruta": "/examenes",
        "estado": "parcial",
        "roles": ["docente", "coordinador", "orientador", "secretaria academica"],
        "icono": "fa-file-alt",
    },
    {
        "nombre": "Escáner OMR",
        "ruta": "/escanear",
        "estado": "completo",
        "roles": ["docente", "coordinador", "orientador", "secretaria academica"],
        "icono": "fa-qrcode",
    },
    {
        "nombre": "Resultados",
        "ruta": "/resultados",
        "estado": "parcial",
        "roles": [
            "docente",
            "admin",
            "rector",
            "coordinador",
            "orientador",
            "secretaria academica",
        ],
        "icono": "fa-chart-bar",
    },
    {
        "nombre": "Estudiantes",
        "ruta": "/estudiantes",
        "estado": "completo",
        "roles": [
            "docente",
            "admin",
            "rector",
            "coordinador",
            "secretaria",
            "orientador",
            "secretaria academica",
        ],
        "icono": "fa-users",
    },
    {
        "nombre": "Administración",
        "ruta": "/superadmin",
        "estado": "completo",
        "roles": ["admin", "rector", "orientador", "secretaria academica"],
        "icono": "fa-cogs",
    },
    {
        "nombre": "Gestión Académica",
        "ruta": "/gestion-academica",
        "estado": "parcial",
        "roles": ["coordinador", "rector", "orientador", "secretaria academica"],
        "icono": "fa-graduation-cap",
    },
    {
        "nombre": "Orientación Escolar",
        "ruta": "/orientacion",
        "estado": "parcial",
        "roles": ["orientador", "secretaria academica"],
        "icono": "fa-user-friends",
    },
    {
        "nombre": "Secretaría Académica",
        "ruta": "/secretaria",
        "estado": "parcial",
        "roles": ["secretaria", "secretaria academica"],
        "icono": "fa-archive",
    },
]

ESTADOS_MODULO = {
    "completo": {"color": "success", "icon": "fa-check-circle", "texto": "Completo"},
    "parcial": {
        "color": "warning",
        "icon": "fa-exclamation-triangle",
        "texto": "En desarrollo",
    },
    "pendiente": {
        "color": "secondary",
        "icon": "fa-times-circle",
        "texto": "Próximamente",
    },
}


def calcular_avance_modulos():
    total = len(MODULOS)
    completos = sum(1 for m in MODULOS if m["estado"] == "completo")
    parciales = sum(1 for m in MODULOS if m["estado"] == "parcial")
    avance = int((completos + 0.5 * parciales) / total * 100) if total else 0
    return avance


# Endpoint visual Swagger UI (debe ir después de instanciar app)


# --- Endpoint para servir OpenAPI como JSON ---
@app.route("/docs")
def docs_swagger():
    """Sirve Swagger UI con la documentación OpenAPI."""
    try:
        with open("openapi_banco_preguntas.yaml", "r", encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        return jsonify(spec)
    except Exception as e:
        return f"Error cargando OpenAPI: {e}", 500


# --- Endpoint para listar y descargar PDFs generados ---
@app.route("/api/v1/examenes/generados", methods=["GET"])
def api_listar_examenes_generados():
    """Lista los PDFs de exámenes generados y permite descargarlos."""
    output_dir = (BASE_DIR / "out_examenes_api").resolve()
    pdfs = []
    for ruta in glob.glob(str(output_dir / "*.pdf")):
        pdfs.append(
            {
                "nombre": os.path.basename(ruta),
                "ruta": str(ruta),
                "descargar": f"/api/v1/examenes/descargar/{os.path.basename(ruta)}",
            }
        )
    return jsonify({"pdfs": pdfs})


@app.route("/api/v1/examenes/descargar/<nombre_pdf>", methods=["GET"])
@app.route("/api/examenes/descargar/<nombre_pdf>", methods=["GET"])
def api_descargar_pdf(nombre_pdf):
    """Descarga un PDF generado por nombre."""
    output_dir = (BASE_DIR / "out_examenes_api").resolve()
    return send_from_directory(str(output_dir), nombre_pdf, as_attachment=True)


from banco_preguntas_profesional import BancoPreguntasProfesional


import json
import os
import subprocess
import sys
import hmac
from datetime import datetime
from pathlib import Path

BASE_DIR = (
    get_db_path().parent
    if "get_db_path" in globals()
    else Path(__file__).resolve().parent
)


def _python_candidates() -> list[Path]:
    current = Path(sys.executable).resolve()
    candidates: list[Path] = []
    for env_name in (".venv", "venv"):
        candidate = (BASE_DIR / env_name / "Scripts" / "python.exe").resolve()
        if candidate.exists() and candidate != current:
            candidates.append(candidate)
    return candidates


def _python_has_module(python_path: Path, module_name: str) -> bool:
    try:
        result = subprocess.run(
            [str(python_path), "-c", f"import {module_name}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception:
        return False
    return result.returncode == 0


def ensure_runtime_module(module_name: str) -> None:
    """Reintenta con el entorno local correcto si falta un módulo clave."""
    try:
        __import__(module_name)
        return
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            raise

    for candidate in _python_candidates():
        if _python_has_module(candidate, module_name):
            print(f"[INFO] {module_name} no está disponible en {sys.executable}")
            print(f"[INFO] Reintentando con {candidate}")
            os.execv(
                str(candidate),
                [str(candidate), str(Path(__file__).resolve()), *sys.argv[1:]],
            )

    raise ModuleNotFoundError(
        f"No se encontró {module_name} en el intérprete actual ni en los entornos locales venv/.venv."
    )


ensure_runtime_module("flask")

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    send_file,
    send_from_directory,
    url_for,
)

from autoevaluacion import ESCALA as AUTOEVALUACION_ESCALA
from autoevaluacion import DIMENSIONES as AUTOEVALUACION_DIMENSIONES
from core import examenes as core_examenes
from core import autoevaluacion_web as core_autoevaluacion_web
from core import autoevaluacion_docente_web as core_autoevaluacion_docente_web
from core import cuadernillos_web as core_cuadernillos_web
from core import examenes_admin_web as core_examenes_admin_web
from core import examenes_web as core_examenes_web
from core import examenes_generacion as core_examenes_generacion
from core import examenes_pdf as core_examenes_pdf
from core import docentes as core_docentes
from core import docentes_web as core_docentes_web
from core import certificados_web as core_certificados_web
from core import gestion_academica_web as core_gestion_academica_web
from core import matricula_web as core_matricula_web
from core import orientacion_web as core_orientacion_web
from core import plan_estudio_web as core_plan_estudio_web
from core import plantel_web as core_plantel_web
from core import preguntas as core_preguntas
from core import resultados_web as core_resultados_web
from core import seguridad_web as core_seguridad_web
from core import superadmin_web as core_superadmin_web
from core import usuarios as core_usuarios
from core import matricula as core_matricula
from core.construir_nombre import construir_nombre
from core import get_connection, get_db_path, ping_db
from core.omr import procesar_imagen_omr, parse_qr_payload

BASE_DIR = get_db_path().parent


def _nombre_estudiante(estudiante):
    nombre = construir_nombre(estudiante)
    if nombre:
        return nombre

    if hasattr(estudiante, "get"):
        documento = str(estudiante.get("documento") or "").strip()
    else:
        documento = str(getattr(estudiante, "documento", "") or "").strip()

    if documento:
        estudiante_bd = core_matricula.buscar_estudiante(documento)
        if estudiante_bd:
            return construir_nombre(estudiante_bd)

    return ""


# Endpoint visual Swagger UI (debe ir después de instanciar app)


API_VERSION = "v1"


def _api_json(payload=None, status=200, headers=None):
    body = dict(payload or {})
    body.setdefault("ok", status < 400)
    body.setdefault("api_version", API_VERSION)
    response = jsonify(body)
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    return response, status


def _api_ok(status=200, **payload):
    return _api_json({"ok": True, **payload}, status=status)


def _api_error(error, status=400, error_code=None, **payload):
    body = {"ok": False, "error": str(error)}
    if error_code:
        body["error_code"] = error_code
    body.update(payload)
    headers = None
    if status == 401:
        headers = {"WWW-Authenticate": "Bearer realm=SEA_API_V1"}
    return _api_json(body, status=status, headers=headers)


def _env_flag(name: str, default: bool = False) -> bool:
    """Convierte variables de entorno comunes a booleanos."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


def _api_v1_auth_required() -> bool:
    """Activa autenticación de /api/v1 cuando SEA_API_V1_AUTH_REQUIRED=1."""
    return _env_flag("SEA_API_V1_AUTH_REQUIRED", default=False)


def _api_v1_expected_token() -> str:
    """Token esperado para API v1 (header Bearer o X-SEA-API-Key)."""
    return str(os.environ.get("SEA_API_V1_KEY", "")).strip()


def _api_v1_is_public_path(path: str) -> bool:
    return path in {
        "/api/v1/health",
        "/api/v1/auth/status",
    }


def _api_v1_read_token() -> str:
    auth_header = str(request.headers.get("Authorization", "")).strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return str(request.headers.get("X-SEA-API-Key", "")).strip()


@app.before_request
def _api_v1_auth_guard():
    path = str(request.path or "")
    if not path.startswith("/api/v1/"):
        return None

    if _api_v1_is_public_path(path):
        return None

    if not _api_v1_auth_required():
        return None

    expected = _api_v1_expected_token()
    if not expected:
        return _api_error(
            "api_auth_misconfigured",
            status=500,
            error_code="auth_not_configured",
        )

    provided = _api_v1_read_token()
    if not provided:
        return _api_error("auth_required", status=401, error_code="missing_token")

    if not hmac.compare_digest(provided, expected):
        return _api_error("auth_invalid_token", status=401, error_code="invalid_token")

    return None


_WEB_PUBLIC_PATHS = {
    "/acceso",
    "/salir",
    "/favicon.ico",
}


def _resolver_identidad_web_por_documento(documento):
    identidad, _error = core_usuarios.resolver_identidad_acceso(documento)
    return identidad


def _web_current_user():
    user = session.get("web_user")
    return user if isinstance(user, dict) else {}


def _web_current_role():
    return core_usuarios.normalizar_rol(_web_current_user().get("rol"))


def _normalize_next_url(next_url):
    candidate = str(next_url or "/").strip() or "/"
    return candidate if candidate.startswith("/") else "/"


def _login_media_url(path_ref):
    ruta_txt = str(path_ref or "").strip()
    if not ruta_txt:
        return ""

    ruta = Path(ruta_txt)
    if not ruta.is_absolute():
        ruta = (BASE_DIR / ruta).resolve()
    else:
        ruta = ruta.resolve()

    if not ruta.exists() or not ruta.is_file():
        return ""

    try:
        rel = ruta.relative_to(BASE_DIR)
    except Exception:
        return ""

    rel_posix = rel.as_posix()
    if rel_posix.startswith("static/"):
        return "/" + rel_posix
    return url_for("web_login_media", rel_path=rel_posix)


def _ensure_contenido_institucional_login_web():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS contenido_institucional (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                mensaje TEXT NOT NULL,
                ruta_imagen TEXT,
                estado TEXT DEFAULT 'activo',
                orden INTEGER DEFAULT 0,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def _listar_contenido_institucional_login_web():
    _ensure_contenido_institucional_login_web()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, titulo, mensaje, ruta_imagen
            FROM contenido_institucional
            WHERE LOWER(TRIM(COALESCE(estado, 'activo'))) = 'activo'
            ORDER BY COALESCE(orden, 0), id
            """
        )
        rows = cur.fetchall()

    return [
        {
            "id": int(row[0]),
            "titulo": str(row[1] or "").strip(),
            "mensaje": str(row[2] or "").strip(),
            "image_url": _login_media_url(row[3] or ""),
        }
        for row in rows
    ]


def _formatear_nombre_institucion_login_web(nombre):
    texto = " ".join(str(nombre or "").strip().split())
    if not texto:
        return ""

    palabras = texto.split()
    if len(palabras) <= 3:
        return texto

    total = len(texto)
    mejor_indice = 1
    mejor_diferencia = total
    acumulado = 0
    for indice, palabra in enumerate(palabras[:-1], start=1):
        acumulado += len(palabra) + (1 if indice > 1 else 0)
        diferencia = abs((total / 2.0) - acumulado)
        if diferencia < mejor_diferencia:
            mejor_diferencia = diferencia
            mejor_indice = indice

    linea_1 = " ".join(palabras[:mejor_indice]).strip()
    linea_2 = " ".join(palabras[mejor_indice:]).strip()
    if not linea_1 or not linea_2:
        return texto
    return f"{linea_1}\n{linea_2}"


def _build_login_context(next_url="/"):
    plantel = core_plantel_web.obtener_configuracion_plantel()
    items = _listar_contenido_institucional_login_web()
    if not items:
        items = [
            {
                "id": 0,
                "titulo": "Bienvenidos",
                "mensaje": "Un entorno digital pensado para fortalecer la evaluación formativa, la toma de decisiones pedagógicas y el acceso ágil a la información académica.",
                "image_url": "",
            }
        ]

    logo_institucion = _login_media_url(plantel.get("logo_path") or "")
    if not logo_institucion:
        logo_institucion = _login_media_url(
            Path("imagenes_preguntas") / "logo_institucion.png"
        )

    return {
        "next_url": next_url,
        "login_nombre_institucion": _formatear_nombre_institucion_login_web(
            plantel.get("nombre_institucion")
            or "Institución Educativa Departamental Dagoberto Orozco Borja"
        ),
        "login_logo_sistema": _login_media_url("ICONO SEA.jpeg"),
        "login_logo_institucion": logo_institucion,
        "login_subtitulo": "Plataforma institucional para la gestión, aplicación y seguimiento de evaluaciones académicas.",
        "login_items": items,
        "login_footer_text": "Diseñador: Robert Calanche Villa | Versión 1.0 | 2026 | Todos los derechos reservados.",
    }


def _web_forbidden_response():
    mensaje = "Tu rol no tiene acceso a este recurso."
    if str(request.path or "").startswith("/api/"):
        return _api_error(mensaje, status=403, error_code="forbidden")
    flash(mensaje, "error")
    return redirect(url_for("index"))


def _web_session_api_is_public(path):
    normalized = core_usuarios.normalizar_api_path(path)
    return normalized in {"/api/health", "/api/auth/status"}


@app.context_processor
def _inject_web_access_context():
    web_user = _web_current_user()
    web_role = _web_current_role()
    return {
        "web_user": web_user,
        "web_role": web_role,
        "web_role_is": lambda *roles: web_role
        in {str(r or "").strip().lower() for r in roles},
        "web_can_access": lambda path: core_usuarios.rol_tiene_acceso_web(
            web_role, path
        ),
        "web_can_access_api": lambda path, method="GET": core_usuarios.rol_tiene_acceso_api(
            web_role, path, method
        ),
    }


@app.before_request
def _web_document_guard():
    path = str(request.path or "")

    if path.startswith("/api") or path.startswith("/static/"):
        return None

    if path.startswith("/login-media/"):
        return None

    if path in _WEB_PUBLIC_PATHS:
        return None

    if request.method == "OPTIONS":
        return None

    if session.get("web_user"):
        return None

    next_url = request.full_path if request.query_string else request.path
    return redirect(url_for("web_acceso", next=next_url))


@app.before_request
def _web_role_guard():
    path = str(request.path or "")

    if path.startswith("/static/"):
        return None

    if request.method == "OPTIONS":
        return None

    if path.startswith("/api/"):
        if _web_session_api_is_public(path):
            return None

        token_present = False
        if path.startswith("/api/v1/"):
            token_present = bool(_api_v1_read_token())

        user = _web_current_user()
        role = _web_current_role()

        if not user:
            if path.startswith("/api/v1/"):
                return None
            return _api_error(
                "auth_required",
                status=401,
                error_code="web_session_required",
            )

        if token_present and not role:
            return None

        if not core_usuarios.rol_tiene_acceso_api(role, path, request.method):
            return _api_error(
                "acceso_denegado",
                status=403,
                error_code="forbidden",
                rol=role,
            )
        return None

    if path in _WEB_PUBLIC_PATHS:
        return None

    if not session.get("web_user"):
        return None

    if not core_usuarios.rol_tiene_acceso_web(_web_current_role(), path):
        return _web_forbidden_response()

    return None


def get_ssl_context():
    """Usa HTTPS solo cuando se solicita explícitamente o en producción."""
    if _env_flag("SEA_DISABLE_HTTPS", default=False):
        return None

    raw_mode = (
        str(os.environ.get("SEA_RUNTIME_MODE", os.environ.get("SEA_ENV", "")))
        .strip()
        .lower()
    )
    https_requested = _env_flag("SEA_ENABLE_HTTPS", default=False) or raw_mode in {
        "prod",
        "produccion",
        "production",
    }
    if not https_requested:
        return None

    cert_path = BASE_DIR / "certs" / "server.pem"
    key_path = BASE_DIR / "certs" / "server_key.pem"

    if cert_path.exists() and key_path.exists():
        return (str(cert_path), str(key_path))

    if _env_flag("SEA_ALLOW_ADHOC_HTTPS", default=False):
        return "adhoc"

    return None


def get_access_scheme() -> str:
    """Esquema expuesto al cliente según la configuración SSL."""
    return "https" if get_ssl_context() else "http"


def _resolve_web_runtime(debug, use_reloader):
    """Resuelve perfil dev/prod para el servidor web.

    Prioridad:
    1) Parámetros explícitos en run_web_server
    2) Variables de entorno SEA_RUNTIME_MODE / SEA_ENV
    """
    raw_mode = (
        str(os.environ.get("SEA_RUNTIME_MODE", os.environ.get("SEA_ENV", "")))
        .strip()
        .lower()
    )
    env_dev = raw_mode in {"dev", "desarrollo", "development"}

    if debug is None:
        debug = env_dev

    if use_reloader is None:
        use_reloader = bool(debug)

    return bool(debug), bool(use_reloader)


def run_web_server(
    host: str = "0.0.0.0",
    port: int = 5000,
    debug: bool | None = None,
    use_reloader: bool | None = None,
    threaded: bool = True,
) -> None:
    """Punto único de arranque para Flask web/API."""
    debug, use_reloader = _resolve_web_runtime(debug, use_reloader)
    app.run(
        host=host,
        port=port,
        debug=debug,
        use_reloader=use_reloader,
        threaded=threaded,
        ssl_context=get_ssl_context(),
    )


# =============================================================================
# RUTAS WEB (HTML)
# =============================================================================


@app.get("/login-media/<path:rel_path>")
def web_login_media(rel_path):
    ruta = (BASE_DIR / str(rel_path or "")).resolve()
    try:
        ruta.relative_to(BASE_DIR)
    except Exception:
        abort(404)
    if not ruta.exists() or not ruta.is_file():
        abort(404)
    return send_file(str(ruta))


@app.get("/acceso")
def web_acceso():
    next_url = str(request.args.get("next") or "/").strip() or "/"
    return render_template("acceso.html", **_build_login_context(next_url=next_url))


@app.post("/acceso")
def web_acceso_submit():
    documento = str(request.form.get("documento") or "").strip()
    clave_maestra = str(request.form.get("clave_maestra") or "").strip()
    next_url = _normalize_next_url(request.form.get("next") or "/")

    if not documento:
        flash("Debe ingresar el documento.", "error")
        return redirect(url_for("web_acceso", next=next_url))

    try:
        identidad, error = core_usuarios.resolver_identidad_acceso(
            documento,
            clave_maestra=clave_maestra,
        )
    except Exception:
        identidad = None
        error = "documento_no_encontrado"

    if not identidad:
        mensajes = {
            "clave_maestra_requerida": "Para ingresar como administrador debes digitar la clave maestra.",
            "clave_maestra_invalida": "La clave maestra es incorrecta.",
            "clave_personal_requerida": "Para ingresar como personal (rector, secretaria, coordinador, orientador, etc.) debes digitar la clave. La clave por defecto es el número de documento.",
            "clave_personal_invalida": "La clave es incorrecta. Recuerda que la clave por defecto es el número de documento.",
            "documento_no_encontrado": "Documento no encontrado.",
        }
        flash(mensajes.get(error, "No fue posible validar el acceso."), "error")
        return redirect(url_for("web_acceso", next=next_url))

    session["web_user"] = identidad
    session.permanent = True
    flash(
        f"Acceso concedido. Bienvenido {identidad.get('nombre', '')}.",
        "success",
    )
    return redirect(next_url)


@app.get("/salir")
def web_salir():
    session.pop("web_user", None)
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("web_acceso"))


@app.get("/")
def index():
    """Dashboard principal con visualización progresiva de módulos."""
    try:
        grados = core_usuarios.cargar_grados()
        areas = core_preguntas.cargar_areas()
    except Exception:
        grados, areas = [], []
    web_user = session.get("web_user") or {}
    rol = core_usuarios.normalizar_rol(web_user.get("rol"))
    # Filtrar módulos por rol
    modulos_visibles = [
        {
            **m,
            "estado_info": ESTADOS_MODULO.get(m["estado"], ESTADOS_MODULO["pendiente"]),
        }
        for m in MODULOS
        if rol in m["roles"]
    ]
    avance = calcular_avance_modulos()
    return render_template(
        "index.html",
        grados=grados,
        areas=areas,
        web_user=web_user,
        modulos=modulos_visibles,
        avance_migracion=avance,
    )


@app.get("/superadmin")
def web_superadmin():
    """Hub del módulo SuperAdmin migrado por fases."""
    return render_template("superadmin.html", web_user=session.get("web_user"))


@app.get("/matricula")
def web_matricula():
    """Gestor de matrícula web (Fase 2)."""
    return render_template("matricula.html", web_user=session.get("web_user"))


@app.get("/plan-estudios")
def web_plan_estudios():
    """Módulo web de Plan de Estudios (Fase 2)."""
    return render_template("plan_estudios.html", web_user=session.get("web_user"))


@app.get("/seguridad")
def web_seguridad():
    """Seguridad y acceso maestro web (Fase 3)."""
    return render_template("seguridad.html", web_user=session.get("web_user"))


@app.get("/maestro")
def web_maestro():
    """Acceso Maestro web para seguimiento y control de resultados."""
    try:
        grados = core_usuarios.cargar_grados()
        areas = core_preguntas.cargar_areas()
    except Exception:
        grados, areas = [], []
    return render_template(
        "docente.html",
        grados=grados,
        areas=areas,
        web_user=session.get("web_user"),
        maestro_mode=True,
    )


@app.get("/configuracion-plantel")
def web_configuracion_plantel():
    """Configuración institucional del plantel (Fase 4)."""
    return render_template(
        "configuracion_plantel.html", web_user=session.get("web_user")
    )


@app.get("/planta-docente")
def web_planta_docente():
    """Gestión de la planta docente (Fase 5)."""
    return render_template("planta_docente.html", web_user=session.get("web_user"))


@app.get("/carga-academica")
def web_carga_academica():
    """Gestión web de carga académica."""
    return render_template("carga_academica.html", web_user=session.get("web_user"))


@app.get("/gestion-academica")
def web_gestion_academica():
    """Hub administrativo para la operacion academica institucional."""
    return render_template("gestion_academica.html", web_user=session.get("web_user"))


@app.get("/orientacion")
def web_orientacion():
    """Hub de orientacion escolar para seguimiento academico y apoyo institucional."""
    try:
        grados = core_usuarios.cargar_grados()
        areas = core_preguntas.cargar_areas()
    except Exception:
        grados, areas = [], []
    return render_template(
        "orientacion.html",
        web_user=session.get("web_user"),
        grados=grados,
        areas=areas,
    )


@app.get("/secretaria")
def web_secretaria():
    """Hub de secretaria academica para tramites, exportaciones y soporte documental."""
    return render_template("secretaria.html", web_user=session.get("web_user"))


@app.get("/examenes")
def web_examenes():
    """Gestión y generación de exámenes."""
    try:
        grados = core_usuarios.cargar_grados()
        areas = core_preguntas.cargar_areas()
    except Exception:
        grados, areas = [], []
    return render_template(
        "examenes.html",
        grados=grados,
        areas=areas,
        web_user=session.get("web_user"),
    )


@app.get("/docente")
def web_docente():
    """Panel docente web con configuración y seguimiento de estudiantes."""
    try:
        grados = core_usuarios.cargar_grados()
        areas = core_preguntas.cargar_areas()
    except Exception:
        grados, areas = [], []
    return render_template(
        "docente.html",
        grados=grados,
        areas=areas,
        web_user=session.get("web_user"),
    )


@app.get("/banco-preguntas")
def web_banco_preguntas():
    """Gestión del banco de preguntas."""
    try:
        areas = core_preguntas.cargar_areas()
        grados = core_usuarios.cargar_grados()
    except Exception:
        areas, grados = [], []
    return render_template(
        "banco_preguntas.html",
        areas=areas,
        grados=grados,
        web_user=session.get("web_user"),
    )


@app.get("/calificaciones")
def web_calificaciones():
    """Consulta de calificaciones."""
    try:
        grados = core_usuarios.cargar_grados()
        areas = core_preguntas.cargar_areas()
    except Exception:
        grados, areas = [], []
    return render_template(
        "calificaciones.html",
        grados=grados,
        areas=areas,
        web_user=session.get("web_user"),
    )


@app.get("/escanear")
def web_escanear():
    """Escáner OMR desde navegador (acceso con cámara del dispositivo móvil)."""
    return render_template("escanear.html", web_user=session.get("web_user"))


@app.get("/examen")
def web_examen():
    """Portal de examen para el estudiante (SPA)."""
    return render_template("examen.html", web_user=session.get("web_user"))


@app.get("/autoevaluacion")
def web_autoevaluacion():
    """Portal web de autoevaluacion para el estudiante."""
    return render_template(
        "autoevaluacion.html",
        web_user=session.get("web_user"),
        escala=AUTOEVALUACION_ESCALA,
    )


@app.get("/docente/autoevaluacion")
def web_docente_autoevaluacion():
    """Constructor y panel de autoevaluacion para docentes."""
    web_user = session.get("web_user") or {}
    return render_template(
        "autoevaluacion_docente.html",
        web_user=web_user,
        escala=AUTOEVALUACION_ESCALA,
        dimensiones=AUTOEVALUACION_DIMENSIONES,
        proxy_mode=core_usuarios.normalizar_rol(web_user.get("rol"))
        == core_usuarios.ROL_ADMIN,
    )


# ===================== NUEVAS VISTAS WEB =====================
@app.get("/resultados")
def web_resultados():
    """Vista de resultados de exámenes y evaluaciones."""
    try:
        grados = core_usuarios.cargar_grados()
        areas = core_preguntas.cargar_areas()
    except Exception:
        grados, areas = [], []
    return render_template(
        "resultados.html",
        web_user=session.get("web_user"),
        grados=grados,
        areas=areas,
    )


@app.get("/estudiantes")
def web_estudiantes():
    """Vista de gestión y consulta de estudiantes."""
    return render_template("estudiantes.html", web_user=session.get("web_user"))


# =============================================================================
# API — Examen Web (Estudiante)
# =============================================================================

# =============================================================================
# API — Banco de Preguntas Profesional (CRUD)
# =============================================================================

from banco_preguntas_profesional import BancoPreguntasProfesional


@app.get("/api/v1/banco-preguntas")
def api_banco_preguntas_listar():
    """Lista preguntas filtradas del banco profesional (filtros: grado, area, evaluacion)."""
    grado = request.args.get("grado")
    area = request.args.get("area")
    evaluacion = request.args.get("evaluacion")
    try:
        banco = BancoPreguntasProfesional()
        preguntas = banco.obtener_preguntas_filtradas(
            grado=grado, area=area, evaluacion=evaluacion
        )
        # Limitar columnas sensibles si es necesario
        preguntas_json = preguntas.to_dict(orient="records")
        return _api_ok(total=len(preguntas_json), items=preguntas_json)
    except Exception as exc:
        return _api_error(str(exc), status=500)


@app.post("/api/examenes/generar")
def api_examenes_generar():
    """Genera exámenes desde el formulario web y retorna el resumen de resultados."""
    payload = request.get_json(force=True, silent=True) or {}
    return _procesar_generacion_examenes(payload)


def _examen_require_student():
    """Retorna la identidad del estudiante en sesión o un error 401/403."""
    user = _web_current_user()
    if not user or not user.get("documento"):
        return None, _api_error("auth_required", status=401)
    if core_usuarios.normalizar_rol(user.get("rol")) != core_usuarios.ROL_ESTUDIANTE:
        return None, _api_error(
            "solo_estudiantes", status=403, error_code="student_only"
        )
    return user, None


def _docente_require_user(payload=None):
    user = _web_current_user()
    if not user or not user.get("documento"):
        return None, _api_error("auth_required", status=401)

    role = core_usuarios.normalizar_rol(user.get("rol"))
    if role not in {
        core_usuarios.ROL_DOCENTE,
        core_usuarios.ROL_ADMIN,
        core_usuarios.ROL_COORDINADOR,
        core_usuarios.ROL_RECTOR,
    }:
        return None, _api_error("solo_docentes", status=403, error_code="teacher_only")

    if role == core_usuarios.ROL_DOCENTE:
        return str(user.get("documento") or "").strip(), None

    source = dict(payload or {})
    docente_documento = str(
        source.get("docente_documento") or request.args.get("docente_documento") or ""
    ).strip()
    if not docente_documento:
        return None, _api_error(
            "docente_documento_requerido",
            status=400,
            error_code="teacher_document_required",
        )
    return docente_documento, None


@app.get("/api/v1/examen/areas")
@app.get("/api/examen/areas")
def api_examen_areas():
    """Lista las áreas disponibles con estado para el estudiante autenticado."""
    user, err = _examen_require_student()
    if err:
        return err
    try:
        areas = core_examenes_web.listar_areas_con_estado(
            documento=user["documento"],
            grado=str(user.get("grado") or "").strip(),
            curso=user.get("curso"),
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(areas=areas)


@app.post("/api/v1/examen/iniciar")
@app.post("/api/examen/iniciar")
def api_examen_iniciar():
    """Inicia o reanuda un examen para el área indicada."""
    user, err = _examen_require_student()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    area = str(data.get("area") or "").strip()
    preflight = bool(data.get("__preflight"))
    if not area:
        return _api_error("parametro_area_requerido", status=400)

    try:
        resultado = core_examenes_web.iniciar_o_reanudar_examen(
            documento=user["documento"],
            nombre=_nombre_estudiante(user),
            grado=str(user.get("grado") or "").strip(),
            area=area,
            curso=user.get("curso"),
            preflight=preflight,
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    if not resultado.get("ok"):
        return _api_error(resultado.get("error", "error_inicio"), status=400)
    return _api_ok(**{k: v for k, v in resultado.items() if k != "ok"})


@app.post("/api/v1/examen/respuesta")
@app.post("/api/examen/respuesta")
def api_examen_respuesta():
    """Guarda una respuesta individual (llamada después de cada pregunta)."""
    user, err = _examen_require_student()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    area = str(data.get("area") or "").strip()
    evaluacion = str(data.get("evaluacion") or "").strip()
    enunciado = str(data.get("enunciado") or "").strip()
    seleccion = str(data.get("seleccion") or "").strip().upper()

    try:
        intento_num = int(data.get("intento_num", 0) or 0)
        pregunta_id = int(data.get("pregunta_id", 0) or 0)
    except (ValueError, TypeError):
        return _api_error("parametros_invalidos", status=400)

    if not area or not evaluacion:
        return _api_error("area_y_evaluacion_requeridos", status=400)
    if pregunta_id <= 0 or intento_num <= 0:
        return _api_error("intento_o_pregunta_invalidos", status=400)
    if seleccion not in {"A", "B", "C", "D"}:
        return _api_error("respuesta_invalida__debe_ser_A_B_C_o_D", status=400)

    try:
        resultado = core_examenes_web.guardar_respuesta(
            documento=user["documento"],
            nombre=_nombre_estudiante(user),
            grado=str(user.get("grado") or "").strip(),
            curso=str(user.get("curso") or "").strip(),
            area=area,
            evaluacion=evaluacion,
            intento_num=intento_num,
            pregunta_id=pregunta_id,
            enunciado=enunciado,
            seleccion=seleccion,
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    if not resultado.get("ok"):
        return _api_error(resultado.get("error", "error_guardar"), status=400)
    return _api_ok(
        guardado=True,
        es_correcta=resultado.get("es_correcta"),
    )


@app.post("/api/v1/examen/finalizar")
@app.post("/api/examen/finalizar")
def api_examen_finalizar():
    """Finaliza el examen, calcula nota y persiste el resultado."""
    user, err = _examen_require_student()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    area = str(data.get("area") or "").strip()

    try:
        intento_num = int(data.get("intento_num", 0) or 0)
        intento_id = int(data.get("intento_id", 0) or 0)
    except (ValueError, TypeError):
        return _api_error("parametros_invalidos", status=400)

    if not area or intento_num <= 0 or intento_id <= 0:
        return _api_error("area_intento_id_requeridos", status=400)

    try:
        resultado = core_examenes_web.finalizar_examen(
            documento=user["documento"],
            area=area,
            intento_num=intento_num,
            intento_id=intento_id,
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    if not resultado.get("ok"):
        return _api_error(resultado.get("error", "error_finalizar"), status=400)
    return _api_ok(
        nota=resultado["nota"],
        correctas=resultado["correctas"],
        total=resultado["total"],
        nivel_desempeno=resultado["nivel_desempeno"],
        recomendacion=resultado["recomendacion"],
    )


@app.get("/api/v1/examen/historial")
@app.get("/api/examen/historial")
def api_examen_historial():
    """Retorna el historial de intentos del estudiante autenticado."""
    user, err = _examen_require_student()
    if err:
        return err
    try:
        historial = core_examenes_web.historial_estudiante(user["documento"])
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(historial=historial)


@app.get("/api/v1/examen/detalle")
@app.get("/api/examen/detalle")
def api_examen_detalle():
    """Retorna el detalle de respuestas de un intento (requiere puede_revisar=1)."""
    user, err = _examen_require_student()
    if err:
        return err

    area = str(request.args.get("area") or "").strip()
    try:
        intento_num = int(request.args.get("intento") or 0)
    except (ValueError, TypeError):
        return _api_error("parametro_intento_invalido", status=400)

    if not area or intento_num <= 0:
        return _api_error("area_e_intento_requeridos", status=400)

    # Verificar que el intento pertenece al usuario y tiene revisión autorizada
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT puede_revisar FROM resultados "
                "WHERE documento=? AND area=? AND intento=? ORDER BY id DESC LIMIT 1",
                (user["documento"], area, intento_num),
            )
            row = cur.fetchone()
    except Exception as exc:
        return _api_error(exc, status=500)

    if not row:
        return _api_error("intento_no_encontrado", status=404)
    if not row[0]:
        return _api_error(
            "revision_no_autorizada",
            status=403,
            error_code="revision_no_autorizada",
        )

    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT pregunta_id, enunciado, respuesta_seleccionada, "
                "respuesta_correcta, es_correcta "
                "FROM respuestas_estudiantes "
                "WHERE documento=? AND area=? AND intento=? ORDER BY pregunta_id ASC",
                (user["documento"], area, intento_num),
            )
            cols = [d[0] for d in cur.description]
            respuestas = [dict(zip(cols, r)) for r in cur.fetchall()]
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(area=area, intento=intento_num, respuestas=respuestas)


@app.get("/api/v1/autoevaluacion/activas")
@app.get("/api/autoevaluacion/activas")
def api_autoevaluacion_activas():
    user, err = _examen_require_student()
    if err:
        return err
    try:
        instrumentos = core_autoevaluacion_web.listar_instrumentos_estudiante(
            documento=user["documento"],
            grado=str(user.get("grado") or "").strip(),
            curso=str(user.get("curso") or "").strip(),
        )
        historial = core_autoevaluacion_web.resumir_historial_estudiante(
            documento=user["documento"],
            grado=str(user.get("grado") or "").strip(),
            curso=str(user.get("curso") or "").strip(),
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(instrumentos=instrumentos, historial=historial)


@app.get("/api/v1/autoevaluacion/<int:instrumento_id>")
@app.get("/api/autoevaluacion/<int:instrumento_id>")
def api_autoevaluacion_detalle(instrumento_id):
    user, err = _examen_require_student()
    if err:
        return err
    try:
        instrumento = core_autoevaluacion_web.obtener_instrumento_estudiante(
            documento=user["documento"],
            grado=str(user.get("grado") or "").strip(),
            curso=str(user.get("curso") or "").strip(),
            instrumento_id=instrumento_id,
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    if not instrumento:
        return _api_error("autoevaluacion_no_encontrada", status=404)
    return _api_ok(instrumento=instrumento)


@app.post("/api/v1/autoevaluacion/<int:instrumento_id>/responder")
@app.post("/api/autoevaluacion/<int:instrumento_id>/responder")
def api_autoevaluacion_responder(instrumento_id):
    user, err = _examen_require_student()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    respuestas = data.get("respuestas") or []

    try:
        resultado = core_autoevaluacion_web.responder_instrumento_estudiante(
            documento=user["documento"],
            grado=str(user.get("grado") or "").strip(),
            curso=str(user.get("curso") or "").strip(),
            instrumento_id=instrumento_id,
            respuestas=respuestas,
        )
    except ValueError as exc:
        message = str(exc)
        status = 400
        if message == "autoevaluacion_no_encontrada":
            status = 404
        elif message == "autoevaluacion_ya_respondida":
            status = 409
        return _api_error(message, status=status)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(**resultado)


@app.get("/api/v1/docente/autoevaluacion/resumen")
@app.get("/api/docente/autoevaluacion/resumen")
def api_docente_autoevaluacion_resumen():
    docente_documento, err = _docente_require_user()
    if err:
        return err
    try:
        fuentes = core_autoevaluacion_docente_web.listar_fuentes_docente(
            docente_documento
        )
        instrumentos = core_autoevaluacion_docente_web.listar_instrumentos_docente(
            docente_documento
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(fuentes=fuentes, instrumentos=instrumentos)


@app.post("/api/v1/docente/autoevaluacion/instrumentos")
@app.post("/api/docente/autoevaluacion/instrumentos")
def api_docente_autoevaluacion_guardar():
    data = request.get_json(silent=True) or {}
    docente_documento, err = _docente_require_user(payload=data)
    if err:
        return err
    try:
        instrumento_id = data.get("instrumento_id")
        if instrumento_id in (None, ""):
            instrumento_id = None
        else:
            instrumento_id = int(instrumento_id)
        resultado = core_autoevaluacion_docente_web.guardar_instrumento_docente(
            docente_documento,
            instrumento_id=instrumento_id,
            area=data.get("area"),
            grado=data.get("grado"),
            curso=data.get("curso"),
            periodo=data.get("periodo"),
            preguntas=data.get("preguntas") or [],
            habilitada=_payload_bool(data.get("habilitada"), default=False),
        )
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(mensaje="Instrumento guardado", **resultado)


@app.post("/api/v1/docente/autoevaluacion/instrumentos/<int:instrumento_id>/estado")
@app.post("/api/docente/autoevaluacion/instrumentos/<int:instrumento_id>/estado")
def api_docente_autoevaluacion_estado(instrumento_id):
    data = request.get_json(silent=True) or {}
    docente_documento, err = _docente_require_user(payload=data)
    if err:
        return err
    try:
        resultado = core_autoevaluacion_docente_web.cambiar_estado_instrumento_docente(
            docente_documento,
            instrumento_id,
            _payload_bool(data.get("habilitada"), default=False),
        )
    except ValueError as exc:
        return _api_error(str(exc), status=404)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(mensaje="Estado actualizado", **resultado)


@app.get("/api/v1/docente/autoevaluacion/resultados")
@app.get("/api/docente/autoevaluacion/resultados")
def api_docente_autoevaluacion_resultados():
    docente_documento, err = _docente_require_user()
    if err:
        return err
    try:
        data = core_autoevaluacion_docente_web.consultar_resultados_docente(
            docente_documento,
            area=request.args.get("area"),
            grado=request.args.get("grado"),
            curso=request.args.get("curso"),
            periodo=request.args.get("periodo"),
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**data)


@app.get("/api/v1/docente/autoevaluacion/exportar")
@app.get("/api/docente/autoevaluacion/exportar")
def api_docente_autoevaluacion_exportar():
    docente_documento, err = _docente_require_user()
    if err:
        return err
    try:
        archivo = core_autoevaluacion_docente_web.exportar_resultados_docente_excel(
            docente_documento,
            area=request.args.get("area"),
            grado=request.args.get("grado"),
            curso=request.args.get("curso"),
            periodo=request.args.get("periodo"),
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return send_file(
        archivo,
        as_attachment=True,
        download_name="autoevaluacion_docente.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/api/v1/docente/autoevaluacion/resultados/<int:respuesta_id>")
@app.get("/api/docente/autoevaluacion/resultados/<int:respuesta_id>")
def api_docente_autoevaluacion_resultado_detalle(respuesta_id):
    docente_documento, err = _docente_require_user()
    if err:
        return err
    try:
        detalle = core_autoevaluacion_docente_web.detalle_resultado_docente(
            docente_documento,
            respuesta_id,
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    if not detalle:
        return _api_error("resultado_no_encontrado", status=404)
    return _api_ok(detalle=detalle)


@app.get("/api/v1/usuarios/estudiante/<documento>")
@app.get("/api/usuarios/estudiante/<documento>")
def api_validar_estudiante(documento):
    data = core_usuarios.validar_estudiante(documento)
    if not data:
        return _api_error("estudiante_no_encontrado", status=404)
    return _api_ok(estudiante=data)


@app.get("/api/v1/superadmin/resumen")
@app.get("/api/superadmin/resumen")
def api_superadmin_resumen():
    """Resumen y roadmap del módulo SuperAdmin web por fases."""
    try:
        data = core_superadmin_web.resumen_superadmin()
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**data)


@app.get("/api/v1/plan-estudios/catalogos")
@app.get("/api/plan-estudios/catalogos")
def api_plan_estudios_catalogos():
    try:
        data = core_plan_estudio_web.catalogos_plan_estudio()
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**data)


@app.get("/api/v1/plan-estudios")
@app.get("/api/plan-estudios")
def api_plan_estudios_listado():
    try:
        data = core_plan_estudio_web.listar_plan_estudio(
            nivel=request.args.get("nivel"),
            grado=request.args.get("grado"),
            curso=request.args.get("curso"),
            area=request.args.get("area"),
            limit=request.args.get("limit", 200),
            offset=request.args.get("offset", 0),
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(total=data["total"], items=data["items"])


@app.post("/api/v1/plan-estudios")
@app.post("/api/plan-estudios")
def api_plan_estudios_crear():
    payload = request.get_json(silent=True) or {}
    try:
        new_id = core_plan_estudio_web.crear_registro(payload)
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(mensaje="Registro creado", id=new_id)


@app.put("/api/v1/plan-estudios/<int:registro_id>")
@app.put("/api/plan-estudios/<int:registro_id>")
def api_plan_estudios_actualizar(registro_id):
    payload = request.get_json(silent=True) or {}
    try:
        core_plan_estudio_web.actualizar_registro(registro_id, payload)
    except ValueError as exc:
        status = 404 if str(exc) == "registro_no_encontrado" else 400
        return _api_error(str(exc), status=status)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(mensaje="Registro actualizado", id=registro_id)


@app.delete("/api/v1/plan-estudios/<int:registro_id>")
@app.delete("/api/plan-estudios/<int:registro_id>")
def api_plan_estudios_eliminar(registro_id):
    try:
        deleted = core_plan_estudio_web.eliminar_registro(registro_id)
    except Exception as exc:
        return _api_error(exc, status=500)
    if deleted <= 0:
        return _api_error("registro_no_encontrado", status=404)
    return _api_ok(mensaje="Registro eliminado", id=registro_id)


@app.post("/api/v1/plan-estudios/copiar")
@app.post("/api/plan-estudios/copiar")
def api_plan_estudios_copiar():
    payload = request.get_json(silent=True) or {}
    try:
        data = core_plan_estudio_web.copiar_plan(
            origen_grado=payload.get("origen_grado"),
            origen_curso=payload.get("origen_curso"),
            destino_grado=payload.get("destino_grado"),
            destino_curso=payload.get("destino_curso"),
            reemplazar=payload.get("reemplazar", False),
        )
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(mensaje="Plan copiado", **data)


@app.post("/api/v1/plan-estudios/importar")
@app.post("/api/plan-estudios/importar")
def api_plan_estudios_importar():
    archivo = request.files.get("archivo")
    if not archivo:
        return _api_error("archivo_requerido", status=400)

    raw = archivo.read() or b""
    if not raw:
        return _api_error("archivo_vacio", status=400)

    try:
        data = core_plan_estudio_web.importar_plan_estudio_desde_archivo(
            filename=archivo.filename,
            raw_bytes=raw,
        )
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(mensaje="Importación completada", **data)


@app.get("/api/v1/matricula/listado")
@app.get("/api/matricula/listado")
def api_matricula_listado():
    try:
        data = core_matricula_web.listar_estudiantes(
            grado=request.args.get("grado"),
            curso=request.args.get("curso"),
            jornada=request.args.get("jornada"),
            nombre=request.args.get("nombre"),
            limit=request.args.get("limit", 200),
            offset=request.args.get("offset", 0),
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(total=data["total"], estudiantes=data["estudiantes"])


@app.get("/api/v1/matricula/catalogos")
@app.get("/api/matricula/catalogos")
def api_matricula_catalogos():
    try:
        data = core_matricula_web.catalogos()
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**data)


@app.post("/api/v1/matricula/importar")
@app.post("/api/matricula/importar")
def api_matricula_importar():
    archivo = request.files.get("archivo")
    if not archivo:
        return _api_error("archivo_requerido", status=400)
    raw = archivo.read() or b""
    if not raw:
        return _api_error("archivo_vacio", status=400)
    try:
        total = core_matricula_web.importar_masivo_desde_archivo(
            filename=archivo.filename,
            raw_bytes=raw,
        )
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(mensaje="Importación completada", total=total)


@app.post("/api/v1/matricula/cambiar-curso")
@app.post("/api/matricula/cambiar-curso")
def api_matricula_cambiar_curso():
    data = request.get_json(silent=True) or {}
    try:
        total = core_matricula_web.cambiar_curso_masivo(
            documentos=data.get("documentos") or [],
            nuevo_grado=data.get("nuevo_grado"),
            nuevo_curso=data.get("nuevo_curso"),
            nueva_jornada=data.get("nueva_jornada"),
        )
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(mensaje="Cambio de curso aplicado", total=total)


@app.get("/api/v1/seguridad/resumen")
@app.get("/api/seguridad/resumen")
def api_seguridad_resumen():
    try:
        data = core_seguridad_web.resumen_seguridad()
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**data)


@app.post("/api/v1/seguridad/cambiar-clave")
@app.post("/api/seguridad/cambiar-clave")
def api_seguridad_cambiar_clave():
    data = request.get_json(silent=True) or {}
    try:
        result = core_seguridad_web.cambiar_clave_maestra(
            actual=data.get("clave_actual"),
            nueva=data.get("clave_nueva"),
            confirmar=data.get("clave_confirmar"),
        )
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**result)


@app.get("/api/v1/plantel/config")
@app.get("/api/plantel/config")
def api_plantel_config_get():
    try:
        data = core_plantel_web.obtener_configuracion_plantel()
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(configuracion=data)


@app.put("/api/v1/plantel/config")
@app.put("/api/plantel/config")
def api_plantel_config_put():
    data = request.get_json(silent=True) or {}
    try:
        result = core_plantel_web.guardar_configuracion_plantel(data)
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**result)


@app.get("/api/v1/plantel/escala")
@app.get("/api/plantel/escala")
def api_plantel_escala_get():
    try:
        escala = core_plantel_web.obtener_escala_valoracion()
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(escala=escala)


@app.put("/api/v1/plantel/escala")
@app.put("/api/plantel/escala")
def api_plantel_escala_put():
    data = request.get_json(silent=True) or {}
    try:
        result = core_plantel_web.guardar_escala_valoracion(data.get("escala"))
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**result)


@app.post("/api/v1/plantel/logo")
@app.post("/api/plantel/logo")
def api_plantel_logo_post():
    archivo = request.files.get("archivo")
    if not archivo:
        return _api_error("archivo_requerido", status=400)
    raw = archivo.read() or b""
    try:
        result = core_plantel_web.guardar_logo_plantel(
            filename=archivo.filename,
            raw_bytes=raw,
            base_dir=BASE_DIR,
        )
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**result)


@app.get("/api/v1/secretaria/estudiante")
@app.get("/api/secretaria/estudiante")
def api_secretaria_estudiante():
    documento = request.args.get("documento")
    try:
        estudiante = core_certificados_web.obtener_estudiante(documento)
        historial = core_certificados_web.listar_documentos(
            documento=documento, limit=10
        )
    except ValueError as exc:
        message = str(exc)
        status = 404 if message == "estudiante_no_encontrado" else 400
        return _api_error(message, status=status)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(estudiante=estudiante, historial=historial)


@app.get("/api/v1/secretaria/documentos")
@app.get("/api/secretaria/documentos")
def api_secretaria_documentos():
    documento = request.args.get("documento")
    limit = request.args.get("limit", 20)
    try:
        historial = core_certificados_web.listar_documentos(
            documento=documento, limit=limit
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(documentos=historial, total=len(historial))


@app.get("/api/v1/secretaria/documentos/matricula")
@app.get("/api/secretaria/documentos/matricula")
def api_secretaria_documento_matricula():
    documento = request.args.get("documento")
    try:
        result = core_certificados_web.generar_certificado_matricula_web(documento)
    except ValueError as exc:
        message = str(exc)
        status = 404 if message == "estudiante_no_encontrado" else 400
        return _api_error(message, status=status)
    except Exception as exc:
        return _api_error(exc, status=500)
    return send_file(
        str(result["ruta"]),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=result["nombre_archivo"],
    )


@app.get("/api/v1/secretaria/documentos/acta-grado")
@app.get("/api/secretaria/documentos/acta-grado")
def api_secretaria_documento_acta_grado():
    documento = request.args.get("documento")
    numero_acta = request.args.get("numero_acta")
    fecha_grado = request.args.get("fecha_grado")
    try:
        result = core_certificados_web.generar_acta_grado_web(
            documento,
            numero_acta=numero_acta,
            fecha_grado=fecha_grado,
        )
    except ValueError as exc:
        message = str(exc)
        status = 404 if message == "estudiante_no_encontrado" else 400
        return _api_error(message, status=status)
    except Exception as exc:
        return _api_error(exc, status=500)
    return send_file(
        str(result["ruta"]),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=result["nombre_archivo"],
    )


@app.get("/api/v1/secretaria/documentos/calificaciones")
@app.get("/api/secretaria/documentos/calificaciones")
def api_secretaria_documento_calificaciones():
    documento = request.args.get("documento")
    try:
        result = core_certificados_web.generar_certificado_calificaciones_web(documento)
    except ValueError as exc:
        message = str(exc)
        status = 404 if message == "estudiante_no_encontrado" else 400
        return _api_error(message, status=status)
    except Exception as exc:
        return _api_error(exc, status=500)
    return send_file(
        str(result["ruta"]),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=result["nombre_archivo"],
    )


@app.get("/api/v1/secretaria/documentos/diploma")
@app.get("/api/secretaria/documentos/diploma")
def api_secretaria_documento_diploma():
    documento = request.args.get("documento")
    numero_diploma = request.args.get("numero_diploma")
    fecha_grado = request.args.get("fecha_grado")
    try:
        result = core_certificados_web.generar_diploma_web(
            documento,
            numero_diploma=numero_diploma,
            fecha_grado=fecha_grado,
        )
    except ValueError as exc:
        message = str(exc)
        status = 404 if message == "estudiante_no_encontrado" else 400
        return _api_error(message, status=status)
    except Exception as exc:
        return _api_error(exc, status=500)
    return send_file(
        str(result["ruta"]),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=result["nombre_archivo"],
    )


@app.get("/api/v1/usuarios/docente/<documento>")
@app.get("/api/usuarios/docente/<documento>")
def api_validar_docente(documento):
    nombre = core_usuarios.validar_docente(documento)
    if not nombre:
        return _api_error("docente_no_encontrado", status=404)
    return _api_ok(nombre=nombre)


@app.get("/api/v1/docentes")
@app.get("/api/docentes")
def api_docentes():
    """Lista docentes con filtros opcionales."""
    estado = request.args.get("estado")
    cargo = request.args.get("cargo")
    limit = request.args.get("limit", 100)
    offset = request.args.get("offset", 0)

    try:
        data = core_docentes.listar_docentes(
            estado=estado,
            cargo=cargo,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(total=data["total"], docentes=data["docentes"])


@app.post("/api/v1/docentes")
@app.post("/api/docentes")
def api_crear_docente():
    """Crea un docente."""
    data = request.get_json() or {}

    try:
        core_docentes.crear_o_actualizar_docente(
            tipo_documento=data.get("tipo_documento", "CC"),
            documento=data.get("documento"),
            nombre=data.get("nombre"),
            sexo=data.get("sexo", ""),
            fecha_nacimiento=data.get("fecha_nacimiento", ""),
            telefono=data.get("telefono", ""),
            correo=data.get("correo", ""),
            cargo=data.get("cargo", "Docente"),
            jornada=data.get("jornada", "Mañana"),
            sede=data.get("sede", ""),
            estado=data.get("estado", "Activo"),
        )
    except ValueError as e:
        return _api_error(e, status=400)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(mensaje="Docente guardado")


@app.put("/api/v1/docentes/<documento>")
@app.put("/api/docentes/<documento>")
def api_actualizar_docente(documento):
    """Actualiza un docente por documento."""
    data = request.get_json() or {}

    try:
        actualizado = core_docentes.crear_o_actualizar_docente(
            tipo_documento=data.get("tipo_documento", "CC"),
            documento=data.get("documento", documento),
            nombre=data.get("nombre"),
            sexo=data.get("sexo", ""),
            fecha_nacimiento=data.get("fecha_nacimiento", ""),
            telefono=data.get("telefono", ""),
            correo=data.get("correo", ""),
            cargo=data.get("cargo", "Docente"),
            jornada=data.get("jornada", "Mañana"),
            sede=data.get("sede", ""),
            estado=data.get("estado", "Activo"),
            documento_original=documento,
        )
        if not actualizado:
            return _api_error("docente_no_encontrado", status=404)
    except ValueError as e:
        return _api_error(e, status=400)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(mensaje="Docente actualizado")


@app.delete("/api/v1/docentes/<documento>")
@app.delete("/api/docentes/<documento>")
def api_eliminar_docente(documento):
    """Elimina un docente por documento."""
    try:
        eliminados = core_docentes.eliminar_docente(documento)
        if not eliminados:
            return _api_error("docente_no_encontrado", status=404)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(mensaje="Docente eliminado")


@app.get("/api/v1/docentes/buscar/<documento>")
@app.get("/api/docentes/buscar/<documento>")
def api_buscar_docente(documento):
    """Busca un docente por documento."""
    try:
        docente = core_docentes.buscar_docente(documento)
        if not docente:
            return _api_error("docente_no_encontrado", status=404)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(docente=docente)


@app.get("/api/v1/docentes/selector")
@app.get("/api/docentes/selector")
def api_docentes_selector():
    """Lista simple de docentes para combos/selectores."""
    solo_activos = _payload_bool(request.args.get("solo_activos"), default=False)

    try:
        docentes = core_docentes.listar_docentes_selector(solo_activos=solo_activos)
    except Exception as exc:
        return _api_error(exc, status=500)

    items = []
    for documento, nombre in docentes:
        doc = str(documento or "").strip()
        nom = str(nombre or "").strip()
        items.append(
            {
                "documento": doc,
                "nombre": nom,
                "label": f"{nom} ({doc})" if nom else doc,
            }
        )

    return _api_ok(total=len(items), docentes=items)


@app.get("/api/v1/docentes/<documento>/horas-config")
@app.get("/api/docentes/<documento>/horas-config")
def api_docente_horas_config(documento):
    """Obtiene la configuración de horas de un docente."""
    try:
        if not core_docentes.buscar_docente(documento):
            return _api_error("docente_no_encontrado", status=404)
        horas_normales_max, horas_extras_max, configurado = (
            core_docentes.obtener_limites_docente(documento)
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(
        docente_documento=str(documento or "").strip(),
        horas_normales_max=horas_normales_max,
        horas_extras_max=horas_extras_max,
        configurado=configurado,
    )


@app.put("/api/v1/docentes/<documento>/horas-config")
@app.put("/api/docentes/<documento>/horas-config")
def api_guardar_docente_horas_config(documento):
    """Crea o actualiza la configuración de horas de un docente."""
    data = request.get_json() or {}

    try:
        if not core_docentes.buscar_docente(documento):
            return _api_error("docente_no_encontrado", status=404)

        core_docentes.guardar_limites_docente(
            documento,
            data.get("horas_normales_max", 22),
            data.get("horas_extras_max", 0),
        )
        horas_normales_max, horas_extras_max, configurado = (
            core_docentes.obtener_limites_docente(documento)
        )
    except ValueError as exc:
        return _api_error(exc, status=400)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(
        mensaje="Configuración de horas guardada",
        docente_documento=str(documento or "").strip(),
        horas_normales_max=horas_normales_max,
        horas_extras_max=horas_extras_max,
        configurado=configurado,
    )


@app.post("/api/v1/docentes/importar")
@app.post("/api/docentes/importar")
def api_docentes_importar():
    """Importa docentes desde un archivo CSV o Excel."""
    import io

    archivo = request.files.get("archivo")
    if not archivo or not archivo.filename:
        return _api_error("archivo_requerido", status=400)

    nombre = archivo.filename.lower()
    try:
        if nombre.endswith(".csv"):
            import csv

            content = archivo.read().decode("utf-8-sig", errors="replace")
            filas = list(csv.DictReader(io.StringIO(content)))
        elif nombre.endswith((".xlsx", ".xls")):
            import pandas as _pd

            df = _pd.read_excel(io.BytesIO(archivo.read()))
            df = df.where(_pd.notnull(df), None)
            filas = df.to_dict("records")
        else:
            return _api_error("formato_no_soportado", status=400)
    except Exception as exc:
        return _api_error(f"error_lectura: {exc}", status=400)

    # Mapeo flexible de nombres de columna
    _ALIAS = {
        "tipo_documento": ["tipodocumento", "tipodoc", "tipoid", "tipoidentificacion"],
        "documento": [
            "documento",
            "numerodedocumento",
            "cedula",
            "identificacion",
            "doc",
        ],
        "nombre": ["nombre", "nombrecompleto", "nombres", "docente"],
        "sexo": ["sexo", "genero"],
        "fecha_nacimiento": ["fechanacimiento", "fechanac", "nacimiento"],
        "telefono": ["telefono", "celular", "movil"],
        "correo": ["correo", "email", "mail"],
        "cargo": ["cargo", "rol"],
        "jornada": ["jornada"],
        "sede": ["sede"],
        "estado": ["estado"],
    }

    def _norm_col(c):
        return str(c or "").strip().lower().replace(" ", "").replace("_", "")

    cols_raw = list((filas[0] or {}).keys()) if filas else []
    col_map = {_norm_col(c): c for c in cols_raw}

    campo_col = {}
    for campo, posibles in _ALIAS.items():
        for p in posibles:
            if p in col_map:
                campo_col[campo] = col_map[p]
                break

    if "documento" not in campo_col or "nombre" not in campo_col:
        return _api_error("columnas_documento_nombre_requeridas", status=400)

    def _val(fila, campo):
        col = campo_col.get(campo)
        if not col:
            return ""
        v = str(fila.get(col) or "").strip()
        return "" if v.lower() in ("nan", "none") else v

    insertados = duplicados = invalidos = 0
    errores = []
    docs_vistos = set()

    for i, fila in enumerate(filas):
        doc = str(_val(fila, "documento")).strip()
        # limpiar .0 flotante
        if doc.endswith(".0") and doc[:-2].isdigit():
            doc = doc[:-2]
        nombre_val = _val(fila, "nombre")

        if not doc or not nombre_val or not doc.isdigit():
            invalidos += 1
            continue
        if doc in docs_vistos:
            duplicados += 1
            continue
        docs_vistos.add(doc)

        try:
            core_docentes.crear_o_actualizar_docente(
                tipo_documento=_val(fila, "tipo_documento") or "CC",
                documento=doc,
                nombre=nombre_val,
                sexo=_val(fila, "sexo"),
                fecha_nacimiento=_val(fila, "fecha_nacimiento"),
                telefono=_val(fila, "telefono"),
                correo=_val(fila, "correo"),
                cargo=_val(fila, "cargo") or "Docente",
                jornada=_val(fila, "jornada") or "Mañana",
                sede=_val(fila, "sede"),
                estado=_val(fila, "estado") or "Activo",
            )
            insertados += 1
        except ValueError:
            duplicados += 1
        except Exception as exc:
            invalidos += 1
            errores.append({"fila": i + 2, "error": str(exc)})

    return _api_ok(
        insertados=insertados,
        duplicados=duplicados,
        invalidos=invalidos,
        errores=errores,
    )


@app.get("/api/v1/docentes/exportar")
@app.get("/api/docentes/exportar")
def api_docentes_exportar():
    """Exporta la planta docente completa como archivo Excel."""
    import io
    import pandas as _pd

    try:
        docentes = core_docentes.listar_docentes_exportacion()
    except Exception as exc:
        return _api_error(exc, status=500)

    columnas = [
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
        "fecha_registro",
    ]
    filas = [tuple(str(d.get(c) or "") for c in columnas) for d in docentes]
    df = _pd.DataFrame(filas, columns=columnas)

    buf = io.BytesIO()
    with _pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Planta Docente")
    buf.seek(0)

    from flask import send_file

    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="planta_docente.xlsx",
    )


@app.get("/api/v1/carga-academica")
@app.get("/api/carga-academica")
def api_listar_carga_academica():
    """Lista carga académica con filtros opcionales."""
    try:
        cargas = core_docentes.listar_carga_academica(
            docente_documento=request.args.get("docente_documento"),
            area=request.args.get("area"),
            grado=request.args.get("grado"),
            curso=request.args.get("curso"),
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(total=len(cargas), cargas=cargas)


@app.get("/api/gestion-academica/resumen")
def api_resumen_gestion_academica():
    """Resumen transversal y auditoría operativa de gestión académica."""
    try:
        payload = core_gestion_academica_web.resumen_gestion_academica(
            grado=request.args.get("grado"),
            curso=request.args.get("curso"),
        )
    except ValueError as exc:
        return _api_error(exc, status=400)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(**payload)


@app.get("/api/v1/carga-academica/<int:carga_id>")
@app.get("/api/carga-academica/<int:carga_id>")
def api_obtener_carga_academica(carga_id):
    """Obtiene una carga académica por ID."""
    try:
        carga = core_docentes.obtener_carga_academica(carga_id)
        if not carga:
            return _api_error("carga_academica_no_encontrada", status=404)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(carga=carga)


@app.post("/api/v1/carga-academica")
@app.post("/api/carga-academica")
def api_crear_carga_academica():
    """Crea uno o varios registros de carga académica."""
    data = request.get_json() or {}
    raw_items = data.get("items") if isinstance(data, dict) else None
    items = raw_items if isinstance(raw_items, list) and raw_items else [data]

    try:
        preparado = core_docentes.preparar_cargas_academicas(items)
        guardadas = core_docentes.crear_cargas_academicas(preparado["items"])
    except ValueError as exc:
        return _api_error(exc, status=400)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(
        mensaje="Carga académica guardada",
        guardadas=guardadas,
        usa_horas_extras=bool(preparado.get("usa_horas_extras")),
        items=preparado["items"],
    )


@app.put("/api/v1/carga-academica/<int:carga_id>")
@app.put("/api/carga-academica/<int:carga_id>")
def api_actualizar_carga_academica(carga_id):
    """Actualiza un registro de carga académica."""
    data = request.get_json() or {}

    try:
        actual = core_docentes.obtener_carga_academica(carga_id)
        if not actual:
            return _api_error("carga_academica_no_encontrada", status=404)

        preparado = core_docentes.preparar_carga_academica(
            docente_documento=data.get(
                "docente_documento", actual.get("docente_documento")
            ),
            area=data.get("area", actual.get("area")),
            grado=data.get("grado", actual.get("grado")),
            curso=data.get("curso", actual.get("curso")),
            horas_asignadas=data.get(
                "horas_asignadas", actual.get("horas_asignadas", 0)
            ),
            anio_lectivo=data.get("anio_lectivo", actual.get("anio_lectivo")),
            estado=data.get("estado", actual.get("estado", "Activo")),
            director_grupo_documento=data.get(
                "director_grupo_documento",
                actual.get("director_grupo_documento"),
            ),
            excluir_id=carga_id,
        )
        actualizados = core_docentes.actualizar_carga_academica(
            carga_id,
            preparado["docente_documento"],
            preparado["area"],
            preparado["grado"],
            preparado["curso"],
            preparado["horas_asignadas"],
            preparado["horas_extras_usadas"],
            preparado["anio_lectivo"],
            preparado["estado"],
            preparado.get("director_grupo_documento"),
        )
        core_docentes.actualizar_director_grupo(
            preparado["grado"],
            preparado["curso"],
            preparado["anio_lectivo"],
            preparado.get("director_grupo_documento"),
        )
        if not actualizados:
            return _api_error("carga_academica_no_encontrada", status=404)
    except ValueError as exc:
        return _api_error(exc, status=400)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(
        mensaje="Carga académica actualizada",
        carga={
            "id": carga_id,
            **{
                key: value
                for key, value in preparado.items()
                if key != "usa_horas_extras"
            },
        },
        usa_horas_extras=bool(preparado.get("usa_horas_extras")),
    )


@app.delete("/api/v1/carga-academica/<int:carga_id>")
@app.delete("/api/carga-academica/<int:carga_id>")
def api_eliminar_carga_academica(carga_id):
    """Elimina un registro de carga académica."""
    try:
        eliminados = core_docentes.eliminar_carga_academica(carga_id)
        if not eliminados:
            return _api_error("carga_academica_no_encontrada", status=404)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(mensaje="Carga académica eliminada")


@app.get("/api/v1/preguntas")
@app.get("/api/preguntas")
def api_preguntas():
    grado = request.args.get("grado")
    area = request.args.get("area")
    evaluacion = request.args.get("evaluacion")
    curso = request.args.get("curso")

    df = core_preguntas.cargar_preguntas_filtradas(
        area=area,
        grado=grado,
        evaluacion=evaluacion,
        curso=curso,
    )

    if df is None or df.empty:
        return _api_ok(total=0, preguntas=[])

    # Limite de salida para respuestas HTTP livianas en red local.
    max_rows = int(request.args.get("limit", 50))
    max_rows = 1 if max_rows < 1 else min(max_rows, 500)
    out = df.head(max_rows).fillna("").to_dict(orient="records")

    return _api_ok(total=int(len(df)), preguntas=out)


@app.get("/api/v1/examenes/config")
@app.get("/api/examenes/config")
def api_config_examen():
    area = request.args.get("area")
    grado = request.args.get("grado")
    evaluacion = request.args.get("evaluacion")
    curso = request.args.get("curso")

    if not area:
        return _api_error("parametro_area_requerido", status=400)

    duracion, cantidad, max_intentos, permitir_reintentos, habilitado = (
        core_examenes.cargar_config_examen(
            area=area,
            grado=grado,
            evaluacion=evaluacion,
            curso=curso,
        )
    )

    return _api_ok(
        config={
            "duracion_segundos": int(duracion),
            "cantidad_preguntas": int(cantidad),
            "max_intentos": int(max_intentos),
            "permitir_reintentos": int(permitir_reintentos),
            "habilitado": int(habilitado),
        }
    )


@app.get("/api/v1/examenes/multi-area/catalogos")
@app.get("/api/examenes/multi-area/catalogos")
def api_examenes_multi_area_catalogos():
    try:
        data = core_cuadernillos_web.catalogos_multi_area(
            grado=request.args.get("grado"),
            curso=request.args.get("curso"),
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**data)


@app.get("/api/v1/examenes/multi-area/disponibilidad")
@app.get("/api/examenes/multi-area/disponibilidad")
def api_examenes_multi_area_disponibilidad():
    try:
        data = core_cuadernillos_web.disponibilidad_multi_area(
            grado=request.args.get("grado"),
            area=request.args.get("area"),
            evaluacion=request.args.get("evaluacion"),
        )
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**data)


@app.post("/api/v1/examenes/multi-area/generar")
@app.post("/api/examenes/multi-area/generar")
def api_examenes_multi_area_generar():
    payload = request.get_json(silent=True) or {}
    try:
        result = core_cuadernillos_web.generar_cuadernillo_multi_area(
            grado=payload.get("grado"),
            curso=payload.get("curso"),
            modo_generacion=payload.get("modo_generacion"),
            estudiante_documento=payload.get("estudiante_documento"),
            configuraciones_areas=payload.get("areas") or [],
            output_dir=BASE_DIR / "out_examenes_api" / "multi_area",
        )
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)

    return send_file(
        str(result["path"]),
        as_attachment=True,
        download_name=result["filename"],
        mimetype="application/pdf" if result["tipo"] == "pdf" else "application/zip",
    )


@app.get("/api/v1/docente/panel")
@app.get("/api/docente/panel")
def api_docente_panel():
    """Lista estudiantes y su último estado evaluativo para el panel docente."""
    try:
        rows = core_docentes_web.listar_panel_docente(
            grado=request.args.get("grado"),
            curso=request.args.get("curso"),
            area=request.args.get("area"),
            evaluacion=request.args.get("evaluacion"),
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(total=len(rows), registros=rows)


@app.get("/api/v1/docente/cursos")
@app.get("/api/docente/cursos")
def api_docente_cursos():
    try:
        cursos = core_docentes_web.listar_cursos_por_grado(request.args.get("grado"))
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(cursos=cursos)


@app.post("/api/v1/docente/config")
@app.post("/api/docente/config")
def api_docente_guardar_config():
    """Guarda la configuración de examen desde el panel docente web."""
    data = request.get_json(silent=True) or {}
    try:
        grado = str(data.get("grado") or "").strip()
        area = str(data.get("area") or "").strip()
        evaluacion = str(data.get("evaluacion") or "").strip()
        curso = str(data.get("curso") or "").strip()
        duracion_min = int(data.get("duracion_min", 0) or 0)
        cantidad_preguntas = int(data.get("cantidad_preguntas", 0) or 0)
        max_intentos = int(data.get("max_intentos", 1) or 1)
        permitir_reintentos = (
            1 if _payload_bool(data.get("permitir_reintentos"), default=False) else 0
        )
        habilitado = 1 if _payload_bool(data.get("habilitado"), default=False) else 0
    except Exception:
        return _api_error("payload_invalido", status=400)

    if not grado or not area or not evaluacion or not curso:
        return _api_error("grado_area_evaluacion_curso_requeridos", status=400)
    if duracion_min <= 0 or cantidad_preguntas <= 0 or max_intentos <= 0:
        return _api_error("duracion_cantidad_intentos_invalidos", status=400)

    try:
        ok = core_examenes.guardar_config_examen(
            grado=grado,
            area=area,
            evaluacion=evaluacion,
            duracion_segundos=duracion_min * 60,
            cantidad_preguntas=cantidad_preguntas,
            max_intentos=max_intentos,
            permitir_reintentos=permitir_reintentos,
            habilitado=habilitado,
            curso=curso,
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    if not ok:
        return _api_error("no_se_pudo_guardar_la_configuracion", status=400)
    return _api_ok(mensaje="Configuración guardada")


@app.post("/api/v1/docente/autorizar-revision")
@app.post("/api/docente/autorizar-revision")
def api_docente_autorizar_revision():
    data = request.get_json(silent=True) or {}
    documento = str(data.get("documento") or "").strip()
    area = str(data.get("area") or "").strip() or None
    if not documento:
        return _api_error("documento_requerido", status=400)
    try:
        core_examenes.autorizar_revision(documento, area=area)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(mensaje="Revisión autorizada")


@app.post("/api/v1/docente/reset")
@app.post("/api/docente/reset")
def api_docente_reset():
    data = request.get_json(silent=True) or {}
    documento = str(data.get("documento") or "").strip()
    area = str(data.get("area") or "").strip()
    if not documento or not area:
        return _api_error("documento_y_area_requeridos", status=400)
    try:
        ok = core_examenes.resetear_examen(documento, area)
    except Exception as exc:
        return _api_error(exc, status=500)
    if not ok:
        return _api_error("no_se_pudo_resetear", status=400)
    return _api_ok(mensaje="Intento reseteado")


@app.get("/api/v1/docente/detalle")
@app.get("/api/docente/detalle")
def api_docente_detalle():
    documento = str(request.args.get("documento") or "").strip()
    area = str(request.args.get("area") or "").strip() or None
    intento = request.args.get("intento")
    try:
        intento = int(intento) if intento not in (None, "") else None
    except Exception:
        return _api_error("parametro_intento_invalido", status=400)
    if not documento:
        return _api_error("documento_requerido", status=400)
    try:
        respuestas = core_docentes_web.obtener_detalle_docente(
            documento=documento,
            area=area,
            intento=intento,
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(total=len(respuestas or []), respuestas=respuestas or [])


@app.get("/api/v1/docente/exportar")
@app.get("/api/docente/exportar")
def api_docente_exportar():
    try:
        archivo = core_docentes_web.exportar_reporte_excel(
            grado=request.args.get("grado"),
            curso=request.args.get("curso"),
            area=request.args.get("area"),
            evaluacion=request.args.get("evaluacion"),
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return send_file(
        archivo,
        as_attachment=True,
        download_name="reporte_docente.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/api/v1/docente/exportar-consolidado")
@app.get("/api/docente/exportar-consolidado")
def api_docente_exportar_consolidado():
    grado = request.args.get("grado")
    area = request.args.get("area")
    curso = request.args.get("curso")
    if not grado or not area:
        return _api_error("grado_y_area_requeridos", status=400)
    try:
        archivo = core_docentes_web.exportar_consolidado_excel(
            grado=grado,
            area=area,
            curso=curso,
        )
    except ValueError as exc:
        return _api_error(str(exc), status=400)
    except Exception as exc:
        return _api_error(exc, status=500)
    return send_file(
        archivo,
        as_attachment=True,
        download_name="consolidado_periodo.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# =============================================================================
# API — Banco de Preguntas
# =============================================================================


@app.get("/api/v1/banco-preguntas/areas")
@app.get("/api/banco-preguntas/areas")
def api_areas():
    """Lista todas las áreas disponibles en el banco."""
    return _api_ok(areas=core_preguntas.cargar_areas())


@app.get("/api/v1/banco-preguntas/grados")
@app.get("/api/banco-preguntas/grados")
def api_grados():
    """Lista todos los grados con preguntas registradas."""
    return _api_ok(grados=core_preguntas.cargar_grados_banco())


@app.get("/api/v1/banco-preguntas/evaluaciones")
@app.get("/api/banco-preguntas/evaluaciones")
def api_evaluaciones():
    """Lista evaluaciones filtradas por grado y área."""
    grado = request.args.get("grado")
    area = request.args.get("area")
    evs = core_preguntas.cargar_evaluaciones_por_grado_y_area(grado, area)
    return _api_ok(evaluaciones=evs)


@app.get("/api/v1/banco-preguntas")
@app.get("/api/banco-preguntas")
def api_banco_preguntas_listar_legacy():
    """Lista preguntas con paginación y filtros opcionales."""
    grado = request.args.get("grado")
    area = request.args.get("area")
    evaluacion = request.args.get("evaluacion")
    curso = request.args.get("curso")
    limit = request.args.get("limit", 50)
    offset = request.args.get("offset", 0)

    try:
        data = core_preguntas.listar_banco_preguntas(
            grado=grado,
            area=area,
            evaluacion=evaluacion,
            curso=curso,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(
        total=data["total"],
        limit=data["limit"],
        offset=data["offset"],
        preguntas=data["preguntas"],
    )


@app.post("/api/v1/banco-preguntas")
@app.post("/api/banco-preguntas")
def api_banco_preguntas_crear():
    """Crea una pregunta en el banco."""
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _api_error("payload_invalido", status=400)

    try:
        pregunta_id = core_preguntas.crear_pregunta_banco(**payload)
    except Exception as exc:
        return _api_error(exc, status=400)

    return _api_ok(status=201, id=pregunta_id)


@app.put("/api/v1/banco-preguntas/<pregunta_id>")
@app.put("/api/banco-preguntas/<pregunta_id>")
def api_banco_preguntas_actualizar(pregunta_id):
    """Actualiza una pregunta del banco."""
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _api_error("payload_invalido", status=400)

    try:
        actualizado = core_preguntas.actualizar_pregunta_banco(pregunta_id, **payload)
    except Exception as exc:
        return _api_error(exc, status=400)

    if not actualizado:
        return _api_error("pregunta_no_encontrada", status=404)

    return _api_ok(id=payload.get("id", pregunta_id))


@app.delete("/api/v1/banco-preguntas/<int:pregunta_id>")
@app.delete("/api/banco-preguntas/<int:pregunta_id>")
def api_banco_preguntas_eliminar(pregunta_id: int):
    """Elimina una pregunta del banco por ID."""
    try:
        core_preguntas.eliminar_pregunta_banco(pregunta_id)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(eliminado=pregunta_id)


@app.get("/api/v1/banco-preguntas/<int:pregunta_id>")
@app.get("/api/banco-preguntas/<int:pregunta_id>")
def api_banco_preguntas_obtener(pregunta_id: int):
    """Obtiene una pregunta del banco por ID."""
    pregunta = core_preguntas.obtener_pregunta_banco(pregunta_id)
    if not pregunta:
        return _api_error("pregunta_no_encontrada", status=404)
    return _api_ok(pregunta=pregunta)


@app.delete("/api/v1/banco-preguntas/vaciar")
@app.delete("/api/banco-preguntas/vaciar")
def api_banco_preguntas_vaciar():
    """Elimina TODAS las preguntas del banco."""
    try:
        eliminadas = core_preguntas.vaciar_banco_preguntas()
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(eliminadas=eliminadas)


@app.post("/api/v1/banco-preguntas/limpiar")
@app.post("/api/banco-preguntas/limpiar")
def api_banco_preguntas_limpiar():
    """Elimina preguntas que coinciden con los filtros indicados."""
    payload = request.get_json(silent=True) or {}
    grado = payload.get("grado") or None
    area = payload.get("area") or None
    evaluacion = payload.get("evaluacion") or None
    curso = payload.get("curso") or None
    try:
        eliminadas = core_preguntas.eliminar_preguntas_banco(
            grado=grado, area=area, evaluacion=evaluacion, curso=curso
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(eliminadas=eliminadas)


@app.post("/api/v1/banco-preguntas/importar")
@app.post("/api/banco-preguntas/importar")
def api_banco_preguntas_importar():
    """Importa preguntas desde un archivo CSV o Excel."""
    import io

    archivo = request.files.get("archivo")
    if not archivo or not archivo.filename:
        return _api_error("archivo_requerido", status=400)

    nombre = archivo.filename.lower()
    try:
        if nombre.endswith(".csv"):
            import csv

            content = archivo.read().decode("utf-8-sig", errors="replace")
            reader = csv.DictReader(io.StringIO(content))
            filas = list(reader)
        elif nombre.endswith((".xlsx", ".xls")):
            import pandas as _pd

            df = _pd.read_excel(io.BytesIO(archivo.read()))
            df = df.where(_pd.notnull(df), None)
            filas = df.to_dict("records")
        else:
            return _api_error("formato_no_soportado", status=400)
    except Exception as exc:
        return _api_error(f"error_lectura: {exc}", status=400)

    guardadas = 0
    errores = []
    for i, fila in enumerate(filas):
        datos = {
            k: (v if v not in ("", "nan", "NaN") else None)
            for k, v in (fila or {}).items()
            if k
        }
        if not datos.get("enunciado"):
            continue
        try:
            core_preguntas.crear_pregunta_banco(**datos)
            guardadas += 1
        except Exception as exc:
            errores.append({"fila": i + 2, "error": str(exc)})

    return _api_ok(guardadas=guardadas, errores=errores)


# =============================================================================
# API — Estudiantes
# =============================================================================


@app.get("/api/v1/estudiantes")
@app.get("/api/estudiantes")
def api_estudiantes():
    """Lista estudiantes con filtros opcionales."""
    grado = request.args.get("grado")
    curso = request.args.get("curso")
    limit = request.args.get("limit", 100)
    offset = request.args.get("offset", 0)

    try:
        data = core_usuarios.listar_estudiantes(
            grado=grado,
            curso=curso,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(total=data["total"], estudiantes=data["estudiantes"])


@app.post("/api/v1/estudiantes")
@app.post("/api/estudiantes")
def api_crear_estudiante():
    """Crea o actualiza un estudiante."""
    data = request.get_json() or {}

    try:
        core_matricula.crear_o_actualizar_estudiante(
            documento=data.get("documento"),
            apellido1=data.get("apellido1", ""),
            apellido2=data.get("apellido2", ""),
            nombre1=data.get("nombre1", ""),
            nombre2=data.get("nombre2", ""),
            grado=data.get("grado"),
            curso=data.get("curso"),
            jornada=data.get("jornada", ""),
            tipodoc=data.get("tipo_documento", "CC"),
            fecha_nacimiento=data.get("fecha_nacimiento", ""),
            telefono=data.get("telefono", ""),
            correo=data.get("correo", ""),
            genero=data.get("sexo", ""),
            sede=data.get("sede", ""),
            estado_academico=data.get("estado", "Activo"),
        )
    except ValueError as e:
        return _api_error(e, status=400)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(mensaje="Estudiante guardado")


@app.put("/api/v1/estudiantes/<documento>")
@app.put("/api/estudiantes/<documento>")
def api_actualizar_estudiante(documento):
    """Actualiza estudiante por documento."""
    data = request.get_json() or {}

    try:
        core_matricula.crear_o_actualizar_estudiante(
            documento=documento,
            apellido1=data.get("apellido1", ""),
            apellido2=data.get("apellido2", ""),
            nombre1=data.get("nombre1", ""),
            nombre2=data.get("nombre2", ""),
            grado=data.get("grado"),
            curso=data.get("curso"),
            jornada=data.get("jornada", ""),
            tipodoc=data.get("tipo_documento", "CC"),
            fecha_nacimiento=data.get("fecha_nacimiento", ""),
            telefono=data.get("telefono", ""),
            correo=data.get("correo", ""),
            genero=data.get("sexo", ""),
            sede=data.get("sede", ""),
            estado_academico=data.get("estado", "Activo"),
        )
    except ValueError as e:
        return _api_error(e, status=400)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(mensaje="Estudiante actualizado")


@app.delete("/api/v1/estudiantes/<documento>")
@app.delete("/api/estudiantes/<documento>")
def api_eliminar_estudiante(documento):
    """Elimina un estudiante por documento."""
    try:
        core_matricula.eliminar_estudiante(documento)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(mensaje="Estudiante eliminado")


@app.get("/api/v1/estudiantes/buscar/<documento>")
@app.get("/api/estudiantes/buscar/<documento>")
def api_buscar_estudiante(documento):
    """Busca un estudiante por documento."""
    try:
        est = core_matricula.buscar_estudiante(documento)
        if not est:
            return _api_error("estudiante_no_encontrado", status=404)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(estudiante=est)


@app.put("/api/v1/estudiantes/<documento>/estado")
@app.put("/api/estudiantes/<documento>/estado")
def api_cambiar_estado_estudiante(documento):
    """Cambia el estado de un estudiante (Activo, Inactivo, Retirado)."""
    payload = request.get_json(silent=True) or {}
    nuevo_estado = str(payload.get("estado", "")).strip()
    estados_validos = {"Activo", "Inactivo", "Retirado"}
    if nuevo_estado not in estados_validos:
        return _api_error(
            f"Estado invalido. Valores permitidos: {', '.join(sorted(estados_validos))}",
            status=422,
        )
    try:
        core_matricula.cambiar_estado_estudiante(documento, nuevo_estado)
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(mensaje=f"Estado actualizado a {nuevo_estado}.")


@app.get("/api/v1/estudiantes/exportar")
@app.get("/api/estudiantes/exportar")
def api_exportar_estudiantes():
    """Exporta estudiantes como Excel con filtros opcionales de grado/curso/jornada."""
    import io
    import pandas as _pd

    grado = request.args.get("grado", "").strip()
    curso = request.args.get("curso", "").strip()
    jornada = request.args.get("jornada", "").strip()

    try:
        todos = core_matricula.cargar_todos_estudiantes_dataframe()
    except Exception as exc:
        return _api_error(exc, status=500)

    if grado:
        todos = [r for r in todos if str(r.get("grado", "")).strip() == grado]
    if curso:
        todos = [r for r in todos if str(r.get("curso", "")).strip() == curso]
    if jornada:
        todos = [r for r in todos if str(r.get("jornada", "")).strip() == jornada]

    columnas = [
        "sede",
        "jornada",
        "grado",
        "curso",
        "nombre",
        "tipo_documento",
        "documento",
        "fecha_nacimiento",
        "telefono",
        "correo",
        "sexo",
        "estado",
    ]
    filas = [tuple(str(r.get(c) or "") for c in columnas) for r in todos]
    df = _pd.DataFrame(filas, columns=columnas)

    buf = io.BytesIO()
    with _pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Estudiantes")
    buf.seek(0)

    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="estudiantes.xlsx",
    )


# =============================================================================
# API — Calificaciones
# =============================================================================


@app.get("/api/v1/calificaciones")
@app.get("/api/calificaciones")
def api_calificaciones():
    """Consulta calificaciones con filtros opcionales."""
    documento = request.args.get("documento")
    grado = request.args.get("grado")
    area = request.args.get("area")
    curso = request.args.get("curso")
    evaluacion = request.args.get("evaluacion")
    limit = request.args.get("limit", 100)
    offset = request.args.get("offset", 0)

    try:
        data = core_examenes.listar_calificaciones(
            documento=documento,
            grado=grado,
            area=area,
            curso=curso,
            evaluacion=evaluacion,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(total=data["total"], calificaciones=data["calificaciones"])


@app.get("/api/v1/resultados/panel")
def api_resultados_panel():
    try:
        payload = core_resultados_web.panel_resultados(
            documento=request.args.get("documento"),
            grado=request.args.get("grado"),
            area=request.args.get("area"),
            curso=request.args.get("curso"),
            evaluacion=request.args.get("evaluacion"),
            limit=request.args.get("limit", 50),
            offset=request.args.get("offset", 0),
        )
    except Exception as exc:
        return _api_error(exc, status=500)
    return _api_ok(**payload)


@app.get("/api/v1/resultados/exportar")
@app.get("/api/resultados/exportar")
def api_resultados_exportar():
    try:
        buffer = core_resultados_web.exportar_resultados_excel(
            documento=request.args.get("documento"),
            grado=request.args.get("grado"),
            area=request.args.get("area"),
            curso=request.args.get("curso"),
            evaluacion=request.args.get("evaluacion"),
        )
    except ValueError as exc:
        return _api_error(exc, status=400)
    except Exception as exc:
        return _api_error(exc, status=500)

    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="resultados_filtrados.xlsx",
    )


@app.get("/api/v1/resultados/exportar-consolidado")
@app.get("/api/resultados/exportar-consolidado")
def api_resultados_exportar_consolidado():
    grado = request.args.get("grado")
    area = request.args.get("area")
    curso = request.args.get("curso")
    if not str(grado or "").strip() or not str(area or "").strip():
        return _api_error("grado_y_area_requeridos", status=400)

    try:
        buffer = core_resultados_web.exportar_consolidado_excel(
            grado=grado,
            area=area,
            curso=curso,
        )
    except ValueError as exc:
        return _api_error(exc, status=400)
    except Exception as exc:
        return _api_error(exc, status=500)

    nombre = f"consolidado_resultados_{str(grado).strip()}_{str(area).strip().replace(' ', '_')}.xlsx"
    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=nombre,
    )


@app.get("/api/v1/orientacion/resumen")
@app.get("/api/orientacion/resumen")
def api_orientacion_resumen():
    """Resumen operativo del modulo de Orientacion Escolar."""
    try:
        payload = core_orientacion_web.resumen_orientacion(
            grado=request.args.get("grado"),
            area=request.args.get("area"),
            curso=request.args.get("curso"),
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(**payload)


@app.get("/api/v1/calificaciones/camara")
@app.get("/api/calificaciones/camara")
def api_calificaciones_camara():
    """Consulta calificaciones registradas por lectura de cámara."""
    documento = request.args.get("documento")
    grado = request.args.get("grado")
    area = request.args.get("area")
    limit = request.args.get("limit", 100)
    offset = request.args.get("offset", 0)

    try:
        data = core_examenes.listar_calificaciones_camara(
            documento=documento,
            grado=grado,
            area=area,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(total=data["total"], calificaciones=data["calificaciones"])


@app.get("/api/v1/calificaciones/resumen")
@app.get("/api/calificaciones/resumen")
def api_calificaciones_resumen():
    """Resumen estadístico de calificaciones por área y grado."""
    try:
        rows = core_examenes.resumen_calificaciones_por_grado_area()
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(resumen=rows)


# =============================================================================
# API — OMR / Procesamiento de hojas desde cámara móvil
# =============================================================================


@app.post("/api/v1/omr/procesar")
@app.post("/api/omr/procesar")
def api_omr_procesar():
    """Recibe una imagen de hoja de respuestas y el texto del QR,
    detecta las respuestas marcadas, calcula la nota y la persiste.

    Espera multipart/form-data con:
      - ``imagen``: archivo de imagen (JPG/PNG)
      - ``qr``    : texto decodificado del QR (string)

    Devuelve JSON con los resultados de la calificación.
    """
    if "imagen" not in request.files:
        return _api_error("campo_imagen_requerido", status=400)
    qr_text = request.form.get("qr", "").strip()
    if not qr_text:
        return _api_error("campo_qr_requerido", status=400)

    image_bytes = request.files["imagen"].read()
    if not image_bytes:
        return _api_error("imagen_vacia", status=400)

    resultado = procesar_imagen_omr(
        image_bytes=image_bytes,
        qr_text=qr_text,
        db_path=get_db_path(),
        base_dir=BASE_DIR,
    )

    status_code = 200 if resultado.get("ok") else 422
    return _api_json(resultado, status=status_code)


@app.post("/api/v1/omr/procesar-json")
@app.post("/api/omr/procesar-json")
def api_omr_procesar_json():
    """Variante que acepta JSON con imagen en base64.

    Body JSON:
      ``{"imagen_b64": "<base64>", "qr": "<texto_qr>"}``
    """
    import base64

    data = request.get_json(silent=True) or {}
    img_b64 = data.get("imagen_b64", "")
    qr_text = str(data.get("qr", "")).strip()

    if not img_b64:
        return _api_error("campo_imagen_b64_requerido", status=400)
    if not qr_text:
        return _api_error("campo_qr_requerido", status=400)

    try:
        image_bytes = base64.b64decode(img_b64)
    except Exception:
        return _api_error("imagen_b64_invalida", status=400)

    resultado = procesar_imagen_omr(
        image_bytes=image_bytes,
        qr_text=qr_text,
        db_path=get_db_path(),
        base_dir=BASE_DIR,
    )

    status_code = 200 if resultado.get("ok") else 422
    return _api_json(resultado, status=status_code)


@app.post("/api/v1/omr/parsear-qr")
@app.post("/api/omr/parsear-qr")
def api_omr_parsear_qr():
    """Parsea el texto de un QR y devuelve los campos del examen (sin imagen)."""
    data = request.get_json(silent=True) or {}
    qr_text = str(data.get("qr", "")).strip()
    if not qr_text:
        return _api_error("campo_qr_requerido", status=400)
    parsed = parse_qr_payload(qr_text)
    return _api_ok(payload=parsed)


# =============================================================================
# API — Configuración del Sistema
# =============================================================================

from core import configuracion as core_configuracion


@app.get("/api/v1/sistema/config/<clave>")
@app.get("/api/sistema/config/<clave>")
def api_obtener_config(clave):
    """Obtiene el valor de una configuración del sistema por clave."""
    try:
        valor = core_configuracion.obtener_config(clave)
        if valor is None:
            return _api_error(f"configuracion_no_encontrada: {clave}", status=404)
        return _api_ok(clave=clave, valor=valor)
    except Exception as exc:
        return _api_error(exc, status=500)


@app.put("/api/v1/sistema/config/<clave>")
@app.put("/api/sistema/config/<clave>")
def api_guardar_config(clave):
    """Guarda o actualiza una configuración del sistema."""
    data = request.get_json() or {}
    valor = data.get("valor", "")

    try:
        core_configuracion.guardar_config(clave, valor)
        return _api_ok(clave=clave, valor=valor)
    except Exception as exc:
        return _api_error(exc, status=500)


@app.get("/api/v1/sistema/config-todas")
@app.get("/api/sistema/config-todas")
def api_listar_configuraciones():
    """Obtiene todas las configuraciones del sistema."""
    try:
        todas = core_configuracion.listar_todas_configuraciones()
        return _api_ok(configuraciones=todas)
    except Exception as exc:
        return _api_error(exc, status=500)


# =============================================================================
# API — Exámenes (generación y consulta)
# =============================================================================


def _listar_estudiantes_para_generacion(grado, curso=None):
    """Obtiene estudiantes activos para generación masiva."""
    estudiantes = []
    offset = 0
    page_size = 500

    while True:
        data = core_usuarios.listar_estudiantes(
            grado=grado,
            curso=curso,
            limit=page_size,
            offset=offset,
        )
        chunk = data.get("estudiantes", [])
        if not chunk:
            break
        estudiantes.extend(chunk)
        offset += len(chunk)
        if len(chunk) < page_size:
            break

    return estudiantes


def _payload_bool(value, default=False):
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    txt = str(value).strip().lower()
    if txt in {"1", "true", "yes", "on", "si", "sí"}:
        return True
    if txt in {"0", "false", "no", "off", ""}:
        return False
    return bool(default)


class _WebPdfWriterContext:
    """Adapter mínimo para reutilizar el render PDF desde API web."""

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.imagenes_dir = str((self.base_dir / "imagenes_preguntas").resolve())
        self.conn = get_connection()
        self.cur = self.conn.cursor()
        self._ensure_configuracion_plantel()

    def _ensure_configuracion_plantel(self):
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS configuracion_plantel (
                   clave TEXT PRIMARY KEY,
                   valor TEXT
               )"""
        )
        self.conn.commit()

    def _get_config_plantel(self, clave):
        self._ensure_configuracion_plantel()
        self.cur.execute(
            "SELECT valor FROM configuracion_plantel WHERE clave=?",
            (clave,),
        )
        row = self.cur.fetchone()
        return row[0] if row else ""

    def close(self):
        try:
            if self.cur is not None:
                self.cur.close()
        except Exception:
            pass
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception:
            pass


def _procesar_generacion_examenes(payload):
    """Genera exámenes para la pestaña Evaluaciones con soporte de modos web/escritorio."""
    if not isinstance(payload, dict):
        return _api_error("payload_invalido", status=400)

    grado = str(payload.get("grado", "") or "").strip()
    area = str(payload.get("area", "") or "").strip()
    evaluacion = str(payload.get("evaluacion", "") or "").strip() or None
    curso = str(payload.get("curso", "") or "").strip() or None
    estudiante_documento = (
        str(
            payload.get("estudiante_documento") or payload.get("estudiante") or ""
        ).strip()
        or None
    )
    docente_nombre = (
        str(payload.get("docente_nombre") or payload.get("docente") or "").strip()
        or None
    )
    fecha_examen = str(payload.get("fecha") or "").strip() or None
    formato_documento = (
        str(payload.get("formato_documento") or payload.get("formato") or "").strip()
        or None
    )
    modo_generacion = str(payload.get("modo_generacion") or "").strip().lower() or ""
    modo_hoja_respuestas = (
        str(
            payload.get("modo_hoja_respuestas") or payload.get("modo_hoja") or ""
        ).strip()
        or None
    )
    generar_hoja_respuestas = _payload_bool(
        payload.get("generar_hoja_respuestas", payload.get("hoja_respuestas")),
        default=False,
    )
    generar_pdf = _payload_bool(payload.get("generar_pdf"), default=False)

    if not grado:
        return _api_error("parametro_grado_requerido", status=400)
    if not area:
        return _api_error("parametro_area_requerido", status=400)

    try:
        cantidad_versiones = int(
            payload.get("cantidad_versiones", payload.get("versiones", 1)) or 1
        )
    except Exception:
        return _api_error("cantidad_versiones_invalida", status=400)

    try:
        cantidad_textos = int(
            payload.get("cantidad_textos", payload.get("n_textos", 0)) or 0
        )
    except Exception:
        return _api_error("cantidad_textos_invalida", status=400)

    try:
        cantidad_manual = payload.get("cantidad_preguntas", payload.get("n_preguntas"))
        cantidad_manual = (
            int(cantidad_manual)
            if cantidad_manual is not None and str(cantidad_manual).strip() != ""
            else None
        )
    except Exception:
        return _api_error("cantidad_preguntas_invalida", status=400)

    cantidad_versiones = max(1, min(26, cantidad_versiones))
    cantidad_textos = max(0, cantidad_textos)

    if not modo_generacion:
        modo_generacion = "individual" if estudiante_documento else "todos"
    if modo_generacion not in {"individual", "todos", "todos_un_pdf"}:
        return _api_error("modo_generacion_invalido", status=400)
    if modo_generacion == "individual" and not estudiante_documento:
        return _api_error("estudiante_documento_requerido", status=400)
    if modo_generacion == "todos_un_pdf" and not generar_pdf:
        return _api_error("pdf_requerido_para_consolidado", status=400)

    df = core_preguntas.cargar_preguntas_filtradas(
        area=area,
        grado=grado,
        evaluacion=evaluacion,
        curso=curso,
    )
    if df is None or df.empty:
        return _api_error("no_hay_preguntas_disponibles", status=400)

    cfg = core_examenes.cargar_config_examen(
        area=area,
        grado=grado,
        evaluacion=evaluacion,
        curso=curso,
    )
    cantidad = int(cfg[1]) if cfg else len(df)

    if cantidad_manual is not None:
        if cantidad_manual <= 0:
            return _api_error("cantidad_preguntas_invalida", status=400)
        cantidad = cantidad_manual

    if cantidad > len(df):
        cantidad = len(df)
    if cantidad <= 0:
        return _api_error("cantidad_preguntas_invalida", status=400)

    if cantidad < len(df) and not (cantidad_textos and cantidad_textos > 0):
        df = df.head(cantidad).copy()

    if estudiante_documento:
        estudiante = core_matricula.buscar_estudiante(estudiante_documento)
        if not estudiante:
            return _api_error("estudiante_no_encontrado", status=404)
        estudiantes = [
            {
                "documento": estudiante.get("documento", estudiante_documento),
                "apellido1": estudiante.get("apellido1", ""),
                "apellido2": estudiante.get("apellido2", ""),
                "nombre1": estudiante.get("nombre1", ""),
                "nombre2": estudiante.get("nombre2", ""),
                "grado": estudiante.get("grado", grado),
                "curso": estudiante.get("curso", curso or ""),
            }
        ]
    else:
        estudiantes = _listar_estudiantes_para_generacion(grado=grado, curso=curso)
        if not estudiantes:
            return _api_error("no_hay_estudiantes_para_filtro", status=400)
        if len(estudiantes) > 500:
            return _api_error(
                "demasiados_estudiantes_en_lote",
                status=400,
                maximo_permitido=500,
                total_detectado=len(estudiantes),
            )

    etiquetas_version = core_examenes_generacion.generar_etiquetas_version(
        cantidad_versiones
    )
    examenes_por_version = {}
    if cantidad_versiones > 1:
        for ver in etiquetas_version:
            seed_ver = f"{grado}|{area}|{evaluacion or ''}|{ver}"
            examenes_por_version[ver] = (
                core_examenes_generacion.seleccionar_preguntas_por_textos(
                    df,
                    cantidad,
                    cantidad_textos,
                    rnd_seed=seed_ver,
                )
            )

    pdf_writer = _WebPdfWriterContext(BASE_DIR) if generar_pdf else None
    output_dir = (BASE_DIR / "out_examenes_api").resolve()
    if generar_pdf:
        output_dir.mkdir(parents=True, exist_ok=True)
    rutas_pdfs = []

    try:
        generados = []
        for idx, est in enumerate(estudiantes, start=1):
            version = etiquetas_version[(idx - 1) % len(etiquetas_version)]
            if cantidad_versiones > 1:
                df_sel = examenes_por_version.get(version)
                if df_sel is None or df_sel.empty:
                    return _api_error(
                        "version_sin_preguntas", status=500, version=version
                    )
            else:
                seed = (
                    est.get("documento")
                    or est.get("id")
                    or _nombre_estudiante(est)
                    or idx
                )
                df_sel = core_examenes_generacion.seleccionar_preguntas_por_textos(
                    df,
                    cantidad,
                    cantidad_textos,
                    rnd_seed=seed,
                )

            exam_code = core_examenes_generacion.crear_codigo_examen(version)
            ruta_pdf = ""
            ruta_pdf_url = ""
            if generar_pdf and pdf_writer is not None:
                doc_raw = str(est.get("documento") or "").strip() or "sin_documento"
                doc_safe = (
                    "".join(ch for ch in doc_raw if ch.isalnum()) or "sin_documento"
                )
                pdf_name = f"{exam_code}_{doc_safe}.pdf"
                pdf_path = output_dir / pdf_name
                try:
                    core_examenes_pdf.write_exam_pdf(
                        pdf_writer,
                        preguntas_df=df_sel,
                        estudiante={
                            "documento": est.get("documento") or "",
                            "apellido1": est.get("apellido1") or "",
                            "apellido2": est.get("apellido2") or "",
                            "nombre1": est.get("nombre1") or "",
                            "nombre2": est.get("nombre2") or "",
                            "grado": est.get("grado") or grado,
                            "curso": est.get("curso") or curso or "",
                        },
                        path=str(pdf_path),
                        cantidad=cantidad,
                        area=area,
                        evaluacion=evaluacion,
                        fecha=fecha_examen,
                        cantidad_textos=cantidad_textos,
                        formato_examen=formato_documento,
                        docente_nombre=docente_nombre,
                        modo_hoja_respuestas=modo_hoja_respuestas,
                        generar_hoja_respuestas=generar_hoja_respuestas,
                        version=version,
                        exam_id=exam_code,
                    )
                    ruta_pdf = str(pdf_path)
                    ruta_pdf_url = f"/api/examenes/{exam_code}/pdf"
                    rutas_pdfs.append(ruta_pdf)
                except Exception as exc:
                    return _api_error(
                        "error_generando_pdf",
                        status=500,
                        detalle=str(exc),
                        exam_code=exam_code,
                    )

            core_examenes_generacion.guardar_detalle_examen(exam_code, df_sel)
            core_examenes_generacion.guardar_examen_generado(
                exam_code=exam_code,
                grado=grado,
                curso=est.get("curso") or "",
                area=area,
                evaluacion=evaluacion or "",
                version=version,
                estudiante_nombre=_nombre_estudiante(est),
                estudiante_documento=est.get("documento") or "",
                ruta_pdf=ruta_pdf,
            )

            generados.append(
                {
                    "exam_code": exam_code,
                    "codigo": exam_code,
                    "version": version,
                    "estudiante_documento": est.get("documento") or "",
                    "estudiante_nombre": _nombre_estudiante(est),
                    "estudiante": _nombre_estudiante(est),
                    "cantidad_preguntas": int(len(df_sel)),
                    "n_preguntas": int(len(df_sel)),
                    "ruta_pdf": ruta_pdf_url,
                    "pdf": ruta_pdf_url,
                    "download_url": ruta_pdf_url,
                }
            )

        ruta_pdf_consolidado = None
        ruta_pdf_consolidado_url = ""
        archivo_generado_url = ""
        archivo_generado_nombre = ""
        archivo_generado_tipo = ""
        if generar_pdf and modo_generacion == "individual" and generados:
            archivo_generado_url = str(generados[0].get("download_url") or "")
            archivo_generado_nombre = (
                os.path.basename(rutas_pdfs[0]) if rutas_pdfs else ""
            )
            archivo_generado_tipo = "pdf"
        elif generar_pdf and modo_generacion == "todos" and rutas_pdfs:
            try:
                import zipfile

                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ruta_zip = output_dir / f"examenes_generados_{stamp}.zip"
                with zipfile.ZipFile(
                    ruta_zip, "w", compression=zipfile.ZIP_DEFLATED
                ) as zip_file:
                    for ruta_pdf_item in rutas_pdfs:
                        zip_file.write(
                            ruta_pdf_item, arcname=os.path.basename(ruta_pdf_item)
                        )
                archivo_generado_url = (
                    f"/api/examenes/descargar/{os.path.basename(ruta_zip)}"
                )
                archivo_generado_nombre = ruta_zip.name
                archivo_generado_tipo = "zip"
            except Exception as exc:
                return _api_error("error_generando_zip", status=500, detalle=str(exc))
        if generar_pdf and modo_generacion == "todos_un_pdf" and rutas_pdfs:
            try:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ruta_pdf_consolidado = str(
                    output_dir / f"cuadernillo_consolidado_{stamp}.pdf"
                )
                core_examenes_generacion.unir_pdfs(rutas_pdfs, ruta_pdf_consolidado)
                ruta_pdf_consolidado_url = (
                    f"/api/examenes/descargar/{os.path.basename(ruta_pdf_consolidado)}"
                )
                archivo_generado_url = ruta_pdf_consolidado_url
                archivo_generado_nombre = os.path.basename(ruta_pdf_consolidado)
                archivo_generado_tipo = "pdf"
            except Exception as exc:
                return _api_error(
                    "error_generando_pdf_consolidado", status=500, detalle=str(exc)
                )
    finally:
        if pdf_writer is not None:
            pdf_writer.close()

    return _api_ok(
        mensaje="Exámenes generados y registrados",
        total_generados=len(generados),
        parametros={
            "grado": grado,
            "area": area,
            "evaluacion": evaluacion,
            "curso": curso,
            "cantidad_preguntas": cantidad,
            "cantidad_textos": cantidad_textos,
            "cantidad_versiones": cantidad_versiones,
            "modo_generacion": modo_generacion,
            "formato_documento": formato_documento,
        },
        examenes=generados,
        resultados=generados,
        ruta_pdf_consolidado=ruta_pdf_consolidado or "",
        ruta_pdf_consolidado_url=ruta_pdf_consolidado_url,
        archivo_generado_url=archivo_generado_url,
        archivo_generado_nombre=archivo_generado_nombre,
        archivo_generado_tipo=archivo_generado_tipo,
        rutas_pdfs=rutas_pdfs,
    )


@app.post("/api/v1/examenes/generar")
@app.post("/api/examenes/generar")
def api_generar_examenes():
    """Genera exámenes desde API y persiste clave/metadata en BD.

    Nota: este endpoint registra exámenes y claves en BD usando core,
    pero no renderiza PDF (adaptador PDF aún acoplado al contexto desktop).
    """
    payload = request.get_json(silent=True) or {}
    return _procesar_generacion_examenes(payload)


@app.get("/api/v1/examenes/generados")
@app.get("/api/examenes/generados")
def api_examenes_generados():
    """Lista los exámenes generados (registros en detalle_examen)."""
    limit = request.args.get("limit", 50)
    offset = request.args.get("offset", 0)

    try:
        rows = core_examenes.listar_examenes_generados(limit=limit, offset=offset)
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(examenes=rows)


@app.get("/api/v1/examenes/panel")
@app.get("/api/examenes/panel")
def api_examenes_panel():
    """Resumen operativo del modulo de Examenes."""
    try:
        payload = core_examenes_admin_web.panel_examenes()
    except Exception as exc:
        return _api_error(exc, status=500)

    return _api_ok(**payload)


@app.get("/api/v1/examenes/<exam_id>/clave")
@app.get("/api/examenes/<exam_id>/clave")
def api_examen_clave(exam_id: str):
    """Devuelve la clave de respuestas de un examen generado."""
    from core.omr import obtener_clave_examen

    exam_id = exam_id.strip().upper()
    clave = obtener_clave_examen(exam_id)
    if not clave:
        return _api_error("examen_no_encontrado", status=404)
    return _api_ok(
        id_examen=exam_id,
        clave={str(k): v for k, v in clave.items()},
    )


@app.get("/api/v1/examenes/<exam_id>")
@app.get("/api/examenes/<exam_id>")
def api_examen_generado_detalle(exam_id: str):
    """Devuelve el detalle de un examen generado por su código."""
    codigo = str(exam_id or "").strip().upper()
    if not codigo:
        return _api_error("exam_id_requerido", status=400)

    try:
        examen = core_examenes_generacion.obtener_examen_generado_por_codigo(codigo)
    except Exception as exc:
        return _api_error(exc, status=500)

    if not examen:
        return _api_error("examen_no_encontrado", status=404)

    ruta_pdf = str(examen.get("ruta_pdf") or "").strip()
    pdf_disponible = bool(ruta_pdf and os.path.exists(ruta_pdf))
    return _api_ok(
        examen={
            **examen,
            "pdf_disponible": pdf_disponible,
            "download_url": f"/api/examenes/{codigo}/pdf" if pdf_disponible else "",
        }
    )


@app.get("/api/v1/examenes/<exam_id>/pdf")
@app.get("/api/examenes/<exam_id>/pdf")
def api_examen_generado_pdf(exam_id: str):
    """Descarga el PDF asociado a un examen generado por su código."""
    codigo = str(exam_id or "").strip().upper()
    if not codigo:
        return _api_error("exam_id_requerido", status=400)

    try:
        examen = core_examenes_generacion.obtener_examen_generado_por_codigo(codigo)
    except Exception as exc:
        return _api_error(exc, status=500)

    if not examen:
        return _api_error("examen_no_encontrado", status=404)

    ruta_pdf = str(examen.get("ruta_pdf") or "").strip()
    if not ruta_pdf or not os.path.exists(ruta_pdf):
        return _api_error("pdf_no_disponible", status=404)

    return send_file(
        ruta_pdf,
        as_attachment=True,
        download_name=os.path.basename(ruta_pdf),
        mimetype="application/pdf",
    )


@app.get("/api/v1/examenes/descargar/<nombre_pdf>")
@app.get("/api/examenes/descargar/<nombre_pdf>")
def api_examen_descargar_por_nombre(nombre_pdf: str):
    """Descarga un archivo generado desde el directorio web de salida."""
    nombre = secure_filename(str(nombre_pdf or "").strip())
    if not nombre:
        return _api_error("nombre_pdf_requerido", status=400)

    output_dir = (BASE_DIR / "out_examenes_api").resolve()
    ruta = (output_dir / nombre).resolve()
    try:
        ruta.relative_to(output_dir)
    except Exception:
        return _api_error("nombre_pdf_invalido", status=400)

    if not ruta.exists() or not ruta.is_file():
        return _api_error("archivo_no_disponible", status=404)

    return send_file(
        str(ruta),
        as_attachment=True,
        download_name=nombre,
        mimetype=(
            "application/zip" if ruta.suffix.lower() == ".zip" else "application/pdf"
        ),
    )


# =============================================================================
# API — Utilidades / Health
# =============================================================================


@app.get("/api/v1/health")
@app.get("/api/health")
def health():
    print("==[DEBUG]== Entrando a /api/health")
    """Health check — verifica conectividad con la base de datos."""
    db_ok = ping_db()

    return _api_json(
        {
            "ok": db_ok,
            "servicio": "SEA Web",
            "arquitectura": "hibrida",
            "db": str(get_db_path()),
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.get("/api/v1/auth/status")
@app.get("/api/auth/status")
def api_auth_status():
    """Estado del scaffold de autenticación para API v1."""
    required = _api_v1_auth_required()
    configured = bool(_api_v1_expected_token())
    return _api_ok(
        auth={
            "mode": "token",
            "applies_to": "/api/v1/*",
            "required": required,
            "token_configured": configured,
            "accepted_headers": [
                "Authorization: Bearer <token>",
                "X-SEA-API-Key: <token>",
            ],
        }
    )


@app.get("/api/v1/info")
@app.get("/api/info")
def api_info():
    print("==[DEBUG]== Entrando a /api/info")
    """Información del sistema y endpoints disponibles."""
    return _api_ok(
        sistema="SEA — Sistema de Evaluación Automatizada",
        version="2.0",
        arquitectura="Escritorio (Tkinter) + Web (Flask) + API Móvil",
        api_bases=["/api", "/api/v1"],
        auth={
            "scheme": "token",
            "env_required_flag": "SEA_API_V1_AUTH_REQUIRED",
            "env_token": "SEA_API_V1_KEY",
            "status_endpoint": "/api/v1/auth/status",
        },
        endpoints={
            "health": "GET /api/v1/health",
            "auth_status": "GET /api/v1/auth/status",
            "estudiante": "GET /api/v1/usuarios/estudiante/<documento>",
            "docente": "GET /api/v1/usuarios/docente/<documento>",
            "estudiantes": "GET /api/v1/estudiantes?grado=...&curso=...",
            "plan_estudios": "GET /api/v1/plan-estudios?grado=...&curso=...",
            "plan_estudios_catalogos": "GET /api/v1/plan-estudios/catalogos",
            "plan_estudios_crear": "POST /api/v1/plan-estudios",
            "plan_estudios_actualizar": "PUT /api/v1/plan-estudios/<id>",
            "plan_estudios_eliminar": "DELETE /api/v1/plan-estudios/<id>",
            "plan_estudios_copiar": "POST /api/v1/plan-estudios/copiar",
            "plan_estudios_importar": "POST /api/v1/plan-estudios/importar",
            "docentes": "GET /api/v1/docentes?estado=...&cargo=...",
            "docentes_selector": "GET /api/v1/docentes/selector?solo_activos=true",
            "docente_crear": "POST /api/v1/docentes",
            "docente_actualizar": "PUT /api/v1/docentes/<documento>",
            "docente_eliminar": "DELETE /api/v1/docentes/<documento>",
            "docente_horas_config": "GET|PUT /api/v1/docentes/<documento>/horas-config",
            "carga_academica": "GET /api/v1/carga-academica?docente_documento=...&area=...&grado=...&curso=...",
            "carga_academica_detalle": "GET /api/v1/carga-academica/<id>",
            "carga_academica_crear": "POST /api/v1/carga-academica",
            "carga_academica_actualizar": "PUT /api/v1/carga-academica/<id>",
            "carga_academica_eliminar": "DELETE /api/v1/carga-academica/<id>",
            "preguntas": "GET /api/v1/preguntas?grado=...&area=...&evaluacion=...",
            "banco_preguntas": "GET /api/v1/banco-preguntas?grado=...&area=...&limit=...&offset=...",
            "banco_crear": "POST /api/v1/banco-preguntas",
            "banco_actualizar": "PUT /api/v1/banco-preguntas/<id>",
            "banco_eliminar": "DELETE /api/v1/banco-preguntas/<id>",
            "areas": "GET /api/v1/banco-preguntas/areas",
            "grados": "GET /api/v1/banco-preguntas/grados",
            "evaluaciones": "GET /api/v1/banco-preguntas/evaluaciones?grado=...&area=...",
            "config_examen": "GET /api/v1/examenes/config?area=...&grado=...&evaluacion=...",
            "examenes_generar": "POST /api/v1/examenes/generar",
            "examenes_generados": "GET /api/v1/examenes/generados",
            "clave_examen": "GET /api/v1/examenes/<id>/clave",
            "calificaciones": "GET /api/v1/calificaciones?documento=...&grado=...&area=...",
            "calificaciones_camara": "GET /api/v1/calificaciones/camara",
            "calificaciones_resumen": "GET /api/v1/calificaciones/resumen",
            "omr_procesar": "POST /api/v1/omr/procesar  (multipart: imagen + qr)",
            "omr_procesar_json": "POST /api/v1/omr/procesar-json  (json: imagen_b64 + qr)",
            "omr_parsear_qr": "POST /api/v1/omr/parsear-qr  (json: qr)",
        },
    )


if __name__ == "__main__":
    import socket

    def _local_domains():
        raw = str(
            os.environ.get(
                "SEA_LOCAL_DOMAINS", "sea.local,evaluaciones.local,admin.local"
            )
        ).strip()
        values = []
        for item in raw.split(","):
            domain = str(item or "").strip().lower()
            if domain and domain not in values:
                values.append(domain)
        return values or ["sea.local"]

    def _format_url(
        scheme_value: str, host_value: str, port_value: int, path_value: str = ""
    ) -> str:
        suffix = (
            path_value
            if path_value.startswith("/") or not path_value
            else f"/{path_value}"
        )
        if int(port_value) == 80:
            return f"{scheme_value}://{host_value}{suffix}"
        return f"{scheme_value}://{host_value}:{port_value}{suffix}"

    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "127.0.0.1"

    scheme = get_access_scheme()
    debug_mode, reload_mode = _resolve_web_runtime(None, None)

    print("=" * 60)
    print("  SEA — Servidor Web + API")
    print("=" * 60)
    print(f"  Runtime:  {'DESARROLLO' if debug_mode else 'PRODUCCIÓN'}")
    print(f"  Debug:    {'ON' if debug_mode else 'OFF'}")
    print(f"  Reloader: {'ON' if reload_mode else 'OFF'}")
    local_domains = _local_domains()
    print(f"  Acceso local: {_format_url(scheme, local_domains[0], 5000)}")
    if len(local_domains) > 1:
        print(
            "  Alias locales: "
            + " | ".join(_format_url(scheme, item, 5000) for item in local_domains[1:])
        )
    print(f"  Red local:    {_format_url(scheme, local_ip, 5000)}")
    print(f"  Escáner OMR:  {_format_url(scheme, local_ip, 5000, '/escanear')}")
    print(f"  API:          {_format_url(scheme, local_ip, 5000, '/api/info')}")
    if scheme == "https":
        print("  Nota:         HTTPS activo para contexto seguro de cámara.")
    else:
        print("  Hosts Windows: C:\\Windows\\System32\\drivers\\etc\\hosts")
        print(
            "  Nota:         Los alias .local aplican al PC; en celular usa la IP local o HTTPS si el navegador exige contexto seguro para cámara."
        )
    print("=" * 60)

    run_web_server(
        host="0.0.0.0", port=5000, debug=debug_mode, use_reloader=reload_mode
    )


@app.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")
