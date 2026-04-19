from core.util_nombres import obtener_nombre_completo
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from tkinter import ttk

# superadmin module needed for master-key login
from modulo_superadmin import ModuloSuperAdmin
import pandas as pd
import sqlite3
from pathlib import Path
import sys
from datetime import datetime, timedelta
import random
import json

BASE_DIR = Path(__file__).resolve().parent
ESTUDIANTES_FILE = BASE_DIR / "estudiantes.xlsx"
PREGUNTAS_FILE = BASE_DIR / "preguntas.xlsx"
DB_FILE = BASE_DIR / "sistema.db"


def obtener_ruta_icono():
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            ruta_meipass = Path(meipass) / "sea_icon.ico"
            if ruta_meipass.exists():
                return ruta_meipass
        return Path(sys.executable).resolve().parent / "sea_icon.ico"
    return BASE_DIR / "sea_icon.ico"


# ================= BASE DE DATOS =================


def crear_base_datos():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            documento TEXT,
            nombre TEXT,
            grado TEXT,
            area TEXT,
            nota REAL,
            estado_examen TEXT,
            hora_inicio TEXT,
            hora_fin TEXT,
            intento INTEGER DEFAULT 1,
            puede_revisar INTEGER DEFAULT 0,
            respuestas TEXT
        )
    """
    )

    conn.commit()
    conn.close()
    crear_tabla_config()
    # Tabla para respuestas por estudiante (detalle por pregunta)
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS respuestas_estudiantes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    documento TEXT,
                    nombre TEXT,
                    grado TEXT,
                    area TEXT,
                    intento INTEGER,
                    pregunta_id INTEGER,
                    enunciado TEXT,
                    respuesta_seleccionada TEXT,
                    respuesta_correcta TEXT,
                    es_correcta INTEGER,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(documento, area, intento, pregunta_id)
                )
            """
            )
            conn.commit()
    except Exception:
        pass
    # Asegurar que existan columnas opcionales
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for col, tipo in [("intento", "INTEGER DEFAULT 1"), ("respuestas", "TEXT")]:
            try:
                cursor.execute(f"ALTER TABLE resultados ADD COLUMN {col} {tipo}")
            except Exception:
                pass
        conn.commit()
        conn.close()
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def crear_tabla_config():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS config_examenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grado TEXT,
            area TEXT,
            evaluacion TEXT,
            duracion_segundos INTEGER,
            cantidad_preguntas INTEGER,
            max_intentos INTEGER DEFAULT 1,
            permitir_reintentos INTEGER DEFAULT 1,
            habilitado INTEGER DEFAULT 0,
            UNIQUE(grado, area, evaluacion)
        )
    """
    )

    conn.commit()
    conn.close()
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for col, tipo in [
            ("grado", "TEXT"),
            ("evaluacion", "TEXT"),
            ("habilitado", "INTEGER DEFAULT 0"),
            ("max_intentos", "INTEGER DEFAULT 1"),
            ("permitir_reintentos", "INTEGER DEFAULT 1"),
        ]:
            try:
                cursor.execute(f"ALTER TABLE config_examenes ADD COLUMN {col} {tipo}")
            except Exception:
                pass
        conn.commit()
        conn.close()
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def registrar_inicio(documento, nombre, grado, area="General"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    hora_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "SELECT MAX(intento) FROM resultados WHERE documento = ? AND area = ?",
        (documento, area),
    )
    resultado = cursor.fetchone()
    intento = (resultado[0] or 0) + 1

    cursor.execute(
        """
        INSERT INTO resultados (documento, nombre, grado, area, nota, estado_examen, hora_inicio, hora_fin, intento)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            documento,
            nombre,
            grado,
            area,
            None,
            "EN_PROCESO",
            hora_inicio,
            None,
            intento,
        ),
    )

    intento_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return intento, intento_id


def registrar_final(documento, nota, respuestas=None, area="General", intento_id=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    hora_fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if respuestas and isinstance(respuestas, str):
        try:
            datos = json.loads(respuestas)
            respuestas = json.dumps(datos)
        except Exception:
            respuestas = respuestas
    elif respuestas:
        respuestas = (
            json.dumps(respuestas) if not isinstance(respuestas, str) else respuestas
        )

    # Actualizar registro principal en resultados
    if intento_id is not None:
        if respuestas is not None:
            cursor.execute(
                """
                UPDATE resultados
                SET nota = ?, estado_examen = ?, hora_fin = ?, respuestas = ?
                WHERE id = ?
            """,
                (nota, "FINALIZADO", hora_fin, respuestas, intento_id),
            )
        else:
            cursor.execute(
                """
                UPDATE resultados
                SET nota = ?, estado_examen = ?, hora_fin = ?
                WHERE id = ?
            """,
                (nota, "FINALIZADO", hora_fin, intento_id),
            )
    else:
        if respuestas is not None:
            cursor.execute(
                """
                UPDATE resultados
                SET nota = ?, estado_examen = ?, hora_fin = ?, respuestas = ?
                WHERE documento = ? AND area = ? AND estado_examen = 'EN_PROCESO'
            """,
                (nota, "FINALIZADO", hora_fin, respuestas, documento, area),
            )
        else:
            cursor.execute(
                """
                UPDATE resultados
                SET nota = ?, estado_examen = ?, hora_fin = ?
                WHERE documento = ? AND area = ? AND estado_examen = 'EN_PROCESO'
            """,
                (nota, "FINALIZADO", hora_fin, documento, area),
            )

    conn.commit()
    # Insertar detalle de respuestas en la tabla respuestas_estudiantes
    try:
        respuestas_list = None
        if respuestas:
            if isinstance(respuestas, str):
                try:
                    respuestas_list = json.loads(respuestas)
                except Exception:
                    respuestas_list = None
            elif isinstance(respuestas, list):
                respuestas_list = respuestas

        if respuestas_list:
            with sqlite3.connect(DB_FILE) as conn2:
                cur2 = conn2.cursor()
                cur2.execute(
                    "SELECT intento, nombre, grado FROM resultados WHERE documento = ? AND area = ? AND estado_examen = 'FINALIZADO' ORDER BY id DESC LIMIT 1",
                    (documento, area),
                )
                fila = cur2.fetchone()
                intento_val = fila[0] if fila else None
                nombre_val = fila[1] if fila and len(fila) > 1 else None
                grado_val = fila[2] if fila and len(fila) > 2 else None

                for r in respuestas_list:
                    try:
                        pregunta_id = (
                            int(r.get("pregunta_id", 0))
                            if isinstance(r, dict) and r.get("pregunta_id") is not None
                            else None
                        )
                    except Exception:
                        pregunta_id = None

                    enunciado = r.get("enunciado") if isinstance(r, dict) else None
                    imagen = r.get("imagen") if isinstance(r, dict) else None
                    resp_sel = (
                        r.get("respuesta_dada")
                        if isinstance(r, dict)
                        else (r if not isinstance(r, dict) else None)
                    )
                    resp_corr = (
                        r.get("respuesta_correcta") if isinstance(r, dict) else None
                    )
                    es_corr = 1 if (isinstance(r, dict) and r.get("correcta")) else 0

                    exists = False
                    if pregunta_id is not None:
                        cur2.execute(
                            "SELECT id FROM respuestas_estudiantes WHERE documento = ? AND area = ? AND intento = ? AND pregunta_id = ? LIMIT 1",
                            (documento, area, intento_val, pregunta_id),
                        )
                        if cur2.fetchone():
                            exists = True

                    if not exists:
                        cur2.execute(
                            "INSERT OR IGNORE INTO respuestas_estudiantes (documento, nombre, grado, area, intento, pregunta_id, enunciado, respuesta_seleccionada, respuesta_correcta, es_correcta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (
                                documento,
                                nombre_val,
                                grado_val,
                                area,
                                intento_val,
                                pregunta_id,
                                enunciado,
                                resp_sel,
                                resp_corr,
                                es_corr,
                            ),
                        )

                conn2.commit()
    except Exception:
        pass


def obtener_todas_respuestas_desde_bd(documento, area, intento):
    """Recupera todas las respuestas guardadas en respuestas_estudiantes y las retorna como JSON.
    Útil para restaurar el estado completo del examen cuando se reanuda."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pregunta_id, enunciado, respuesta_seleccionada, respuesta_correcta, es_correcta
            FROM respuestas_estudiantes
            WHERE documento = ? AND area = ? AND intento = ?
            ORDER BY rowid ASC
            """,
            (documento, area, intento),
        )
        filas = cursor.fetchall()
        conn.close()

        respuestas_recuperadas = []
        for pregunta_id, enunciado, resp_sel, resp_corr, es_corr in filas:
            respuestas_recuperadas.append(
                {
                    "pregunta_id": pregunta_id,
                    "enunciado": enunciado,
                    "imagen": None,  # Las imágenes no se guardan en respuestas_estudiantes
                    "respuesta_dada": resp_sel,
                    "respuesta_correcta": resp_corr,
                    "correcta": bool(es_corr),
                }
            )

        return json.dumps(respuestas_recuperadas) if respuestas_recuperadas else None
    except Exception as e:
        print(f"[ERROR] obtener_todas_respuestas_desde_bd: {e}")
        return None


def ya_presento(documento):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT estado_examen FROM resultados
        WHERE documento = ? AND estado_examen = 'FINALIZADO'
    """,
        (documento,),
    )

    resultado = cursor.fetchone()
    conn.close()

    return resultado is not None


def obtener_estado_area(documento, area):
    """
    Obtiene el estado del estudiante en una área específica.
    Retorna: ('DISPONIBLE', None), ('PRESENTADO', nota), ('REVISION_ACTIVA', nota), o None si no existe.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT estado_examen, nota, puede_revisar FROM resultados
        WHERE documento = ? AND area = ?
        ORDER BY id DESC
        LIMIT 1
    """,
        (documento, area),
    )

    resultado = cursor.fetchone()
    conn.close()

    if not resultado:
        return None

    estado_examen, nota, puede_revisar = resultado

    if estado_examen == "FINALIZADO" and puede_revisar == 1:
        return ("REVISION_ACTIVA", nota)
    elif estado_examen == "FINALIZADO":
        return ("PRESENTADO", nota)
    else:
        return (estado_examen, nota)


def obtener_intento_area(documento, area):
    """Obtiene el registro completo del último intento en un área (incluye respuestas)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, nota, estado_examen, puede_revisar, respuestas FROM resultados
        WHERE documento = ? AND area = ?
        ORDER BY id DESC
        LIMIT 1
    """,
        (documento, area),
    )

    resultado = cursor.fetchone()
    conn.close()

    return resultado


def autorizar_revision(documento, area=None):
    """Autoriza a un estudiante para revisar sus aciertos y errores.

    Si se proporciona `area`, autoriza sólo el último intento FINALIZADO en esa área para el documento.
    Si no, autoriza todos los intentos FINALIZADO del documento (comportamiento previo).
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if area:
        cursor.execute(
            "SELECT id FROM resultados WHERE documento = ? AND area = ? AND estado_examen = 'FINALIZADO' ORDER BY id DESC LIMIT 1",
            (documento, area),
        )
        fila = cursor.fetchone()
        if fila:
            cursor.execute(
                "UPDATE resultados SET puede_revisar = 1 WHERE id = ?", (fila[0],)
            )
    else:
        cursor.execute(
            """
            UPDATE resultados
            SET puede_revisar = 1
            WHERE documento = ? AND estado_examen = 'FINALIZADO'
        """,
            (documento,),
        )

    conn.commit()
    conn.close()


def puede_revisar(documento):
    """Verifica si un estudiante está autorizado para revisar sus resultados."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT puede_revisar FROM resultados
        WHERE documento = ? AND estado_examen = 'FINALIZADO'
        ORDER BY id DESC
        LIMIT 1
    """,
        (documento,),
    )

    resultado = cursor.fetchone()
    conn.close()

    return resultado is not None and resultado[0] == 1


def obtener_respuestas_estudiante(documento, area=None, intento=None):
    """Devuelve las filas de `respuestas_estudiantes` para un estudiante con textos de opciones.

    Args:
        documento (str): documento del estudiante
        area (str|None): filtrar por área si se suministra
        intento (int|None): filtrar por intento si se suministra

    Returns:
        list[dict]: lista de diccionarios con las columnas de la tabla + textos de opciones
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            query = "SELECT id, documento, nombre, grado, area, intento, pregunta_id, enunciado, respuesta_seleccionada, respuesta_correcta, es_correcta, fecha FROM respuestas_estudiantes WHERE documento = ?"
            params = [documento]
            if area:
                query += " AND area = ?"
                params.append(area)
            if intento is not None:
                query += " AND intento = ?"
                params.append(intento)

            query += " ORDER BY intento DESC, pregunta_id ASC"
            cur.execute(query, tuple(params))
            rows = cur.fetchall()

            cols = [
                "id",
                "documento",
                "nombre",
                "grado",
                "area",
                "intento",
                "pregunta_id",
                "enunciado",
                "respuesta_seleccionada",
                "respuesta_correcta",
                "es_correcta",
                "fecha",
            ]
            resultados = [dict(zip(cols, row)) for row in rows]

            # Cargar el Excel de preguntas para obtener los textos de las opciones
            try:
                df_preg = pd.read_excel(PREGUNTAS_FILE)
                df_preg.columns = df_preg.columns.str.strip().str.lower()
            except Exception:
                df_preg = pd.DataFrame()

            # Para cada resultado, buscar el texto de las opciones
            for resultado in resultados:
                preg_id = resultado.get("pregunta_id")
                letra_sel = resultado.get("respuesta_seleccionada", "").strip().upper()
                letra_corr = resultado.get("respuesta_correcta", "").strip().upper()

                # Buscar la pregunta en el Excel
                if not df_preg.empty and preg_id is not None:
                    preg_row = df_preg[df_preg["id"] == preg_id]
                    if not preg_row.empty:
                        # Obtener textos de opciones
                        opcion_a = (
                            str(preg_row.iloc[0].get("opcion_a", "")).strip()
                            if "opcion_a" in df_preg.columns
                            else ""
                        )
                        opcion_b = (
                            str(preg_row.iloc[0].get("opcion_b", "")).strip()
                            if "opcion_b" in df_preg.columns
                            else ""
                        )
                        opcion_c = (
                            str(preg_row.iloc[0].get("opcion_c", "")).strip()
                            if "opcion_c" in df_preg.columns
                            else ""
                        )
                        opcion_d = (
                            str(preg_row.iloc[0].get("opcion_d", "")).strip()
                            if "opcion_d" in df_preg.columns
                            else ""
                        )

                        opciones = {
                            "A": opcion_a,
                            "B": opcion_b,
                            "C": opcion_c,
                            "D": opcion_d,
                        }

                        # Enriquecer resultado con textos
                        resultado["respuesta_seleccionada_texto"] = opciones.get(
                            letra_sel, letra_sel
                        )
                        resultado["respuesta_correcta_texto"] = opciones.get(
                            letra_corr, letra_corr
                        )
                    else:
                        resultado["respuesta_seleccionada_texto"] = letra_sel
                        resultado["respuesta_correcta_texto"] = letra_corr
                else:
                    resultado["respuesta_seleccionada_texto"] = letra_sel
                    resultado["respuesta_correcta_texto"] = letra_corr

            return resultados
    except Exception:
        return []


def resetear_examen(documento, area):
    """Elimina intentos y respuestas de un estudiante para un área (o todas las áreas si area es None).

    Retorna True si la operación se completó, False en caso de error.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            if area:
                cursor.execute(
                    "DELETE FROM respuestas_estudiantes WHERE documento = ? AND area = ?",
                    (documento, area),
                )
                cursor.execute(
                    "DELETE FROM resultados WHERE documento = ? AND area = ?",
                    (documento, area),
                )
            else:
                cursor.execute(
                    "DELETE FROM respuestas_estudiantes WHERE documento = ?",
                    (documento,),
                )
                cursor.execute(
                    "DELETE FROM resultados WHERE documento = ?", (documento,)
                )
            conn.commit()
        return True
    except Exception:
        return False


# ================= VALIDACIONES =================


def validar_estudiante(documento):
    """Valida estudiante con nueva estructura Excel (14 columnas).
    Campos obligatorios: documento, nombre, grado, curso, estado.
    Estado debe ser 'Matriculado' o 'MA'.
    Retorna: Series o None.
    """
    try:
        df = pd.read_excel(ESTUDIANTES_FILE)
    except Exception:
        return None

    # Normalizar nombres de columnas a minúsculas
    df.columns = df.columns.str.lower().str.strip()

    # Convertir documento a string
    if "documento" in df.columns:
        df["documento"] = df["documento"].astype(str)
    else:
        return None

    # Buscar estudiante
    estudiante = df[df["documento"] == str(documento).strip()]
    if estudiante.empty:
        return None

    estudiante_data = estudiante.iloc[0]

    # Validar campos obligatorios
    campos_obligatorios = ["documento", "nombre", "grado", "curso", "estado"]
    for campo in campos_obligatorios:
        if campo not in estudiante_data.index:
            return None
        valor = estudiante_data.get(campo, "")
        if pd.isna(valor) or str(valor).strip() == "":
            return None

    # Validar estado
    estado = str(estudiante_data.get("estado", "")).strip().lower()
    if estado not in ["matriculado", "ma"]:
        return None

    # Convertir documento a string
    estudiante_data["documento"] = str(estudiante_data["documento"]).strip()

    return estudiante_data


def validar_docente(documento):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT nombre FROM docentes WHERE documento = ? AND estado = 'Activo'",
                (str(documento),),
            )
            row = cursor.fetchone()
            if row:
                return row[0]
    except Exception:
        pass
    return None


def cargar_preguntas():
    df = pd.read_excel(PREGUNTAS_FILE)
    df.columns = df.columns.str.strip().str.lower()
    return df.sample(frac=1).reset_index(drop=True)


def cargar_areas():
    """Carga las áreas únicas desde el archivo de preguntas."""
    try:
        df = pd.read_excel(PREGUNTAS_FILE)
        df.columns = df.columns.str.strip().str.lower()
        if "area" in df.columns:
            areas = sorted(df["area"].dropna().unique().tolist())
            return areas if areas else ["General"]
        return ["General"]
    except Exception:
        return ["General"]


def cargar_grados():
    """Carga los grados únicos desde el archivo de preguntas."""
    try:
        df = pd.read_excel(PREGUNTAS_FILE)
        df.columns = df.columns.str.strip().str.lower()
        if "grado" in df.columns:
            grados = sorted(
                df["grado"].dropna().unique().tolist(), key=lambda x: str(x)
            )
            return grados if grados else []
        return []
    except Exception:
        return []


def cargar_areas_por_grado(grado):
    """Carga áreas disponibles para un grado específico desde preguntas.xlsx."""
    try:
        df = pd.read_excel(PREGUNTAS_FILE)
        df.columns = df.columns.str.strip().str.lower()
        if "grado" in df.columns and "area" in df.columns:
            df_filtrado = df[df["grado"].astype(str).str.strip() == str(grado).strip()]
            areas = sorted(df_filtrado["area"].dropna().unique().tolist())
            return areas if areas else []
        return []
    except Exception:
        return []


def cargar_evaluaciones(grado, area):
    """Carga evaluaciones disponibles para una combinación de grado y área."""
    try:
        df = pd.read_excel(PREGUNTAS_FILE)
        df.columns = df.columns.str.strip().str.lower()
        if (
            "grado" in df.columns
            and "area" in df.columns
            and "evaluacion" in df.columns
        ):
            df_filtrado = df[
                (df["grado"].astype(str).str.strip() == str(grado).strip())
                & (df["area"].astype(str).str.strip() == str(area).strip())
            ]
            evaluaciones = sorted(df_filtrado["evaluacion"].dropna().unique().tolist())
            return evaluaciones if evaluaciones else []
        return []
    except Exception:
        return []


def cargar_preguntas_filtradas(area=None, grado=None, evaluacion=None, periodo=None):
    try:
        df = pd.read_excel(PREGUNTAS_FILE)
    except Exception:
        return pd.DataFrame()  # Retorna vacío si no puede leer el archivo

    df.columns = df.columns.str.strip().str.lower()

    if area:
        df = df[df["area"].astype(str).str.strip() == str(area).strip()]

    if grado:
        df_grado = df[df["grado"].astype(str).str.strip() == str(grado).strip()]
        # Si hay preguntas para ese grado, usa esas; si no, ignora el filtro de grado
        if not df_grado.empty:
            df = df_grado

    if evaluacion:
        df = df[df["evaluacion"].astype(str).str.strip() == str(evaluacion).strip()]

    if periodo:
        df = df[df["periodo"].astype(str).str.strip() == str(periodo).strip()]

    if df.empty:
        return pd.DataFrame()  # Retorna vacío sin excepción

    # Validar que existan las columnas requeridas para ordenar
    if "id_contexto" in df.columns and "id" in df.columns:
        return df.sort_values(by=["id_contexto", "id"]).reset_index(drop=True)
    else:
        return df.reset_index(drop=True)


def cargar_config_examen(area, grado=None, evaluacion=None):
    """Carga configuración de examen (duración, cantidad de preguntas, máximo de intentos y habilitado) para un área.
    Si se proporciona grado y evaluacion, filtra por esos valores.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        if grado and evaluacion:
            # Filtrar por los tres parámetros
            cursor.execute(
                "SELECT duracion_segundos, cantidad_preguntas, COALESCE(max_intentos, 1), COALESCE(permitir_reintentos, 1), COALESCE(habilitado, 0) FROM config_examenes WHERE grado = ? AND area = ? AND evaluacion = ?",
                (grado, area, evaluacion),
            )
        else:
            # Filtrar solo por área (retrocompatibilidad)
            cursor.execute(
                "SELECT duracion_segundos, cantidad_preguntas, COALESCE(max_intentos, 1), COALESCE(permitir_reintentos, 1), COALESCE(habilitado, 0) FROM config_examenes WHERE area = ?",
                (area,),
            )

        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            return (
                resultado[0],
                resultado[1],
                resultado[2],
                resultado[3],
                resultado[4],
            )  # duracion, cantidad, max_intentos, permitir_reintentos, habilitado
        return 120, 10, 1, 1, 0  # valores por defecto
    except Exception:
        return 120, 10, 1, 1, 0


def guardar_config_examen(
    area,
    duracion_segundos,
    cantidad_preguntas,
    max_intentos=1,
    permitir_reintentos=1,
    grado=None,
    evaluacion=None,
    habilitado=0,
):
    """Guarda o actualiza configuración de examen con filtrado por grado+área+evaluación.

    Args:
        area: El área del examen
        duracion_segundos: Duración en segundos
        cantidad_preguntas: Cantidad de preguntas
        max_intentos: Máximo de intentos (default 1)
        permitir_reintentos: Si permite reintentos (default 1)
        grado: Grado correspondiente (opcional, para compatibilidad)
        evaluacion: Evaluación correspondiente (opcional, para compatibilidad)
        habilitado: Si el examen está habilitado (0 o 1)
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        if grado and evaluacion:
            # Guardar con filtrado por grado+area+evaluacion
            cursor.execute(
                "SELECT id FROM config_examenes WHERE grado = ? AND area = ? AND evaluacion = ?",
                (grado, area, evaluacion),
            )
            existe = cursor.fetchone()

            if existe:
                cursor.execute(
                    "UPDATE config_examenes SET duracion_segundos = ?, cantidad_preguntas = ?, max_intentos = ?, permitir_reintentos = ?, habilitado = ? WHERE grado = ? AND area = ? AND evaluacion = ?",
                    (
                        duracion_segundos,
                        cantidad_preguntas,
                        max_intentos,
                        permitir_reintentos,
                        habilitado,
                        grado,
                        area,
                        evaluacion,
                    ),
                )
            else:
                cursor.execute(
                    "INSERT INTO config_examenes (grado, area, evaluacion, duracion_segundos, cantidad_preguntas, max_intentos, permitir_reintentos, habilitado) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        grado,
                        area,
                        evaluacion,
                        duracion_segundos,
                        cantidad_preguntas,
                        max_intentos,
                        permitir_reintentos,
                        habilitado,
                    ),
                )
        else:
            # Compatibilidad: guardar solo por area (retrocompatibilidad)
            cursor.execute(
                "SELECT id FROM config_examenes WHERE area = ? AND grado IS NULL",
                (area,),
            )
            existe = cursor.fetchone()

            if existe:
                cursor.execute(
                    "UPDATE config_examenes SET duracion_segundos = ?, cantidad_preguntas = ?, max_intentos = ?, permitir_reintentos = ?, habilitado = ? WHERE area = ? AND grado IS NULL",
                    (
                        duracion_segundos,
                        cantidad_preguntas,
                        max_intentos,
                        permitir_reintentos,
                        habilitado,
                        area,
                    ),
                )
            else:
                cursor.execute(
                    "INSERT INTO config_examenes (area, duracion_segundos, cantidad_preguntas, max_intentos, permitir_reintentos, habilitado) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        area,
                        duracion_segundos,
                        cantidad_preguntas,
                        max_intentos,
                        permitir_reintentos,
                        habilitado,
                    ),
                )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False


# ================= VISTA HISTORIAL (Componente Reutilizable) =================


class VistaHistorialExamenes:
    """Componente reutilizable para mostrar historial de exámenes de un estudiante."""

    def __init__(self, padre, documento, nombre, editable=False, callback_revisar=None):
        """
        Args:
            padre: Widget padre (Frame o Tk)
            documento: Documento del estudiante
            nombre: Nombre del estudiante
            editable: Si True, muestra botones para ver detalle/revisar
            callback_revisar: Función callback cuando se hace clic en revisar
        """
        self.documento = documento
        self.nombre = nombre
        self.editable = editable
        self.callback_revisar = callback_revisar

        # Frame contenedor
        self.frame = tk.Frame(padre, bg="white", relief="solid", borderwidth=1)

        # Encabezado
        header = tk.Frame(self.frame, bg=COLOR_PRIMARIO)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"📋 Historial de {nombre}",
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
        ).pack(anchor="w", padx=15, pady=10)

        # Canvas con scroll
        canvas_frame = tk.Frame(self.frame, bg="white")
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Cargar historial
        self._cargar_historial()

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _cargar_historial(self):
        """Carga el historial de la BD y lo muestra."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT area, nota, estado_examen, puede_revisar, hora_fin, intento FROM resultados 
            WHERE documento = ? 
            ORDER BY id DESC
        """,
            (self.documento,),
        )
        registros = cursor.fetchall()
        conn.close()

        if not registros:
            tk.Label(
                self.scrollable_frame,
                text="Sin historial de exámenes.",
                font=("Segoe UI", 11),
                bg="white",
                fg="#999",
            ).pack(pady=20)
            return

        # Agrupar intentos por área
        intentos_por_area = {}
        for area, nota, estado, puede_revisar_val, fecha, intento in registros:
            if area not in intentos_por_area:
                intentos_por_area[area] = []
            intentos_por_area[area].append(
                {
                    "nota": nota,
                    "estado": estado,
                    "puede_revisar": puede_revisar_val,
                    "fecha": fecha,
                    "intento": intento,
                }
            )

        # Mostrar por área
        for area in intentos_por_area:
            self._mostrar_area_historial(area, intentos_por_area[area])

    def _mostrar_area_historial(self, area, intentos):
        """Muestra los intentos de un área."""
        area_frame = tk.Frame(
            self.scrollable_frame, bg="#f5f5f5", relief="solid", borderwidth=1
        )
        area_frame.pack(fill="x", padx=5, pady=8)

        # Header del área
        tk.Label(
            area_frame,
            text=f"📖 {area.title()}",
            font=("Segoe UI", 11, "bold"),
            bg="#f5f5f5",
            fg=COLOR_TEXTO,
        ).pack(anchor="w", padx=10, pady=(8, 5))

        # Intentos
        for intento_data in intentos:
            intento_frame = tk.Frame(
                area_frame, bg="white", relief="solid", borderwidth=1
            )
            intento_frame.pack(fill="x", padx=10, pady=4)

            # Info básica
            info_text = f"Intento {intento_data['intento']}"
            if intento_data["nota"] is not None:
                info_text += f" • Nota: {intento_data['nota']}/5.0"

            tk.Label(
                intento_frame, text=info_text, font=("Segoe UI", 10), bg="white"
            ).pack(anchor="w", padx=10, pady=(5, 2))

            # Estado
            estado_is_presentado = intento_data["estado"] in (
                "PRESENTADO",
                "FINALIZADO",
            )
            estado_color = (
                "#51cf66"
                if intento_data["puede_revisar"]
                else "#747bff" if estado_is_presentado else "#ff9500"
            )
            estado_text = (
                "Revisión activa"
                if intento_data["puede_revisar"]
                else (
                    "Esperando revisión"
                    if estado_is_presentado
                    else intento_data["estado"]
                )
            )

            tk.Label(
                intento_frame,
                text=f"Estado: {estado_text}",
                font=("Segoe UI", 9),
                bg="white",
                fg=estado_color,
            ).pack(anchor="w", padx=20, pady=2)

            # Fecha
            if intento_data["fecha"]:
                tk.Label(
                    intento_frame,
                    text=f"Fecha: {intento_data['fecha']}",
                    font=("Segoe UI", 8),
                    bg="white",
                    fg="#666",
                ).pack(anchor="w", padx=20, pady=(2, 5))

            # Botón revisar si está disponible
            if (
                self.editable
                and intento_data["puede_revisar"]
                and self.callback_revisar
            ):
                tk.Button(
                    intento_frame,
                    text="📖 Ver Detalle",
                    command=lambda a=area: self.callback_revisar(a),
                    font=("Segoe UI", 9),
                    bg=COLOR_PRIMARIO,
                    fg="white",
                    relief="flat",
                    cursor="hand2",
                ).pack(anchor="w", padx=20, pady=(0, 5))

    def pack(self, **kwargs):
        """Métodos de empaquetamiento"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Métodos de grid"""
        self.frame.grid(**kwargs)

    def place(self, **kwargs):
        """Métodos de place"""
        self.frame.place(**kwargs)


# ================= MÓDULO DOCENTE =================


class ModuloDocente:

    def __init__(self, ventana, nombre):
        self.ventana = ventana
        self.nombre = nombre

        self.ventana.title("Panel del Docente")
        self.ventana.geometry("1000x700")
        self.ventana.configure(bg=COLOR_SECUNDARIO)

        # Header moderno
        header = tk.Frame(self.ventana, bg=COLOR_PRIMARIO, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"👨‍🏫 {self.nombre.title()}",
            font=("Segoe UI", 16, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
        ).pack(anchor="w", padx=20, pady=(15, 5))

        tk.Label(
            header,
            text="Panel de Control • Gestión de Exámenes",
            font=("Segoe UI", 11),
            bg=COLOR_PRIMARIO,
            fg="#e0e0ff",
        ).pack(anchor="w", padx=20, pady=(0, 15))

        # Toolbar mejorado
        toolbar = tk.Frame(self.ventana, bg=COLOR_SECUNDARIO)
        toolbar.pack(fill="x", padx=15, pady=10)

        tk.Label(
            toolbar,
            text="🔍 Filtrar por grado:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(0, 8))
        self.combo_grado = ttk.Combobox(
            toolbar, values=["Todos"], state="readonly", width=15, font=("Segoe UI", 10)
        )
        self.combo_grado.current(0)
        self.combo_grado.pack(side="left", padx=(0, 15))
        self.combo_grado.bind("<<ComboboxSelected>>", lambda e: self.cargar_datos())

        # Espaciador
        tk.Frame(toolbar, bg=COLOR_SECUNDARIO).pack(side="left", fill="x", expand=True)

        # Contenedor separado para botones de acción (debajo del toolbar) — asegura suficiente ancho
        actions_container = tk.Frame(self.ventana, bg=COLOR_SECUNDARIO)
        actions_container.pack(fill="x", padx=15)

        actions_frame = tk.Frame(actions_container, bg=COLOR_SECUNDARIO)
        actions_frame.pack(side="right")

        # Botones de acciones (dentro de actions_frame) empacados left->right para asegurar visibilidad
        tk.Button(
            actions_frame,
            text="📥 Exportar Excel",
            command=self.exportar_excel,
            font=("Segoe UI", 9, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=5)
        tk.Button(
            actions_frame,
            text="🔎 Ver Detalle",
            command=self.ver_detalle_selected,
            font=("Segoe UI", 9, "bold"),
            bg="#0078D7",
            fg="white",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=5)
        tk.Button(
            actions_frame,
            text="⭐ Autorizar Revisión",
            command=self.autorizar_revision_selected,
            font=("Segoe UI", 9, "bold"),
            bg="#51cf66",
            fg="white",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=5)
        tk.Button(
            actions_frame,
            text="🔄 Resetear Nota",
            command=self.reset_selected,
            font=("Segoe UI", 9, "bold"),
            bg="#ff9500",
            fg="white",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=5)

        # Panel de configuración de examen
        config_frame = tk.LabelFrame(
            self.ventana,
            text="⚙️  Configuración de Examen",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        )
        config_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Fila 1: Grado, Área, Evaluación
        config_row1 = tk.Frame(config_frame, bg=COLOR_SECUNDARIO)
        config_row1.pack(fill="x", padx=10, pady=5)

        # Grado
        tk.Label(
            config_row1,
            text="Grado:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(5, 5))
        self.combo_grado_config = ttk.Combobox(
            config_row1,
            values=[],
            state="readonly",
            width=10,
            font=("Segoe UI", 10),
        )
        self.combo_grado_config.pack(side="left", padx=5)
        self.combo_grado_config.bind(
            "<<ComboboxSelected>>", self._on_grado_config_selected
        )

        # Área
        tk.Label(
            config_row1,
            text="Área:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(15, 5))
        self.combo_area = ttk.Combobox(
            config_row1,
            values=[],
            state="readonly",
            width=10,
            font=("Segoe UI", 10),
        )
        self.combo_area.pack(side="left", padx=5)
        self.combo_area.bind("<<ComboboxSelected>>", self._on_area_config_selected)

        # Evaluación
        tk.Label(
            config_row1,
            text="Evaluación:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(15, 5))
        self.combo_evaluacion = ttk.Combobox(
            config_row1,
            values=[],
            state="readonly",
            width=12,
            font=("Segoe UI", 10),
        )
        self.combo_evaluacion.pack(side="left", padx=5)
        self.combo_evaluacion.bind("<<ComboboxSelected>>", self._cargar_config_examen)

        # Fila 2: Duración, Preguntas, Máx Intentos, Permitir Reintentos
        config_row2 = tk.Frame(config_frame, bg=COLOR_SECUNDARIO)
        config_row2.pack(fill="x", padx=10, pady=5)

        tk.Label(
            config_row2,
            text="Duración (min):",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(5, 5))
        self.entry_duracion = tk.Entry(
            config_row2, width=6, font=("Segoe UI", 10), relief="flat", bd=1
        )
        self.entry_duracion.insert(0, "2")
        self.entry_duracion.pack(side="left", padx=5)

        tk.Label(
            config_row2,
            text="Preguntas:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(15, 5))
        self.entry_cantidad = tk.Entry(
            config_row2, width=6, font=("Segoe UI", 10), relief="flat", bd=1
        )
        self.entry_cantidad.insert(0, "10")
        self.entry_cantidad.pack(side="left", padx=5)

        tk.Label(
            config_row2,
            text="Máx. Intentos:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(15, 5))
        self.entry_max_intentos = tk.Entry(
            config_row2, width=6, font=("Segoe UI", 10), relief="flat", bd=1
        )
        self.entry_max_intentos.insert(0, "1")
        self.entry_max_intentos.pack(side="left", padx=5)

        tk.Label(
            config_row2,
            text="Permitir Reintentos:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(15, 5))
        self.var_permitir_reintentos = tk.BooleanVar(value=True)
        check_reintentos = tk.Checkbutton(
            config_row2,
            variable=self.var_permitir_reintentos,
            bg=COLOR_SECUNDARIO,
            cursor="hand2",
        )
        check_reintentos.pack(side="left", padx=5)

        # Fila 3: Habilitar Examen y botón Guardar
        config_row3 = tk.Frame(config_frame, bg=COLOR_SECUNDARIO)
        config_row3.pack(fill="x", padx=10, pady=5)

        tk.Label(
            config_row3,
            text="Habilitar Examen:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(5, 5))

        self.var_habilitado = tk.BooleanVar(value=False)
        check_habilitado = tk.Checkbutton(
            config_row3,
            variable=self.var_habilitado,
            bg=COLOR_SECUNDARIO,
            cursor="hand2",
        )
        check_habilitado.pack(side="left", padx=5)

        tk.Button(
            config_row3,
            text="💾 Guardar",
            command=self.guardar_config,
            font=("Segoe UI", 9, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=15)

        # Cargar grados desde preguntas.xlsx
        self._llenar_combo_grados_config()

        # Crear la tabla siempre, independientemente de si hay datos
        self.crear_tabla()

        self.btn_actualizar = tk.Button(
            self.ventana,
            text="🔄 Actualizar Datos",
            command=self.cargar_datos,
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
            relief="flat",
            padx=15,
            pady=8,
            cursor="hand2",
        )
        self.btn_actualizar.pack(pady=12)

        # Iniciar actualización automática para que el módulo docente sincronice cambios recientes
        def _auto_refresh():
            try:
                self.cargar_datos()
            except Exception:
                pass
            try:
                self.ventana.after(5000, _auto_refresh)
            except Exception:
                pass

        _auto_refresh()

        self._llenar_combo_grados()
        self._cargar_config_examen()
        self.cargar_datos()

    def cargar_datos(self):
        # limpiar tabla
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)

        grado_sel = None
        try:
            val = self.combo_grado.get()
            if val and val != "Todos":
                grado_sel = val
        except Exception:
            grado_sel = None

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Depuración: imprimir todos los registros en la tabla `resultados` (temporal)
        try:
            cursor.execute("SELECT * FROM resultados")
            all_rows = cursor.fetchall()
            print("DEBUG - resultados (all):", all_rows)
        except Exception:
            print("DEBUG - no se pudo leer resultados para depuración")

        # Consultar sólo intentos finalizados/presentados para mostrar en el panel docente
        if grado_sel:
            cursor.execute(
                "SELECT grado, documento, nombre, area, nota, estado_examen, hora_inicio, hora_fin FROM resultados WHERE grado = ? AND estado_examen IN ('FINALIZADO','PRESENTADO') ORDER BY COALESCE(hora_fin, hora_inicio) DESC",
                (grado_sel,),
            )
        else:
            cursor.execute(
                "SELECT grado, documento, nombre, area, nota, estado_examen, hora_inicio, hora_fin FROM resultados WHERE estado_examen IN ('FINALIZADO','PRESENTADO') ORDER BY COALESCE(hora_fin, hora_inicio) DESC"
            )

        registros = cursor.fetchall()

        for fila in registros:
            grado_db, documento, nombre, area, nota, estado, hora_inicio, hora_fin = (
                fila
            )
            # Obtener grado oficial desde el archivo de estudiantes.xlsx si está disponible
            try:
                estudiante = validar_estudiante(documento)
                grado_oficial = None
                if estudiante is not None:
                    # intentar claves comunes ('grado' o 'Grado')
                    if "grado" in estudiante.index:
                        grado_oficial = estudiante["grado"]
                    elif "Grado" in estudiante.index:
                        grado_oficial = estudiante["Grado"]

                if grado_oficial is not None and not pd.isna(grado_oficial):
                    grado = str(grado_oficial).strip()
                else:
                    grado = str(grado_db) if grado_db is not None else ""
            except Exception:
                grado = str(grado_db) if grado_db is not None else ""
            fecha = hora_fin if hora_fin is not None else hora_inicio
            duracion = ""
            try:
                if hora_inicio and hora_fin:
                    hi = datetime.strptime(hora_inicio, "%Y-%m-%d %H:%M:%S")
                    hf = datetime.strptime(hora_fin, "%Y-%m-%d %H:%M:%S")
                    delta = hf - hi
                    # formatear hh:mm:ss
                    total_seconds = int(delta.total_seconds())
                    horas = total_seconds // 3600
                    minutos = (total_seconds % 3600) // 60
                    segundos = total_seconds % 60
                    duracion = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                elif hora_inicio and not hora_fin:
                    duracion = "EN_PROCESO"
            except Exception:
                duracion = ""

            # determinar tag según estado
            tag = None
            try:
                est_up = str(estado).upper()
                if "FINAL" in est_up or "FINALIZADO" in est_up:
                    tag = "finalizado"
                elif (
                    "EN_PROCESO" in est_up
                    or "PROCESO" in est_up
                    or "EN PROCESO" in est_up
                ):
                    tag = "en_proceso"
            except Exception:
                tag = None

            if tag:
                self.tabla.insert(
                    "",
                    "end",
                    values=(
                        grado,
                        documento,
                        nombre,
                        area,
                        nota,
                        estado,
                        fecha,
                        duracion,
                    ),
                    tags=(tag,),
                )
            else:
                self.tabla.insert(
                    "",
                    "end",
                    values=(
                        grado,
                        documento,
                        nombre,
                        area,
                        nota,
                        estado,
                        fecha,
                        duracion,
                    ),
                )

        conn.close()

    def _llenar_combo_grados(self):
        """Llena el combo de grados del toolbar para filtrar resultados."""
        try:
            # Preferir obtener los grados desde el archivo estudiantes.xlsx para
            # asegurar que coincidan con los registros oficiales.
            try:
                df = pd.read_excel(ESTUDIANTES_FILE)
                df.columns = df.columns.str.strip().str.lower()
                if "grado" in df.columns:
                    grados = sorted(
                        df["grado"].dropna().unique().tolist(), key=lambda x: str(x)
                    )
                else:
                    grados = []
            except Exception:
                grados = []

            # Fallback: si no hay grados en el Excel, usar la base de datos como respaldo
            if not grados:
                try:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT DISTINCT grado FROM resultados WHERE grado IS NOT NULL ORDER BY grado"
                    )
                    grados = [r[0] for r in cursor.fetchall() if r[0] is not None]
                    conn.close()
                except Exception:
                    grados = []

            valores = ["Todos"] + [str(g) for g in grados]
            self.combo_grado["values"] = valores
            self.combo_grado.current(0)
        except Exception:
            pass

    def _llenar_combo_grados_config(self):
        """Llena el combo de grados en el panel de configuración desde preguntas.xlsx."""
        try:
            grados = cargar_grados()
            if grados:
                self.combo_grado_config["values"] = grados
                self.combo_grado_config.current(0)
            else:
                self.combo_grado_config["values"] = []
        except Exception:
            pass

    def _on_grado_config_selected(self, event=None):
        """Maneja la selección de grado en el panel de configuración."""
        try:
            grado = self.combo_grado_config.get()
            if not grado:
                self.combo_area["values"] = []
                self.combo_evaluacion["values"] = []
                return

            # Cargar áreas para el grado seleccionado
            areas = cargar_areas_por_grado(grado)
            if areas:
                self.combo_area["values"] = areas
                self.combo_area.current(0)
            else:
                self.combo_area["values"] = []

            # Limpiar evaluaciones
            self.combo_evaluacion["values"] = []
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar áreas: {e}")

    def _on_area_config_selected(self, event=None):
        """Maneja la selección de área en el panel de configuración."""
        try:
            grado = self.combo_grado_config.get()
            area = self.combo_area.get()

            if not grado or not area:
                self.combo_evaluacion["values"] = []
                return

            # Cargar evaluaciones para la combinación grado+área
            evaluaciones = cargar_evaluaciones(grado, area)
            if evaluaciones:
                self.combo_evaluacion["values"] = evaluaciones
                self.combo_evaluacion.current(0)
            else:
                self.combo_evaluacion["values"] = []
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar evaluaciones: {e}")

    def _cargar_config_examen(self, event=None):
        """Carga la configuración actual del examen seleccionado (grado+área+evaluación) en los campos."""
        try:
            grado = self.combo_grado_config.get()
            area = self.combo_area.get()
            evaluacion = self.combo_evaluacion.get()

            if not grado or not area or not evaluacion:
                # Limpiar campos si no está todo seleccionado
                self.entry_duracion.delete(0, tk.END)
                self.entry_duracion.insert(0, "2")
                self.entry_cantidad.delete(0, tk.END)
                self.entry_cantidad.insert(0, "10")
                self.entry_max_intentos.delete(0, tk.END)
                self.entry_max_intentos.insert(0, "1")
                self.var_permitir_reintentos.set(True)
                self.var_habilitado.set(False)
                return

            # Cargar configuración con los tres parámetros
            duracion, cantidad, max_intentos, permitir_reintentos, habilitado = (
                cargar_config_examen(area, grado, evaluacion)
            )

            # Convertir segundos a minutos
            duracion_min = duracion // 60

            self.entry_duracion.delete(0, tk.END)
            self.entry_duracion.insert(0, str(duracion_min))

            self.entry_cantidad.delete(0, tk.END)
            self.entry_cantidad.insert(0, str(cantidad))

            self.entry_max_intentos.delete(0, tk.END)
            self.entry_max_intentos.insert(0, str(max_intentos))

            self.var_permitir_reintentos.set(bool(permitir_reintentos))
            self.var_habilitado.set(bool(habilitado))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la configuración: {e}")

    def guardar_config(self):
        """Guarda la configuración de examen con filtrado por grado+área+evaluación."""
        try:
            grado = self.combo_grado_config.get()
            area = self.combo_area.get()
            evaluacion = self.combo_evaluacion.get()

            if not grado or not area or not evaluacion:
                messagebox.showwarning(
                    "Advertencia",
                    "Debe seleccionar Grado, Área y Evaluación antes de guardar.",
                )
                return

            duracion_min = int(self.entry_duracion.get())
            cantidad = int(self.entry_cantidad.get())
            max_intentos = int(self.entry_max_intentos.get())
            permitir_reintentos = 1 if self.var_permitir_reintentos.get() else 0
            habilitado = 1 if self.var_habilitado.get() else 0

            if duracion_min <= 0 or cantidad <= 0 or max_intentos <= 0:
                messagebox.showwarning(
                    "Advertencia",
                    "Duración, cantidad e intentos deben ser mayores que 0.",
                )
                return

            duracion_seg = duracion_min * 60
            if guardar_config_examen(
                area,
                duracion_seg,
                cantidad,
                max_intentos,
                permitir_reintentos,
                grado,
                evaluacion,
                habilitado,
            ):
                reintentos_txt = "Sí" if permitir_reintentos else "No"
                habilitado_txt = "Sí" if habilitado else "No"
                messagebox.showinfo(
                    "Éxito",
                    f"Configuración guardada:\n"
                    f"- Grado: {grado}\n"
                    f"- Área: {area}\n"
                    f"- Evaluación: {evaluacion}\n"
                    f"- Duración: {duracion_min} min\n"
                    f"- Preguntas: {cantidad}\n"
                    f"- Máx. Intentos: {max_intentos}\n"
                    f"- Permitir Reintentos: {reintentos_txt}\n"
                    f"- Habilitado: {habilitado_txt}",
                )
            else:
                messagebox.showerror("Error", "No se pudo guardar la configuración.")
        except ValueError:
            messagebox.showerror("Error", "Todos los campos deben ser números enteros.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}")

    def _ajustar_columnas(self):
        try:
            ancho_total = self.tabla.winfo_width()
            if ancho_total <= 50:
                return

            # Proporciones (sum 1.0): Grado, Documento, Nombre, Area, Nota, Estado, Fecha, Duracion
            props = [0.08, 0.12, 0.30, 0.08, 0.07, 0.12, 0.13, 0.10]

            columnas = [
                "Grado",
                "Documento",
                "Nombre",
                "Area",
                "Nota",
                "Estado",
                "Fecha",
                "Duracion",
            ]
            for col, p in zip(columnas, props):
                ancho = max(50, int(ancho_total * p))
                try:
                    self.tabla.column(col, width=ancho)
                except Exception:
                    pass
        except Exception:
            pass

    def crear_tabla(self):
        """Crea el `Treeview` para el módulo docente (siempre)."""
        # Columnas: Grado | Documento | Nombre | Area | Nota | Estado | Fecha finalización | Duración
        self.tabla = ttk.Treeview(
            self.ventana,
            columns=(
                "Grado",
                "Documento",
                "Nombre",
                "Area",
                "Nota",
                "Estado",
                "Fecha",
                "Duracion",
            ),
            show="headings",
        )

        self.tabla.heading("Grado", text="Grado")
        self.tabla.heading("Documento", text="Documento")
        self.tabla.heading("Nombre", text="Nombre")
        self.tabla.heading("Area", text="Area")
        self.tabla.heading("Nota", text="Nota")
        self.tabla.heading("Estado", text="Estado")
        self.tabla.heading("Fecha", text="Fecha finalización")
        self.tabla.heading("Duracion", text="Duración prueba")

        self.tabla.pack(fill="both", expand=True, padx=20, pady=0)

        # Permitir que las columnas se estiren y ajustar al cambiar tamaño
        self.tabla.column("Grado", stretch=True)
        self.tabla.column("Documento", stretch=True)
        self.tabla.column("Nombre", stretch=True)
        self.tabla.column("Area", stretch=True)
        self.tabla.column("Nota", stretch=True)
        self.tabla.column("Estado", stretch=True)
        self.tabla.column("Fecha", stretch=True)
        self.tabla.column("Duracion", stretch=True)

        # Ajuste dinámico de anchos cuando se redimensiona la ventana
        try:
            self.ventana.bind("<Configure>", lambda e: self._ajustar_columnas())
        except Exception:
            pass

        # Configurar estilos modernos por estado
        try:
            self.tabla.tag_configure(
                "finalizado", background="#e6ffed"
            )  # verde muy claro
            self.tabla.tag_configure(
                "en_proceso", background="#fff9f0"
            )  # naranja muy claro
        except Exception:
            pass

    def reset_selected(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning(
                "Advertencia", "Seleccione un registro para resetear la nota."
            )
            return

        item = sel[0]
        # la columna Documento está en el índice 1 (Grado, Documento, Nombre, ...)
        documento = self.tabla.item(item, "values")[1]

        pregunta = f"¿Desea resetear la nota del documento {documento}?"
        if messagebox.askyesno("Confirmar", pregunta):
            vals = self.tabla.item(item, "values")
            area_sel = vals[3] if len(vals) > 3 else None

            try:
                ok = resetear_examen(documento, area_sel)
            except Exception as e:
                # Mostrar error detallado si la función lanza excepción
                messagebox.showerror(
                    "Error", f"No se pudo resetear la nota (error interno): {e}"
                )
                return

            if ok:
                messagebox.showinfo(
                    "Éxito", "Intento(s) y respuestas eliminadas correctamente."
                )
                try:
                    self.cargar_datos()
                except Exception:
                    pass
                return

            # Fallback: intentar eliminar directamente desde la BD y mostrar el error si falla
            try:
                with sqlite3.connect(DB_FILE) as conn:
                    cur = conn.cursor()
                    if area_sel:
                        cur.execute(
                            "DELETE FROM respuestas_estudiantes WHERE documento = ? AND area = ?",
                            (documento, area_sel),
                        )
                        cur.execute(
                            "DELETE FROM resultados WHERE documento = ? AND area = ?",
                            (documento, area_sel),
                        )
                    else:
                        cur.execute(
                            "DELETE FROM respuestas_estudiantes WHERE documento = ?",
                            (documento,),
                        )
                        cur.execute(
                            "DELETE FROM resultados WHERE documento = ?", (documento,)
                        )
                    conn.commit()

                messagebox.showinfo(
                    "Éxito",
                    "Intento(s) y respuestas eliminadas correctamente (fallback).",
                )
                try:
                    self.cargar_datos()
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror(
                    "Error", f"No se pudo eliminar intentos/respuestas: {e}"
                )

    def autorizar_revision_selected(self):
        """Autoriza la revisión del estudiante seleccionado (último intento por área)."""
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning(
                "Advertencia", "Seleccione un registro para autorizar la revisión."
            )
            return

        item = sel[0]
        vals = self.tabla.item(item, "values")
        documento = vals[1] if len(vals) > 1 else None
        area_sel = vals[3] if len(vals) > 3 else None

        if not documento:
            messagebox.showerror(
                "Error", "No se pudo determinar el documento del registro seleccionado."
            )
            return

        try:
            # Si hay un área, autorizar solo esa área; si no, autorizar todas las áreas finalizadas
            if area_sel:
                autorizar_revision(documento, area_sel)
                messagebox.showinfo(
                    "Éxito", f"Revisión autorizada para {documento} en {area_sel}."
                )
            else:
                autorizar_revision(documento)
                messagebox.showinfo(
                    "Éxito",
                    f"Revisión autorizada para {documento} (todas las áreas finalizadas).",
                )
            self.cargar_datos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo autorizar la revisión: {e}")

    def ver_detalle_selected(self):
        """Muestra el detalle de respuestas del estudiante seleccionado usando la tabla `respuestas_estudiantes`."""
        sel = self.tabla.selection()
        if not sel:
            messagebox.showwarning(
                "Advertencia", "Seleccione un registro para ver el detalle."
            )
            return

        item = sel[0]
        vals = self.tabla.item(item, "values")
        documento = vals[1]
        area = vals[3] if len(vals) > 3 else None

        try:
            # Obtener último intento finalizado/presentado para ese documento/area
            intento_val = None
            with sqlite3.connect(DB_FILE) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT intento FROM resultados WHERE documento = ? AND area = ? AND estado_examen IN ('FINALIZADO','PRESENTADO') ORDER BY id DESC LIMIT 1",
                    (documento, area),
                )
                fila = cur.fetchone()
                if fila:
                    intento_val = fila[0]

            respuestas = obtener_respuestas_estudiante(
                documento, area=area, intento=intento_val
            )

            if not respuestas:
                messagebox.showwarning(
                    "Sin datos",
                    f"No se encontraron respuestas guardadas para {documento} en {area} (intento {intento_val}).",
                )
                return

            # Mostrar ventana con detalle
            ventana_det = tk.Tk()
            ventana_det.title(f"Detalle - {documento} • {area}")
            ventana_det.geometry("900x600")

            tk.Label(
                ventana_det,
                text=f"Detalle de Respuestas - Documento: {documento}  Área: {area}  Intento: {intento_val}",
                font=("Segoe UI", 12, "bold"),
            ).pack(pady=8)

            canvas_frame = tk.Frame(ventana_det)
            canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
            canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
            scrollbar = tk.Scrollbar(
                canvas_frame, orient="vertical", command=canvas.yview
            )
            scrollable = tk.Frame(canvas, bg="white")

            scrollable.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
            )
            canvas.create_window((0, 0), window=scrollable, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            for idx, r in enumerate(respuestas, 1):
                qf = tk.Frame(scrollable, bg="#f9f9f9", relief="solid", borderwidth=1)
                qf.pack(fill="x", padx=8, pady=6)

                enun = r.get("enunciado", f"Pregunta {r.get('pregunta_id', idx)}")
                seleccion = r.get(
                    "respuesta_seleccionada_texto", r.get("respuesta_seleccionada", "")
                )
                correcta = r.get(
                    "respuesta_correcta_texto", r.get("respuesta_correcta", "")
                )
                letra_sel = r.get("respuesta_seleccionada", "").strip().upper()
                es_corr = r.get("es_correcta", 0)

                tk.Label(
                    qf,
                    text=f"Pregunta {idx}: {enun}",
                    font=("Segoe UI", 10, "bold"),
                    bg="#f9f9f9",
                    wraplength=800,
                    justify="left",
                ).pack(anchor="w", padx=10, pady=6)

                # Imagen si existe (campo no obligatorio)
                try:
                    if r.get("imagen"):
                        ruta_im = BASE_DIR / "imagenes_preguntas" / str(r.get("imagen"))
                        if ruta_im.exists():
                            img = Image.open(ruta_im)
                            max_an = 500
                            w, h = img.size
                            if w > max_an:
                                ratio = max_an / float(w)
                                img = img.resize((int(w * ratio), int(h * ratio)))
                            img_tk = ImageTk.PhotoImage(img)
                            lbl = tk.Label(qf, image=img_tk, bg="#f9f9f9")
                            lbl.image = img_tk
                            lbl.pack(anchor="w", padx=10, pady=(0, 6))
                except Exception:
                    pass

                tk.Label(
                    qf,
                    text=f"Tu respuesta: {letra_sel} - {seleccion}",
                    font=("Segoe UI", 10),
                    bg="#f9f9f9",
                ).pack(anchor="w", padx=20)
                tk.Label(
                    qf,
                    text=f"Respuesta correcta: {correcta}",
                    font=("Segoe UI", 10),
                    bg="#f9f9f9",
                    fg="#0078D7",
                ).pack(anchor="w", padx=20, pady=(0, 6))

                estado_text = "Correcta ✅" if es_corr else "Incorrecta ❌"
                tk.Label(
                    qf,
                    text=estado_text,
                    font=("Segoe UI", 10, "bold"),
                    bg="#f9f9f9",
                    fg="#51cf66" if es_corr else "#ff6b6b",
                ).pack(anchor="w", padx=20, pady=(0, 8))

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            tk.Button(
                ventana_det, text="Cerrar", command=ventana_det.destroy, width=20
            ).pack(pady=8)
            ventana_det.mainloop()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener detalle: {e}")

    def exportar_excel(self):
        try:
            # Validar que el usuario haya seleccionado primero Grado y luego Área
            grado_sel = None
            try:
                g = self.combo_grado.get()
                if g and g.strip() != "":
                    grado_sel = g.strip()
            except Exception:
                grado_sel = None

            area_sel = None
            try:
                a = self.combo_area.get()
                if a and a.strip() != "":
                    area_sel = a.strip()
            except Exception:
                area_sel = None

            if not grado_sel:
                messagebox.showwarning(
                    "Filtro requerido", "Seleccione primero el Grado antes de exportar."
                )
                return

            if not area_sel:
                messagebox.showwarning(
                    "Filtro requerido", "Seleccione el Área después de elegir el Grado."
                )
                return

            # Construir consulta según filtros. La exportación completa solo se permite
            # si el usuario selecciona explícitamente "Todos" en los filtros.
            base_query = "SELECT grado, documento, nombre, area, nota, estado_examen, hora_inicio, hora_fin FROM resultados"
            order_clause = " ORDER BY COALESCE(hora_fin, hora_inicio) DESC"

            params = ()
            if grado_sel == "Todos" and area_sel == "Todos":
                query = base_query + order_clause
            elif grado_sel != "Todos" and area_sel == "Todos":
                query = base_query + " WHERE grado = ?" + order_clause
                params = (grado_sel,)
            elif grado_sel == "Todos" and area_sel != "Todos":
                query = base_query + " WHERE area = ?" + order_clause
                params = (area_sel,)
            else:
                # ambos específicos
                query = base_query + " WHERE grado = ? AND area = ?" + order_clause
                params = (grado_sel, area_sel)

            ruta = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")],
                initialfile="resultados_export.xlsx",
            )
            if not ruta:
                return

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(query, params)
            filas = cursor.fetchall()
            conn.close()

            rows = []
            for fila in filas:
                (
                    grado_db,
                    documento,
                    nombre,
                    area,
                    nota,
                    estado,
                    hora_inicio,
                    hora_fin,
                ) = fila
                fecha = hora_fin if hora_fin is not None else hora_inicio
                duracion = ""
                try:
                    if hora_inicio and hora_fin:
                        hi = datetime.strptime(hora_inicio, "%Y-%m-%d %H:%M:%S")
                        hf = datetime.strptime(hora_fin, "%Y-%m-%d %H:%M:%S")
                        delta = hf - hi
                        total_seconds = int(delta.total_seconds())
                        horas = total_seconds // 3600
                        minutos = (total_seconds % 3600) // 60
                        segundos = total_seconds % 60
                        duracion = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                    elif hora_inicio and not hora_fin:
                        duracion = "EN_PROCESO"
                except Exception:
                    duracion = ""

                # Intentar obtener grado oficial desde estudiantes.xlsx
                try:
                    estudiante = validar_estudiante(documento)
                    grado_oficial = None
                    if estudiante is not None:
                        if "grado" in estudiante.index:
                            grado_oficial = estudiante["grado"]
                        elif "Grado" in estudiante.index:
                            grado_oficial = estudiante["Grado"]

                    if grado_oficial is not None and not pd.isna(grado_oficial):
                        grado = str(grado_oficial).strip()
                    else:
                        grado = str(grado_db) if grado_db is not None else ""
                except Exception:
                    grado = str(grado_db) if grado_db is not None else ""

                rows.append(
                    (grado, documento, nombre, area, nota, estado, fecha, duracion)
                )

            df = pd.DataFrame(
                rows,
                columns=[
                    "grado",
                    "documento",
                    "nombre",
                    "area",
                    "nota",
                    "estado",
                    "fecha",
                    "duracion",
                ],
            )
            df.to_excel(ruta, index=False)
            messagebox.showinfo("Exportado", f"Resultados exportados a {ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")


def abrir_docente(nombre):
    ventana_docente = tk.Tk()
    # Maximizar la ventana al abrir (Windows: 'zoomed')
    try:
        ventana_docente.state("zoomed")
    except Exception:
        # Fallback a pantalla completa si 'zoomed' no está disponible
        try:
            ventana_docente.attributes("-fullscreen", True)
        except Exception:
            pass

    ModuloDocente(ventana_docente, nombre)
    ventana_docente.mainloop()


# ================= MÓDULO ESTUDIANTE =================


class ModuloEstudiante:

    def __init__(self, ventana, documento, nombre, grado):
        self.ventana = ventana
        self.documento = documento
        self.nombre = nombre
        self.grado = grado
        self.current_intento_id = None

        self.ventana.title("Panel del Estudiante")
        self.ventana.configure(bg=COLOR_SECUNDARIO)

        header = tk.Frame(self.ventana, bg=COLOR_PRIMARIO, height=100)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"👤 {nombre.title()}",
            font=("Segoe UI", 16, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
        ).pack(anchor="w", padx=20, pady=(15, 5))

        tk.Label(
            header,
            text=f"Grado {grado} • Mis Exámenes",
            font=("Segoe UI", 11),
            bg=COLOR_PRIMARIO,
            fg="#e0e0ff",
        ).pack(anchor="w", padx=20)

        # Barra de acciones (historial)
        acciones_frame = tk.Frame(self.ventana, bg=COLOR_SECUNDARIO)
        acciones_frame.pack(fill="x", padx=20, pady=(8, 4))

        tk.Button(
            acciones_frame,
            text="📋 Ver Historial de Calificaciones",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
            relief="flat",
            cursor="hand2",
            command=self._mostrar_historial,
        ).pack(side="left")

        self.contenido = tk.Frame(self.ventana, bg=COLOR_SECUNDARIO)
        self.contenido.pack(fill="both", expand=True)

        self._mostrar_areas()

    # ---------------------------------------------------

    def _mostrar_areas(self):
        for w in self.contenido.winfo_children():
            w.destroy()

        areas = cargar_areas()

        def on_area_click(a):
            estado_info = obtener_estado_area(self.documento, a)
            if estado_info is None or estado_info[0] == "DISPONIBLE":
                self._iniciar_examen(a)
            elif estado_info[0] == "PRESENTADO":
                nota = estado_info[1]
                messagebox.showinfo(
                    "Area presentada",
                    f"Ya presentaste esta área.\nNota: {nota}\nEl docente no ha autorizado la revisión.",
                )
            elif estado_info[0] == "REVISION_ACTIVA":
                self._ver_resultado(a)
            else:
                self._iniciar_examen(a)

        # Canvas con scroll para las áreas
        canvas = tk.Canvas(self.contenido, bg=COLOR_SECUNDARIO, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            self.contenido, orient="vertical", command=canvas.yview
        )
        frame_areas = tk.Frame(canvas, bg=COLOR_SECUNDARIO)

        frame_areas.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame_areas, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Permitir scroll con rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Crear botones de áreas con colores según estado
        for area in areas:
            estado_info = obtener_estado_area(self.documento, area)

            # Determinar color según estado
            if estado_info is None or estado_info[0] == "DISPONIBLE":
                color_bg = "#51cf66"  # Verde - disponible
                texto_estado = "📖 Disponible"
                icono = "✓"
            elif estado_info[0] == "REVISION_ACTIVA":
                color_bg = "#0078D7"  # Azul - revisión activa
                texto_estado = "📖 Revisar"
                icono = "👁"
            else:  # PRESENTADO
                color_bg = "#999999"  # Gris - presentado sin revisar
                texto_estado = "📖 Presentado"
                icono = "✗"
                nota = estado_info[1] if estado_info else "N/A"

            frame_btn = tk.Frame(frame_areas, bg=COLOR_SECUNDARIO)
            frame_btn.pack(fill="x", padx=20, pady=10)

            if estado_info and estado_info[0] == "PRESENTADO":
                nota = estado_info[1]
                btn_text = f"{icono} {area.upper()} - Nota: {nota}"
            else:
                btn_text = f"{icono} {area.upper()}"

            tk.Button(
                frame_btn,
                text=btn_text,
                font=("Segoe UI", 11, "bold"),
                bg=color_bg,
                fg="white",
                relief="flat",
                padx=15,
                pady=12,
                cursor="hand2",
                command=lambda a=area: on_area_click(a),
            ).pack(fill="x")

    # ---------------------------------------------------
    def _mostrar_historial(self):
        """Muestra el historial de calificaciones dentro del mismo módulo (no nueva ventana)."""
        for w in self.contenido.winfo_children():
            w.destroy()

        header = tk.Frame(self.contenido, bg=COLOR_PRIMARIO)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"📋 Historial de Calificaciones - {self.nombre.title()}",
            font=("Segoe UI", 14, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
        ).pack(side="left", padx=20, pady=10)

        tk.Button(
            header,
            text="← Volver",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            relief="flat",
            cursor="hand2",
            command=self._mostrar_areas,
        ).pack(side="right", padx=12, pady=10)

        # Canvas con scroll para el historial
        canvas = tk.Canvas(self.contenido, bg=COLOR_SECUNDARIO, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            self.contenido, orient="vertical", command=canvas.yview
        )
        frame_scroll = tk.Frame(canvas, bg=COLOR_SECUNDARIO)

        frame_scroll.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame_scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Obtener registros desde la BD
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, area, intento, nota, estado_examen, hora_fin, puede_revisar
                FROM resultados
                WHERE documento = ?
                ORDER BY id DESC
            """,
                (self.documento,),
            )
            registros = cur.fetchall()
            conn.close()
        except Exception:
            registros = []

        if not registros:
            tk.Label(
                frame_scroll,
                text="No se encontraron intentos de examen.",
                bg=COLOR_SECUNDARIO,
                font=("Segoe UI", 11),
            ).pack(pady=20)
            return

        for _id, area, intento, nota, estado, hora_fin, puede_rev in registros:
            fila = tk.Frame(frame_scroll, bg="#f9f9f9", bd=1, relief="solid")
            fila.pack(fill="x", padx=12, pady=8)

            info_txt = f"Área: {area}  •  Intento: {intento}  •  Nota: {nota}  •  Estado: {estado}"
            tk.Label(
                fila,
                text=info_txt,
                bg="#f9f9f9",
                font=("Segoe UI", 10, "bold"),
                anchor="w",
                justify="left",
            ).pack(fill="x", padx=10, pady=(8, 4))

            fecha_txt = hora_fin if hora_fin is not None else "(sin finalizar)"
            tk.Label(
                fila,
                text=f"Fecha de finalización: {fecha_txt}",
                bg="#f9f9f9",
                font=("Segoe UI", 10),
            ).pack(anchor="w", padx=10, pady=(0, 8))

            # Mostrar botón "Ver Detalle" sólo si FINALIZADO y puede_revisar == 1
            if str(estado).upper() == "FINALIZADO" and int(puede_rev or 0) == 1:
                tk.Button(
                    fila,
                    text="👁 Ver Detalle",
                    font=("Segoe UI", 10),
                    bg=COLOR_PRIMARIO,
                    fg="white",
                    relief="flat",
                    cursor="hand2",
                    command=lambda a=area, i=intento: self._mostrar_detalle(a, i),
                ).pack(side="right", padx=10, pady=8)
            elif str(estado).upper() == "FINALIZADO":
                tk.Label(
                    fila,
                    text="⏳ El docente aún no ha autorizado la revisión.",
                    bg="#f9f9f9",
                    font=("Segoe UI", 10, "italic"),
                    fg="#666666",
                ).pack(side="right", padx=10, pady=8)

    def _mostrar_detalle(self, area, intento):
        """Muestra el detalle de un intento (preguntas y respuestas) dentro del mismo módulo."""
        # Verificar permiso global (no permitir si no está autorizado)
        try:
            if not puede_revisar(self.documento):
                messagebox.showinfo(
                    "Revisión no autorizada",
                    "⏳ El docente aún no ha autorizado la revisión.",
                )
                return
        except Exception:
            # En caso de error conservador, denegar acceso
            messagebox.showinfo(
                "Revisión no autorizada",
                "⏳ El docente aún no ha autorizado la revisión.",
            )
            return

        respuestas = obtener_respuestas_estudiante(
            self.documento, area=area, intento=intento
        )

        for w in self.contenido.winfo_children():
            w.destroy()

        header = tk.Frame(self.contenido, bg=COLOR_PRIMARIO)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"Detalle - {area} (Intento {intento})",
            font=("Segoe UI", 14, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
        ).pack(side="left", padx=20, pady=10)

        tk.Button(
            header,
            text="← Volver al Historial",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            relief="flat",
            cursor="hand2",
            command=self._mostrar_historial,
        ).pack(side="right", padx=12, pady=10)

        canvas = tk.Canvas(self.contenido, bg=COLOR_SECUNDARIO, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            self.contenido, orient="vertical", command=canvas.yview
        )
        frame_scroll = tk.Frame(canvas, bg=COLOR_SECUNDARIO)

        frame_scroll.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame_scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not respuestas:
            tk.Label(
                frame_scroll,
                text="No hay detalles de respuestas para este intento.",
                bg=COLOR_SECUNDARIO,
            ).pack(pady=20)
            return

        for idx, r in enumerate(respuestas, start=1):
            qf = tk.Frame(frame_scroll, bg="#ffffff", bd=1, relief="solid")
            qf.pack(fill="x", padx=12, pady=8)

            enun = r.get("enunciado", "")
            tk.Label(
                qf,
                text=f"{idx}. {enun}",
                font=("Segoe UI", 11, "bold"),
                bg="#ffffff",
                wraplength=900,
                justify="left",
            ).pack(fill="x", padx=10, pady=(8, 6))

            # Imagen si existe
            try:
                imagen = r.get("imagen")
                if imagen:
                    ruta = BASE_DIR / "imagenes_preguntas" / str(imagen)
                    if ruta.exists():
                        img = Image.open(ruta)
                        max_ancho = 800
                        w, h = img.size
                        if w > max_ancho:
                            ratio = max_ancho / float(w)
                            img = img.resize(
                                (int(w * ratio), int(h * ratio)), Image.LANCZOS
                            )
                        img_tk = ImageTk.PhotoImage(img)
                        lbl_im = tk.Label(qf, image=img_tk, bg="#ffffff")
                        lbl_im.image = img_tk
                        lbl_im.pack(padx=10, pady=(0, 8))
            except Exception:
                pass

            seleccion = r.get(
                "respuesta_seleccionada_texto", r.get("respuesta_seleccionada", "")
            )
            correcta = r.get(
                "respuesta_correcta_texto", r.get("respuesta_correcta", "")
            )
            letra_sel = r.get("respuesta_seleccionada", "").strip().upper()
            es_corr = bool(r.get("es_correcta", False))

            tk.Label(
                qf,
                text=f"Tu respuesta: {letra_sel} - {seleccion}",
                font=("Segoe UI", 10),
                bg="#ffffff",
            ).pack(anchor="w", padx=12)

            tk.Label(
                qf,
                text=f"Respuesta correcta: {correcta}",
                font=("Segoe UI", 10),
                bg="#ffffff",
            ).pack(anchor="w", padx=12, pady=(0, 6))

            estado_text = "✅ Correcta" if es_corr else "❌ Incorrecta"
            tk.Label(
                qf,
                text=estado_text,
                font=("Segoe UI", 10, "bold"),
                bg="#ffffff",
                fg=("#2b8a3e" if es_corr else "#d9534f"),
            ).pack(anchor="w", padx=12, pady=(0, 8))

    # ---------------------------------------------------

    def _obtener_examen_en_proceso(self, area):
        """Verifica si hay un examen EN_PROCESO para este estudiante y área.
        Retorna: (intento_num, intento_id, respuestas_guardadas) o None si no existe.
        """
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Buscar registro EN_PROCESO más reciente
            cursor.execute(
                """
                SELECT intento, id FROM resultados 
                WHERE documento = ? AND area = ? AND estado_examen = 'EN_PROCESO'
                ORDER BY id DESC LIMIT 1
                """,
                (self.documento, area),
            )
            resultado = cursor.fetchone()

            if not resultado:
                conn.close()
                return None

            intento_num, intento_id = resultado

            # Contar respuestas guardadas para determinar última pregunta respondida
            cursor.execute(
                """
                SELECT COUNT(*) FROM respuestas_estudiantes 
                WHERE documento = ? AND area = ? AND intento = ?
                """,
                (self.documento, area, intento_num),
            )
            respuestas_guardadas = cursor.fetchone()[0]
            conn.close()

            return (intento_num, intento_id, respuestas_guardadas)
        except Exception as e:
            print(f"[ERROR] _obtener_examen_en_proceso: {e}")
            return None

    def _iniciar_examen(self, area):
        estado_info = obtener_estado_area(self.documento, area)

        # Verificar que al menos una evaluación esté habilitada para este grado+área
        examen_habilitado = False
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            # Convertir a TEXT para evitar problemas de tipo de datos
            cursor.execute(
                "SELECT COUNT(*) FROM config_examenes WHERE CAST(grado AS TEXT) = ? AND CAST(area AS TEXT) = ? AND habilitado = 1",
                (str(self.grado), str(area)),
            )
            resultado = cursor.fetchone()
            conn.close()

            if resultado and resultado[0] > 0:
                examen_habilitado = True

        except Exception as e:
            # Si hay error, permitir continuar (retrocompatibilidad)
            pass

        if not examen_habilitado:
            messagebox.showwarning(
                "Examen no disponible",
                f"El examen de {area} aún no ha sido habilitado por el docente.",
            )
            return

        # Cargar configuración (usar la primera evaluación habilitada)
        evaluacion = None
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            # Buscar primero la configuración habilitada para este grado+area
            cursor.execute(
                "SELECT evaluacion, duracion_segundos, cantidad_preguntas, COALESCE(max_intentos, 1), COALESCE(permitir_reintentos, 1) FROM config_examenes WHERE CAST(grado AS TEXT) = ? AND CAST(area AS TEXT) = ? AND habilitado = 1 LIMIT 1",
                (str(self.grado), str(area)),
            )
            resultado = cursor.fetchone()
            conn.close()

            if resultado:
                evaluacion, duracion, cantidad, max_intentos, permitir_reintentos = (
                    resultado
                )
            else:
                # Retrocompatibilidad: usar valores por defecto
                duracion_result = cargar_config_examen(area)
                if isinstance(duracion_result, tuple) and len(duracion_result) >= 4:
                    duracion, cantidad, max_intentos, permitir_reintentos = (
                        duracion_result[:4]
                    )
                else:
                    duracion, cantidad, max_intentos, permitir_reintentos = (
                        120,
                        10,
                        1,
                        1,
                    )
        except Exception:
            duracion_result = cargar_config_examen(area)
            if isinstance(duracion_result, tuple) and len(duracion_result) >= 4:
                duracion, cantidad, max_intentos, permitir_reintentos = duracion_result[
                    :4
                ]
            else:
                duracion, cantidad, max_intentos, permitir_reintentos = 120, 10, 1, 1

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM resultados WHERE documento=? AND area=? AND estado_examen IN ('FINALIZADO','PRESENTADO')",
            (self.documento, area),
        )
        intentos_previos = cursor.fetchone()[0]
        conn.close()

        if estado_info and estado_info[0] in ["PRESENTADO", "REVISION_ACTIVA"]:
            if not permitir_reintentos or intentos_previos >= max_intentos:
                messagebox.showwarning(
                    "No disponible", "Ya alcanzaste el límite de intentos."
                )
                return

        # ============ VERIFICAR SI EXISTE EXAMEN EN_PROCESO (REANUDACIÓN) ============
        examen_reanudado = self._obtener_examen_en_proceso(area)

        if examen_reanudado:
            # Examen interrumpido encontrado - reanudarlo
            intento_num, intento_id, respuestas_guardadas = examen_reanudado
            self.current_intento_id = intento_id
            self.current_intento_num = intento_num
            es_reanudacion = True
            indice_inicial = respuestas_guardadas
        else:
            # Nuevo examen
            intento_num, intento_id = registrar_inicio(
                self.documento, self.nombre, self.grado, area
            )
            self.current_intento_id = intento_id
            self.current_intento_num = intento_num
            es_reanudacion = False
            indice_inicial = 0

        self._mostrar_pantalla_informativa(
            area, cantidad, duracion, evaluacion, es_reanudacion, indice_inicial
        )

    # ---------------------------------------------------

    def _mostrar_pantalla_informativa(
        self,
        area,
        cantidad_preguntas,
        duracion_segundos,
        evaluacion=None,
        es_reanudacion=False,
        indice_inicial=0,
    ):
        """Muestra pantalla informativa previa al examen con instrucciones y requisitos."""
        for w in self.contenido.winfo_children():
            w.destroy()

        # Activar pantalla completa
        try:
            self.ventana.state("zoomed")
        except Exception:
            try:
                self.ventana.attributes("-fullscreen", True)
            except Exception:
                pass

        # Convertir duración de segundos a minutos
        minutos = duracion_segundos // 60

        # Frame principal con scrollbar
        canvas = tk.Canvas(self.contenido, bg=COLOR_SECUNDARIO, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            self.contenido, orient="vertical", command=canvas.yview
        )
        frame_scroll = tk.Frame(canvas, bg=COLOR_SECUNDARIO)

        frame_scroll.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame_scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Título
        tk.Label(
            frame_scroll,
            text=f"📋 Información del Examen - {area.upper()}",
            font=("Segoe UI", 18, "bold"),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_PRIMARIO,
        ).pack(pady=30, padx=30)

        # Información general del examen
        info_frame = tk.Frame(frame_scroll, bg="white", relief="solid", borderwidth=1)
        info_frame.pack(fill="x", padx=40, pady=20)

        info_items = [
            ("Total de preguntas:", str(cantidad_preguntas)),
            ("Tiempo disponible:", f"{minutos} minutos"),
            ("Área de evaluación:", area.upper()),
            ("Documento:", self.documento),
            ("Nombre:", self.nombre.title()),
        ]

        for label_text, value_text in info_items:
            item_frame = tk.Frame(info_frame, bg="white")
            item_frame.pack(fill="x", padx=15, pady=10)

            tk.Label(
                item_frame,
                text=label_text,
                font=("Segoe UI", 11, "bold"),
                bg="white",
                fg=COLOR_PRIMARIO,
                anchor="w",
            ).pack(side="left", padx=5)

            tk.Label(
                item_frame,
                text=value_text,
                font=("Segoe UI", 11),
                bg="white",
                fg=COLOR_TEXTO,
                anchor="w",
            ).pack(side="left", padx=5, fill="x", expand=True)

        # Instrucciones
        tk.Label(
            frame_scroll,
            text="📌 Instrucciones Importantes",
            font=("Segoe UI", 14, "bold"),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_PRIMARIO,
        ).pack(pady=(30, 15), padx=30, anchor="w")

        instrucciones_frame = tk.Frame(
            frame_scroll, bg="#f9f9f9", relief="solid", borderwidth=1
        )
        instrucciones_frame.pack(fill="x", padx=40, pady=10)

        instrucciones = [
            "1. Lee cuidadosamente cada pregunta y todas las opciones de respuesta.",
            "2. Selecciona una única opción (A, B, C o D) para cada pregunta.",
            "3. El tiempo comienza cuando hagas clic en 'Comenzar Examen'.",
            "4. Responde el máximo número de preguntas antes de que se agote el tiempo.",
            "5. Al finalizar, se guardará tu calificación automáticamente.",
        ]

        for instruccion in instrucciones:
            tk.Label(
                instrucciones_frame,
                text=instruccion,
                font=("Segoe UI", 10),
                bg="#f9f9f9",
                fg=COLOR_TEXTO,
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=15, pady=8, anchor="w")

        # Restricciones
        tk.Label(
            frame_scroll,
            text="⚠️  Restricciones del Examen",
            font=("Segoe UI", 14, "bold"),
            bg=COLOR_SECUNDARIO,
            fg="#ff6b6b",
        ).pack(pady=(30, 15), padx=30, anchor="w")

        restricciones_frame = tk.Frame(
            frame_scroll, bg="#fff3f3", relief="solid", borderwidth=1
        )
        restricciones_frame.pack(fill="x", padx=40, pady=10)

        restricciones = [
            "❌ NO puedes retroceder a preguntas anteriores.",
            "❌ NO puedes cambiar de respuesta una vez avanzado.",
            "❌ NO puedes repetir el examen sin autorización del docente.",
            "⏱️  El tiempo se descontará automáticamente durante el examen.",
        ]

        for restriccion in restricciones:
            tk.Label(
                restricciones_frame,
                text=restriccion,
                font=("Segoe UI", 10),
                bg="#fff3f3",
                fg=COLOR_TEXTO,
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=15, pady=8, anchor="w")

        # Mensaje de reanudación si aplica
        if es_reanudacion:
            reanudacion_frame = tk.Frame(
                frame_scroll, bg="#e6f3ff", relief="solid", borderwidth=1
            )
            reanudacion_frame.pack(fill="x", padx=40, pady=15)

            tk.Label(
                reanudacion_frame,
                text="🔄 Se ha detectado un examen incompleto",
                font=("Segoe UI", 11, "bold"),
                bg="#e6f3ff",
                fg="#0066cc",
                anchor="w",
            ).pack(fill="x", padx=15, pady=(8, 4), anchor="w")

            tk.Label(
                reanudacion_frame,
                text=f"Continuarás desde la pregunta {indice_inicial + 1}. Tus respuestas anteriores han sido guardadas.",
                font=("Segoe UI", 10),
                bg="#e6f3ff",
                fg=COLOR_TEXTO,
                anchor="w",
                justify="left",
                wraplength=600,
            ).pack(fill="x", padx=15, pady=(0, 8), anchor="w")

        # Espacio en blanco
        tk.Label(frame_scroll, text="", bg=COLOR_SECUNDARIO).pack(pady=10)

        # Botones
        botones_frame = tk.Frame(frame_scroll, bg=COLOR_SECUNDARIO)
        botones_frame.pack(pady=30)

        tk.Button(
            botones_frame,
            text="🚀 Comenzar Examen",
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
            relief="flat",
            padx=25,
            pady=12,
            cursor="hand2",
            command=lambda: self._mostrar_examen(
                area,
                cantidad_preguntas,
                duracion_segundos,
                evaluacion,
                es_reanudacion,
                indice_inicial,
            ),
        ).pack(side="left", padx=10)

        tk.Button(
            botones_frame,
            text="❌ Cancelar",
            font=("Segoe UI", 12, "bold"),
            bg="#ff6b6b",
            fg="white",
            relief="flat",
            padx=25,
            pady=12,
            cursor="hand2",
            command=self._mostrar_areas,
        ).pack(side="left", padx=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ---------------------------------------------------

    def _mostrar_examen(
        self,
        area,
        cantidad_preguntas,
        duracion_segundos,
        evaluacion=None,
        es_reanudacion=False,
        indice_inicial=0,
    ):
        for w in self.contenido.winfo_children():
            w.destroy()

        todas = cargar_preguntas_filtradas(
            area=area, grado=self.grado, evaluacion=evaluacion
        )

        if todas.empty:
            messagebox.showwarning(
                "Sin preguntas",
                f"No hay preguntas configuradas para el área '{area}'.\n\nVerifica que:\n"
                f"• El archivo 'preguntas.xlsx' exista\n"
                f"• Tenga preguntas para el área '{area}'\n"
                f"• Las columnas estén correctamente configuradas",
            )
            self._mostrar_areas()
            return

        preguntas = todas.head(cantidad_preguntas).reset_index(drop=True)

        contador = {
            "indice": int(
                indice_inicial
            ),  # Comenzar desde la última pregunta respondida
            "correctas": 0,
            "tiempo": int(duracion_segundos),
            "timer_id": None,
        }
        respuestas = []

        # ============ RECUPERAR CORRECTAS PREVIAS SI ES REANUDACIÓN ============
        if es_reanudacion and indice_inicial > 0:
            try:
                conn_anterior = sqlite3.connect(DB_FILE)
                cursor_anterior = conn_anterior.cursor()
                cursor_anterior.execute(
                    """
                    SELECT COUNT(*) FROM respuestas_estudiantes 
                    WHERE documento = ? AND area = ? AND intento = ? AND es_correcta = 1
                    """,
                    (self.documento, area, self.current_intento_num),
                )
                resultado = cursor_anterior.fetchone()
                if resultado:
                    contador["correctas"] = resultado[0]
                conn_anterior.close()
            except Exception as e:
                print(f"[INFO] No se pudieron recuperar correctas previas: {e}")

        # Mostrar mensaje de reanudación si aplica
        if es_reanudacion:
            messagebox.showinfo(
                "Examen Reanudado",
                f"✅ Se ha reanudado tu examen.\n\n"
                f"Continuarás desde la pregunta {indice_inicial + 1} de {len(preguntas)}.\n"
                f"Tus respuestas anteriores han sido guardadas y recuperadas.",
            )

        # ================ HEADER =================
        header = tk.Frame(self.contenido, bg=COLOR_PRIMARIO)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"Examen - {area}",
            font=("Segoe UI", 14, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
        ).pack(side="left", padx=20, pady=10)

        label_timer = tk.Label(
            header,
            text="Tiempo: 00:00",
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_PRIMARIO,
            fg="yellow",
        )
        label_timer.pack(side="right", padx=20)

        progreso = ttk.Progressbar(
            header, length=300, mode="determinate", maximum=len(preguntas)
        )
        progreso.pack(side="right", padx=10, pady=10)

        # indicador textual de la pregunta actual (pregunta x de total)
        label_pregunta = tk.Label(
            header,
            text=f"Pregunta 1 de {len(preguntas)}",
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
        )
        label_pregunta.pack(side="right", padx=10)

        # ================ SCROLL AREA =================
        canvas = tk.Canvas(self.contenido, bg=COLOR_SECUNDARIO, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            self.contenido, orient="vertical", command=canvas.yview
        )
        frame_scroll = tk.Frame(canvas, bg=COLOR_SECUNDARIO)

        frame_scroll.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame_scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # ================= CONTENIDO (IMAGEN antes CONTEXTO) =================
        label_imagen = tk.Label(frame_scroll, bg=COLOR_SECUNDARIO)
        label_imagen.pack(pady=10)

        label_contexto = tk.Label(
            frame_scroll,
            text="",
            wraplength=900,
            justify="left",
            font=("Segoe UI", 12),
            bg=COLOR_SECUNDARIO,
        )
        label_contexto.pack(pady=10, padx=30)

        label_enunciado = tk.Label(
            frame_scroll,
            text="",
            wraplength=900,
            justify="left",
            font=("Segoe UI", 13, "bold"),
            bg=COLOR_SECUNDARIO,
        )
        label_enunciado.pack(pady=10, padx=30)

        var = tk.StringVar(value="")
        radios = {}
        for opt in ["A", "B", "C", "D"]:
            rb = tk.Radiobutton(
                frame_scroll,
                text="",
                variable=var,
                value=opt,
                font=("Segoe UI", 11),
                bg=COLOR_SECUNDARIO,
                anchor="w",
                justify="left",
            )
            rb.pack(anchor="w", padx=60, pady=5, fill="x")
            radios[opt] = rb

        btn_siguiente = tk.Button(
            frame_scroll,
            text="Siguiente",
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
            pady=10,
        )
        btn_siguiente.pack(fill="x", padx=40, pady=20)

        # ================ FUNCIONES =================

        def _format_time(segundos):
            minutos = segundos // 60
            s = segundos % 60
            return f"{minutos:02}:{s:02}"

        def actualizar_timer():
            label_timer.config(text=f"Tiempo: {_format_time(contador['tiempo'])}")
            if contador["tiempo"] <= 0:
                finalizar()
                return
            contador["tiempo"] -= 1
            contador["timer_id"] = self.ventana.after(1000, actualizar_timer)

        def mostrar():
            if contador["indice"] >= len(preguntas):
                finalizar()
                return

            progreso["value"] = contador["indice"]
            # actualizar texto de número de pregunta
            try:
                label_pregunta.config(
                    text=f"Pregunta {contador['indice']+1} de {len(preguntas)}"
                )
            except Exception:
                pass

            preg = preguntas.iloc[contador["indice"]]

            try:
                imagen_ref = preg.get("imagen")
                if pd.notna(imagen_ref) and str(imagen_ref).strip() != "":
                    ruta = BASE_DIR / "imagenes_preguntas" / str(imagen_ref)
                    if ruta.exists():
                        img = Image.open(ruta)
                        max_ancho = 800
                        w, h = img.size
                        if w > max_ancho:
                            ratio = max_ancho / float(w)
                            img = img.resize(
                                (int(w * ratio), int(h * ratio)), Image.LANCZOS
                            )
                        img_tk = ImageTk.PhotoImage(img)
                        label_imagen.config(image=img_tk)
                        label_imagen.image = img_tk
                    else:
                        label_imagen.config(image="")
                        label_imagen.image = None
                else:
                    label_imagen.config(image="")
                    label_imagen.image = None
            except Exception:
                label_imagen.config(image="")
                label_imagen.image = None

            label_contexto.config(text=str(preg.get("contexto", "")))
            label_enunciado.config(text=str(preg.get("enunciado", "")))

            radios["A"].config(text="A. " + str(preg.get("opcion_a", "")))
            radios["B"].config(text="B. " + str(preg.get("opcion_b", "")))
            radios["C"].config(text="C. " + str(preg.get("opcion_c", "")))
            radios["D"].config(text="D. " + str(preg.get("opcion_d", "")))

            var.set("")
            canvas.yview_moveto(0)

        def siguiente():
            if var.get() == "":
                messagebox.showwarning("Advertencia", "Selecciona una respuesta.")
                return

            preg = preguntas.iloc[contador["indice"]]
            correcta = str(preg.get("correcta", "")).strip().upper()
            seleccion = var.get().strip().upper()
            es_corr = 1 if seleccion == correcta else 0

            if es_corr:
                contador["correctas"] += 1

            try:
                pregunta_id = (
                    int(preg.get("id"))
                    if "id" in preg and pd.notna(preg.get("id"))
                    else None
                )
            except Exception:
                pregunta_id = None

            enunciado = str(preg.get("enunciado", ""))

            respuestas.append(
                {
                    "pregunta_id": pregunta_id,
                    "enunciado": enunciado,
                    "imagen": (
                        str(preg.get("imagen", ""))
                        if pd.notna(preg.get("imagen", ""))
                        else None
                    ),
                    "respuesta_dada": seleccion,
                    "respuesta_correcta": correcta,
                    "correcta": bool(es_corr),
                }
            )

            # ============ GUARDAR RESPUESTA INMEDIATAMENTE EN BD ============
            try:
                conn_inmediata = sqlite3.connect(DB_FILE)
                cursor_inmediata = conn_inmediata.cursor()

                cursor_inmediata.execute(
                    """
                    INSERT INTO respuestas_estudiantes 
                    (documento, nombre, grado, area, intento, pregunta_id, enunciado, 
                     respuesta_seleccionada, respuesta_correcta, es_correcta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(documento, area, intento, pregunta_id) 
                    DO UPDATE SET 
                        respuesta_seleccionada = EXCLUDED.respuesta_seleccionada,
                        es_correcta = EXCLUDED.es_correcta
                    """,
                    (
                        self.documento,
                        self.nombre,
                        self.grado,
                        area,
                        self.current_intento_num,
                        pregunta_id,
                        enunciado,
                        seleccion,
                        correcta,
                        es_corr,
                    ),
                )
                conn_inmediata.commit()
                conn_inmediata.close()
            except Exception as e:
                # Log silencioso - no interrumpir el flujo del examen
                print(f"[INFO] Respuesta guardada en BD: P{pregunta_id} = {seleccion}")

            contador["indice"] += 1
            mostrar()

        def finalizar():
            try:
                if contador["timer_id"]:
                    self.ventana.after_cancel(contador["timer_id"])
            except Exception:
                pass

            total = len(preguntas)

            # ============ RECUPERAR TODAS LAS RESPUESTAS SI ES REANUDACIÓN ============
            respuestas_finales = respuestas
            if es_reanudacion and self.current_intento_num:
                respuestas_bd = obtener_todas_respuestas_desde_bd(
                    self.documento, area, self.current_intento_num
                )
                if respuestas_bd:
                    respuestas_finales_json = json.loads(respuestas_bd)
                    # Recalcular correctas basándose en TODAS las respuestas
                    total_correctas_bd = sum(
                        1 for r in respuestas_finales_json if r.get("correcta", False)
                    )
                    contador["correctas"] = total_correctas_bd
                    respuestas_finales = respuestas_finales_json

            nota = round((contador["correctas"] / total) * 5, 2) if total > 0 else 0.0

            try:
                registrar_final(
                    self.documento,
                    nota,
                    area=area,
                    intento_id=self.current_intento_id,
                    respuestas=(
                        json.dumps(respuestas_finales)
                        if isinstance(respuestas_finales, list)
                        else respuestas_finales
                    ),
                )
            except TypeError:
                try:
                    registrar_final(
                        self.documento,
                        nota,
                        area=area,
                        intento_id=self.current_intento_id,
                    )
                except Exception:
                    pass
            except Exception:
                pass

            messagebox.showinfo(
                "Examen Finalizado",
                f"Correctas: {contador['correctas']} de {total}\nNota: {nota}/5.0",
            )

            self._mostrar_areas()

        btn_siguiente.config(command=siguiente)

        actualizar_timer()
        mostrar()

    # ---------------------------------------------------

    def _ver_resultado(self, area):
        intento = obtener_intento_area(self.documento, area)
        if not intento:
            messagebox.showinfo(
                "No hay registro", "No se encontró intento para esta área."
            )
            return

        id_reg, nota, estado_examen, puede_revisar, respuestas_raw = intento

        if estado_examen != "FINALIZADO":
            messagebox.showinfo(
                "Resultado no disponible", "El examen no ha sido finalizado."
            )
            return

        if puede_revisar != 1:
            messagebox.showinfo(
                "Revisión no autorizada", "El docente no ha autorizado la revisión."
            )
            return

        for w in self.contenido.winfo_children():
            w.destroy()

        header = tk.Frame(self.contenido, bg=COLOR_PRIMARIO)
        header.pack(fill="x")
        tk.Label(
            header,
            text=f"Revisión - {area}  |  Nota: {nota}",
            font=("Segoe UI", 14, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
        ).pack(side="left", padx=20, pady=10)

        canvas = tk.Canvas(self.contenido, bg=COLOR_SECUNDARIO, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            self.contenido, orient="vertical", command=canvas.yview
        )
        frame_scroll = tk.Frame(canvas, bg=COLOR_SECUNDARIO)
        frame_scroll.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=frame_scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        respuestas_list = []
        try:
            if isinstance(respuestas_raw, str):
                respuestas_list = json.loads(respuestas_raw)
            elif isinstance(respuestas_raw, list):
                respuestas_list = respuestas_raw
        except Exception:
            respuestas_list = []

        if not respuestas_list:
            tk.Label(
                frame_scroll,
                text="No hay detalles de respuestas para revisar.",
                bg=COLOR_SECUNDARIO,
            ).pack(pady=20)
            return

        for idx, r in enumerate(respuestas_list, start=1):
            enunciado = r.get("enunciado", "")
            resp_sel = r.get("respuesta_dada", "")
            resp_corr = r.get("respuesta_correcta", "")
            correcta = r.get("correcta", False)

            frame_q = tk.Frame(frame_scroll, bg=COLOR_SECUNDARIO, bd=1, relief="solid")
            frame_q.pack(fill="x", padx=20, pady=10)

            tk.Label(
                frame_q,
                text=f"{idx}. {enunciado}",
                font=("Segoe UI", 11, "bold"),
                bg=COLOR_SECUNDARIO,
                anchor="w",
                justify="left",
                wraplength=900,
            ).pack(fill="x", padx=10, pady=(8, 4))
            tk.Label(
                frame_q,
                text=f"Tu respuesta: {resp_sel}",
                font=("Segoe UI", 11),
                bg=COLOR_SECUNDARIO,
                fg=("#2b8a3e" if correcta else "#d9534f"),
            ).pack(anchor="w", padx=10)
            tk.Label(
                frame_q,
                text=f"Respuesta correcta: {resp_corr}",
                font=("Segoe UI", 11),
                bg=COLOR_SECUNDARIO,
            ).pack(anchor="w", padx=10, pady=(0, 8))


def abrir_docente(nombre):
    ventana_docente = tk.Tk()
    ModuloDocente(ventana_docente, nombre)
    ventana_docente.mainloop()


# ================= LOGIN =================


def validar_maestra(documento):
    """Verifica si el valor proporcionado coincide con la clave maestra almacenada.
    Devuelve True si el documento (texto) coincide exactamente con la clave maestra.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM config_sistema WHERE clave='master_key'")
        row = cursor.fetchone()
        conn.close()
        if row and str(row[0]) == str(documento):
            return True
    except Exception:
        pass
    return False


def requerir_clave_maestra(documento):
    """True si el texto ingresado debe solicitar la clave maestra.

    Actualmente se activa cuando se escribe exactamente "admin" (ignora mayúsculas).
    """
    return str(documento).strip().lower() == "admin"


def ingresar():
    documento = entry_documento.get()

    if documento == "":
        messagebox.showwarning("Advertencia", "Debe ingresar el documento.")
        return

    # Master key route (super admin)
    # - if the user types the actual master key value, grant access immediately
    # - if the user types the literal word "admin" (case-insensitive), prompt
    #   for the master password using a dialog.
    es_admin_literal = str(documento).strip().lower() == "admin"
    if es_admin_literal or validar_maestra(documento):
        # si sólo escribió 'admin', pedir clave maestra para confirmar
        if es_admin_literal:
            clave = simpledialog.askstring(
                "Acceso SuperAdmin",
                "Clave maestra:",
                show="*",
                parent=ventana,
            )
            # si canceló o no suministró algo, abortar
            if clave is None or clave == "":
                return
            if not validar_maestra(clave):
                messagebox.showerror("Acceso denegado", "Clave incorrecta.")
                return

        # el usuario ya está autenticado, abrir interfaz SuperAdmin
        ventana.destroy()
        admin_root = tk.Tk()
        admin_root.withdraw()

        msa = ModuloSuperAdmin(admin_root, db_path=str(DB_FILE), base_dir=str(BASE_DIR))
        msa.open_interface()
        try:
            msa.win.state("zoomed")
        except Exception:
            try:
                msa.win.attributes("-fullscreen", True)
            except Exception:
                pass
        msa.win.mainloop()
        return

    # Validar docente
    nombre_docente = validar_docente(documento)
    if nombre_docente:
        ventana.destroy()
        abrir_docente(nombre_docente)
        return

    # Validar estudiante
    estudiante = validar_estudiante(documento)

    if estudiante is None:
        messagebox.showerror("Error", "Documento no encontrado.")
        return

    # Acceder al Módulo Estudiante
    ventana.destroy()
    ventana_est = tk.Tk()
    # Maximizar la ventana del estudiante tras ingresar
    try:
        ventana_est.state("zoomed")
    except Exception:
        try:
            ventana_est.attributes("-fullscreen", True)
        except Exception:
            pass
    nombre = obtener_nombre_completo(estudiante)
    grado = estudiante.get("grado", "")
    curso = estudiante.get("curso", None)
    ModuloEstudiante(ventana_est, documento, nombre, grado, curso)
    ventana_est.mainloop()


def abrir_examen_legacy(documento, nombre, grado):
    """DEPRECADO: Usa abrir_estudiante en su lugar."""
    messagebox.showwarning(
        "Función descontinuada",
        "El flujo de examen ha sido unificado.\n"
        "Por favor, usa el módulo de estudiante para acceder a los exámenes.",
    )


class abrir_estudiante:
    def __init__(self, documento):
        self.documento = documento


# Nueva función que mantiene compatibilidad: redirige a abrir_estudiante
def abrir_examen(documento, nombre, grado):
    """Abre el módulo de estudiante (nuevo flujo unificado)."""
    abrir_estudiante(documento)


# ================= INICIO =================

crear_base_datos()

# Configuración de colores modernos
COLOR_PRIMARIO = "#0066cc"
COLOR_SECUNDARIO = "#f5f7fa"
COLOR_TEXTO = "#1a1a1a"
COLOR_BORDE = "#e0e0e0"
COLOR_EXITO = "#51cf66"
COLOR_ADVERTENCIA = "#ff6b6b"

ventana = tk.Tk()
ventana.title("Sistema de Evaluación Automatizada")
ruta_icono = obtener_ruta_icono()
if ruta_icono.exists():
    ventana.iconbitmap(str(ruta_icono))
ventana.geometry("500x600")
ventana.configure(bg=COLOR_SECUNDARIO)
ventana.resizable(False, False)

# Centro la ventana
ventana.update_idletasks()
x = (ventana.winfo_screenwidth() // 2) - (500 // 2)
y = (ventana.winfo_screenheight() // 2) - (600 // 2)
ventana.geometry(f"+{x}+{y}")

# Header con gradiente simulado
header = tk.Frame(ventana, bg=COLOR_PRIMARIO, height=120)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(
    header,
    text="📚 Sistema de Evaluación",
    font=("Segoe UI", 18, "bold"),
    bg=COLOR_PRIMARIO,
    fg="white",
).pack(pady=20)

tk.Label(
    header,
    text="Ingresa tu documento para acceder",
    font=("Segoe UI", 11),
    bg=COLOR_PRIMARIO,
    fg="#e0e0ff",
).pack()

# Panel de login
login_frame = tk.Frame(ventana, bg=COLOR_SECUNDARIO)
login_frame.pack(fill="both", expand=True, padx=40, pady=40)

tk.Label(
    login_frame,
    text="Documento:",
    font=("Segoe UI", 11, "bold"),
    bg=COLOR_SECUNDARIO,
    fg=COLOR_TEXTO,
).pack(anchor="w", pady=(10, 5))

entry_documento = tk.Entry(
    login_frame, width=30, font=("Segoe UI", 12), relief="flat", bd=0
)
entry_documento.pack(fill="x", ipady=10)

# Línea de separación
tk.Frame(login_frame, bg=COLOR_BORDE, height=1).pack(fill="x", pady=(0, 20))

# Botón moderno
tk.Button(
    login_frame,
    text="Ingresar",
    font=("Segoe UI", 12, "bold"),
    command=ingresar,
    bg=COLOR_PRIMARIO,
    fg="white",
    relief="flat",
    bd=0,
    padx=20,
    pady=12,
    cursor="hand2",
).pack(fill="x", pady=20)

# Footer fijo inferior
footer = tk.Frame(ventana, bg=COLOR_SECUNDARIO)
footer.pack(side="bottom", fill="x", padx=40, pady=10)

tk.Label(
    footer,
    text="Todos los derechos reservados autor Robert Calanche Villa 2026",
    font=("Segoe UI", 9),
    bg=COLOR_SECUNDARIO,
    fg="#999999",
).pack()

ventana.mainloop()
