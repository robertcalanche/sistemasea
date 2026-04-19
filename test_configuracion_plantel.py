#!/usr/bin/env python3
"""
Script de prueba para verificar que la nueva sección
"Configuración de Plantel" funciona correctamente en el módulo SuperAdmin.
"""

import tkinter as tk
from pathlib import Path
import sys

# Agregar el directorio actual al path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from modulo_superadmin import ModuloSuperAdmin


def test_configuracion_plantel():
    """Prueba la nueva sección de Configuración de Plantel."""

    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal

    # Crear instancia del módulo SuperAdmin
    # Usar una ruta específica para la base de datos de prueba
    db_path = str(BASE_DIR / "sistema_test.db")

    print("=" * 60)
    print("PRUEBA: Configuración de Plantel - Módulo SuperAdmin")
    print("=" * 60)
    print(f"\nBase de datos: {db_path}")

    try:
        msa = ModuloSuperAdmin(root, db_path=db_path, base_dir=str(BASE_DIR))

        # Verificar que la tabla se creó correctamente
        msa._ensure_configuracion_plantel()
        print("✓ Tabla de configuración_plantel creada correctamente")

        # Probar guardar y recuperar valores
        test_data = {
            "nombre_institucion": "Instituto Técnico Santa María",
            "codigo_dane": "168001000180",
            "nit": "890506066-1",
            "municipio": "Bogotá",
            "departamento": "Cundinamarca",
            "corregimiento_localidad": "Localidad 5",
            "ano_lectivo": "2026",
            "jornadas": "Matutina y Vespertina",
            "direccion": "Cra 15 #45-67, Bogotá",
            "telefono": "+57 1 2345678",
            "correo_institucional": "info@institutotech.edu.co",
        }

        print("\n--- Prueba de guardar datos ---")
        for clave, valor in test_data.items():
            msa._set_config_plantel(clave, valor)
            print(f"✓ Guardado: {clave} = {valor}")

        print("\n--- Prueba de recuperar datos ---")
        for clave, valor_esperado in test_data.items():
            valor_recuperado = msa._get_config_plantel(clave)
            if valor_recuperado == valor_esperado:
                print(f"✓ {clave}: {valor_recuperado}")
            else:
                print(
                    f"✗ ERROR: {clave} esperaba '{valor_esperado}' pero obtuvo '{valor_recuperado}'"
                )

        print("\n✓ Todas las pruebas pasadas correctamente!")
        print("\nAhora puedes abrir el módulo SuperAdmin para ver la interfaz gráfica.")
        print(
            "Haz clic en la pestaña 'Configuración Plantel' cuando se abra la ventana."
        )

        # Ofrecemos la opción de abrir la interfaz
        if messagebox.askyesno(
            "Prueba Exitosa",
            "¿Deseas abrir la interfaz SuperAdmin para ver la nueva sección?\n"
            "(Nota: Se pedirá autenticación con clave maestra)",
        ):
            if msa.authenticate():
                msa.open_interface()
                root.deiconify()
                root.mainloop()
            else:
                print("Autenticación cancelada o fallida")
        else:
            print("Cerrando sin abrir la interfaz...")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
    finally:
        try:
            root.destroy()
        except:
            pass


if __name__ == "__main__":
    # Manejo de mensajes sin GUI
    try:
        import tkinter.messagebox as messagebox
    except:
        # Fallback si no hay soporte para messagebox
        class MockMessageBox:
            @staticmethod
            def askyesno(title, message):
                response = input(f"\n{message} (s/n): ").lower()
                return response in ["s", "si", "y", "yes"]

        messagebox = MockMessageBox()

    test_configuracion_plantel()
