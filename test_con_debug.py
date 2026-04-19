#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test visual con debug - Abre la interfaz y muestra debug info
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import tkinter as tk
from modulo_superadmin import ModuloSuperAdmin

root = tk.Tk()
root.withdraw()

# Crear módulo
DB_FILE = BASE_DIR / "sistema.db"
msa = ModuloSuperAdmin(root, db_path=str(DB_FILE), base_dir=str(BASE_DIR))

# Autenticar
if not msa.authenticate():
    root.destroy()
    sys.exit(1)

# Abrir interfaz
msa.open_interface()

# Después de abrir la interfaz, verificar el estado del banco
print("=" * 70)
print("INFORMACIÓN DESPUÉS DE ABRIR INTERFAZ")
print("=" * 70)
print(f"\n✓ Banco cargado: {msa.banco is not None}")
print(f"✓ Total preguntas: {len(msa.banco.df)}")
print(f"✓ tab_preguntas existe: {msa.tab_preguntas is not None}")

# Verificar si tree_preg existe
if hasattr(msa, "tree_preg"):
    print(f"✓ tree_preg existe")
    # Obtener children en el treeview
    items = msa.tree_preg.get_children()
    print(f"✓ Filas en tree_preg: {len(items)}")
    if len(items) > 0:
        first_item = items[0]
        values = msa.tree_preg.item(first_item)["values"]
        print(f"✓ Primera fila tiene {len(values)} columnas")
        if len(values) > 0:
            print(f"  ID: {values[0]}")
    else:
        print("✗ No hay filas en tree_preg!")
else:
    print("✗ tree_preg NO EXISTE")

# Mostrar ventana
try:
    msa.win.state("zoomed")
except:
    pass

print("\n✓ Interfaz abierta - verifica manualmente la pestaña 'Banco Preguntas'")
print("✓ Presiona Ctrl+C para cerrar\n")

try:
    msa.win.mainloop()
except KeyboardInterrupt:
    msa.win.destroy()
    root.destroy()
