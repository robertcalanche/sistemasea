DESKTOP_SUPERADMIN_TAB_PERMISSIONS = {
    "Académico": "desktop.superadmin.tab.academico",
    "Configuración": "desktop.superadmin.tab.configuracion",
    "Planta Docente": "desktop.superadmin.tab.docentes",
    "Carga Académica": "desktop.superadmin.tab.carga_academica",
    "Plan de Estudios": "desktop.superadmin.tab.plan_estudio",
    "Matrícula": "desktop.superadmin.tab.matricula",
    "Banco Preguntas": "desktop.superadmin.tab.banco_preguntas",
    "Evaluaciones": "desktop.superadmin.tab.evaluaciones",
    "Planillas": "desktop.superadmin.tab.planillas",
    "Certificados": "desktop.superadmin.tab.certificados",
    "Acceso Docente": "desktop.superadmin.tab.acceso_docente",
    "Boletines": "desktop.superadmin.tab.boletines",
    "Desempeños": "desktop.superadmin.tab.desempenos",
}


def cambiar_clave_personal(documento, clave_actual, clave_nueva):
    """
    Cambia la clave de acceso para personal (docente, secretaria, rector, coordinador, etc.).
    Retorna True si el cambio fue exitoso, False si la clave actual no coincide o el usuario no existe.
    """
    from .docentes import cambiar_clave_docente

    return cambiar_clave_docente(documento, clave_actual, clave_nueva)


def validar_clave_personal(documento, clave):
    """Valida la clave de acceso para personal (docente, secretaria, rector, coordinador, etc.)."""
    from .docentes import buscar_docente

    doc = str(documento or "").strip()
    clave_in = str(clave or "").strip()
    if not doc or not clave_in:
        return False
    docente = buscar_docente(doc)
    if not docente:
        return False
    clave_db = docente.get("clave")
    # Si no hay clave registrada, la clave por defecto es el documento
    if not clave_db or str(clave_db).strip() == "":
        return clave_in == doc
    return clave_db == clave_in


from . import get_connection
from .construir_nombre import construir_nombre
from .configuracion import obtener_clave_maestra, obtener_config
from .preguntas import normalizar_grado
import unicodedata


ROL_ADMIN = "admin"
ROL_DOCENTE = "docente"
ROL_ESTUDIANTE = "estudiante"
ROL_SUPERADMIN = "superadmin"
ROL_RECTOR = "rector"
ROL_SECRETARIA = "secretaria"
ROL_COORDINADOR = "coordinador"
ROL_ORIENTADOR = "orientador"
ROL_SECRETARIA_ACADEMICA = "secretaria academica"

ROLES_WEB_TODOS = {
    ROL_ADMIN,
    ROL_DOCENTE,
    ROL_ESTUDIANTE,
    ROL_RECTOR,
    ROL_SECRETARIA,
    ROL_COORDINADOR,
    ROL_ORIENTADOR,
    ROL_SECRETARIA_ACADEMICA,
}
ROLES_WEB_DOCENTE = {ROL_ADMIN, ROL_DOCENTE, ROL_COORDINADOR, ROL_RECTOR}
ROLES_WEB_ADMIN = {ROL_ADMIN}
ROLES_WEB_DIRECTIVOS = {ROL_ADMIN, ROL_RECTOR, ROL_SECRETARIA, ROL_COORDINADOR}
ROLES_WEB_GESTION = {ROL_ADMIN, ROL_RECTOR, ROL_COORDINADOR}
ROLES_WEB_SECRETARIA = {ROL_ADMIN, ROL_SECRETARIA}
ROLES_WEB_RECTOR = {ROL_ADMIN, ROL_RECTOR}

_ROLE_ALIASES = {
    ROL_ADMIN: ROL_SUPERADMIN,
    ROL_SUPERADMIN: ROL_SUPERADMIN,
    ROL_DOCENTE: ROL_DOCENTE,
    ROL_ESTUDIANTE: ROL_ESTUDIANTE,
    ROL_RECTOR: ROL_RECTOR,
    ROL_SECRETARIA: ROL_SECRETARIA,
    ROL_COORDINADOR: ROL_COORDINADOR,
    ROL_ORIENTADOR: ROL_ORIENTADOR,
    ROL_SECRETARIA_ACADEMICA: ROL_SECRETARIA_ACADEMICA,
    "secretaría": ROL_SECRETARIA,
    "coordinadora": ROL_COORDINADOR,
    "rectora": ROL_RECTOR,
    "orientador": ROL_ORIENTADOR,
    "orientadora": ROL_ORIENTADOR,
    "secretaria academica": ROL_SECRETARIA_ACADEMICA,
    "secretario academico": ROL_SECRETARIA_ACADEMICA,
}

_DEFAULT_DESKTOP_PERMISSIONS_BY_ROLE = {
    ROL_SUPERADMIN: {"*", "desktop.superadmin.tab.academico"},
    ROL_DOCENTE: {
        "desktop.session.open.docente",
        "desktop.docente.banco_preguntas",
        "desktop.docente.autoevaluacion",
        "desktop.docente.configuracion_examen",
        "desktop.docente.exportar_excel",
        "desktop.docente.exportar_consolidado",
        "desktop.docente.ver_detalle",
        "desktop.docente.autorizar_revision",
        "desktop.docente.resetear_nota",
        "desktop.docente.filtros",
        "desktop.docente.tabla",
    },
    ROL_ESTUDIANTE: {
        "desktop.session.open.estudiante",
        "desktop.estudiante.historial",
        "desktop.estudiante.autoevaluacion",
        "desktop.estudiante.presentar_examen",
    },
    ROL_RECTOR: {
        "desktop.superadmin.tab.configuracion",
        "desktop.superadmin.tab.docentes",
        "desktop.superadmin.tab.carga_academica",
        "desktop.superadmin.tab.plan_estudio",
        "desktop.superadmin.tab.matricula",
        "desktop.superadmin.tab.evaluaciones",
        "desktop.superadmin.tab.planillas",
        "desktop.superadmin.tab.certificados",
        "desktop.superadmin.tab.boletines",
        "desktop.superadmin.tab.desempenos",
        "desktop.superadmin.docentes.recargar",
        "desktop.superadmin.docentes.exportar",
        "desktop.superadmin.carga_academica.actualizar",
        "desktop.superadmin.plan_estudio.actualizar",
        "desktop.superadmin.evaluaciones.consultar_examen",
        "desktop.superadmin.evaluaciones.ver_resultados_camara",
        "desktop.superadmin.boletines.actualizar",
        "desktop.superadmin.boletines.exportar_pdf",
    },
    ROL_SECRETARIA: {
        "desktop.superadmin.tab.matricula",
        "desktop.superadmin.tab.certificados",
        "desktop.superadmin.tab.boletines",
        "desktop.superadmin.matricula.importar",
        "desktop.superadmin.matricula.crear",
        "desktop.superadmin.matricula.editar",
        "desktop.superadmin.matricula.cambiar_curso",
        "desktop.superadmin.boletines.actualizar",
        "desktop.superadmin.boletines.exportar_pdf",
    },
    ROL_COORDINADOR: {
        "desktop.superadmin.tab.docentes",
        "desktop.superadmin.tab.carga_academica",
        "desktop.superadmin.tab.plan_estudio",
        "desktop.superadmin.tab.evaluaciones",
        "desktop.superadmin.tab.planillas",
        "desktop.superadmin.tab.acceso_docente",
        "desktop.superadmin.tab.boletines",
        "desktop.superadmin.tab.desempenos",
        "desktop.superadmin.docentes.recargar",
        "desktop.superadmin.carga_academica.crear",
        "desktop.superadmin.carga_academica.editar",
        "desktop.superadmin.carga_academica.actualizar",
        "desktop.superadmin.planillas.asistencia.guardar",
        "desktop.superadmin.planillas.asistencia.descargar",
        "desktop.superadmin.planillas.calificaciones.guardar",
        "desktop.superadmin.planillas.calificaciones.descargar",
        "desktop.superadmin.boletines.actualizar",
        "desktop.superadmin.boletines.exportar_pdf",
        "desktop.superadmin.desempenos.cargar",
        "desktop.superadmin.desempenos.guardar",
        "desktop.superadmin.desempenos.actualizar",
    },
}

_DOCENTE_CARGO_ROLE_ALIASES = {
    "docente": ROL_DOCENTE,
    "profesor": ROL_DOCENTE,
    "maestro": ROL_DOCENTE,
    "rector": ROL_RECTOR,
    "rectora": ROL_RECTOR,
    "secretaria": ROL_SECRETARIA,
    "secretario": ROL_SECRETARIA,
    "secretaria academica": ROL_SECRETARIA_ACADEMICA,
    "secretario academico": ROL_SECRETARIA_ACADEMICA,
    "coordinador": ROL_COORDINADOR,
    "coordinadora": ROL_COORDINADOR,
    "coordinador academico": ROL_COORDINADOR,
    "coordinadora academica": ROL_COORDINADOR,
    "orientador": ROL_ORIENTADOR,
    "orientadora": ROL_ORIENTADOR,
}


def _normalizar_texto_simple(valor):
    texto = str(valor or "").strip().lower()
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return " ".join(texto.split())


def _resolver_rol_desde_cargo_docente(cargo):
    cargo_norm = _normalizar_texto_simple(cargo)
    return _DOCENTE_CARGO_ROLE_ALIASES.get(cargo_norm, ROL_DOCENTE)


DESKTOP_PERMISSION_GROUPS = {
    "Sesión": [
        "desktop.session.open.docente",
        "desktop.session.open.estudiante",
    ],
    "Docente": [
        "desktop.docente.banco_preguntas",
        "desktop.docente.autoevaluacion",
        "desktop.docente.configuracion_examen",
        "desktop.docente.exportar_excel",
        "desktop.docente.exportar_consolidado",
        "desktop.docente.ver_detalle",
        "desktop.docente.autorizar_revision",
        "desktop.docente.resetear_nota",
        "desktop.docente.filtros",
        "desktop.docente.tabla",
    ],
    "Estudiante": [
        "desktop.estudiante.historial",
        "desktop.estudiante.autoevaluacion",
        "desktop.estudiante.presentar_examen",
    ],
    "Super Admin - Pestañas": [],
    "Super Admin - Docentes": [
        "desktop.superadmin.docentes.crear",
        "desktop.superadmin.docentes.editar",
        "desktop.superadmin.docentes.carga_academica",
        "desktop.superadmin.docentes.eliminar",
        "desktop.superadmin.docentes.recargar",
        "desktop.superadmin.docentes.importar",
        "desktop.superadmin.docentes.exportar",
    ],
    "Super Admin - Carga Académica": [
        "desktop.superadmin.carga_academica.crear",
        "desktop.superadmin.carga_academica.editar",
        "desktop.superadmin.carga_academica.eliminar",
        "desktop.superadmin.carga_academica.actualizar",
        "desktop.superadmin.carga_academica.horas",
    ],
    "Super Admin - Matrícula": [
        "desktop.superadmin.matricula.importar",
        "desktop.superadmin.matricula.crear",
        "desktop.superadmin.matricula.editar",
        "desktop.superadmin.matricula.cambiar_curso",
        "desktop.superadmin.matricula.eliminar",
        "desktop.superadmin.matricula.vaciar",
    ],
    "Super Admin - Plan de Estudios": [
        "desktop.superadmin.plan_estudio.importar",
        "desktop.superadmin.plan_estudio.agregar",
        "desktop.superadmin.plan_estudio.editar",
        "desktop.superadmin.plan_estudio.copiar",
        "desktop.superadmin.plan_estudio.catalogo_areas",
        "desktop.superadmin.plan_estudio.eliminar",
        "desktop.superadmin.plan_estudio.vaciar",
        "desktop.superadmin.plan_estudio.actualizar",
    ],
    "Super Admin - Áreas": [
        "desktop.superadmin.areas.agregar",
        "desktop.superadmin.areas.editar",
        "desktop.superadmin.areas.eliminar",
        "desktop.superadmin.areas.importar",
        "desktop.superadmin.areas.actualizar",
    ],
    "Super Admin - Evaluaciones": [
        "desktop.superadmin.evaluaciones.generar_pdf",
        "desktop.superadmin.evaluaciones.actualizar_preguntas",
        "desktop.superadmin.evaluaciones.generar_cuadernillo_multi_area",
        "desktop.superadmin.evaluaciones.consultar_examen",
        "desktop.superadmin.evaluaciones.calificar_camara",
        "desktop.superadmin.evaluaciones.ver_resultados_camara",
    ],
    "Super Admin - Planillas": [
        "desktop.superadmin.planillas.asistencia.guardar",
        "desktop.superadmin.planillas.asistencia.descargar",
        "desktop.superadmin.planillas.calificaciones.guardar",
        "desktop.superadmin.planillas.calificaciones.descargar",
    ],
    "Super Admin - Boletines": [
        "desktop.superadmin.boletines.actualizar",
        "desktop.superadmin.boletines.exportar_pdf",
    ],
    "Super Admin - Desempeños": [
        "desktop.superadmin.desempenos.cargar",
        "desktop.superadmin.desempenos.guardar",
        "desktop.superadmin.desempenos.sugerir",
        "desktop.superadmin.desempenos.eliminar",
        "desktop.superadmin.desempenos.actualizar",
    ],
    "Super Admin - Acceso Docente": [
        "desktop.superadmin.maestro.configuracion.guardar",
        "desktop.superadmin.maestro.autoevaluacion",
        "desktop.superadmin.maestro.vaciar_calificaciones",
        "desktop.superadmin.maestro.actualizar",
        "desktop.superadmin.maestro.exportar_excel",
        "desktop.superadmin.maestro.exportar_consolidado",
        "desktop.superadmin.maestro.ver_detalle",
        "desktop.superadmin.maestro.autorizar_revision",
        "desktop.superadmin.maestro.resetear_nota",
        "desktop.superadmin.maestro.filtros.limpiar",
        "desktop.superadmin.maestro.filtros.buscar",
    ],
    "Super Admin - Configuración": [
        "desktop.superadmin.configuracion_plantel.guardar",
        "desktop.superadmin.contenido_institucional.guardar",
        "desktop.superadmin.contenido_institucional.eliminar",
        "desktop.superadmin.seguridad",
    ],
}

DESKTOP_PERMISSION_LABELS = {
    "desktop.session.open.docente": "Abrir módulo docente",
    "desktop.session.open.estudiante": "Abrir módulo estudiante",
    "desktop.docente.banco_preguntas": "Docente: banco de preguntas",
    "desktop.docente.autoevaluacion": "Docente: autoevaluación",
    "desktop.docente.configuracion_examen": "Docente: configuración de examen",
    "desktop.docente.exportar_excel": "Docente: exportar Excel",
    "desktop.docente.exportar_consolidado": "Docente: exportar consolidado",
    "desktop.docente.ver_detalle": "Docente: ver detalle",
    "desktop.docente.autorizar_revision": "Docente: autorizar revisión",
    "desktop.docente.resetear_nota": "Docente: resetear nota",
    "desktop.docente.filtros": "Docente: usar filtros",
    "desktop.docente.tabla": "Docente: ver tabla",
    "desktop.estudiante.historial": "Estudiante: ver historial",
    "desktop.estudiante.autoevaluacion": "Estudiante: responder autoevaluación",
    "desktop.estudiante.presentar_examen": "Estudiante: presentar examen",
    "desktop.superadmin.tab.configuracion": "Super Admin: abrir Configuración",
    "desktop.superadmin.tab.docentes": "Super Admin: abrir Planta Docente",
    "desktop.superadmin.tab.carga_academica": "Super Admin: abrir Carga Académica",
    "desktop.superadmin.tab.plan_estudio": "Super Admin: abrir Plan de Estudios",
    "desktop.superadmin.tab.matricula": "Super Admin: abrir Matrícula",
    "desktop.superadmin.tab.banco_preguntas": "Super Admin: abrir Banco de Preguntas",
    "desktop.superadmin.tab.evaluaciones": "Super Admin: abrir Evaluaciones",
    "desktop.superadmin.tab.planillas": "Super Admin: abrir Planillas",
    "desktop.superadmin.tab.certificados": "Super Admin: abrir Certificados",
    "desktop.superadmin.tab.acceso_docente": "Super Admin: abrir Acceso Docente",
    "desktop.superadmin.tab.boletines": "Super Admin: abrir Boletines",
    "desktop.superadmin.tab.desempenos": "Super Admin: abrir Desempeños",
    "desktop.superadmin.docentes.crear": "Docentes: crear registro",
    "desktop.superadmin.docentes.editar": "Docentes: editar registro",
    "desktop.superadmin.docentes.carga_academica": "Docentes: abrir carga académica",
    "desktop.superadmin.docentes.eliminar": "Docentes: eliminar registro",
    "desktop.superadmin.docentes.recargar": "Docentes: recargar listado",
    "desktop.superadmin.docentes.importar": "Docentes: importar desde archivo",
    "desktop.superadmin.docentes.exportar": "Docentes: exportar listado",
    "desktop.superadmin.carga_academica.crear": "Carga académica: crear asignación",
    "desktop.superadmin.carga_academica.editar": "Carga académica: editar asignación",
    "desktop.superadmin.carga_academica.eliminar": "Carga académica: eliminar asignación",
    "desktop.superadmin.carga_academica.actualizar": "Carga académica: actualizar vista",
    "desktop.superadmin.carga_academica.horas": "Carga académica: configurar horas docentes",
    "desktop.superadmin.matricula.importar": "Matrícula: importar estudiantes",
    "desktop.superadmin.matricula.crear": "Matrícula: crear estudiante",
    "desktop.superadmin.matricula.editar": "Matrícula: editar estudiante",
    "desktop.superadmin.matricula.cambiar_curso": "Matrícula: cambiar curso",
    "desktop.superadmin.matricula.eliminar": "Matrícula: eliminar estudiante",
    "desktop.superadmin.matricula.vaciar": "Matrícula: vaciar todo",
    "desktop.superadmin.plan_estudio.importar": "Plan de Estudios: importar",
    "desktop.superadmin.plan_estudio.agregar": "Plan de Estudios: agregar",
    "desktop.superadmin.plan_estudio.editar": "Plan de Estudios: editar",
    "desktop.superadmin.plan_estudio.copiar": "Plan de Estudios: copiar plan",
    "desktop.superadmin.plan_estudio.catalogo_areas": "Plan de Estudios: abrir catálogo de áreas",
    "desktop.superadmin.plan_estudio.eliminar": "Plan de Estudios: eliminar registro",
    "desktop.superadmin.plan_estudio.vaciar": "Plan de Estudios: vaciar todo",
    "desktop.superadmin.plan_estudio.actualizar": "Plan de Estudios: actualizar vista",
    "desktop.superadmin.areas.agregar": "Áreas: agregar",
    "desktop.superadmin.areas.editar": "Áreas: editar",
    "desktop.superadmin.areas.eliminar": "Áreas: eliminar",
    "desktop.superadmin.areas.importar": "Áreas: importar CSV",
    "desktop.superadmin.areas.actualizar": "Áreas: actualizar catálogo",
    "desktop.superadmin.evaluaciones.generar_pdf": "Evaluaciones: generar PDF",
    "desktop.superadmin.evaluaciones.actualizar_preguntas": "Evaluaciones: actualizar preguntas",
    "desktop.superadmin.evaluaciones.generar_cuadernillo_multi_area": "Evaluaciones: generar cuadernillo multi-área",
    "desktop.superadmin.evaluaciones.consultar_examen": "Evaluaciones: consultar examen",
    "desktop.superadmin.evaluaciones.calificar_camara": "Evaluaciones: calificar con cámara",
    "desktop.superadmin.evaluaciones.ver_resultados_camara": "Evaluaciones: ver resultados de cámara",
    "desktop.superadmin.planillas.asistencia.guardar": "Planillas asistencia: guardar",
    "desktop.superadmin.planillas.asistencia.descargar": "Planillas asistencia: descargar",
    "desktop.superadmin.planillas.calificaciones.guardar": "Planillas calificaciones: guardar",
    "desktop.superadmin.planillas.calificaciones.descargar": "Planillas calificaciones: descargar",
    "desktop.superadmin.boletines.actualizar": "Boletines: actualizar panel",
    "desktop.superadmin.boletines.exportar_pdf": "Boletines: exportar PDF",
    "desktop.superadmin.desempenos.cargar": "Desempeños: cargar plantilla",
    "desktop.superadmin.desempenos.guardar": "Desempeños: guardar plantilla",
    "desktop.superadmin.desempenos.sugerir": "Desempeños: generar sugerencias",
    "desktop.superadmin.desempenos.eliminar": "Desempeños: eliminar plantilla",
    "desktop.superadmin.desempenos.actualizar": "Desempeños: actualizar catálogos",
    "desktop.superadmin.maestro.configuracion.guardar": "Acceso Docente: guardar configuración",
    "desktop.superadmin.maestro.autoevaluacion": "Acceso Docente: autoevaluación",
    "desktop.superadmin.maestro.vaciar_calificaciones": "Acceso Docente: vaciar calificaciones",
    "desktop.superadmin.maestro.actualizar": "Acceso Docente: actualizar datos",
    "desktop.superadmin.maestro.exportar_excel": "Acceso Docente: exportar Excel",
    "desktop.superadmin.maestro.exportar_consolidado": "Acceso Docente: exportar consolidado",
    "desktop.superadmin.maestro.ver_detalle": "Acceso Docente: ver detalle",
    "desktop.superadmin.maestro.autorizar_revision": "Acceso Docente: autorizar revisión",
    "desktop.superadmin.maestro.resetear_nota": "Acceso Docente: resetear nota",
    "desktop.superadmin.maestro.filtros.limpiar": "Acceso Docente: limpiar filtros",
    "desktop.superadmin.maestro.filtros.buscar": "Acceso Docente: buscar con filtros",
    "desktop.superadmin.configuracion_plantel.guardar": "Configuración Plantel: guardar",
    "desktop.superadmin.contenido_institucional.guardar": "Contenido Institucional: guardar",
    "desktop.superadmin.contenido_institucional.eliminar": "Contenido Institucional: eliminar",
    "desktop.superadmin.seguridad": "Seguridad: acciones críticas",
}

DESKTOP_SUPERADMIN_TAB_PERMISSIONS = {
    "Configuración": "desktop.superadmin.tab.configuracion",
    "Planta Docente": "desktop.superadmin.tab.docentes",
    "Carga Académica": "desktop.superadmin.tab.carga_academica",
    "Plan de Estudios": "desktop.superadmin.tab.plan_estudio",
    "Matrícula": "desktop.superadmin.tab.matricula",
    "Banco Preguntas": "desktop.superadmin.tab.banco_preguntas",
    "Evaluaciones": "desktop.superadmin.tab.evaluaciones",
    "Planillas": "desktop.superadmin.tab.planillas",
    "Certificados": "desktop.superadmin.tab.certificados",
    "Acceso Docente": "desktop.superadmin.tab.acceso_docente",
    "Boletines": "desktop.superadmin.tab.boletines",
    "Desempeños": "desktop.superadmin.tab.desempenos",
}

SUPERADMIN_ACTION_PREFIX_TO_TAB = {
    "desktop.superadmin.docentes.": "desktop.superadmin.tab.docentes",
    "desktop.superadmin.carga_academica.": "desktop.superadmin.tab.carga_academica",
    "desktop.superadmin.matricula.": "desktop.superadmin.tab.matricula",
    "desktop.superadmin.plan_estudio.": "desktop.superadmin.tab.plan_estudio",
    "desktop.superadmin.areas.": "desktop.superadmin.tab.plan_estudio",
    "desktop.superadmin.evaluaciones.": "desktop.superadmin.tab.evaluaciones",
    "desktop.superadmin.planillas.": "desktop.superadmin.tab.planillas",
    "desktop.superadmin.maestro.": "desktop.superadmin.tab.acceso_docente",
    "desktop.superadmin.boletines.": "desktop.superadmin.tab.boletines",
    "desktop.superadmin.desempenos.": "desktop.superadmin.tab.desempenos",
    "desktop.superadmin.configuracion_plantel.": "desktop.superadmin.tab.configuracion",
    "desktop.superadmin.contenido_institucional.": "desktop.superadmin.tab.configuracion",
    "desktop.superadmin.seguridad": "desktop.superadmin.tab.configuracion",
}

DESKTOP_PERMISSION_GROUPS["Super Admin - Pestañas"] = list(
    DESKTOP_SUPERADMIN_TAB_PERMISSIONS.values()
)


def listar_permisos_pestanas_superadmin():
    return list(DESKTOP_SUPERADMIN_TAB_PERMISSIONS.values())


PERMISSION_GROUPS_HIDDEN_IN_EDITOR = {"Super Admin - Pestañas"}


def listar_permisos_superadmin():
    permisos = []
    for permiso in listar_todos_los_permisos():
        if str(permiso).startswith("desktop.superadmin."):
            permisos.append(permiso)
    return permisos


def resolver_pestana_superadmin_para_permiso(permiso):
    permiso_txt = str(permiso or "").strip()
    if not permiso_txt:
        return ""
    if permiso_txt in DESKTOP_SUPERADMIN_TAB_PERMISSIONS.values():
        return permiso_txt
    for prefijo, permiso_tab in SUPERADMIN_ACTION_PREFIX_TO_TAB.items():
        if permiso_txt == prefijo or permiso_txt.startswith(prefijo):
            return permiso_tab
    return ""


def tiene_algun_permiso(usuario, permisos):
    for permiso in permisos or []:
        if tiene_permiso(usuario, permiso):
            return True
    return False


def superadmin_tab_habilitada(usuario, permiso_tab):
    permiso_tab_txt = str(permiso_tab or "").strip()
    if not permiso_tab_txt:
        return False
    if tiene_permiso(usuario, permiso_tab_txt):
        return True

    if usuario is None:
        return False

    permisos_set = obtener_permisos_efectivos_usuario(usuario)

    if "*" in permisos_set:
        return True

    for permiso in permisos_set:
        if resolver_pestana_superadmin_para_permiso(permiso) == permiso_tab_txt:
            return True
    return False


def puede_abrir_superadmin(usuario):
    return tiene_algun_permiso(usuario, listar_permisos_superadmin())


def _ensure_rbac_schema():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rbac_role_profiles (
                rol TEXT PRIMARY KEY,
                personalizado INTEGER DEFAULT 1,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rbac_role_permissions (
                rol TEXT NOT NULL,
                permiso TEXT NOT NULL,
                PRIMARY KEY (rol, permiso)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rbac_user_profiles (
                documento TEXT NOT NULL,
                rol TEXT NOT NULL,
                personalizado INTEGER DEFAULT 1,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (documento, rol)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rbac_user_permissions (
                documento TEXT NOT NULL,
                rol TEXT NOT NULL,
                permiso TEXT NOT NULL,
                PRIMARY KEY (documento, rol, permiso)
            )
            """
        )
        conn.commit()


def listar_catalogo_permisos():
    catalogo = {}
    for grupo, permisos in DESKTOP_PERMISSION_GROUPS.items():
        catalogo[grupo] = [
            permiso for permiso in permisos if permiso and permiso != "*"
        ]
    return catalogo


def listar_catalogo_permisos_asignables():
    catalogo = {}
    for grupo, permisos in listar_catalogo_permisos().items():
        if grupo in PERMISSION_GROUPS_HIDDEN_IN_EDITOR:
            continue
        catalogo[grupo] = list(permisos)
    return catalogo


def listar_todos_los_permisos():
    permisos = []
    vistos = set()
    for grupo_permisos in listar_catalogo_permisos().values():
        for permiso in grupo_permisos:
            if permiso in vistos:
                continue
            vistos.add(permiso)
            permisos.append(permiso)
    return permisos


def describir_permiso(permiso):
    permiso_txt = str(permiso or "").strip()
    if not permiso_txt:
        return ""
    if permiso_txt in DESKTOP_PERMISSION_LABELS:
        return DESKTOP_PERMISSION_LABELS[permiso_txt]
    base = permiso_txt.split(".")
    if len(base) >= 2:
        return " > ".join(part.replace("_", " ").title() for part in base[1:])
    return permiso_txt


def _listar_permisos_predeterminados_rol(rol):
    rol_norm = normalizar_rol_rbac(rol)
    if rol_norm == ROL_SUPERADMIN:
        return {"*"}
    return set(_DEFAULT_DESKTOP_PERMISSIONS_BY_ROLE.get(rol_norm, set()))


def obtener_configuracion_permisos_rol(rol):
    rol_norm = normalizar_rol_rbac(rol)
    predeterminados = _listar_permisos_predeterminados_rol(rol_norm)
    if rol_norm == ROL_SUPERADMIN:
        return {
            "rol": rol_norm,
            "permisos": {"*"},
            "predeterminados": {"*"},
            "personalizado": False,
        }

    _ensure_rbac_schema()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT personalizado FROM rbac_role_profiles WHERE rol = ?",
            (rol_norm,),
        )
        perfil = cur.fetchone()
        if not perfil:
            return {
                "rol": rol_norm,
                "permisos": set(predeterminados),
                "predeterminados": set(predeterminados),
                "personalizado": False,
            }

        cur.execute(
            "SELECT permiso FROM rbac_role_permissions WHERE rol = ? ORDER BY permiso",
            (rol_norm,),
        )
        permisos = {
            str(row[0]).strip() for row in cur.fetchall() if row and str(row[0]).strip()
        }
    return {
        "rol": rol_norm,
        "permisos": permisos,
        "predeterminados": set(predeterminados),
        "personalizado": True,
    }


def obtener_configuracion_permisos_usuario(documento, rol):
    rol_norm = normalizar_rol_rbac(rol)
    doc = str(documento or "").strip()
    cfg_rol = obtener_configuracion_permisos_rol(rol_norm)
    if rol_norm == ROL_SUPERADMIN:
        return {
            "documento": doc,
            "rol": rol_norm,
            "permisos": {"*"},
            "personalizado": False,
            "origen": "superadmin",
            "heredados": {"*"},
        }

    if not doc:
        return {
            "documento": doc,
            "rol": rol_norm,
            "permisos": set(cfg_rol["permisos"]),
            "personalizado": False,
            "origen": "rol",
            "heredados": set(cfg_rol["permisos"]),
        }

    _ensure_rbac_schema()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT personalizado FROM rbac_user_profiles WHERE documento = ? AND rol = ?",
            (doc, rol_norm),
        )
        perfil = cur.fetchone()
        if not perfil:
            return {
                "documento": doc,
                "rol": rol_norm,
                "permisos": set(cfg_rol["permisos"]),
                "personalizado": False,
                "origen": "rol",
                "heredados": set(cfg_rol["permisos"]),
            }

        cur.execute(
            "SELECT permiso FROM rbac_user_permissions WHERE documento = ? AND rol = ? ORDER BY permiso",
            (doc, rol_norm),
        )
        permisos = {
            str(row[0]).strip() for row in cur.fetchall() if row and str(row[0]).strip()
        }
    return {
        "documento": doc,
        "rol": rol_norm,
        "permisos": permisos,
        "personalizado": True,
        "origen": "usuario",
        "heredados": set(cfg_rol["permisos"]),
    }


def guardar_permisos_rol(rol, permisos):
    rol_norm = normalizar_rol_rbac(rol)
    if rol_norm == ROL_SUPERADMIN:
        raise ValueError(
            "El rol SuperAdmin conserva acceso total y no se puede restringir."
        )

    permisos_validos = {
        str(permiso).strip()
        for permiso in (permisos or [])
        if str(permiso).strip() in set(listar_todos_los_permisos())
    }
    _ensure_rbac_schema()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO rbac_role_profiles(rol, personalizado, fecha_actualizacion) VALUES (?, 1, CURRENT_TIMESTAMP)",
            (rol_norm,),
        )
        cur.execute("DELETE FROM rbac_role_permissions WHERE rol = ?", (rol_norm,))
        cur.executemany(
            "INSERT INTO rbac_role_permissions(rol, permiso) VALUES (?, ?)",
            [(rol_norm, permiso) for permiso in sorted(permisos_validos)],
        )
        conn.commit()


def restablecer_permisos_rol(rol):
    rol_norm = normalizar_rol_rbac(rol)
    if rol_norm == ROL_SUPERADMIN:
        return
    _ensure_rbac_schema()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM rbac_role_permissions WHERE rol = ?", (rol_norm,))
        cur.execute("DELETE FROM rbac_role_profiles WHERE rol = ?", (rol_norm,))
        conn.commit()


def guardar_permisos_usuario(documento, rol, permisos):
    rol_norm = normalizar_rol_rbac(rol)
    doc = str(documento or "").strip()
    if not doc:
        raise ValueError(
            "El documento es obligatorio para guardar permisos personalizados."
        )
    if rol_norm == ROL_SUPERADMIN:
        raise ValueError(
            "SuperAdmin conserva acceso total y no requiere permisos personalizados."
        )

    permisos_validos = {
        str(permiso).strip()
        for permiso in (permisos or [])
        if str(permiso).strip() in set(listar_todos_los_permisos())
    }
    _ensure_rbac_schema()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO rbac_user_profiles(documento, rol, personalizado, fecha_actualizacion) VALUES (?, ?, 1, CURRENT_TIMESTAMP)",
            (doc, rol_norm),
        )
        cur.execute(
            "DELETE FROM rbac_user_permissions WHERE documento = ? AND rol = ?",
            (doc, rol_norm),
        )
        cur.executemany(
            "INSERT INTO rbac_user_permissions(documento, rol, permiso) VALUES (?, ?, ?)",
            [(doc, rol_norm, permiso) for permiso in sorted(permisos_validos)],
        )
        conn.commit()


def restablecer_permisos_usuario(documento, rol):
    rol_norm = normalizar_rol_rbac(rol)
    doc = str(documento or "").strip()
    if not doc or rol_norm == ROL_SUPERADMIN:
        return
    _ensure_rbac_schema()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM rbac_user_permissions WHERE documento = ? AND rol = ?",
            (doc, rol_norm),
        )
        cur.execute(
            "DELETE FROM rbac_user_profiles WHERE documento = ? AND rol = ?",
            (doc, rol_norm),
        )
        conn.commit()


def listar_usuarios_para_permisos(rol):
    rol_norm = normalizar_rol_rbac(rol)
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            if rol_norm in {
                ROL_DOCENTE,
                ROL_RECTOR,
                ROL_SECRETARIA,
                ROL_COORDINADOR,
            }:
                cur.execute(
                    "SELECT documento, nombre, cargo FROM docentes WHERE estado = 'Activo' ORDER BY nombre, documento"
                )
                rows = cur.fetchall()
                return [
                    {
                        "documento": str(doc or "").strip(),
                        "nombre": str(nombre or "").strip() or str(doc or "").strip(),
                        "rol": rol_norm,
                    }
                    for doc, nombre, cargo in rows
                    if str(doc or "").strip()
                    and _resolver_rol_desde_cargo_docente(cargo) == rol_norm
                ]
            if rol_norm == ROL_ESTUDIANTE:
                cur.execute(
                    """
                    SELECT documento, apellido1, apellido2, nombre1, nombre2
                    FROM estudiantes
                    WHERE estado = 'Activo'
                    ORDER BY apellido1, apellido2, nombre1, nombre2, documento
                    """
                )
                rows = cur.fetchall()
                usuarios = []
                for row in rows:
                    estudiante = {
                        "documento": row[0],
                        "apellido1": row[1],
                        "apellido2": row[2],
                        "nombre1": row[3],
                        "nombre2": row[4],
                    }
                    doc = str(estudiante.get("documento") or "").strip()
                    if not doc:
                        continue
                    usuarios.append(
                        {
                            "documento": doc,
                            "nombre": construir_nombre(estudiante) or doc,
                            "rol": rol_norm,
                        }
                    )
                return usuarios
    except Exception:
        return []
    return []


def normalizar_rol_rbac(rol):
    return _ROLE_ALIASES.get(
        str(rol or "").strip().lower(), str(rol or "").strip().lower()
    )


def listar_permisos_rol(rol):
    return set(obtener_configuracion_permisos_rol(rol).get("permisos", set()))


def listar_permisos_usuario(documento, rol):
    return set(
        obtener_configuracion_permisos_usuario(documento, rol).get("permisos", set())
    )


def enriquecer_usuario_rbac(usuario):
    data = {}
    if usuario is None:
        pass
    elif hasattr(usuario, "__dict__") and isinstance(vars(usuario), dict):
        data = {key: value for key, value in vars(usuario).items()}
    elif isinstance(usuario, dict):
        data = {key: value for key, value in usuario.items()}
    rol_original = str(data.get("rol") or "").strip().lower()
    rol_norm = normalizar_rol_rbac(rol_original)
    documento = str(data.get("documento") or "").strip()
    data["rol_original"] = rol_original
    data["rol_canonico"] = rol_norm
    permisos_usuario = set(listar_permisos_usuario(documento, rol_norm))
    if rol_norm == ROL_SUPERADMIN:
        permisos_usuario.add("*")
        permisos_usuario.add("desktop.superadmin.tab.academico")
    data["permisos"] = sorted(permisos_usuario)
    return data


def obtener_permisos_efectivos_usuario(usuario):
    if usuario is None:
        return set()

    if isinstance(usuario, dict):
        rol = usuario.get("rol_canonico") or usuario.get("rol")
        documento = usuario.get("documento")
        permisos = usuario.get("permisos")
    else:
        rol = getattr(usuario, "rol_canonico", None) or getattr(usuario, "rol", None)
        documento = getattr(usuario, "documento", None)
        permisos = getattr(usuario, "permisos", None)

    rol_norm = normalizar_rol_rbac(rol)
    documento_txt = str(documento or "").strip()
    permisos_set = set(permisos or [])

    if rol_norm == ROL_SUPERADMIN or "*" in permisos_set:
        return permisos_set or {"*"}

    if documento_txt and rol_norm:
        permisos_db = listar_permisos_usuario(documento_txt, rol_norm)
        if permisos_db:
            return set(permisos_db)

    return permisos_set


def tiene_permiso(usuario, permiso):
    permiso_txt = str(permiso or "").strip()
    if not permiso_txt:
        return False

    if usuario is None:
        return False

    permisos_set = obtener_permisos_efectivos_usuario(usuario)

    return "*" in permisos_set or permiso_txt in permisos_set


_WEB_ROLE_RULES = (
    ("/", ROLES_WEB_TODOS),
    ("/superadmin", ROLES_WEB_RECTOR),
    ("/matricula", ROLES_WEB_SECRETARIA),
    ("/gestion-academica", ROLES_WEB_GESTION),
    ("/orientacion", ROLES_WEB_ADMIN),
    ("/secretaria", ROLES_WEB_SECRETARIA),
    ("/plan-estudios", ROLES_WEB_GESTION),
    ("/seguridad", ROLES_WEB_ADMIN),
    ("/configuracion-plantel", ROLES_WEB_RECTOR),
    ("/planta-docente", ROLES_WEB_GESTION),
    ("/carga-academica", ROLES_WEB_GESTION),
    ("/estudiantes", ROLES_WEB_DIRECTIVOS),
    ("/maestro", ROLES_WEB_GESTION),
    ("/docente", ROLES_WEB_DOCENTE),
    ("/examen", ROLES_WEB_TODOS),
    ("/autoevaluacion", ROLES_WEB_TODOS),
    ("/examenes", ROLES_WEB_DOCENTE),
    ("/banco-preguntas", ROLES_WEB_DOCENTE),
    ("/calificaciones", ROLES_WEB_DOCENTE),
    ("/resultados", ROLES_WEB_DOCENTE),
    ("/escanear", ROLES_WEB_DOCENTE),
)

_API_ROLE_RULES = (
    ("/api/health", None, ROLES_WEB_TODOS),
    ("/api/auth/status", None, ROLES_WEB_TODOS),
    ("/api/info", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/usuarios/estudiante", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/usuarios/docente", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/superadmin/resumen", ("GET",), ROLES_WEB_RECTOR),
    ("/api/matricula/listado", ("GET",), ROLES_WEB_SECRETARIA),
    ("/api/matricula/catalogos", ("GET",), ROLES_WEB_SECRETARIA),
    ("/api/matricula/importar", ("POST",), ROLES_WEB_SECRETARIA),
    ("/api/matricula/cambiar-curso", ("POST",), ROLES_WEB_SECRETARIA),
    ("/api/seguridad/resumen", ("GET",), ROLES_WEB_ADMIN),
    ("/api/seguridad/cambiar-clave", ("POST",), ROLES_WEB_ADMIN),
    ("/api/plantel/config", ("GET",), ROLES_WEB_RECTOR),
    ("/api/plantel/config", ("PUT",), ROLES_WEB_ADMIN),
    ("/api/plantel/escala", ("GET",), ROLES_WEB_RECTOR),
    ("/api/plantel/escala", ("PUT",), ROLES_WEB_ADMIN),
    ("/api/plantel/logo", ("POST",), ROLES_WEB_ADMIN),
    ("/api/secretaria", None, ROLES_WEB_SECRETARIA),
    ("/api/gestion-academica", None, ROLES_WEB_GESTION),
    ("/api/orientacion", None, ROLES_WEB_ADMIN),
    ("/api/resultados", None, ROLES_WEB_DOCENTE),
    ("/api/docentes/importar", ("POST",), ROLES_WEB_ADMIN),
    ("/api/docentes/exportar", ("GET",), ROLES_WEB_GESTION),
    ("/api/docentes", ("GET",), ROLES_WEB_GESTION),
    ("/api/docentes", ("POST", "PUT", "DELETE"), ROLES_WEB_ADMIN),
    ("/api/carga-academica", ("GET",), ROLES_WEB_GESTION),
    ("/api/carga-academica", ("POST", "PUT", "DELETE"), ROLES_WEB_ADMIN),
    ("/api/estudiantes", ("GET",), ROLES_WEB_DIRECTIVOS),
    ("/api/estudiantes", ("POST", "PUT", "DELETE"), ROLES_WEB_ADMIN),
    ("/api/sistema/config", None, ROLES_WEB_ADMIN),
    ("/api/sistema/config-todas", ("GET",), ROLES_WEB_ADMIN),
    ("/api/preguntas", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/examenes/config", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/examenes/generar", ("POST",), ROLES_WEB_DOCENTE),
    ("/api/examenes/generados", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/examenes/multi-area", None, ROLES_WEB_DOCENTE),
    ("/api/examenes/", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/banco-preguntas/areas", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/banco-preguntas/grados", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/banco-preguntas/evaluaciones", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/banco-preguntas", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/banco-preguntas", ("POST", "PUT", "DELETE"), ROLES_WEB_ADMIN),
    ("/api/calificaciones/resumen", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/calificaciones/camara", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/calificaciones", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/docente/panel", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/docente/autoevaluacion", None, ROLES_WEB_DOCENTE),
    ("/api/docente/cursos", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/docente/config", ("POST",), ROLES_WEB_DOCENTE),
    ("/api/docente/autorizar-revision", ("POST",), ROLES_WEB_DOCENTE),
    ("/api/docente/reset", ("POST",), ROLES_WEB_DOCENTE),
    ("/api/docente/detalle", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/docente/exportar", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/docente/exportar-consolidado", ("GET",), ROLES_WEB_DOCENTE),
    ("/api/omr/procesar", ("POST",), ROLES_WEB_DOCENTE),
    ("/api/omr/procesar-json", ("POST",), ROLES_WEB_DOCENTE),
    ("/api/omr/parsear-qr", ("POST",), ROLES_WEB_DOCENTE),
    # Rutas de examen para estudiantes (y docentes/admin)
    ("/api/examen/areas", ("GET",), ROLES_WEB_TODOS),
    ("/api/examen/iniciar", ("POST",), ROLES_WEB_TODOS),
    ("/api/examen/respuesta", ("POST",), ROLES_WEB_TODOS),
    ("/api/examen/finalizar", ("POST",), ROLES_WEB_TODOS),
    ("/api/examen/historial", ("GET",), ROLES_WEB_TODOS),
    ("/api/examen/detalle", ("GET",), ROLES_WEB_TODOS),
    ("/api/autoevaluacion", None, ROLES_WEB_TODOS),
)


def normalizar_rol(rol):
    return str(rol or "").strip().lower()


def validar_clave_maestra(valor):
    clave_maestra = str(obtener_clave_maestra() or "").strip()
    return bool(clave_maestra) and str(valor or "").strip() == clave_maestra


def obtener_perfil_superadmin():
    nombres = str(obtener_config("superadmin_nombres") or "").strip()
    apellidos = str(obtener_config("superadmin_apellidos") or "").strip()
    documento = str(obtener_config("superadmin_documento") or "").strip() or "admin"
    nombre_completo = " ".join(
        parte for parte in (nombres, apellidos) if str(parte or "").strip()
    ).strip()
    return {
        "documento": documento,
        "nombres": nombres,
        "apellidos": apellidos,
        "nombre": nombre_completo or "Administrador",
    }


def resolver_identidad_acceso(documento, clave_maestra=None):
    doc = str(documento or "").strip()
    if not doc:
        return None, "documento_requerido"

    if doc.lower() == "admin":
        if not str(clave_maestra or "").strip():
            return None, "clave_maestra_requerida"
        if not validar_clave_maestra(clave_maestra):
            return None, "clave_maestra_invalida"
        perfil_superadmin = obtener_perfil_superadmin()
        return {
            "documento": perfil_superadmin["documento"],
            "nombre": perfil_superadmin["nombre"],
            "nombres": perfil_superadmin["nombres"],
            "apellidos": perfil_superadmin["apellidos"],
            "alias_acceso": "admin",
            "rol": ROL_ADMIN,
        }, None

    if validar_clave_maestra(doc):
        perfil_superadmin = obtener_perfil_superadmin()
        return {
            "documento": perfil_superadmin["documento"],
            "nombre": perfil_superadmin["nombre"],
            "nombres": perfil_superadmin["nombres"],
            "apellidos": perfil_superadmin["apellidos"],
            "alias_acceso": "admin",
            "rol": ROL_ADMIN,
        }, None

    # Personal: requiere clave
    from .docentes import buscar_docente

    docente = buscar_docente(doc)
    if docente and docente.get("estado", "").lower() == "activo":
        # Si no se pasa clave_maestra, se interpreta como clave personal
        clave_personal = str(clave_maestra or "").strip()
        if not clave_personal:
            return None, "clave_personal_requerida"
        if not validar_clave_personal(doc, clave_personal):
            return None, "clave_personal_invalida"
        return {
            "documento": doc,
            "nombre": str(docente.get("nombre") or "").strip() or "Docente",
            "rol": _resolver_rol_desde_cargo_docente(docente.get("cargo")),
            "cargo": str(docente.get("cargo") or "").strip(),
        }, None

    estudiante = validar_estudiante(doc)
    if estudiante:
        nombre_est = construir_nombre(estudiante) or "Estudiante"
        return {
            "documento": doc,
            "nombre": nombre_est,
            "rol": ROL_ESTUDIANTE,
            "grado": estudiante.get("grado"),
            "curso": estudiante.get("curso"),
            "jornada": estudiante.get("jornada"),
        }, None

    return None, "documento_no_encontrado"


def normalizar_api_path(path):
    path_text = str(path or "").strip()
    if path_text.startswith("/api/v1/"):
        return "/api/" + path_text[len("/api/v1/") :]
    return path_text


def _path_matches(path, prefix):
    if prefix == "/":
        return path == "/"
    if path == prefix:
        return True
    if prefix.endswith("/"):
        return path.startswith(prefix)
    return path.startswith(prefix + "/")


def rol_tiene_acceso_web(rol, path):
    rol_norm = normalizar_rol(rol)
    path_text = str(path or "").strip() or "/"
    for prefix, roles in _WEB_ROLE_RULES:
        if _path_matches(path_text, prefix):
            return rol_norm in roles
    return rol_norm == ROL_ADMIN


def rol_tiene_acceso_api(rol, path, method="GET"):
    rol_norm = normalizar_rol(rol)
    path_norm = normalizar_api_path(path)
    method_norm = str(method or "GET").strip().upper()

    for prefix, methods, roles in _API_ROLE_RULES:
        if not _path_matches(path_norm, prefix):
            continue
        if methods is not None and method_norm not in methods:
            continue
        return rol_norm in roles

    return rol_norm == ROL_ADMIN


def validar_estudiante(documento):
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT tipo_documento, documento, apellido1, apellido2, nombre1, nombre2, grado, curso, jornada, estado
                FROM estudiantes
                WHERE documento = ?
                """,
                (documento,),
            )
            row = cur.fetchone()
        if not row:
            return None
        if str(row[9]).strip().lower() != "activo":
            return None
        estudiante = {
            "tipo_documento": row[0],
            "documento": row[1],
            "apellido1": row[2],
            "apellido2": row[3],
            "nombre1": row[4],
            "nombre2": row[5],
            "grado": row[6],
            "curso": row[7],
            "jornada": row[8],
            "estado": row[9],
        }
        estudiante["nombre"] = construir_nombre(estudiante)
        return estudiante
    except Exception:
        return None


def validar_docente(documento):
    docente = obtener_docente_activo(documento)
    return str(docente.get("nombre") or "").strip() if docente else None


def obtener_docente_activo(documento):
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT documento, nombre, cargo, jornada, sede FROM docentes WHERE documento = ? AND estado = 'Activo'",
                (str(documento),),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {
            "documento": str(row[0] or "").strip(),
            "nombre": str(row[1] or "").strip(),
            "cargo": str(row[2] or "").strip(),
            "jornada": str(row[3] or "").strip(),
            "sede": str(row[4] or "").strip(),
        }
    except Exception:
        return None


def cargar_grados():
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT DISTINCT grado FROM estudiantes WHERE estado = 'Activo'"
            )
            rows = cur.fetchall()
        return sorted([normalizar_grado(r[0]) for r in rows if r and r[0]])
    except Exception:
        return []


def cargar_cursos_disponibles(grado):
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT DISTINCT curso
                FROM estudiantes
                WHERE grado = ?
                ORDER BY curso
                """,
                (grado,),
            )
            rows = cur.fetchall()
        return [
            r[0]
            for r in rows
            if r and r[0] and str(r[0]).strip().lower() not in {"none", "nan", ""}
        ]
    except Exception:
        return []


def listar_estudiantes(grado=None, curso=None, limit=100, offset=0):
    limit = max(1, min(500, int(limit)))
    offset = max(0, int(offset))

    with get_connection() as conn:
        filters = ["estado = 'Activo'"]
        params = []
        if grado:
            filters.append("grado = ?")
            params.append(grado)
        if curso:
            filters.append("curso = ?")
            params.append(curso)
        where = "WHERE " + " AND ".join(filters)

        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM estudiantes {where}", params)
        total = int(cur.fetchone()[0])
        cur.execute(
            f"SELECT documento, apellido1, apellido2, nombre1, nombre2, grado, curso, jornada FROM estudiantes {where} ORDER BY apellido1, apellido2, nombre1, nombre2 LIMIT ? OFFSET ?",
            params + [limit, offset],
        )
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    for row in rows:
        row["nombre"] = construir_nombre(row)

    return {"total": total, "estudiantes": rows}


"CUSTOM_NEW_ROLE_FOR_TESTING"
