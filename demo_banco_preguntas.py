#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba visual de la interfaz del Banco de Preguntas en SuperAdmin
"""

import sys
from pathlib import Path
import tkinter as tk

# Agregar ruta del proyecto
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from modulo_superadmin import ModuloSuperAdmin

print("=" * 60)
print("INICIANDO DEMOSTRACIÓN DEL BANCO DE PREGUNTAS")
print("=" * 60)
print("\n✓ Abriendo módulo SuperAdmin...")
print("✓ Accede a la pestaña 'Banco de Preguntas'")
print("\n📋 EN LA INTERFAZ PUEDES:")
print("   • Ver el listado de todas las preguntas")
print("   • Filtrar por Grado, Área y Evaluación")
print("   • Doble clic en una pregunta para EDITAR")
print("   • Clic derecho para MENÚ CONTEXTUAL (Edit/Delete)")
print("   • Usar el botón ✏️ EDITAR para editar seleccionados")
print("   • Usar el botón 🗑️ ELIMINAR para eliminar seleccionados")
print("   • Usar el botón ➕ AGREGAR para nuevas preguntas")
print("\n" + "=" * 60 + "\n")

# Crear ventana principal
root = tk.Tk()
root.withdraw()  # Ocultar ventana principal mientras se carga
root.title("SuperAdmin - Banco de Preguntas")

# Crear instancia de ModuloSuperAdmin
DB_FILE = BASE_DIR / "resultados.db"

try:
    msa = ModuloSuperAdmin(root, db_path=str(DB_FILE), base_dir=str(BASE_DIR))

    # Si se requiere autenticación, hacer login
    if msa.authenticate():
        msa.open_interface()
        try:
            msa.win.state("zoomed")
        except:
            try:
                msa.win.attributes("-fullscreen", True)
            except:
                pass
        msa.win.mainloop()
    else:
        print("✗ Autenticación cancelada o incorrecta")
        root.destroy()
except Exception as e:
    print(f"✗ Error al cargar el módulo: {e}")
    import traceback

    traceback.print_exc()
    root.destroy()
