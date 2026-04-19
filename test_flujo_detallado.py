#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test detallado del flujo de carga de preguntas
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("=" * 70)
print("TEST DETALLADO DEL FLUJO DE CARGA")
print("=" * 70)

from banco_preguntas_profesional import BancoPreguntasProfesional

# Paso 1: Crear banco directamente
print("\n1. Creando BancoPreguntasProfesional...")
banco = BancoPreguntasProfesional(str(BASE_DIR / "preguntas.xlsx"))
print(f"   ✓ DataFrame cargado: {len(banco.df)} filas")

# Paso 2: Obtener TODOS sin filtros
print("\n2. Llamando a obtener_preguntas_filtradas(None, None, None)...")
df_todas = banco.obtener_preguntas_filtradas(grado=None, area=None, evaluacion=None)
print(f"   ✓ Resultado: {len(df_todas)} filas")

if len(df_todas) == 0:
    print("   ✗ ERROR: DataFrame está vacío!")
else:
    print(f"   ✓ Primera fila ID: {df_todas.iloc[0]['id']}")
    print(f"   ✓ Columnas: {list(df_todas.columns)}")

# Paso 3: Simular lo que hace aplicar_filtros
print("\n3. Simulando aplicar_filtros()...")


def _norm(val):
    if val is None:
        return None
    v = str(val).strip()
    if not v or v == "(Todos)":
        return None
    return v.lower()


grado_sel = "(Todos)"
area_sel = "(Todos)"
eval_sel = "(Todos)"

grado_val = _norm(grado_sel)
area_val = _norm(area_sel)
eval_val = _norm(eval_sel)

print(f"   Después de _norm:")
print(f"   - grado_val: {grado_val}")
print(f"   - area_val: {area_val}")
print(f"   - eval_val: {eval_val}")

df_filtrado = banco.obtener_preguntas_filtradas(
    grado=grado_val, area=area_val, evaluacion=eval_val
)

print(f"   ✓ Resultado después de filtro: {len(df_filtrado)} filas")

if len(df_filtrado) > 0:
    print(f"   ✓ OK - Las preguntas deberían mostrarse!")
else:
    print(f"   ✗ ERROR - DataFrame está vacío!")

# Paso 4: Normalizar como lo hace aplicar_filtros
print("\n4. Normalizando columnas del DataFrame...")

for col in ("grado", "area", "evaluacion"):
    if col in df_filtrado.columns:
        print(f"   - Normalizando {col}...")
        df_filtrado[col] = df_filtrado[col].astype(str).str.strip().str.lower()

print(f"   ✓ Normalización completada - {len(df_filtrado)} filas")

# Paso 5: Insertar en treeview (simulado)
print("\n5. Insertando en treeview (simulado)...")
contador = 0
for _, row in df_filtrado.iterrows():
    imagen_str = "✓" if row.get("imagen") and str(row.get("imagen")).strip() else ""
    contador += 1

print(f"   ✓ Se insertarían {contador} preguntas en la tabla")

print("\n" + "=" * 70)
if contador > 0:
    print(f"✓ TODO CORRECTO - {contador} preguntas listas para mostrar")
else:
    print("✗ ERROR - No hay preguntas para mostrar")
print("=" * 70)
