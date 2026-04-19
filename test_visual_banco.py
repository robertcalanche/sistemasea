#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba visual de carga del Banco de Preguntas
Abre la interfaz y cierra automáticamente después de 5 segundos
"""

import os
import sys
import threading
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import tkinter as tk
from modulo_superadmin import ModuloSuperAdmin

print("=" * 70)
print("PRUEBA VISUAL DEL BANCO DE PREGUNTAS")
print("=" * 70)
print("\n✓ Abriendo interfaz SuperAdmin...")
print("✓ La ventana se cerrará automáticamente en 5 segundos")
print("✓ Verifica que la tabla tenga preguntas cargadas\n")

# Crear ventana principal
root = tk.Tk()
root.withdraw()

# Crear ModuloSuperAdmin
DB_FILE = BASE_DIR / "sistema.db"
msa = ModuloSuperAdmin(root, db_path=str(DB_FILE), base_dir=str(BASE_DIR))

# Autenticarse
if not msa.authenticate():
    print("✗ Autenticación cancelada")
    root.destroy()
    sys.exit(1)

print("✓ Autenticación completada")

# Abrir interfaz
msa.open_interface()

# Maximizar ventana
try:
    msa.win.state("zoomed")
except:
    try:
        msa.win.attributes("-fullscreen", True)
    except:
        pass

print("✓ Interfaz abierta")
print("✓ Verifica la pestaña 'Banco Preguntas' - debería mostrar 48 preguntas")


# Función para cerrar la ventana después de 5 segundos
def cerrar_automatico():
    time.sleep(5)
    print("\n✓ Cerrando ventana automáticamente...")
    try:
        msa.win.destroy()
    except:
        pass
    try:
        root.destroy()
    except:
        pass


# Iniciar thread para cierre automático
thread = threading.Thread(target=cerrar_automatico, daemon=True)
thread.start()

# Iniciar loop de la ventana
try:
    msa.win.mainloop()
except:
    pass

print("=" * 70)
print("✓ Prueba completada")
print("=" * 70)
