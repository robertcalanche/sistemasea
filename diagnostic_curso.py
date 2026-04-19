#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de diagnóstico para verificar datos de curso en banco_preguntas"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "sistema.db"


def test_database():
    """Verifica los datos de curso en la base de datos"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 1. Verificar si la tabla existe
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='banco_preguntas'"
        )
        if not cursor.fetchone():
            print("❌ La tabla banco_preguntas no existe")
            return

        print("✅ Tabla banco_preguntas existe\n")

        # 2. Verificar columnas
        cursor.execute("PRAGMA table_info(banco_preguntas)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Columnas existentes: {columns}")
        if "curso" not in columns:
            print("❌ La columna curso NO existe en banco_preguntas")
            return
        print("✅ La columna curso existe\n")

        # 3. Contar registros total
        cursor.execute("SELECT COUNT(*) FROM banco_preguntas")
        total = cursor.fetchone()[0]
        print(f"Total de registros: {total}\n")

        # 4. Ver cursos únicos
        print("=== CURSOS ÚNICOS EN BANCO_PREGUNTAS ===")
        cursor.execute("SELECT DISTINCT curso FROM banco_preguntas ORDER BY curso")
        cursos = cursor.fetchall()
        for curso in cursos:
            cursor.execute(
                "SELECT COUNT(*) FROM banco_preguntas WHERE curso = ?", (curso[0],)
            )
            count = cursor.fetchone()[0]
            print(f"  Curso: {repr(curso[0])} → {count} registros")

        # 5. Ver grados únicos
        print("\n=== GRADOS ÚNICOS EN BANCO_PREGUNTAS ===")
        cursor.execute("SELECT DISTINCT grado FROM banco_preguntas ORDER BY grado")
        grados = cursor.fetchall()
        for grado in grados:
            print(f"  Grado: {repr(grado[0])}")

        # 6. Ver combinación grado-curso
        print("\n=== COMBINACIÓN GRADO-CURSO ===")
        cursor.execute(
            "SELECT DISTINCT grado, curso FROM banco_preguntas ORDER BY grado, curso"
        )
        combos = cursor.fetchall()
        for grado, curso in combos:
            cursor.execute(
                "SELECT COUNT(*) FROM banco_preguntas WHERE grado = ? AND curso IS ?",
                (grado, curso if curso else None),
            )
            count = cursor.fetchone()[0]
            print(f"  Grado: {repr(grado)} | Curso: {repr(curso)} → {count} registros")

        # 7. Ver áreas únicas
        print("\n=== ÁREAS ÚNICAS EN BANCO_PREGUNTAS ===")
        cursor.execute("SELECT DISTINCT area FROM banco_preguntas ORDER BY area")
        areas = cursor.fetchall()
        for area in areas:
            print(f"  Área: {repr(area[0])}")

        # 8. Ver evaluaciones únicas
        print("\n=== EVALUACIONES ÚNICAS EN BANCO_PREGUNTAS ===")
        cursor.execute(
            "SELECT DISTINCT evaluacion FROM banco_preguntas ORDER BY evaluacion"
        )
        evals = cursor.fetchall()
        for eval in evals:
            print(f"  Evaluación: {repr(eval[0])}")

        # 9. Ver muestra de datos
        print("\n=== MUESTRA DE 5 REGISTROS ===")
        cursor.execute(
            """
            SELECT grado, curso, area, evaluacion, enunciado 
            FROM banco_preguntas 
            LIMIT 5
        """
        )
        for row in cursor.fetchall():
            print(
                f"  Grado: {repr(row[0])}, Curso: {repr(row[1])}, Área: {repr(row[2])}, Eval: {repr(row[3])}"
            )
            print(f"    Detalles: {row[4][:50] if row[4] else 'N/A'}...\n")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_database()
