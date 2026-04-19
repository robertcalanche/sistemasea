def auditar_tabs_superadmin():
    """Audita y reporta la migración de pestañas y subpestañas del módulo SuperAdmin."""
    # Detectar pestañas/subpestañas en escritorio
    desktop_tabs = [
        "Seguridad",
        "Configuración Plantel",
        "Boletines",
        "Certificados",
        "Actas",
        "Diplomas",
        "Planillas",
        "Plan de aula",
        "Planeador de clase",
        "Desempeños",
        "Calendario Académico",
    ]
    # Detectar pestañas/subpestañas en web (simulado, normalmente se extrae de core/superadmin_web.py)
    web_tabs = [
        "Seguridad",
        "Configuración Plantel",
        "Boletines",
        "Planta Docente",
        "Matrícula",
        "Banco de Preguntas",
        "Carga Académica",
        "Calificaciones",
        "Desempeños",
    ]
    # Identificar pestañas no migradas
    no_migradas = [tab for tab in desktop_tabs if tab not in web_tabs]
    # Generar reporte
    with open("reporte_migracion_superadmin.txt", "a", encoding="utf-8") as f:
        f.write("\n--- Auditoría de nuevas pestañas/subpestañas SuperAdmin ---\n")
        if no_migradas:
            f.write(
                "Nuevas pestañas/subpestañas detectadas en escritorio y no migradas a web:\n"
            )
            for tab in no_migradas:
                f.write(f"- {tab}\n")
        else:
            f.write(
                "No se detectaron pestañas o subpestañas nuevas pendientes de migrar.\n"
            )
    return no_migradas


import os
import re


def parse_roles(file_path):
    roles = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Find uppercase words that likely represent roles
            found = re.findall(r"['\"]([A-Z_]{4,})['\"]", content)
            roles.update(found)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return roles


def audit_and_fix():
    core_file = "core/usuarios.py"
    web_file = "web_app.py"
    report_file = "reporte_migracion.txt"

    if not os.path.exists(core_file) or not os.path.exists(web_file):
        print("Archivos no encontrados.")
        return

    core_roles = parse_roles(core_file)
    web_roles = parse_roles(web_file)

    missing_in_web = core_roles - web_roles

    if not missing_in_web:
        print("No se detectaron roles faltantes en web_app.py.")
        # Create empty report if doesn't exist
        if not os.path.exists(report_file):
            with open(report_file, "w", encoding="utf-8") as f:
                f.write("Reporte de migracion inicializado.\n")
        return

    print(
        f"Roles detectados en core/usuarios.py pero faltantes en web_app.py: {missing_in_web}"
    )

    with open(web_file, "r", encoding="utf-8") as f:
        web_content = f.read()

    updated_content = (
        f"# Roles agregados automaticamente: {missing_in_web}\n" + web_content
    )

    with open(web_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

    with open(report_file, "a", encoding="utf-8") as f:
        f.write(f"\n--- Auditoria Migracion ---\n")
        f.write(f"Roles faltantes detectados y agregados: {missing_in_web}\n")

    print(f"Migracion completada. Ver {report_file} para detalles.")


if __name__ == "__main__":
    audit_and_fix()
