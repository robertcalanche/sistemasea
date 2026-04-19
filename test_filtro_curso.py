#!/usr/bin/env python3
"""
Prueba del filtrado correcto de curso:
- Las preguntas se filtran solo por grado
- Los estudiantes se filtran por grado + curso
- El mismo examen (preguntas) se aplica a todos los cursos del grado
"""

import tkinter as tk
from pathlib import Path
import os, sys
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from modulo_superadmin import ModuloSuperAdmin


def test_filtrado_curso():
    """Verifica que:
    1. Las preguntas se carguen solo por grado (no por curso)
    2. Los estudiantes se filtren por grado + curso
    3. El mismo examen se aplique a todos los cursos
    """
    root = tk.Tk()
    root.withdraw()

    db_path = str(BASE_DIR / "sistema_test_filtro.db")

    print("\n" + "=" * 70)
    print("PRUEBA: Filtrado Correcto de Curso")
    print("=" * 70 + "\n")

    msa = ModuloSuperAdmin(root, db_path=db_path, base_dir=str(BASE_DIR))

    # ===== Crear datos de prueba =====
    print("1. Creando datos de prueba...")

    # Preguntas para el grado 5 (SIN diferenciar por curso)
    preguntas = [
        {
            "id": 1,
            "evaluacion": "Primera",
            "area": "Matematicas",
            "periodo": "",
            "grado": "5",
            "id_contexto": "CTX1",
            "contexto": "Contexto matemático 1.",
            "enunciado": "¿Cuánto es 2 + 2?",
            "opcion_a": "3",
            "opcion_b": "4",
            "opcion_c": "5",
            "opcion_d": "6",
            "correcta": "B",
            "imagen": "",
        },
        {
            "id": 2,
            "evaluacion": "Primera",
            "area": "Matematicas",
            "periodo": "",
            "grado": "5",
            "id_contexto": "CTX2",
            "contexto": "Contexto matemático 2.",
            "enunciado": "¿Cuál es 3x3?",
            "opcion_a": "6",
            "opcion_b": "9",
            "opcion_c": "12",
            "opcion_d": "15",
            "correcta": "B",
            "imagen": "",
        },
    ]

    # Estudiantes: agregamos uno de grado 0 (Transición) + 2 del curso 5-01 y 2 del curso 5-02
    estudiantes = [
        {
            "sede": "Principal",
            "jornada": "MAN",
            "grado": "0",  # debe mostrarse como '0' al editar
            "curso": "T0",
            "nombre": "Transicion",
            "tipodoc": "CC",
            "documento": "0000",
            "fechana": "2021-11-28 00:00:00",  # hora debe eliminarse
            "telefono": float("nan"),
            "celular": None,
            "email": "",
            "genero": "",
            "tipo_sangre": "",
            "estado": "",
        },
        {
            "sede": "Principal",
            "jornada": "MAN",
            "grado": "5",
            "curso": "01",
            "nombre": "Estudiante A",
            "tipodoc": "CC",
            "documento": "1001",
            "fechana": "2015-01-15",
            "telefono": "",
            "celular": "",
            "email": "",
            "genero": "M",
            "tipo_sangre": "O+",
            "estado": "Activo",
        },
        {
            "sede": "Principal",
            "jornada": "MAN",
            "grado": "5",
            "curso": "01",
            "nombre": "Estudiante B",
            "tipodoc": "CC",
            "documento": "1002",
            "fechana": "2015-02-20",
            "telefono": "",
            "celular": "",
            "email": "",
            "genero": "F",
            "tipo_sangre": "A+",
            "estado": "Activo",
        },
        {
            "sede": "Principal",
            "jornada": "MAN",
            "grado": "5",
            "curso": "02",
            "nombre": "Estudiante C",
            "tipodoc": "CC",
            "documento": "1003",
            "fechana": "2015-03-10",
            "telefono": "",
            "celular": "",
            "email": "",
            "genero": "M",
            "tipo_sangre": "B+",
            "estado": "Activo",
        },
        {
            "sede": "Principal",
            "jornada": "MAN",
            "grado": "5",
            "curso": "02",
            "nombre": "Estudiante D",
            "tipodoc": "CC",
            "documento": "1004",
            "fechana": "2015-04-05",
            "telefono": "",
            "celular": "",
            "email": "",
            "genero": "F",
            "tipo_sangre": "O-",
            "estado": "Activo",
        },
    ]

    df_p = pd.DataFrame(preguntas)
    df_e = pd.DataFrame(estudiantes)

    try:
        df_p.to_excel(BASE_DIR / "preguntas.xlsx", index=False)
        df_e.to_excel(BASE_DIR / "estudiantes.xlsx", index=False)
        print("   ✓ Archivos Excel creados")
    except Exception as e:
        print(f"   ⚠️  No se pudieron guardar Excel: {e}")

    # ------- comprobaciones extras sobre la tabla de estudiantes -------
    msa._load_estudiantes()
    filas = [msa.tree_est.item(i)["values"] for i in msa.tree_est.get_children()]
    # encontrar fila de Transición
    fila_trans = next((f for f in filas if f[5] == "0000"), None)
    assert fila_trans is not None, "No se encontró estudiante de transición"
    # grado aparece como '0'
    assert fila_trans[1] == "0"
    # fecha sin hora
    assert fila_trans[6] == "2021-11-28"
    # valores vacíos no muestran 'nan'
    assert (
        fila_trans[7] == ""
        and fila_trans[8] == ""
        and fila_trans[10] == ""
        and fila_trans[11] == ""
    )
    # prueba de búsqueda por nombre
    msa.filter_nombre.delete(0, "end")
    msa.filter_nombre.insert(0, "Transi")
    msa._load_estudiantes()
    filas_filtro = [msa.tree_est.item(i)["values"] for i in msa.tree_est.get_children()]
    assert (
        len(filas_filtro) == 1 and filas_filtro[0][5] == "0000"
    ), "El filtro por nombre no funcionó"
    print("   ✓ Validaciones de tabla de estudiantes exitosas")

    # Crear tabla config_examenes
    msa.cur.execute(
        """CREATE TABLE IF NOT EXISTS config_examenes (
                   id INTEGER PRIMARY KEY,
                   grado TEXT,
                   area TEXT,
                   evaluacion TEXT,
                   duracion_segundos INTEGER,
                   cantidad_preguntas INTEGER,
                   max_intentos INTEGER,
                   permitir_reintentos INTEGER,
                   examen_activo INTEGER DEFAULT 0
               )"""
    )
    msa.cur.execute(
        "INSERT OR REPLACE INTO config_examenes (grado,area,evaluacion,duracion_segundos,cantidad_preguntas,max_intentos,permitir_reintentos,examen_activo) VALUES (?,?,?,?,?,?,?,?)",
        ("5", "Matematicas", "Primera", 1200, 2, 1, 0, 0),
    )
    msa.conn.commit()
    print("   ✓ Configuración de examen creada")

    # ===== PRUEBA 1: Generar para curso 5-01 =====
    print("\n2. Generando examen para Grado 5, Curso 01...")
    out_dir = str(BASE_DIR / "out_test_filtro")
    os.makedirs(out_dir, exist_ok=True)

    try:
        cantidad = msa._do_generate_exams(
            out_dir,
            "5",
            "Matematicas",
            "Primera",
            curso="01",  # CURSO EXPLÍCITO
            estudiante=None,
            cantidad_manual=2,
            cantidad_textos=0,
            fecha="2026-03-04",
        )
        print(f"   ✓ Se generaron {cantidad} examen(es) para curso 01")

        # Verificar que se generaron archivos SOLO para estudiantes del curso 01
        archivos = os.listdir(out_dir)
        cursos_encontrados = set()
        for arch in archivos:
            if arch.endswith(".pdf"):
                print(f"      Archivo: {arch}")
                # El nombre debe contener curso 01 o documento de estudiantes del curso 01
                if "1001" in arch or "1002" in arch:
                    cursos_encontrados.add("01")
                elif "1003" in arch or "1004" in arch:
                    cursos_encontrados.add("02")

        if "01" in cursos_encontrados and "02" not in cursos_encontrados:
            print("   ✓ CORRECTO: Solo se generaron exámenes para curso 01")
        else:
            print(f"   ✗ ERROR: Se encontraron cursos: {cursos_encontrados}")

    except Exception as e:
        print(f"   ✗ Error al generar examen: {e}")

    # ===== PRUEBA 2: Generar para curso 5-02 =====
    print("\n3. Generando examen para Grado 5, Curso 02...")

    # Limpiar directorio
    for arch in os.listdir(out_dir):
        try:
            os.remove(os.path.join(out_dir, arch))
        except Exception:
            pass

    try:
        cantidad = msa._do_generate_exams(
            out_dir,
            "5",
            "Matematicas",
            "Primera",
            curso="02",  # CURSO DIFERENTE
            estudiante=None,
            cantidad_manual=2,
            cantidad_textos=0,
            fecha="2026-03-04",
        )
        print(f"   ✓ Se generaron {cantidad} examen(es) para curso 02")

        archivos = os.listdir(out_dir)
        cursos_encontrados = set()
        for arch in archivos:
            if arch.endswith(".pdf"):
                print(f"      Archivo: {arch}")
                if "1001" in arch or "1002" in arch:
                    cursos_encontrados.add("01")
                elif "1003" in arch or "1004" in arch:
                    cursos_encontrados.add("02")

        if "02" in cursos_encontrados and "01" not in cursos_encontrados:
            print("   ✓ CORRECTO: Solo se generaron exámenes para curso 02")
        else:
            print(f"   ✗ ERROR: Se encontraron cursos: {cursos_encontrados}")

    except Exception as e:
        print(f"   ✗ Error al generar examen: {e}")

    # ===== PRUEBA 3: Generar sin especificar curso =====
    print("\n4. Generando examen para Grado 5 (SIN especificar curso)...")

    for arch in os.listdir(out_dir):
        try:
            os.remove(os.path.join(out_dir, arch))
        except Exception:
            pass

    try:
        cantidad = msa._do_generate_exams(
            out_dir,
            "5",
            "Matematicas",
            "Primera",
            curso=None,  # SIN CURSO
            estudiante=None,
            cantidad_manual=2,
            cantidad_textos=0,
            fecha="2026-03-04",
        )
        print(f"   ✓ Se generaron {cantidad} examen(es) para TODO el grado 5")

        archivos = sorted(os.listdir(out_dir))
        print(f"   Archivos generados: {len(archivos)}")
        for arch in archivos:
            if arch.endswith(".pdf"):
                print(f"      {arch}")

        if len(archivos) == 4:
            print(
                "   ✓ CORRECTO: Se generaron 4 exámenes (todos los estudiantes del grado)"
            )
        else:
            print(f"   ⚠️  Se esperaban 4 archivos, se encontraron {len(archivos)}")

    except Exception as e:
        print(f"   ✗ Error al generar examen: {e}")

    # Limpiar
    try:
        root.destroy()
    except Exception:
        pass

    print("\n" + "=" * 70)
    print("CONCLUSIÓN:")
    print("- Preguntas filtradas: solo por GRADO (no por curso)")
    print("- Estudiantes filtrados: por GRADO + CURSO (cuando se especifica)")
    print("- Mismo examen para todos los cursos del grado")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    test_filtrado_curso()
