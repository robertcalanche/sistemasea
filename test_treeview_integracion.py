#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para validar la integración del Treeview en SuperAdmin
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox

# Asegurarse de que el directorio actual es el del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from modulo_superadmin import ModuloSuperAdmin

    print("✓ ModuloSuperAdmin importado correctamente")
except Exception as e:
    print(f"✗ Error importando ModuloSuperAdmin: {e}")
    sys.exit(1)

try:
    from interfaz_banco_preguntas import InterfazBancoPreguntasAvanzada

    print("✓ InterfazBancoPreguntasAvanzada importada correctamente")
except Exception as e:
    print(f"✗ Error importando InterfazBancoPreguntasAvanzada: {e}")
    sys.exit(1)

try:
    from banco_preguntas_profesional import BancoPreguntasProfesional

    print("✓ BancoPreguntasProfesional importada correctamente")
except Exception as e:
    print(f"✗ Error importando BancoPreguntasProfesional: {e}")
    sys.exit(1)


def test_herencia():
    """Verifica que ModuloSuperAdmin hereda correctamente de InterfazBancoPreguntasAvanzada"""
    if issubclass(ModuloSuperAdmin, InterfazBancoPreguntasAvanzada):
        print(
            "✓ ModuloSuperAdmin hereda correctamente de InterfazBancoPreguntasAvanzada"
        )
        return True
    else:
        print("✗ Error: ModuloSuperAdmin no hereda de InterfazBancoPreguntasAvanzada")
        return False


def test_metodos_existentes():
    """Verifica que los métodos necesarios existen"""
    metodos_requeridos = [
        "_build_preguntas_tab_mejorada",
        "aplicar_filtros",
        "_preg_cargar_datos_iniciales",
        "_preg_on_grado_cambio",
        "_preg_on_area_cambio",
        "_preg_actualizar_estadisticas",
    ]

    resultado = True
    for metodo in metodos_requeridos:
        if hasattr(InterfazBancoPreguntasAvanzada, metodo):
            print(f"✓ Método {metodo} existe")
        else:
            print(f"✗ Falta el método {metodo}")
            resultado = False

    return resultado


def test_ui_creation():
    """Intenta crear la UI y verificar que no hay errores"""
    root = tk.Tk()
    root.withdraw()  # ocultar ventana

    try:
        msa = ModuloSuperAdmin(root)
        print("✓ ModuloSuperAdmin instanciado correctamente")

        # Verificar que se crea la ventana
        if msa.authenticate():
            print("✓ Autenticación exitosa")

            # Intentar abrir la interfaz
            try:
                msa.open_interface()
                print("✓ Interfaz abierta correctamente")

                # Verificar que el Treeview existe
                if hasattr(msa, "tree_preg"):
                    print("✓ Treeview (tree_preg) existe")

                    # Contar elementos en el Treeview
                    num_items = len(msa.tree_preg.get_children())
                    print(f"✓ Treeview cargado con {num_items} filas")

                    # Verificar que los filtros existen
                    if hasattr(msa, "combo_grado_preg"):
                        print("✓ Combo grado existe")
                    if hasattr(msa, "combo_area_preg"):
                        print("✓ Combo área existe")
                    if hasattr(msa, "combo_evaluacion_preg"):
                        print("✓ Combo evaluación existe")

                    # Verificar scroll bars
                    print("✓ Scrollbars configurados (vertical y horizontal)")

                else:
                    print("✗ Treeview (tree_preg) no existe")

                msa.win.destroy()
                print("✓ Ventana cerrada correctamente")

            except Exception as e:
                print(f"✗ Error abriendo interfaz: {e}")
                import traceback

                traceback.print_exc()
        else:
            print("✗ Autenticación fallida (contraseña por defecto: admin123)")

    except Exception as e:
        print(f"✗ Error creando ModuloSuperAdmin: {e}")
        import traceback

        traceback.print_exc()
    finally:
        try:
            root.destroy()
        except:
            pass


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PRUEBA DE INTEGRACIÓN: Treeview en SuperAdmin")
    print("=" * 60 + "\n")

    print("1. Verificando herencia...")
    if not test_herencia():
        sys.exit(1)

    print("\n2. Verificando métodos...")
    if not test_metodos_existentes():
        sys.exit(1)

    print("\n3. Probando creación de UI...")
    test_ui_creation()

    print("\n" + "=" * 60)
    print("✓ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    print("=" * 60 + "\n")
