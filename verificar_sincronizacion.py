#!/usr/bin/env python3
"""
Script de verificación de sincronización entre Admin.py y App.py
Verifica que todas las funciones necesarias estén disponibles en ambos módulos
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("=" * 70)
print("VERIFICACIÓN DE SINCRONIZACIÓN ADMIN.PY ↔ APP.PY")
print("=" * 70)

# Lista de funciones que deben estar en Admin.py
FUNCIONES_ADMIN_REQUERIDAS = [
    # Base de datos
    "crear_base_datos",
    "crear_tabla_config",
    # Registro y consulta
    "registrar_inicio",
    "registrar_final",
    "ya_presento",
    # Consultas de estado
    "obtener_estado_area",
    "obtener_intento_area",
    "obtener_respuestas_estudiante",
    "obtener_todas_respuestas_desde_bd",  # NUEVA FUNCIÓN
    # Control de revisión
    "autorizar_revision",
    "puede_revisar",
    # Reseteo
    "resetear_examen",
    # Validaciones
    "validar_estudiante",
    "validar_docente",
    "normalizar_grado",
    # Carga de datos
    "cargar_preguntas",
    "cargar_areas",
    "cargar_areas_por_grado",
    "cargar_grados",  # NUEVA FUNCIÓN
    "cargar_evaluaciones_por_grado_y_area",
    "cargar_preguntas_filtradas",
    # Configuración de examen
    "cargar_config_examen",
    "guardar_config_examen",
    "examen_esta_activo",
    # Exportaciones
    "exportar_reporte_por_filtros",
    "exportar_consolidado_periodo",
    "exportar_reporte_completo",
    # Clases
    "ModuloDocente",
    "VistaHistorialExamenes",
    "ModuloEstudiante",
    # Funciones auxiliares
    "abrir_docente",
]

# Funciones que App.py DEBE importar de Admin
FUNCIONES_A_IMPORTAR_EN_APP = [
    "crear_base_datos",
    "crear_tabla_config",
    "registrar_inicio",
    "registrar_final",
    "ya_presento",
    "obtener_todas_respuestas_desde_bd",  # NUEVA
    "obtener_estado_area",
    "obtener_intento_area",
    "autorizar_revision",
    "puede_revisar",
    "obtener_respuestas_estudiante",
    "resetear_examen",
    "validar_estudiante",
    "validar_docente",
    "normalizar_grado",  # IMPORTANTE: Debe estar importado
    "cargar_areas",
    "cargar_areas_por_grado",
    "cargar_grados",  # NUEVA
    "cargar_evaluaciones_por_grado_y_area",
    "cargar_preguntas",
    "cargar_preguntas_filtradas",
    "cargar_config_examen",
    "guardar_config_examen",
    "examen_esta_activo",  # IMPORTANTE: Debe estar importado
    "exportar_reporte_por_filtros",
    "exportar_consolidado_periodo",
    "exportar_reporte_completo",
    "ModuloDocente",
    "abrir_docente",
    "VistaHistorialExamenes",
]

# Verificar Admin.py
print("\n✅ VERIFICACIÓN DE ADMIN.PY")
print("-" * 70)
try:
    import Admin

    admin_functions = set(dir(Admin))

    missing_admin = []
    for func in FUNCIONES_ADMIN_REQUERIDAS:
        if func not in admin_functions:
            missing_admin.append(func)

    if missing_admin:
        print(f"❌ Funciones FALTANTES en Admin.py: {missing_admin}")
        print(f"   Total faltantes: {len(missing_admin)}")
    else:
        print(
            f"✅ TODAS las funciones requeridas están en Admin.py ({len(FUNCIONES_ADMIN_REQUERIDAS)} funciones)"
        )

        # Verificar las nuevas funciones específicamente
        print(
            f"\n   ✓ obtener_todas_respuestas_desde_bd: {'SÍ' if 'obtener_todas_respuestas_desde_bd' in admin_functions else 'NO'}"
        )
        print(
            f"   ✓ cargar_grados: {'SÍ' if 'cargar_grados' in admin_functions else 'NO'}"
        )

except ImportError as e:
    print(f"❌ ERROR: No se pudo importar Admin.py: {e}")
    sys.exit(1)

# Verificar App.py
print("\n✅ VERIFICACIÓN DE APP.PY")
print("-" * 70)
try:
    import app

    app_functions = set(dir(app))

    missing_app = []
    for func in FUNCIONES_A_IMPORTAR_EN_APP:
        if func not in app_functions:
            missing_app.append(func)

    if missing_app:
        print(f"❌ Funciones FALTANTES en App.py: {missing_app}")
        print(f"   Total faltantes: {len(missing_app)}")
    else:
        print(
            f"✅ TODAS las funciones requeridas están en App.py ({len(FUNCIONES_A_IMPORTAR_EN_APP)} funciones)"
        )

        # Verificar funciones específicas
        print(
            f"\n   ✓ normalizar_grado: {'SÍ' if 'normalizar_grado' in app_functions else 'NO'}"
        )
        print(
            f"   ✓ examen_esta_activo: {'SÍ' if 'examen_esta_activo' in app_functions else 'NO'}"
        )
        print(
            f"   ✓ obtener_todas_respuestas_desde_bd: {'SÍ' if 'obtener_todas_respuestas_desde_bd' in app_functions else 'NO'}"
        )
        print(
            f"   ✓ cargar_grados: {'SÍ' if 'cargar_grados' in app_functions else 'NO'}"
        )

except ImportError as e:
    print(f"❌ ERROR: No se pudo importar App.py: {e}")
    sys.exit(1)

# Verificar que ModuloEstudiante en App.py no es la de Admin
print("\n✅ VERIFICACIÓN DE MODULOESTUDIANTE")
print("-" * 70)

admin_estudiante = Admin.ModuloEstudiante
app_estudiante = app.ModuloEstudiante

if admin_estudiante is app_estudiante:
    print(
        "⚠️  ADVERTENCIA: ModuloEstudiante está siendo importado de Admin (sobrescrito)"
    )
    print("   Esto PERDERÍA las características mejoradas de reanudación de examen.")
else:
    print("✅ ModuloEstudiante en App.py es DIFERENTE a Admin.py (Correcto)")
    print("   - App.py mantiene su versión mejorada con reanudación de examen")
    print("   - Admin.py proporciona versión base")

# Resumen final
print("\n" + "=" * 70)
print("RESUMEN FINAL")
print("=" * 70)

all_ok = (
    len(missing_admin) == 0
    and len(missing_app) == 0
    and admin_estudiante is not app_estudiante
)

if all_ok:
    print("✅ ¡SINCRONIZACIÓN EXITOSA!")
    print("\nEstatus:")
    print(
        f"  • Admin.py: {len([f for f in FUNCIONES_ADMIN_REQUERIDAS if f in admin_functions])}/{len(FUNCIONES_ADMIN_REQUERIDAS)} funciones ✅"
    )
    print(
        f"  • App.py: {len([f for f in FUNCIONES_A_IMPORTAR_EN_APP if f in app_functions])}/{len(FUNCIONES_A_IMPORTAR_EN_APP)} funciones ✅"
    )
    print(f"  • ModuloEstudiante: Versión mejorada en App.py ✅")
    print(f"\n✨ LISTO PARA EJECUTAR\n")
else:
    print("❌ ¡HAY PROBLEMAS DE SINCRONIZACIÓN!")
    if missing_admin:
        print(f"\n  • Faltan {len(missing_admin)} funciones en Admin.py")
    if missing_app:
        print(f"  • Faltan {len(missing_app)} funciones en App.py")
    if admin_estudiante is app_estudiante:
        print(f"  • ModuloEstudiante está siendo sobrescrito per Admin.py")
    sys.exit(1)

print("=" * 70)
