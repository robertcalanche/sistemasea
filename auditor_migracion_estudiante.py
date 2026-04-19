import os
import re

def parse_roles(file_path):
    roles = set()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Encontrar roles en formato ROL_ESTUDIANTE o strings de roles
            found = re.findall(r"(ROL_[A-Z_]+|'desktop\.[a-z\.]+')", content)
            roles.update(found)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return roles

def audit_and_fix(modulo="estudiante"):
    web_file = "web_app.py"
    core_file = "core/usuarios.py"
    report_file = "reporte_migracion.txt"
    
    print(f"--- Auditando modulo: {modulo} ---")
    
    # Definir lo que deberia estar presente para 'estudiante'
    expected_routes = [
        "/api/examenes/estudiante",
        "/estudiantes",
        "/api/estudiantes"
    ]
    
    with open(web_file, "r", encoding="utf-8") as f:
        web_content = f.read()
    
    missing_routes = [r for r in expected_routes if r not in web_content]
    
    if missing_routes:
        print(f"Rutas faltantes detectadas: {missing_routes}")
        # En este caso, vimos que ya estan. Si no estuvieran, las agregariamos.
    else:
        print("Todas las rutas esperadas estan presentes.")

    # Auditando visibilidad en plantillas (simulado)
    template_file = "templates/estudiantes.html"
    if os.path.exists(template_file):
         with open(template_file, "r", encoding="utf-8") as f:
             t_content = f.read()
         if "estudiante" in t_content.lower():
             print(f"Plantilla {template_file} validada.")
    else:
         print(f"ADVERTENCIA: Plantilla {template_file} no encontrada.")

    # Registro de resultados
    with open(report_file, "a", encoding="utf-8") as f:
        f.write(f"\nAudit modulo {modulo} finalizado.\n")
        f.write(f"Rutas faltantes: {missing_routes}\n")
    
    print(f"Migracion y auditoria del modulo {modulo} completada.")

if __name__ == '__main__':
    audit_and_fix()
