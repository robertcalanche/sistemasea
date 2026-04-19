#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que el Banco de Preguntas funciona correctamente
"""

import os
import sys
from pathlib import Path

# Agregar la ruta del proyecto
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Probar importaciones
print("=" * 60)
print("PRUEBA DE CARGA DEL BANCO DE PREGUNTAS")
print("=" * 60)

try:
    from banco_preguntas_profesional import BancoPreguntasProfesional

    print("✓ BancoPreguntasProfesional importado correctamente")
except Exception as e:
    print(f"✗ Error importando BancoPreguntasProfesional: {e}")
    sys.exit(1)

try:
    from interfaz_banco_preguntas import InterfazBancoPreguntasAvanzada

    print("✓ InterfazBancoPreguntasAvanzada importada correctamente")
except Exception as e:
    print(f"✗ Error importando InterfazBancoPreguntasAvanzada: {e}")
    sys.exit(1)

# Verificar archivo de preguntas
preguntas_path = BASE_DIR / "preguntas.xlsx"
print(f"\n📁 Archivo de preguntas: {preguntas_path}")
print(f"   Existe: {preguntas_path.exists()}")

# Cargar banco
banco = BancoPreguntasProfesional(str(preguntas_path))
print(f"\n✓ Banco de preguntas cargado correctamente")

# Obtener estadísticas
stats = banco.obtener_estadisticas()
print(f"\n📊 ESTADÍSTICAS:")
print(f"   Total de preguntas: {stats['total_preguntas']}")
print(f"   Grados únicos: {stats['grados_unicos']}")
print(f"   Áreas únicas: {stats['areas_unicas']}")
print(f"   Evaluaciones únicas: {stats['evaluaciones_unicas']}")
print(f"   Preguntas con imagen: {stats['preguntas_con_imagen']}")

# Obtener grados disponibles
grados = banco.obtener_grados_disponibles()
print(f"\n📚 GRADOS DISPONIBLES: {grados if grados else 'Ninguno'}")

# Obtener áreas disponibles
areas = banco.obtener_areas_disponibles()
print(f"📚 ÁREAS DISPONIBLES: {areas if areas else 'Ninguna'}")

# Obtener evaluaciones disponibles
evaluaciones = banco.obtener_evaluaciones_disponibles()
print(f"📚 EVALUACIONES DISPONIBLES: {evaluaciones if evaluaciones else 'Ninguna'}")

# Si hay preguntas, mostrar una de ejemplo
if stats["total_preguntas"] > 0:
    print(f"\n✓ El banco contiene preguntas y debería mostrarse en la interfaz")
else:
    print(f"\n⚠️  El banco está VACÍO. No hay preguntas para mostrar.")
    print(f"   Necesitas agregar preguntas antes de poder editarlas o eliminarlas.")

print("\n" + "=" * 60)
print("FIN DE LA PRUEBA")
print("=" * 60)
