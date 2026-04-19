#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para recrear BD e importar preguntas/estudiantes sin GUI."""

import sys

sys.path.insert(0, str(__file__))

import sqlite3
import pandas as pd
from pathlib import Path
from core.construir_nombre import construir_nombre

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "sistema.db"
PREGUNTAS_FILE = BASE_DIR / "preguntas.xlsx"
ESTUDIANTES_FILE = BASE_DIR / "estudiantes.xlsx"


def crear_tablas():
    """Crear todas las tablas necesarias."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Tabla estudiantes
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_documento TEXT,
            documento TEXT UNIQUE,
            nombre TEXT,
            apellido1 TEXT,
            apellido2 TEXT,
            nombre1 TEXT,
            nombre2 TEXT,
            sexo TEXT,
            fecha_nacimiento TEXT,
            telefono TEXT,
            correo TEXT,
            grado TEXT,
            curso TEXT,
            jornada TEXT,
            sede TEXT,
            estado TEXT DEFAULT 'Activo',
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Tabla banco_preguntas
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS banco_preguntas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evaluacion TEXT,
            area TEXT,
            periodo TEXT,
            grado TEXT,
            curso TEXT,
            id_contexto TEXT,
            contexto TEXT,
            enunciado TEXT,
            opcion_a TEXT,
            opcion_b TEXT,
            opcion_c TEXT,
            opcion_d TEXT,
            correcta TEXT,
            imagen TEXT,
            nombre TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()
    print("✓ Tablas creadas")


def importar_preguntas():
    """Importar preguntas desde Excel."""
    if not PREGUNTAS_FILE.exists():
        print("⚠ archivo preguntas.xlsx no existe")
        return

    df = pd.read_excel(PREGUNTAS_FILE)
    df.columns = df.columns.str.strip().str.lower()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    count = 0
    for _, row in df.iterrows():
        try:
            cursor.execute(
                """INSERT INTO banco_preguntas
                   (evaluacion,area,periodo,grado,curso,id_contexto,contexto,
                    enunciado,opcion_a,opcion_b,opcion_c,opcion_d,correcta,imagen,nombre)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(row.get("evaluacion", "")).strip(),
                    str(row.get("area", "")).strip(),
                    str(row.get("periodo", "")).strip(),
                    str(row.get("grado", "")).strip(),
                    str(row.get("curso", "")).strip(),
                    str(row.get("id_contexto", "")).strip(),
                    str(row.get("contexto", "")).strip(),
                    str(row.get("enunciado", "")).strip(),
                    str(row.get("opcion_a", "")).strip(),
                    str(row.get("opcion_b", "")).strip(),
                    str(row.get("opcion_c", "")).strip(),
                    str(row.get("opcion_d", "")).strip(),
                    str(row.get("correcta", "")).strip(),
                    str(row.get("imagen", "")).strip(),
                    str(row.get("nombre", "")).strip(),
                ),
            )
            count += 1
        except Exception as e:
            pass

    conn.commit()
    conn.close()
    print(f"✓ Se importaron {count} preguntas")


def importar_estudiantes():
    """Importar estudiantes desde Excel."""
    if not ESTUDIANTES_FILE.exists():
        print("⚠ archivo estudiantes.xlsx no existe")
        return

    df = pd.read_excel(ESTUDIANTES_FILE)
    df.columns = df.columns.str.strip().str.lower()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    count = 0
    for _, row in df.iterrows():
        try:
            documento = str(row.get("documento", "")).strip()
            estudiante = {
                "apellido1": str(row.get("apellido1", "")).strip(),
                "apellido2": str(row.get("apellido2", "")).strip(),
                "nombre1": str(row.get("nombre1", "")).strip(),
                "nombre2": str(row.get("nombre2", "")).strip(),
            }
            nombre = construir_nombre(estudiante)
            grado = str(row.get("grado", "")).strip()

            if documento and nombre and grado:
                cursor.execute(
                    """INSERT OR IGNORE INTO estudiantes
                       (tipo_documento,documento,nombre,apellido1,apellido2,nombre1,nombre2,sexo,fecha_nacimiento,
                        telefono,correo,grado,curso,jornada,sede,estado)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        str(row.get("tipo_documento", "")).strip(),
                        documento,
                        nombre,
                        estudiante["apellido1"],
                        estudiante["apellido2"],
                        estudiante["nombre1"],
                        estudiante["nombre2"],
                        str(row.get("sexo", "")).strip(),
                        str(row.get("fecha_nacimiento", "")).strip(),
                        str(row.get("telefono", "")).strip(),
                        str(row.get("correo", "")).strip(),
                        grado,
                        str(row.get("curso", "")).strip(),
                        str(row.get("jornada", "")).strip(),
                        str(row.get("sede", "")).strip(),
                        "Activo",
                    ),
                )
                count += 1
        except Exception:
            pass

    conn.commit()
    conn.close()
    print(f"✓ Se importaron {count} estudiantes")


if __name__ == "__main__":
    print("=" * 60)
    print("RECREANDO BD E IMPORTANDO DATOS")
    print("=" * 60)

    # Eliminar BD anterior
    DB_FILE.unlink(missing_ok=True)
    print("✓ BD anterior eliminada")

    # Crear tablas
    print("\n1. Creando tablas...")
    crear_tablas()

    # Importar datos
    print("\n2. Importando datos...")
    importar_estudiantes()
    importar_preguntas()

    # Ver estadísticas
    print("\n3. Verificando datos importados...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM estudiantes")
    est_count = cursor.fetchone()[0]
    print(f"   - Estudiantes: {est_count}")

    cursor.execute("SELECT COUNT(*) FROM banco_preguntas")
    preg_count = cursor.fetchone()[0]
    print(f"   - Preguntas: {preg_count}")

    conn.close()

    print("\n✓ COMPLETADO")
    print("=" * 60)
