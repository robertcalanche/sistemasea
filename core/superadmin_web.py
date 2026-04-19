from __future__ import annotations

from . import get_connection


def _scalar(query, params=None):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params or [])
        row = cur.fetchone()
    return int((row[0] if row else 0) or 0)


def resumen_superadmin():
    stats = {
        "docentes": _scalar("SELECT COUNT(*) FROM docentes"),
        "estudiantes": _scalar("SELECT COUNT(*) FROM estudiantes"),
        "preguntas": _scalar("SELECT COUNT(*) FROM banco_preguntas"),
        "cargas": _scalar("SELECT COUNT(*) FROM carga_academica"),
        "resultados": _scalar("SELECT COUNT(*) FROM resultados"),
        "examenes_generados": _scalar(
            "SELECT COUNT(DISTINCT id_examen) FROM detalle_examen"
        ),
    }

    fases = [
        {
            "id": 1,
            "titulo": "Operación Académica",
            "estado": "activa",
            "descripcion": "Hub administrativo con acceso a docentes, carga académica, matrícula, banco de preguntas, exámenes y calificaciones.",
            "items": [
                {"label": "Panel Docente", "href": "/docente", "estado": "migrado"},
                {
                    "label": "Banco de Preguntas",
                    "href": "/banco-preguntas",
                    "estado": "migrado",
                },
                {
                    "label": "Carga Académica",
                    "href": "/carga-academica",
                    "estado": "migrado",
                },
                {"label": "Generar Exámenes", "href": "/examenes", "estado": "migrado"},
                {
                    "label": "Calificaciones",
                    "href": "/calificaciones",
                    "estado": "migrado",
                },
                {
                    "label": "API Estudiantes",
                    "href": "/api/estudiantes?limit=20",
                    "estado": "api",
                },
                {
                    "label": "API Docentes",
                    "href": "/api/docentes?limit=20",
                    "estado": "api",
                },
            ],
        },
        {
            "id": 2,
            "titulo": "Catálogos y Matrícula",
            "estado": "completada",
            "descripcion": "✓ Matrícula y Plan de Estudios web: CRUD completo, carga masiva CSV/XLSX, exportación, copia entre cursos, cambio masivo de curso y hub de gestión académica.",
            "items": [
                {
                    "label": "Gestión Académica",
                    "href": "/gestion-academica",
                    "estado": "migrado",
                },
                {
                    "label": "Gestor Matrícula",
                    "href": "/matricula",
                    "estado": "migrado",
                },
                {
                    "label": "Exportar Estudiantes",
                    "href": "/api/estudiantes/exportar",
                    "estado": "api",
                },
                {
                    "label": "Cambiar Estado",
                    "href": None,
                    "estado": "migrado",
                },
                {
                    "label": "Plan de Estudios",
                    "href": "/plan-estudios",
                    "estado": "migrado",
                },
            ],
        },
        {
            "id": 5,
            "titulo": "Planta Docente",
            "estado": "activa",
            "descripcion": "Gestión completa de la planta docente: registro, edición, búsqueda, importación masiva CSV/XLSX y exportación Excel.",
            "items": [
                {
                    "label": "Planta Docente",
                    "href": "/planta-docente",
                    "estado": "migrado",
                },
                {
                    "label": "Importar Docentes",
                    "href": None,
                    "estado": "migrado",
                },
                {
                    "label": "Exportar Docentes",
                    "href": "/api/docentes/exportar",
                    "estado": "api",
                },
            ],
        },
        {
            "id": 3,
            "titulo": "Acceso Maestro y Seguridad",
            "estado": "activa",
            "descripcion": "Control maestro web para seguimiento, detalle de intentos, autorización de revisión, reset de resultados y cambio de clave maestra.",
            "items": [
                {"label": "Acceso Maestro", "href": "/maestro", "estado": "migrado"},
                {"label": "Seguridad", "href": "/seguridad", "estado": "migrado"},
            ],
        },
        {
            "id": 4,
            "titulo": "Configuración Institucional",
            "estado": "activa",
            "descripcion": "Formulario institucional del plantel y parámetros generales del sistema.",
            "items": [
                {
                    "label": "Configuración Plantel",
                    "href": "/configuracion-plantel",
                    "estado": "migrado",
                },
                {
                    "label": "Orientación Escolar",
                    "href": "/orientacion",
                    "estado": "migrado",
                },
                {
                    "label": "Secretaría Académica",
                    "href": "/secretaria",
                    "estado": "migrado",
                },
            ],
        },
    ]
    return {"stats": stats, "fases": fases}
