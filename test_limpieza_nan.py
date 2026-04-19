#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST - LIMPIEZA DE VALORES NaN
Módulo Estudiante - Sistema SEA

Valida que _limpiar_valor_pregunta() elimina "nan" y valores NULL
"""

import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "#" * 70)
print("# TEST - LIMPIEZA DE VALORES NaN")
print("# Sistema: Módulo Estudiante (SEA)")
print("#" * 70)

# Importar la función
from app import _limpiar_valor_pregunta

# Test cases
test_cases = [
    # (entrada, esperado, descripción)
    ("", "", "String vacío"),
    ("Texto normal", "Texto normal", "Texto válido"),
    ("$x^2$", "$x^2$", "LaTeX válido"),
    (None, "", "None"),
    ("None", "", "String 'None'"),
    ("nan", "", "String 'nan'"),
    ("NaN", "", "String 'NaN' (mayúscula)"),
    ("  nan  ", "", "String 'nan' con espacios"),
    ("<NA>", "", "String '<NA>'"),
    (float("nan"), "", "float NaN"),
    (0, "0", "Número cero"),
    (1, "1", "Número 1"),
    ("0", "0", "String '0'"),
    ("  Texto con espacios  ", "Texto con espacios", "Texto con espacios"),
]

print("\n" + "=" * 70)
print("TEST: LIMPIEZA DE VALORES")
print("=" * 70)

passed = 0
failed = 0

for entrada, esperado, desc in test_cases:
    resultado = _limpiar_valor_pregunta(entrada)

    if resultado == esperado:
        status = "PASS"
        passed += 1
    else:
        status = "FAIL"
        failed += 1

    entrada_repr = repr(entrada)[:40]
    print(f"  [{status}] {desc:30s} | Entrada: {entrada_repr}")

    if status == "FAIL":
        print(f"         Esperado: {repr(esperado)}")
        print(f"         Obtuvo:   {repr(resultado)}")

print(f"\n  Resultado: {passed}/{len(test_cases)} PASADAS")

if failed == 0:
    print("\n  [SUCCESS] Limpieza de NaN funciona correctamente")
    print("  No más 'nan' en la interfaz de estudiante")
    sys.exit(0)
else:
    print(f"\n  [WARNING] {failed} pruebas no pasaron")
    sys.exit(1)
