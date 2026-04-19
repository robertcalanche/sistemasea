#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para recrear BD con preguntas desde Excel."""

import sys
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).parent))

from Admin import crear_base_datos, importar_preguntas_desde_excel, DB_FILE

print("=" * 60)
print("RECREANDO BD E IMPORTANDO PREGUNTAS")
print("=" * 60)

# Eliminar BD anterior
DB_FILE = Path(DB_FILE)
DB_FILE.unlink(missing_ok=True)
print("✓ BD eliminada")

# Recrear BD
print("\n1. Creando tablas...")
crear_base_datos()

print("\n2. Importando preguntas desde Excel (explícito)...")
importar_preguntas_desde_excel()

# Verificar preguntas importadas
print("\n3. Verificando preguntas en la BD...")
try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM banco_preguntas")
    count = cursor.fetchone()[0]

    print(f"   Total de preguntas: {count}")

    if count > 0:
        print("\n4. Primeros 3 preguntas:")
        cursor.execute("SELECT id, area, grado, enunciado FROM banco_preguntas LIMIT 3")
        for row in cursor.fetchall():
            print(f"   ID={row[0]} | Area={row[1]} | Grado={row[2]}")
            print(f"      Enunciado: {row[3][:40]}...")

    conn.close()
    print("\n✓ IMPORTACION COMPLETADA EXITOSAMENTE")

except Exception as e:
    print(f"   Error: {e}")

print("=" * 60)
