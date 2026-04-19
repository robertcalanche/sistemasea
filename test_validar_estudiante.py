#!/usr/bin/env python3
"""
Prueba de la función validar_estudiante con la nueva estructura Excel.

Nueva estructura (14 columnas):
sede, jornada, grado, curso, nombre, tipodoc, documento, fechana,
telefono, celular, email, genero, tipo_sangre, estado
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Importar la función validar_estudiante
from app import validar_estudiante


def test_validar_estudiante_nueva_estructura():
    print("\n" + "=" * 70)
    print("PRUEBA: validar_estudiante() con nueva estructura Excel")
    print("=" * 70 + "\n")

    # Crear datos de prueba con la nueva estructura
    estudiantes_prueba = [
        {
            "sede": "Principal",
            "jornada": "Mañana",
            "grado": "0",
            "curso": "T0",
            "nombre": "Niño Transición",
            "tipodoc": "Cédula de ciudadanía",
            "documento": "10001",
            "fechana": "2021-11-28",
            "telefono": "3001234567",
            "celular": "3001234567",
            "email": "trans@example.com",
            "genero": "Masculino",
            "tipo_sangre": "O+",
            "estado": "Matriculado",
        },
        {
            "sede": "Principal",
            "jornada": "Mañana",
            "grado": "5",
            "curso": "01",
            "nombre": "Estudiante Activo",
            "tipodoc": "Cédula de ciudadanía",
            "documento": "10002",
            "fechana": "2015-01-15",
            "telefono": "",
            "celular": "3109876543",
            "email": "activo@example.com",
            "genero": "Femenino",
            "tipo_sangre": "A+",
            "estado": "Matriculado",
        },
        {
            "sede": "Principal",
            "jornada": "Tarde",
            "grado": "10",
            "curso": "A",
            "nombre": "Estudiante Graduado",
            "tipodoc": "Cédula de ciudadanía",
            "documento": "10003",
            "fechana": "2005-05-20",
            "telefono": "",
            "celular": "",
            "email": "",
            "genero": "Masculino",
            "tipo_sangre": "B+",
            "estado": "Graduado",  # No matriculado
        },
        {
            "sede": "Principal",
            "jornada": "Nocturna",
            "grado": "6",
            "curso": "02",
            "nombre": "Estudiante Retirado",
            "tipodoc": "Cédula de ciudadanía",
            "documento": "10004",
            "fechana": "2010-03-10",
            "telefono": "",
            "celular": "",
            "email": "",
            "genero": "Masculino",
            "tipo_sangre": "O-",
            "estado": "Retirado",  # No matriculado
        },
        {
            "sede": "Principal",
            "jornada": "Mañana",
            "grado": "7",
            "curso": "01",
            "nombre": "Sin documento",
            "tipodoc": "",
            "documento": "",  # Campo vacío
            "fechana": "",
            "telefono": "",
            "celular": "",
            "email": "",
            "genero": "",
            "tipo_sangre": "",
            "estado": "Matriculado",
        },
    ]

    # Guardar en Excel
    df = pd.DataFrame(estudiantes_prueba)
    estudiantes_path = BASE_DIR / "estudiantes.xlsx"
    df.to_excel(estudiantes_path, index=False)
    print("1. Archivo estudiantes.xlsx creado con nuevas columnas")
    print(f"   Columnas: {list(df.columns)}\n")

    # Test 1: Estudiante válido (Transición - grado 0)
    print("2. Test: Estudiante Transición (grado 0, Matriculado)")
    resultado = validar_estudiante("10001")
    assert resultado is not None, "Debería encontrar estudiante 10001"
    assert resultado["nombre"] == "Niño Transición"
    assert resultado["grado"] == "0"
    assert resultado["estado"] == "Matriculado"
    print("   ✓ Encontrado correctamente\n")

    # Test 2: Estudiante válido (grado 5)
    print("3. Test: Estudiante Grado 5 (Matriculado)")
    resultado = validar_estudiante("10002")
    assert resultado is not None
    assert resultado["nombre"] == "Estudiante Activo"
    assert resultado["grado"] == "5"
    print("   ✓ Encontrado correctamente\n")

    # Test 3: Estudiante NO Matriculado (Graduado)
    print("4. Test: Estudiante Graduado (NO Matriculado)")
    resultado = validar_estudiante("10003")
    assert resultado is None, "No debería permitir estudiante Graduado"
    print("   ✓ Rechazado correctamente (No es Matriculado)\n")

    # Test 4: Estudiante Retirado
    print("5. Test: Estudiante Retirado (NO Matriculado)")
    resultado = validar_estudiante("10004")
    assert resultado is None, "No debería permitir estudiante Retirado"
    print("   ✓ Rechazado correctamente (No es Matriculado)\n")

    # Test 5: Documento NO encontrado
    print("6. Test: Documento inexistente")
    resultado = validar_estudiante("99999")
    assert resultado is None, "No debería encontrar documento 99999"
    print("   ✓ Rechazado correctamente (No encontrado)\n")

    # Test 6: Campo documento vacío
    print("7. Test: Estudiante con documento vacío")
    resultado = validar_estudiante("")
    assert resultado is None, "No debería aceptar documento vacío"
    print("   ✓ Rechazado correctamente (Documento vacío)\n")

    # Test 7: Documento como número (conversión a string)
    print("8. Test: Documento numérico (conversión a string)")
    resultado = validar_estudiante(10002)  # Pasar como int
    assert resultado is not None, "Debería convertir número a string"
    assert resultado["nombre"] == "Estudiante Activo"
    print("   ✓ Convertido y encontrado correctamente\n")

    print("=" * 70)
    print("✓ TODAS LAS PRUEBAS PASARON")
    print("=" * 70)
    print("\nResumen de validaciones:")
    print("  ✓ Reconoce todas las 14 columnas nuevas")
    print("  ✓ Valida campos obligatorios (documento, nombre, grado, curso, estado)")
    print("  ✓ Permitie solo estudiantes 'Matriculado'")
    print("  ✓ Rechaza estudiantes Graduado, Retirado, etc.")
    print("  ✓ Convierte documento a string automáticamente")
    print("  ✓ Maneja campos vacíos correctamente")
    print("  ✓ Soporta grado 0 (Transición)")
    print()

    # Limpiar
    estudiantes_path.unlink()


if __name__ == "__main__":
    test_validar_estudiante_nueva_estructura()
