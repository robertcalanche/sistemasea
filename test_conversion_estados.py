#!/usr/bin/env python3
"""
Prueba de conversión de códigos de estado, género, jornada y tipo de documento.
Verifica que 'MA' → 'Matriculado', 'M' → 'Mañana', etc.
"""

import tkinter as tk
from pathlib import Path
import os
import sys
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from modulo_superadmin import ModuloSuperAdmin


def test_conversion_codigos():
    """Verifica que los códigos se conviertan automáticamente al cargar."""
    root = tk.Tk()
    root.withdraw()

    db_path = str(BASE_DIR / "sistema_test_conversion.db")

    print("\n" + "=" * 70)
    print("PRUEBA: Conversión de Códigos (Estado, Género, Jornada, TipoDoc)")
    print("=" * 70 + "\n")

    msa = ModuloSuperAdmin(root, db_path=db_path, base_dir=str(BASE_DIR))

    # Crear datos de prueba con códigos abreviados
    print("1. Creando datos con códigos abreviados...")
    estudiantes = [
        {
            "sede": "Principal",
            "jornada": "M",  # Código para 'Mañana'
            "grado": "0",
            "curso": "T0",
            "nombre": "Transición",
            "tipodoc": "CC",  # Código para 'Cédula de ciudadanía'
            "documento": "0000",
            "fechana": "2021-11-28",
            "telefono": "",
            "celular": "",
            "email": "",
            "genero": "M",  # Código para 'Masculino'
            "tipo_sangre": "O+",
            "estado": "MA",  # Código para 'Matriculado'
        },
        {
            "sede": "Principal",
            "jornada": "T",  # 'Tarde'
            "grado": "5",
            "curso": "01",
            "nombre": "Estudiante Activo",
            "tipodoc": "TI",  # 'Tarjeta de identidad'
            "documento": "1001",
            "fechana": "2015-01-15",
            "telefono": "",
            "celular": "",
            "email": "",
            "genero": "F",  # 'Femenino'
            "tipo_sangre": "A+",
            "estado": "MA",  # 'Matriculado'
        },
        {
            "sede": "Principal",
            "jornada": "N",  # 'Nocturna'
            "grado": "10",
            "curso": "A",
            "nombre": "Egresado",
            "tipodoc": "RC",  # 'Registro civil de nacimiento'
            "documento": "2001",
            "fechana": "2005-05-20",
            "telefono": "",
            "celular": "",
            "email": "",
            "genero": "M",
            "tipo_sangre": "B+",
            "estado": "GR",  # 'Graduado'
        },
        {
            "sede": "Principal",
            "jornada": "M",
            "grado": "6",
            "curso": "02",
            "nombre": "Retirado",
            "tipodoc": "CC",
            "documento": "3001",
            "fechana": "2010-03-10",
            "telefono": "",
            "celular": "",
            "email": "",
            "genero": "M",
            "tipo_sangre": "O-",
            "estado": "RE",  # 'Retirado'
        },
    ]

    df_e = pd.DataFrame(estudiantes)
    try:
        df_e.to_excel(BASE_DIR / "estudiantes.xlsx", index=False)
        print("   ✓ Archivo Excel creado con códigos abreviados")
    except Exception as e:
        print(f"   ✗ Error al guardar: {e}")
        return

    # Cargar estudiantes
    print("\n2. Cargando estudiantes en el módulo...")
    msa._load_estudiantes()
    print("   ✓ Estudiantes cargados")

    # Verificar conversiones en la tabla
    print("\n3. Verificando conversiones en la tabla...")
    filas = [msa.tree_est.item(i)["values"] for i in msa.tree_est.get_children()]

    esperado = [
        {
            "nombre": "Transición",
            "jornada": "Mañana",
            "genero": "Masculino",
            "estado": "Matriculado",
            "tipodoc": "Cédula de ciudadanía",
        },
        {
            "nombre": "Estudiante Activo",
            "jornada": "Tarde",
            "genero": "Femenino",
            "estado": "Matriculado",
            "tipodoc": "Tarjeta de identidad",
        },
        {
            "nombre": "Egresado",
            "jornada": "Nocturna",
            "genero": "Masculino",
            "estado": "Graduado",
            "tipodoc": "Registro civil de nacimiento",
        },
        {
            "nombre": "Retirado",
            "jornada": "Mañana",
            "genero": "Masculino",
            "estado": "Retirado",
            "tipodoc": "Cédula de ciudadanía",
        },
    ]

    # índices: jornada=0, grado=1, curso=2, nombre=3, tipodoc=4, documento=5, ...
    for idx, (fila, exp) in enumerate(zip(filas, esperado)):
        assert (
            fila[0] == exp["jornada"]
        ), f"Fila {idx}: Jornada esperada '{exp['jornada']}', obtuve '{fila[0]}'"
        assert (
            fila[3] == exp["nombre"]
        ), f"Fila {idx}: Nombre esperado '{exp['nombre']}', obtuve '{fila[3]}'"
        assert (
            fila[4] == exp["tipodoc"]
        ), f"Fila {idx}: Tipo doc esperado '{exp['tipodoc']}', obtuve '{fila[4]}'"
        assert (
            fila[10] == exp["genero"]
        ), f"Fila {idx}: Género esperado '{exp['genero']}', obtuve '{fila[10]}'"
        assert (
            fila[12] == exp["estado"]
        ), f"Fila {idx}: Estado esperado '{exp['estado']}', obtuve '{fila[12]}'"
        print(f"   ✓ Fila {idx}: Conversiones correctas")

    # Verificar conversiones en el diálogo de edición
    print("\n4. Verificando conversiones en diálogo de edición...")
    sel = msa.tree_est.get_children()[0]
    vals = msa.tree_est.item(sel)["values"]
    actuales = {
        "jornada": vals[0],
        "grado": vals[1],
        "curso": vals[2],
        "nombre": vals[3],
        "tipodoc": vals[4],
        "documento": vals[5],
        "fechana": vals[6],
        "telefono": vals[7],
        "celular": vals[8],
        "email": vals[9],
        "genero": vals[10],
        "tipo_sangre": vals[11],
        "estado": vals[12],
    }

    # Simulación de apertura del diálogo (sin GUI)
    assert (
        actuales["estado"] == "Matriculado"
    ), f"Estado debe ser 'Matriculado', no '{actuales['estado']}'"
    assert (
        actuales["jornada"] == "Mañana"
    ), f"Jornada debe ser 'Mañana', no '{actuales['jornada']}'"
    assert (
        actuales["genero"] == "Masculino"
    ), f"Género debe ser 'Masculino', no '{actuales['genero']}'"
    assert (
        actuales["tipodoc"] == "Cédula de ciudadanía"
    ), f"Tipo doc debe ser 'Cédula de ciudadanía', no '{actuales['tipodoc']}'"
    print("   ✓ Conversiones correctas en valores seleccionados")

    print("\n✓ TODAS LAS PRUEBAS PASARON")
    print("  - 'MA' → 'Matriculado' ✓")
    print("  - 'GR' → 'Graduado' ✓")
    print("  - 'RE' → 'Retirado' ✓")
    print("  - 'M' (jornada) → 'Mañana' ✓")
    print("  - 'T' (jornada) → 'Tarde' ✓")
    print("  - 'N' (jornada) → 'Nocturna' ✓")
    print("  - 'M' (género) → 'Masculino' ✓")
    print("  - 'F' (género) → 'Femenino' ✓")
    print("  - Tipos de documento convertidos ✓\n")

    root.destroy()


if __name__ == "__main__":
    test_conversion_codigos()
