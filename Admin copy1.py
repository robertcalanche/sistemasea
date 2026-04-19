from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import pandas as pd
import sqlite3
from pathlib import Path
import sys
from modulo_superadmin import ModuloSuperAdmin
from ui_footer import crear_footer
from datetime import datetime, timedelta
import random
import json


def _patch_sqlite_connect():
    """Aplica timeout/busy_timeout globales para reducir bloqueos en red local."""
    original_connect = getattr(sqlite3, "_original_connect", None)
    if original_connect is None:
        original_connect = sqlite3.connect
        sqlite3._original_connect = original_connect

    def _connect_with_defaults(*args, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = 30
        conn = original_connect(*args, **kwargs)
        try:
            conn.execute("PRAGMA busy_timeout = 30000")
        except Exception:
            pass
        return conn

    sqlite3.connect = _connect_with_defaults


_patch_sqlite_connect()


def _runtime_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def obtener_ruta_icono():
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            ruta_meipass = Path(meipass) / "sea_icon.ico"
            if ruta_meipass.exists():
                return ruta_meipass
        return Path(sys.executable).resolve().parent / "sea_icon.ico"
    return Path(__file__).resolve().parent / "sea_icon.ico"


def _leer_config_sistema(config_path):
    config = {"modo": "local", "ruta_servidor": ""}
    try:
        for raw_line in config_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip().lower()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return config


def _resolver_rutas_sistema():
    runtime_dir = _runtime_dir()
    config_path = runtime_dir / "config_sistema"
    config = _leer_config_sistema(config_path)

    modo = str(config.get("modo", "local")).strip().lower()
    ruta_servidor = str(config.get("ruta_servidor", "")).strip().strip('"').strip("'")

    if modo == "red" and ruta_servidor:
        ruta = Path(ruta_servidor)
        if not ruta.is_absolute():
            # Permite rutas relativas al directorio del ejecutable/script.
            ruta = (runtime_dir / ruta).resolve()
        if ruta.suffix.lower() == ".db":
            base_dir = ruta.parent
            db_path = ruta
        else:
            base_dir = ruta
            db_path = base_dir / "sistema.db"
    else:
        base_dir = runtime_dir
        db_path = base_dir / "sistema.db"

    return base_dir, str(db_path), config_path


BASE_DIR, DB_PATH, CONFIG_SISTEMA_FILE = _resolver_rutas_sistema()
DB_FILE = Path(DB_PATH)


def _tiene_valor(valor):
    if valor is None:
        return False
    if isinstance(valor, float) and valor != valor:
        return False
    texto = str(valor).strip()
    return texto != "" and texto.lower() not in {"nan", "none"}


# Configuración de colores compartida (disponible también al importar el módulo)
COLOR_PRIMARIO = "#0066cc"
COLOR_SECUNDARIO = "#f5f7fa"
COLOR_TEXTO = "#1a1a1a"
COLOR_BORDE = "#e0e0e0"
COLOR_EXITO = "#51cf66"
COLOR_ADVERTENCIA = "#ff6b6b"


def obtener_anio_lectivo_activo():
    """Obtiene el año lectivo activo desde config_sistema (fallback: año actual)."""
    anio_default = str(datetime.now().year)
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS config_sistema (
                clave TEXT PRIMARY KEY,
                valor TEXT
            )
            """
        )
        cursor.execute(
            "SELECT valor FROM config_sistema WHERE clave = ?", ("anio_lectivo",)
        )
        row = cursor.fetchone()
        anio = str(row[0] if row and row[0] is not None else "").strip()
        if len(anio) == 4 and anio.isdigit():
            conn.commit()
            return anio

        cursor.execute(
            "REPLACE INTO config_sistema(clave, valor) VALUES (?, ?)",
            ("anio_lectivo", anio_default),
        )
        conn.commit()
        return anio_default
    except Exception:
        return anio_default
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass


# ================= BASE DE DATOS =================


def crear_base_datos():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Tabla de estudiantes
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_documento TEXT,
            documento TEXT UNIQUE,
            nombre TEXT,
            sexo TEXT,
            fecha_nacimiento TEXT,
            telefono TEXT,
            correo TEXT,
            grado TEXT,
            curso TEXT,
            jornada TEXT,
            sede TEXT,
            anio_lectivo TEXT,
            estado TEXT DEFAULT 'Activo',
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Asegurar que todas las columnas de la tabla estudiantes existan
    try:
        cursor.execute("PRAGMA table_info(estudiantes)")
        existing_cols = {row[1].lower() for row in cursor.fetchall()}

        required_cols = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "tipo_documento": "TEXT",
            "documento": "TEXT",
            "nombre": "TEXT",
            "sexo": "TEXT",
            "fecha_nacimiento": "TEXT",
            "telefono": "TEXT",
            "correo": "TEXT",
            "grado": "TEXT",
            "curso": "TEXT",
            "jornada": "TEXT",
            "sede": "TEXT",
            "anio_lectivo": "TEXT",
            "estado": "TEXT DEFAULT 'Activo'",
            "fecha_registro": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            # Nuevos campos para interoperabilidad
            "codigo": "TEXT",
            "apellido1": "TEXT",
            "apellido2": "TEXT",
            "nombre1": "TEXT",
            "nombre2": "TEXT",
        }

        for col_name, col_type in required_cols.items():
            if col_name.lower() not in existing_cols:
                try:
                    cursor.execute(
                        f"ALTER TABLE estudiantes ADD COLUMN {col_name} {col_type}"
                    )
                    conn.commit()
                except Exception:
                    pass
    except Exception:
        pass

    conn.commit()

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
            respuestas TEXT,
            anio_lectivo TEXT
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
    # Asegurar que existan columnas opcionales en respuestas_estudiantes
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for col, tipo in [
            ("curso", "TEXT"),
            ("evaluacion", "TEXT"),
        ]:
            try:
                cursor.execute(
                    f"ALTER TABLE respuestas_estudiantes ADD COLUMN {col} {tipo}"
                )
            except Exception:
                pass
        conn.commit()
        conn.close()
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
    # Asegurar que existan columnas opcionales
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for col, tipo in [
            ("intento", "INTEGER DEFAULT 1"),
            ("respuestas", "TEXT"),
            ("curso", "TEXT"),
            ("evaluacion", "TEXT"),
            ("anio_lectivo", "TEXT"),
        ]:
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

    # La importación desde Excel se deja como operación explícita
    # (manual/script), para evitar dependencias en el arranque.


def importar_estudiantes_desde_excel():
    """Importa estudiantes desde estudiantes.xlsx a la tabla estudiantes de SQLite.
    Solo importa si la tabla está vacía.
    """
    try:
        # Verificar si la tabla ya tiene datos
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM estudiantes")
        count = cursor.fetchone()[0]
        conn.close()

        if count > 0:
            # Ya hay datos, no importar
            return

        # Intentar leer el archivo Excel
        excel_path = BASE_DIR / "estudiantes.xlsx"
        if not excel_path.exists():
            return

        df = pd.read_excel(excel_path)
        df.columns = df.columns.str.strip().str.lower()

        # Conectar a BD
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        anio_lectivo = obtener_anio_lectivo_activo()

        # Insertar estudiantes (sin duplicar)
        for _, row in df.iterrows():
            try:
                documento = str(row.get("documento", "")).strip()
                nombre = str(row.get("nombre", "")).strip()
                grado = str(row.get("grado", "")).strip()
                curso = str(row.get("curso", "")).strip()
                jornada = str(row.get("jornada", "")).strip()
                estado = str(row.get("estado", "Activo")).strip()

                # Normalizar estado (Matriculado -> Activo, MA -> Activo)
                if estado.lower() in ["matriculado", "ma"]:
                    estado = "Activo"

                # Campos opcionales
                tipo_documento = str(row.get("tipo_documento", "")).strip()
                sexo = str(row.get("sexo", "")).strip()
                fecha_nacimiento = str(row.get("fecha_nacimiento", "")).strip()
                telefono = str(row.get("telefono", "")).strip()
                correo = str(row.get("correo", "")).strip()
                sede = str(row.get("sede", "")).strip()

                if documento and nombre and grado:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO estudiantes
                        (tipo_documento, documento, nombre, sexo, fecha_nacimiento,
                         telefono, correo, grado, curso, jornada, sede, anio_lectivo, estado)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            tipo_documento,
                            documento,
                            nombre,
                            sexo,
                            fecha_nacimiento,
                            telefono,
                            correo,
                            grado,
                            curso,
                            jornada,
                            sede,
                            anio_lectivo,
                            estado,
                        ),
                    )
            except Exception as e:
                print(f"Error importando estudiante: {e}")

        conn.commit()
        conn.close()
        print(f"✓ Se importaron estudiantes desde Excel a SQLite")

    except Exception as e:
        print(f"Error en importar_estudiantes_desde_excel: {e}")


def crear_tabla_banco_preguntas():
    """Crea la tabla banco_preguntas si no existe."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

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


def importar_preguntas_desde_excel():
    """Importa preguntas desde preguntas.xlsx a la tabla banco_preguntas de SQLite.
    Solo importa si la tabla está vacía.
    """
    try:
        # Crear tabla primero
        crear_tabla_banco_preguntas()

        # Verificar si la tabla ya tiene datos
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM banco_preguntas")
        count = cursor.fetchone()[0]
        conn.close()

        if count > 0:
            # Ya hay datos, no importar
            return

        # Intentar leer el archivo Excel
        excel_path = BASE_DIR / "preguntas.xlsx"
        if not excel_path.exists():
            return

        df = pd.read_excel(excel_path)
        df.columns = df.columns.str.strip().str.lower()

        # Conectar a BD
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Insertar preguntas (sin duplicar)
        for _, row in df.iterrows():
            try:
                enunciado = str(row.get("enunciado", "")).strip()
                area = str(row.get("area", "")).strip()

                if enunciado and area:
                    cursor.execute(
                        """
                        INSERT INTO banco_preguntas
                        (evaluacion, area, periodo, grado, curso, id_contexto, contexto,
                         enunciado, opcion_a, opcion_b, opcion_c, opcion_d, correcta, imagen, nombre)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(row.get("evaluacion", "")).strip(),
                            area,
                            str(row.get("periodo", "")).strip(),
                            str(row.get("grado", "")).strip(),
                            str(row.get("curso", "")).strip(),
                            str(row.get("id_contexto", "")).strip(),
                            str(row.get("contexto", "")).strip(),
                            enunciado,
                            str(row.get("opcion_a", "")).strip(),
                            str(row.get("opcion_b", "")).strip(),
                            str(row.get("opcion_c", "")).strip(),
                            str(row.get("opcion_d", "")).strip(),
                            str(row.get("correcta", "")).strip(),
                            str(row.get("imagen", "")).strip(),
                            str(row.get("nombre", "")).strip(),
                        ),
                    )
            except Exception as e:
                pass

        conn.commit()
        conn.close()
        print(f"✓ Se importaron preguntas desde Excel a SQLite")

    except Exception as e:
        print(f"Error en importar_preguntas_desde_excel: {e}")


def crear_tabla_config():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Nueva estructura: la configuración depende de grado + curso + area + evaluacion
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS config_examenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grado TEXT,
            curso TEXT,
            area TEXT,
            evaluacion TEXT,
            anio_lectivo TEXT,
            duracion_segundos INTEGER,
            cantidad_preguntas INTEGER,
            max_intentos INTEGER DEFAULT 1,
            permitir_reintentos INTEGER DEFAULT 1,
            habilitado INTEGER DEFAULT 0
        )
    """
    )

    conn.commit()
    conn.close()
    # Verificar columnas obligatorias y agregarlas si faltan.
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(config_examenes)")
        cols = [r[1].lower() for r in cursor.fetchall()]

        required = [
            ("grado", "TEXT"),
            ("curso", "TEXT"),
            ("area", "TEXT"),
            ("evaluacion", "TEXT"),
            ("anio_lectivo", "TEXT"),
            ("duracion_segundos", "INTEGER"),
            ("cantidad_preguntas", "INTEGER"),
            ("max_intentos", "INTEGER DEFAULT 1"),
            ("permitir_reintentos", "INTEGER DEFAULT 1"),
            ("habilitado", "INTEGER DEFAULT 0"),
            ("estado", "TEXT DEFAULT 'borrador'"),  # nuevo campo para estado del examen
        ]

        # Generar y ejecutar ALTER TABLE sólo para columnas faltantes
        for col_name, col_type in required:
            if col_name.lower() not in cols:
                try:
                    sql = (
                        f"ALTER TABLE config_examenes ADD COLUMN {col_name} {col_type}"
                    )
                    cursor.execute(sql)
                except Exception:
                    pass

        # Actualizar la lista de columnas tras posibles ALTER TABLE previos
        cursor.execute("PRAGMA table_info(config_examenes)")
        cols_actual = [r[1].lower() for r in cursor.fetchall()]

        # Si la tabla venía de una versión antigua donde se usaba 'examen_activo',
        # migrar esos valores a la nueva columna 'habilitado' (si existe examen_activo).
        if "examen_activo" in cols_actual and "habilitado" in cols_actual:
            try:
                cursor.execute(
                    "UPDATE config_examenes SET habilitado = examen_activo WHERE habilitado IS NULL"
                )
            except Exception:
                pass

        # Compatibilidad de índices únicos:
        # - Eliminar índice legado (grado, area, evaluacion) para permitir configuración por curso.
        # - Garantizar índice único actual (grado, area, evaluacion, curso).
        try:
            cursor.execute("PRAGMA index_list(config_examenes)")
            indices = cursor.fetchall()
            for idx in indices:
                nombre_idx = idx[1]
                es_unico = bool(idx[2])
                if not es_unico:
                    continue

                cursor.execute(f"PRAGMA index_info('{nombre_idx}')")
                cols_idx = [str(r[2]).lower() for r in cursor.fetchall()]

                if cols_idx == ["grado", "area", "evaluacion"]:
                    nombre_safe = str(nombre_idx).replace('"', '""')
                    cursor.execute(f'DROP INDEX IF EXISTS "{nombre_safe}"')

            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_config_unica ON config_examenes (grado, area, evaluacion, curso)"
            )
        except Exception:
            pass

        conn.commit()
        conn.close()
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def registrar_inicio(
    documento, nombre, grado, area="General", evaluacion=None, curso=None
):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    hora_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "SELECT MAX(intento) FROM resultados WHERE documento = ? AND area = ?",
        (documento, area),
    )
    resultado = cursor.fetchone()
    intento = (resultado[0] or 0) + 1
    anio_lectivo = obtener_anio_lectivo_activo()

    cursor.execute(
        """
        INSERT INTO resultados (documento, nombre, grado, area, nota, estado_examen, hora_inicio, hora_fin, intento, evaluacion, curso, anio_lectivo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            evaluacion,
            curso,
            anio_lectivo,
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
    # Obtener curso y evaluacion para las respuestas
    curso = None
    evaluacion = None
    try:
        cursor.execute(
            "SELECT curso, evaluacion FROM resultados WHERE id = ?", (intento_id,)
        )
        row = cursor.fetchone()
        if row:
            curso, evaluacion = row
    except Exception:
        pass
    conn.close()
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
                            "INSERT OR IGNORE INTO respuestas_estudiantes (documento, nombre, grado, curso, area, evaluacion, intento, pregunta_id, enunciado, respuesta_seleccionada, respuesta_correcta, es_correcta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (
                                documento,
                                nombre_val,
                                grado_val,
                                curso,
                                area,
                                evaluacion,
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

            # Obtener opciones desde SQLite para enriquecer textos de respuestas
            opciones_por_id = {}
            pregunta_ids = sorted(
                {
                    int(resultado["pregunta_id"])
                    for resultado in resultados
                    if resultado.get("pregunta_id") is not None
                }
            )
            if pregunta_ids:
                placeholders = ",".join("?" for _ in pregunta_ids)
                cur.execute(
                    f"SELECT id, opcion_a, opcion_b, opcion_c, opcion_d FROM banco_preguntas WHERE id IN ({placeholders})",
                    tuple(pregunta_ids),
                )
                for pid, opcion_a, opcion_b, opcion_c, opcion_d in cur.fetchall():
                    opciones_por_id[int(pid)] = {
                        "A": str(opcion_a or "").strip(),
                        "B": str(opcion_b or "").strip(),
                        "C": str(opcion_c or "").strip(),
                        "D": str(opcion_d or "").strip(),
                    }

            # Para cada resultado, buscar el texto de las opciones
            for resultado in resultados:
                preg_id = resultado.get("pregunta_id")
                letra_sel = resultado.get("respuesta_seleccionada", "").strip().upper()
                letra_corr = resultado.get("respuesta_correcta", "").strip().upper()

                try:
                    preg_id_int = int(preg_id) if preg_id is not None else None
                except Exception:
                    preg_id_int = None

                opciones = opciones_por_id.get(preg_id_int)
                if opciones:
                    resultado["respuesta_seleccionada_texto"] = opciones.get(
                        letra_sel, letra_sel
                    )
                    resultado["respuesta_correcta_texto"] = opciones.get(
                        letra_corr, letra_corr
                    )
                else:
                    resultado["respuesta_seleccionada_texto"] = letra_sel
                    resultado["respuesta_correcta_texto"] = letra_corr

            return resultados
    except Exception:
        return []


def obtener_todas_respuestas_desde_bd(documento, area, intento):
    """Obtiene todas las respuestas guardadas en BD para un examen completo como JSON.

    Usado para recuperar respuestas durante reanudación o finalización de examen.

    Args:
        documento: Documento del estudiante
        area: Área del examen
        intento: Número de intento

    Returns:
        JSON string con lista de respuestas o None si no hay registros
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT pregunta_id, enunciado, respuesta_seleccionada, respuesta_correcta, es_correcta, imagen
               FROM respuestas_estudiantes 
               WHERE documento = ? AND area = ? AND intento = ?
               ORDER BY pregunta_id ASC""",
            (documento, area, intento),
        )
        respuestas = []
        for row in cursor.fetchall():
            preg_id, enun, resp_sel, resp_corr, es_corr, img = row
            respuestas.append(
                {
                    "pregunta_id": preg_id,
                    "enunciado": enun,
                    "respuesta_dada": resp_sel,
                    "respuesta_correcta": resp_corr,
                    "correcta": bool(es_corr),
                    "imagen": img if img else None,
                }
            )
        conn.close()
        return json.dumps(respuestas) if respuestas else None
    except Exception:
        return None


def cargar_grados():
    """Carga grados únicos desde la base de datos SQLite.

    Retorna lista ordenada de grados normalizados únicos.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT grado FROM estudiantes WHERE estado = 'Activo'")
        grados = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        return sorted([normalizar_grado(g) for g in grados])
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


def normalizar_grado(grado):
    """Normaliza el grado: strip, lower, elimina 'grado', '°', espacios extras.

    Ejemplos:
        'Grado 1' → '1'
        'grado 2°' → '2'
        '3  ' → '3'
        ' GRADO 4 ° ' → '4'
    """
    if grado is None:
        return ""
    # Convertir a string, strip y lower
    result = str(grado).strip().lower()
    # Eliminar la palabra "grado" (con espacios alrededor)
    result = result.replace("grado", "").strip()
    # Eliminar el símbolo °
    result = result.replace("°", "").strip()
    # Eliminar espacios múltiples
    result = " ".join(result.split())
    return result


def validar_estudiante(documento):
    """Valida estudiante desde la base de datos SQLite.
    Retorna: dict con datos del estudiante o None si no es válido.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT documento, nombre, grado, curso, jornada, estado
            FROM estudiantes
            WHERE documento = ?
            """,
            (documento,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            # Validar que el estado sea 'Activo'
            if str(row[5]).lower() != "activo":
                return None

            return {
                "documento": row[0],
                "nombre": row[1],
                "grado": row[2],
                "curso": row[3],
                "jornada": row[4],
                "estado": row[5],
            }

    except Exception as e:
        print("Error validando estudiante:", e)

    return None


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
    """Carga todas las preguntas desde la tabla banco_preguntas en SQLite."""
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM banco_preguntas ORDER BY id DESC", conn)
        conn.close()
        return df.sample(frac=1).reset_index(drop=True)
    except Exception as e:
        print("Error cargando preguntas:", e)
        return pd.DataFrame()


def cargar_areas():
    """Carga las áreas únicas desde la tabla banco_preguntas en SQLite."""
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(
            "SELECT DISTINCT area FROM banco_preguntas WHERE area IS NOT NULL", conn
        )
        conn.close()

        if not df.empty:
            areas = sorted(
                [
                    str(a).strip().lower()
                    for a in df["area"].dropna().unique()
                    if a and str(a).lower() != "none"
                ]
            )
            print(f"[DEBUG] Áreas cargadas desde SQLite: {areas}")
            return areas
        return []
    except Exception as e:
        print(f"[DEBUG] Error al cargar áreas: {e}")
        return []


def cargar_areas_por_grado(grado):
    """Carga las áreas únicas para un grado específico desde SQLite.

    Args:
        grado: El grado del estudiante

    Returns:
        Lista de áreas únicas para ese grado
    """
    print(f"[DEBUG] cargar_areas_por_grado llamada con grado={repr(grado)}")
    try:
        grado_norm = normalizar_grado(grado)
        print(f"[DEBUG] Grado NORMALIZADO: '{grado_norm}'")

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT area FROM banco_preguntas WHERE grado = ? AND area IS NOT NULL",
            (grado_norm,),
        )
        rows = cursor.fetchall()
        conn.close()

        if rows:
            areas = sorted(
                [
                    str(a[0]).strip().lower()
                    for a in rows
                    if a[0] and str(a[0]).lower() != "none"
                ]
            )
            print(f"[DEBUG] areas para grado='{grado_norm}': {areas}")
            return areas
        else:
            print(f"[DEBUG] No hay preguntas para grado='{grado_norm}'")
            return []

    except Exception as e:
        print(f"[DEBUG] Error al cargar áreas por grado: {e}")
        import traceback

        traceback.print_exc()
        return []


def cargar_evaluaciones_por_grado_y_area(grado, area):
    """Carga las evaluaciones únicas para una combinación de grado y área desde SQLite.

    Args:
        grado: El grado del estudiante
        area: El área/asignatura seleccionada

    Returns:
        Lista de evaluaciones ordenadas alfabéticamente
    """
    """
    Carga las evaluaciones únicas para una combinación de grado y área desde SQLite.
    Filtra solo por grado y área, sin incluir curso.
    """
    try:
        grado_norm = normalizar_grado(grado)
        area_norm = str(area).strip().lower() if area is not None else None
        if not grado_norm or not area_norm:
            return []

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT evaluacion
            FROM banco_preguntas
            WHERE grado = ?
              AND LOWER(TRIM(area)) = ?
              AND evaluacion IS NOT NULL
              AND TRIM(evaluacion) <> ''
            ORDER BY evaluacion
            """,
            (grado_norm, area_norm),
        )
        evaluaciones = [
            row[0]
            for row in cursor.fetchall()
            if row[0] and str(row[0]).strip().lower() not in ["nan", "none", ""]
        ]
        conn.close()
        return evaluaciones
    except Exception as e:
        print(f"[DEBUG] Error al cargar evaluaciones: {e}")
        return []


def cargar_cursos_disponibles(grado):
    """Carga los cursos disponibles para un grado desde el banco de preguntas.

    Args:
        grado: El grado seleccionado

    Returns:
        Lista de cursos únicos disponibles para el grado.
    """
    """
    Carga los cursos disponibles para un grado desde la tabla estudiantes.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT curso
            FROM estudiantes
            WHERE grado = ?
            ORDER BY curso
            """,
            (grado,),
        )
        cursos = [
            row[0]
            for row in cursor.fetchall()
            if row[0] and str(row[0]).strip().lower() not in ["nan", "none", ""]
        ]
        conn.close()
        return cursos
    except Exception as e:
        print(f"[DEBUG] Error al cargar cursos: {e}")
        return []


def cargar_evaluaciones_por_grado_area_curso(grado, area, curso=None):
    """Carga las evaluaciones únicas para una combinación de grado, área y curso desde SQLite.

    Args:
        grado: El grado del estudiante
        area: El área/asignatura seleccionada
        curso: El curso seleccionado (opcional). Si es None o "TODOS", se ignora en el filtro.

    Returns:
        Lista de evaluaciones ordenadas alfabéticamente
    """
    print(
        f"[DEBUG] cargar_evaluaciones_por_grado_area_curso llamada con grado={repr(grado)}, area={repr(area)}, curso={repr(curso)}"
    )
    try:
        if not grado or not area:
            print(f"[DEBUG] Grado o área vacíos, retornando lista vacía")
            return []

        grado_norm = normalizar_grado(grado)
        area_norm = str(area).strip().lower()

        # El curso no afecta las evaluaciones disponibles, ya que las preguntas no se filtran por curso.
        # Las evaluaciones son por grado + área, independientemente del curso.
        query = """SELECT DISTINCT evaluacion FROM banco_preguntas 
                   WHERE grado = ? AND LOWER(area) = ? AND evaluacion IS NOT NULL"""
        params = [grado_norm, area_norm]

        print(f"[DEBUG] Query: {query}, Params: {params}")

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        if rows:
            evaluaciones = [
                str(e[0]).strip()
                for e in rows
                if e[0] and str(e[0]).strip().lower() not in ["nan", "none", ""]
            ]
            evaluaciones = sorted(list(set(evaluaciones)))
            print(
                f"[DEBUG] ✅ Evaluaciones encontradas para grado='{grado_norm}', area='{area_norm}': {evaluaciones}"
            )
            return evaluaciones
        else:
            print(
                f"[DEBUG] ❌ No hay evaluaciones para grado='{grado_norm}' Y area='{area_norm}'"
            )
            return []

    except Exception as e:
        print(f"[DEBUG] Error al cargar evaluaciones: {e}")
        import traceback

        traceback.print_exc()
        return []


def exportar_reporte_por_filtros(grado_sel, curso_sel, area_sel, evaluacion_sel):
    """Exporta reporte con filtros de estudiantes: grado, curso, area, evaluacion.

    Incluye todos los estudiantes filtrados, incluso si no presentaron evaluación.
    """
    try:
        # Seleccionar archivo de destino
        ruta = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="resultados_export.xlsx",
        )
        if not ruta:
            return False

        # Obtener estudiantes desde SQLite filtrados por grado y curso
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        query = "SELECT documento, nombre, grado, curso FROM estudiantes WHERE estado = 'Activo'"
        params = []

        if grado_sel:
            query += " AND grado = ?"
            params.append(grado_sel)
        if curso_sel:
            query += " AND curso = ?"
            params.append(curso_sel)

        query += " ORDER BY grado, curso, nombre"
        cursor.execute(query, params)
        estudiantes_filtrados = cursor.fetchall()

        rows = []

        for est in estudiantes_filtrados:
            documento, nombre, grado, curso = est
            documento = str(documento).strip()
            nombre = str(nombre).strip()
            grado = str(grado).strip()
            curso = str(curso).strip()

            # Buscar resultado
            query = """
                SELECT nota, estado_examen, hora_inicio, hora_fin, evaluacion
                FROM resultados
                WHERE documento = ? AND estado_examen IN ('FINALIZADO','PRESENTADO')
            """
            params_res = [documento]
            if area_sel:
                query += " AND area = ?"
                params_res.append(area_sel)
            if evaluacion_sel:
                query += " AND evaluacion = ?"
                params_res.append(evaluacion_sel)
            query += " ORDER BY id DESC LIMIT 1"

            cursor.execute(query, params_res)
            resultado = cursor.fetchone()

            if resultado:
                nota, estado, hora_inicio, hora_fin, evaluacion = resultado
                nota_str = str(nota) if nota is not None else ""
                estado_str = estado.upper()
                fecha = hora_fin if hora_fin else hora_inicio
                evaluacion_str = evaluacion if evaluacion else ""
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
                except Exception:
                    duracion = ""
            else:
                nota_str = ""
                estado_str = "EXAMEN NO PRESENTADO"
                fecha = ""
                evaluacion_str = evaluacion_sel if evaluacion_sel else ""
                duracion = ""

            rows.append(
                (
                    grado,
                    curso,
                    nombre,
                    area_sel if area_sel else "",
                    evaluacion_str,
                    nota_str,
                    estado_str,
                    fecha,
                    duracion,
                )
            )

        conn.close()

        # Crear DataFrame
        df = pd.DataFrame(
            rows,
            columns=[
                "grado",
                "curso",
                "nombre",
                "area",
                "evaluacion",
                "nota",
                "estado",
                "fecha",
                "duracion",
            ],
        )

        # Exportar a Excel
        df.to_excel(ruta, index=False)
        messagebox.showinfo(
            "Exportado",
            f"Reporte exportado a:\n{ruta}\n\nTotal de registros: {len(df)}",
        )
        return True

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo exportar el reporte: {e}")
        return False


def exportar_consolidado_periodo(grado_sel, area_sel, curso_sel=None):
    """Exporta consolidado del período con una columna por evaluación.

    Estructura: grado | curso | nombre | area | eval1 | eval2 | eval3 | ...

    Incluye TODOS los estudiantes del grado/curso, aunque no tengan nota registrada.

    Args:
        grado_sel: Grado seleccionado
        area_sel: Área seleccionada
        curso_sel: Curso seleccionado (opcional)
    """
    try:
        # Seleccionar archivo de destino
        ruta = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="consolidado_periodo.xlsx",
        )
        if not ruta:
            return False

        # Obtener evaluaciones para grado y área
        evaluaciones = cargar_evaluaciones_por_grado_y_area(grado_sel, area_sel)

        if not evaluaciones:
            messagebox.showwarning(
                "Sin datos",
                f"No hay evaluaciones registradas para Grado {grado_sel}, Área {area_sel}",
            )
            return False

        # Obtener estudiantes desde SQLite
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Normalizar selecciones
        grado_sel_norm = normalizar_grado(grado_sel)
        curso_sel_norm = curso_sel.strip().upper() if curso_sel else None

        # Obtener estudiantes del grado (y curso si se especificó)
        query = "SELECT documento, nombre, grado, curso FROM estudiantes WHERE estado = 'Activo' AND grado = ?"
        params = [grado_sel_norm]

        if curso_sel_norm:
            query += " AND curso = ?"
            params.append(curso_sel_norm)

        query += " ORDER BY curso, nombre"
        cursor.execute(query, params)
        estudiantes_filtrados = cursor.fetchall()

        if not estudiantes_filtrados:
            messagebox.showwarning(
                "Sin estudiantes",
                f"No hay estudiantes en Grado {grado_sel}"
                + (f", Curso {curso_sel}" if curso_sel else ""),
            )
            return False

        # Construir datos consolidados
        rows = []

        for est in estudiantes_filtrados:
            documento, nombre, grado, curso = est
            documento = str(documento).strip()
            nombre = str(nombre).strip()
            grado = str(grado).strip()
            curso = str(curso).strip()

            # Fila base: grado, curso, nombre, area
            row = [grado, curso, nombre, area_sel]

            # Agregar notas por evaluación (LEFT JOIN lógico)
            for eval_name in evaluaciones:
                cursor.execute(
                    "SELECT nota FROM resultados WHERE documento = ? AND area = ? AND evaluacion = ? AND estado_examen IN ('FINALIZADO','PRESENTADO') ORDER BY id DESC LIMIT 1",
                    (documento, area_sel, eval_name),
                )
                resultado = cursor.fetchone()
                nota = ""
                if resultado and resultado[0] is not None:
                    nota = str(resultado[0])
                row.append(nota)

            rows.append(row)

        conn.close()

        # Crear columnas dinámicamente
        columns = ["grado", "curso", "nombre", "area"] + evaluaciones

        # Crear DataFrame
        df = pd.DataFrame(rows, columns=columns)

        # Exportar a Excel
        df.to_excel(ruta, index=False)
        messagebox.showinfo(
            "Exportado",
            f"Consolidado del período exportado a:\n{ruta}\n\nTotal de estudiantes: {len(df)}\nEvaluaciones: {len(evaluaciones)}",
        )
        return True

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo exportar el consolidado: {e}")
        return False


def exportar_reporte_completo(grado_sel, area_sel):
    """Exporta reporte completo incluyendo estudiantes sin nota.

    Incluye columnas en el orden: grado, curso, nombre, area, evaluacion, nota, estado, fecha, duracion.
    No excluye registros sin nota.

    Args:
        grado_sel: Grado seleccionado (o "Todos")
        area_sel: Área seleccionada (o "Todos")

    Returns:
        True si se exportó correctamente, False en caso contrario.
    """
    try:
        # Construir consulta según filtros
        base_query = "SELECT grado, documento, nombre, area, nota, estado_examen, hora_inicio, hora_fin, curso, evaluacion FROM resultados"
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

        # Seleccionar archivo de destino
        ruta = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="resultados_export.xlsx",
        )
        if not ruta:
            return False

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
                curso_db,
                evaluacion_db,
            ) = fila

            # Obtener grado y curso oficial desde la tabla estudiantes en SQLite
            try:
                estudiante = validar_estudiante(documento)
                grado_oficial = None
                curso_oficial = None
                if isinstance(estudiante, dict):
                    grado_oficial = estudiante.get("grado") or estudiante.get("Grado")
                    curso_oficial = estudiante.get("curso") or estudiante.get("Curso")

                if _tiene_valor(grado_oficial):
                    grado = str(grado_oficial).strip()
                else:
                    grado = str(grado_db) if grado_db is not None else ""

                if _tiene_valor(curso_oficial):
                    curso = str(curso_oficial).strip()
                else:
                    curso = str(curso_db) if curso_db is not None else ""
            except Exception:
                grado = str(grado_db) if grado_db is not None else ""
                curso = str(curso_db) if curso_db is not None else ""

            # Preparar fecha
            fecha = hora_fin if hora_fin is not None else hora_inicio

            # Preparar nota (vacía si no existe)
            nota_str = "" if nota is None else str(nota)

            # Preparar estado
            estado_str = str(estado).upper() if estado else ""

            # Preparar evaluación (vacía si no existe)
            evaluacion_str = "" if evaluacion_db is None else str(evaluacion_db)

            # Preparar duración
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
            except Exception:
                pass

            # Agregar fila en el orden requerido: grado, curso, nombre, area, evaluacion, nota, estado, fecha, duracion
            rows.append(
                (
                    grado,
                    curso,
                    nombre,
                    area,
                    evaluacion_str,
                    nota_str,
                    estado_str,
                    fecha,
                    duracion,
                )
            )

        # Crear DataFrame con el orden de columnas especificado
        df = pd.DataFrame(
            rows,
            columns=[
                "grado",
                "curso",
                "nombre",
                "area",
                "evaluacion",
                "nota",
                "estado",
                "fecha",
                "duracion",
            ],
        )

        # Exportar a Excel
        df.to_excel(ruta, index=False)
        messagebox.showinfo(
            "Exportado",
            f"Reporte completo exportado a:\n{ruta}\n\nTotal de registros: {len(df)}",
        )
        return True

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo exportar el reporte: {e}")
        return False


def cargar_preguntas_filtradas(area=None, grado=None, evaluacion=None, curso=None):
    """Carga preguntas filtradas por evaluación o por area+grado+curso desde SQLite.

    Args:
        area: Área/asignatura (opcional si se proporciona evaluacion)
        grado: Grado del estudiante (opcional si se proporciona evaluacion)
        evaluacion: Identificador único de evaluación (opcional)
        curso: Curso del estudiante (opcional, se ignora si es None o "TODOS")

    Returns:
        DataFrame con preguntas filtradas
    """
    print(f"\n[DEBUG] ========== CARGAR_PREGUNTAS_FILTRADAS ==========")
    print(
        f"[DEBUG] Parámetros recibidos: area={repr(area)}, grado={repr(grado)}, evaluacion={repr(evaluacion)}, curso={repr(curso)}"
    )

    try:
        conn = sqlite3.connect(DB_FILE)

        # Si evaluacion se proporciona y no es None, SOLO filtra por evaluacion
        if evaluacion is not None and str(evaluacion).strip():
            evaluacion_norm = str(evaluacion).strip().lower()
            if evaluacion_norm not in ["nan", "none", ""]:
                print(
                    f"[DEBUG] FILTRO PRINCIPAL: Usar UNICAMENTE 'evaluacion' = '{evaluacion_norm}'"
                )

                query = "SELECT * FROM banco_preguntas WHERE evaluacion = ?"
                df = pd.read_sql_query(query, conn, params=[evaluacion_norm])
                conn.close()

                if not df.empty:
                    print(
                        f"[DEBUG] RETORNANDO {len(df)} preguntas con evaluacion = '{evaluacion_norm}'"
                    )
                    print(
                        f"[DEBUG] ===================================================\n"
                    )
                    if "id_contexto" in df.columns and "id" in df.columns:
                        return df.sort_values(by=["id_contexto", "id"]).reset_index(
                            drop=True
                        )
                    return df.reset_index(drop=True)
                else:
                    print(
                        f"[DEBUG] ❌ NO hay preguntas con evaluacion = '{evaluacion_norm}'"
                    )
                    print(
                        f"[DEBUG] ===================================================\n"
                    )
                    return pd.DataFrame()

        # FALLBACK: Si no hay evaluacion, usar filtros de area+grado+curso
        print(f"[DEBUG] Sin evaluacion específica. Filtrando por area+grado+curso...")

        # Validar que area y grado se proporcionaron
        if area is None or grado is None:
            print(f"[DEBUG] ❌ area o grado no proporcionados")
            print(f"[DEBUG] ===================================================\n")
            conn.close()
            return pd.DataFrame()

        # Normalizar parámetros
        area_norm = str(area).strip().lower()
        grado_norm = normalizar_grado(grado)

        print(
            f"[DEBUG] Parámetros NORMALIZADOS: area='{area_norm}' | grado='{grado_norm}' | curso='{curso}'"
        )

        query = "SELECT * FROM banco_preguntas WHERE area = ? AND grado = ?"
        params = [area_norm, grado_norm]

        # Si curso está especificado y no es "TODOS", agregarlo al filtro
        if curso and curso != "TODOS":
            query += " AND curso = ?"
            params.append(curso)
            print(f"[DEBUG] Agregando filtro de curso: {curso}")

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if not df.empty:
            print(f"[DEBUG] RETORNANDO {len(df)} preguntas")
            print(f"[DEBUG] ===================================================\n")
            if "id_contexto" in df.columns and "id" in df.columns:
                return df.sort_values(by=["id_contexto", "id"]).reset_index(drop=True)
            return df.reset_index(drop=True)
        else:
            print(
                f"[DEBUG] ❌ NO hay preguntas para área='{area_norm}' Y grado='{grado_norm}' Y curso='{curso}'"
            )
            print(f"[DEBUG] ===================================================\n")
            return pd.DataFrame()

    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        return pd.DataFrame()


def cargar_config_examen(area, grado=None, evaluacion=None, curso=None):
    """Carga configuración de examen.

    Compatibilidad: si se llama sólo con `area` (uso histórico), se intentará
    obtener la configuración por área. Si se suministra `grado` y/o `evaluacion`,
    se prioriza la búsqueda por la combinación `grado + curso + area + evaluacion`.
    Retorna: (duracion_segundos, cantidad_preguntas, max_intentos, permitir_reintentos, habilitado)
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        area_param = str(area).strip().lower() if area is not None else None
        grado_param = normalizar_grado(grado) if grado is not None else None
        evaluacion_param = str(evaluacion).strip() if evaluacion is not None else None
        if evaluacion_param == "":
            evaluacion_param = None

        # Si se dispone de grado y evaluacion -> buscar por los cuatro campos
        if grado_param is not None and evaluacion_param is not None:
            # Normalizar curso: si no está definido o es vacío, se considera 'TODOS'.
            # Esto permite definir una configuración que aplica a todos los cursos.
            curso_param = str(curso).strip().upper() if curso is not None else ""
            if curso_param == "":
                curso_param = "TODOS"

            cursor.execute(
                "SELECT duracion_segundos, cantidad_preguntas, COALESCE(max_intentos, 1), COALESCE(permitir_reintentos, 1), COALESCE(habilitado, 0) "
                "FROM config_examenes "
                "WHERE LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT))) "
                "AND LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT))) "
                "AND LOWER(TRIM(CAST(evaluacion AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT))) "
                "AND (UPPER(TRIM(curso)) = ? OR UPPER(TRIM(curso)) = 'TODOS') "
                "ORDER BY (curso = 'TODOS') ASC LIMIT 1",
                (grado_param, area_param, evaluacion_param, curso_param),
            )
            resultado = cursor.fetchone()

            # Compatibilidad: si no hay registro con curso (o TODOS), intentar buscar sin filtro de curso
            if not resultado:
                cursor.execute(
                    "SELECT duracion_segundos, cantidad_preguntas, COALESCE(max_intentos, 1), COALESCE(permitir_reintentos, 1), COALESCE(habilitado, 0) "
                    "FROM config_examenes "
                    "WHERE LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT))) "
                    "AND LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT))) "
                    "AND LOWER(TRIM(CAST(evaluacion AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))",
                    (grado_param, area_param, evaluacion_param),
                )
                resultado = cursor.fetchone()
        # Si sólo grado está disponible -> buscar por grado + area
        elif grado_param is not None:
            cursor.execute(
                "SELECT duracion_segundos, cantidad_preguntas, COALESCE(max_intentos, 1), COALESCE(permitir_reintentos, 1), COALESCE(habilitado, 0) FROM config_examenes WHERE LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT))) AND LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))",
                (grado_param, area_param),
            )
            resultado = cursor.fetchone()
        else:
            # Compatibilidad: búsqueda sólo por área
            cursor.execute(
                "SELECT duracion_segundos, cantidad_preguntas, COALESCE(max_intentos, 1), COALESCE(permitir_reintentos, 1), COALESCE(habilitado, 0) FROM config_examenes WHERE LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))",
                (area_param,),
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
            )
        return 120, 10, 1, 1, 0
    except Exception:
        return 120, 10, 1, 1, 0


def examen_esta_activo(area):
    """Devuelve True si la configuración del área está habilitada."""
    try:
        _, _, _, _, habilitado = cargar_config_examen(area)
        return bool(habilitado)
    except Exception:
        return False


def guardar_config_examen(
    grado,
    area,
    evaluacion,
    duracion_segundos,
    cantidad_preguntas,
    max_intentos=1,
    permitir_reintentos=1,
    habilitado=0,
    curso=None,
):
    """Guarda o actualiza configuración de examen usando la combinación única grado+curso+area+evaluacion."""
    import time

    # Normalizar parámetros clave para evitar duplicados por espacios/case.
    grado_param = normalizar_grado(grado)
    area_param = str(area).strip().lower() if area is not None else None
    evaluacion_param = str(evaluacion).strip() if evaluacion is not None else None

    if not grado_param or not area_param or not evaluacion_param:
        return False

    # Curso obligatorio para configuración por curso (sin opción "Todos" en UI).
    curso_param = str(curso).strip().upper() if curso is not None else ""
    if curso_param == "":
        return False

    anio_lectivo = obtener_anio_lectivo_activo()

    for intento in range(3):
        conn = None
        try:
            conn = sqlite3.connect(DB_FILE, timeout=15)
            cursor = conn.cursor()
            cursor.execute("PRAGMA busy_timeout = 15000")

            cursor.execute(
                "SELECT id FROM config_examenes WHERE grado = ? AND area = ? AND evaluacion = ? AND curso = ?",
                (grado_param, area_param, evaluacion_param, curso_param),
            )
            existe = cursor.fetchone()

            if existe:
                cursor.execute(
                    "UPDATE config_examenes SET duracion_segundos = ?, cantidad_preguntas = ?, max_intentos = ?, permitir_reintentos = ?, habilitado = ?, anio_lectivo = ? WHERE grado = ? AND area = ? AND evaluacion = ? AND curso = ?",
                    (
                        duracion_segundos,
                        cantidad_preguntas,
                        max_intentos,
                        permitir_reintentos,
                        habilitado,
                        anio_lectivo,
                        grado_param,
                        area_param,
                        evaluacion_param,
                        curso_param,
                    ),
                )
            else:
                cursor.execute(
                    "INSERT INTO config_examenes (grado, curso, area, evaluacion, anio_lectivo, duracion_segundos, cantidad_preguntas, max_intentos, permitir_reintentos, habilitado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        grado_param,
                        curso_param,
                        area_param,
                        evaluacion_param,
                        anio_lectivo,
                        duracion_segundos,
                        cantidad_preguntas,
                        max_intentos,
                        permitir_reintentos,
                        habilitado,
                    ),
                )

            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            # Compatibilidad con índices únicos antiguos (grado+area+evaluacion).
            # En ese caso, actualizar registro existente para no romper guardado.
            if "unique constraint failed" in str(e).lower():
                try:
                    cursor.execute(
                        "UPDATE config_examenes SET curso = ?, duracion_segundos = ?, cantidad_preguntas = ?, max_intentos = ?, permitir_reintentos = ?, habilitado = ?, anio_lectivo = ? WHERE grado = ? AND area = ? AND evaluacion = ?",
                        (
                            curso_param,
                            duracion_segundos,
                            cantidad_preguntas,
                            max_intentos,
                            permitir_reintentos,
                            habilitado,
                            anio_lectivo,
                            grado_param,
                            area_param,
                            evaluacion_param,
                        ),
                    )
                    conn.commit()
                    return True
                except Exception:
                    pass
            print(f"[DEBUG] Error de integridad al guardar configuración: {e}")
            return False
        except sqlite3.OperationalError as e:
            # Reintentar en bloqueos transitorios de SQLite.
            if "locked" in str(e).lower() and intento < 2:
                time.sleep(0.35)
                continue
            print(f"[DEBUG] Error SQLite al guardar configuración: {e}")
            return False
        except Exception as e:
            print(f"[DEBUG] Error al guardar configuración: {e}")
            return False
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

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

    def __init__(self, ventana, nombre, cerrar_sesion_cb=None):
        self.ventana = ventana
        self.nombre = nombre
        self.cerrar_sesion_cb = cerrar_sesion_cb
        # Diccionario para mapear fila_id -> documento (necesario ya que documento no se muestra en tabla)
        self._fila_documento = {}

        self.ventana.title("Panel del Docente")
        self.ventana.geometry("1000x700")
        self.ventana.configure(bg=COLOR_SECUNDARIO)

        # Header moderno
        header = tk.Frame(self.ventana, bg=COLOR_PRIMARIO, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)

        if cerrar_sesion_cb:
            tk.Button(
                header,
                text="🚪 Cerrar sesión",
                font=("Segoe UI", 10, "bold"),
                bg="#cc3300",
                fg="white",
                relief="flat",
                cursor="hand2",
                padx=12,
                pady=6,
                command=cerrar_sesion_cb,
            ).pack(side="right", padx=15, pady=15)

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

        # Panel de configuración de examen (reorganizado en dos filas)
        config_frame = tk.LabelFrame(
            self.ventana,
            text="⚙️  Configuración de Examen",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        )
        config_frame.pack(fill="x", padx=15, pady=(0, 0))

        # Frames internos: identificación (fila 1) y configuración (fila 2)
        frame_identificacion = tk.Frame(config_frame, bg=COLOR_SECUNDARIO)
        frame_identificacion.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        frame_configuracion = tk.Frame(config_frame, bg=COLOR_SECUNDARIO)
        frame_configuracion.grid(row=1, column=0, sticky="ew", padx=8, pady=(4, 8))

        # --- Botón para cuadernillo multi-área ---
        try:
            from Admin import agregar_boton_cuadernillo_multi_area

            agregar_boton_cuadernillo_multi_area(frame_configuracion)
        except Exception as e:
            print("[INFO] No se pudo agregar botón cuadernillo multi-área:", e)

        # Asegurar que los frames puedan expandirse horizontalmente
        config_frame.columnconfigure(0, weight=1)
        for i in range(4):
            frame_identificacion.columnconfigure(i, weight=1)
        for i in range(6):
            frame_configuracion.columnconfigure(i, weight=1)

        padx = 8
        pady = 4

        # --- FILA 1: Identificación del examen ---
        tk.Label(
            frame_identificacion,
            text="Grado:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).grid(row=0, column=0, sticky="w", padx=padx, pady=pady)
        self.combo_grado_cfg = ttk.Combobox(
            frame_identificacion,
            values=["Seleccione"],
            state="readonly",
            width=12,
            font=("Segoe UI", 10),
        )
        self.combo_grado_cfg.current(0)
        self.combo_grado_cfg.grid(
            row=1, column=0, sticky="ew", padx=padx, pady=(0, pady)
        )
        self.combo_grado_cfg.bind("<<ComboboxSelected>>", self._on_grado_selected)

        tk.Label(
            frame_identificacion,
            text="Área:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).grid(row=0, column=1, sticky="w", padx=padx, pady=pady)
        self.combo_area_cfg = ttk.Combobox(
            frame_identificacion,
            values=["General"],
            state="readonly",
            width=14,
            font=("Segoe UI", 10),
        )
        self.combo_area_cfg.current(0)
        self.combo_area_cfg.grid(
            row=1, column=1, sticky="ew", padx=padx, pady=(0, pady)
        )
        self.combo_area_cfg.bind(
            "<<ComboboxSelected>>",
            lambda e: self._on_area_selected_cfg(),
        )
        # Mantener compatibilidad con código previo que usaba `self.combo_area`
        try:
            self.combo_area = self.combo_area_cfg
        except Exception:
            pass

        tk.Label(
            frame_identificacion,
            text="Evaluación:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).grid(row=0, column=2, sticky="w", padx=padx, pady=pady)
        self.combo_evaluacion_cfg = ttk.Combobox(
            frame_identificacion,
            values=["General"],
            state="readonly",
            width=14,
            font=("Segoe UI", 10),
        )
        self.combo_evaluacion_cfg.current(0)
        self.combo_evaluacion_cfg.grid(
            row=1, column=2, sticky="ew", padx=padx, pady=(0, pady)
        )
        self.combo_evaluacion_cfg.bind("<<ComboboxSelected>>", self._cargar_config_area)

        tk.Label(
            frame_identificacion,
            text="Curso:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).grid(row=0, column=3, sticky="w", padx=padx, pady=pady)
        self.combo_curso_cfg = ttk.Combobox(
            frame_identificacion,
            values=["Seleccione"],
            state="readonly",
            width=12,
            font=("Segoe UI", 10),
        )
        self.combo_curso_cfg.current(0)
        self.combo_curso_cfg.grid(
            row=1, column=3, sticky="ew", padx=padx, pady=(0, pady)
        )
        self.combo_curso_cfg.bind("<<ComboboxSelected>>", self._cargar_config_area)

        # --- FILA 2: Configuración ---
        tk.Label(
            frame_configuracion,
            text="Duración (min):",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).grid(row=0, column=0, sticky="w", padx=padx, pady=pady)
        self.entry_duracion = tk.Entry(
            frame_configuracion, width=6, font=("Segoe UI", 10), relief="flat", bd=1
        )
        self.entry_duracion.insert(0, "2")
        self.entry_duracion.grid(row=1, column=0, sticky="w", padx=padx, pady=(0, pady))

        tk.Label(
            frame_configuracion,
            text="Preguntas:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).grid(row=0, column=1, sticky="w", padx=padx, pady=pady)
        self.entry_cantidad = tk.Entry(
            frame_configuracion, width=6, font=("Segoe UI", 10), relief="flat", bd=1
        )
        self.entry_cantidad.insert(0, "10")
        self.entry_cantidad.grid(row=1, column=1, sticky="w", padx=padx, pady=(0, pady))

        tk.Label(
            frame_configuracion,
            text="Máx. Intentos:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).grid(row=0, column=2, sticky="w", padx=padx, pady=pady)
        self.entry_max_intentos = tk.Entry(
            frame_configuracion, width=6, font=("Segoe UI", 10), relief="flat", bd=1
        )
        self.entry_max_intentos.insert(0, "1")
        self.entry_max_intentos.grid(
            row=1, column=2, sticky="w", padx=padx, pady=(0, pady)
        )

        tk.Label(
            frame_configuracion,
            text="Permitir Reintentos:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).grid(row=0, column=3, sticky="w", padx=padx, pady=pady)
        self.var_permitir_reintentos = tk.BooleanVar(value=True)
        check_reintentos = tk.Checkbutton(
            frame_configuracion,
            variable=self.var_permitir_reintentos,
            bg=COLOR_SECUNDARIO,
            cursor="hand2",
        )
        check_reintentos.grid(row=1, column=3, sticky="w", padx=padx, pady=(0, pady))

        tk.Label(
            frame_configuracion,
            text="Habilitar Examen:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).grid(row=0, column=4, sticky="w", padx=padx, pady=pady)
        self.var_examen_activo = tk.BooleanVar(value=False)
        check_examen = tk.Checkbutton(
            frame_configuracion,
            variable=self.var_examen_activo,
            bg=COLOR_SECUNDARIO,
            cursor="hand2",
        )
        check_examen.grid(row=1, column=4, sticky="w", padx=padx, pady=(0, pady))

        # Botón GUARDAR alineado a la derecha (columna 5)
        btn_guardar = tk.Button(
            frame_configuracion,
            text="💾 Guardar",
            command=self.guardar_config,
            font=("Segoe UI", 9, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        )
        btn_guardar.grid(row=1, column=5, sticky="e", padx=(padx, 16), pady=(0, pady))

        # Cargar áreas desde banco_preguntas (SQLite) según el grado seleccionado
        self._llenar_combo_areas_por_grado()

        # Contenedor separado para botones de acción (debajo del header) — asegura suficiente ancho
        actions_container = tk.Frame(self.ventana, bg=COLOR_SECUNDARIO)
        actions_container.pack(fill="x", padx=15, pady=(10, 0))

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
            text="  Consolidado",
            command=self.exportar_consolidado,
            font=("Segoe UI", 9, "bold"),
            bg="#17A2B8",
            fg="white",
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2",
        ).pack(side="left", padx=5)
        tk.Button(
            actions_frame,
            text=" 🔎 Ver Detalle",
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

        # ========== SECCIÓN DE FILTROS DE ESTUDIANTES ==========
        filtros_frame = tk.LabelFrame(
            self.ventana,
            text="🔍 Filtros de Estudiantes",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        )
        filtros_frame.pack(fill="x", padx=15, pady=(10, 0))

        # Fila 1: Grado, Curso, Área, Evaluación
        filtros_row1 = tk.Frame(filtros_frame, bg=COLOR_SECUNDARIO)
        filtros_row1.pack(fill="x", padx=10, pady=8)

        tk.Label(
            filtros_row1,
            text="Grado:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(0, 5))
        self.combo_filtro_grado = ttk.Combobox(
            filtros_row1,
            values=[],
            state="readonly",
            width=8,
            font=("Segoe UI", 10),
        )
        self.combo_filtro_grado.pack(side="left", padx=(0, 15))
        self.combo_filtro_grado.bind(
            "<<ComboboxSelected>>", lambda e: self._on_grado_selected_filtro()
        )

        tk.Label(
            filtros_row1,
            text="Curso:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(0, 5))
        self.combo_filtro_curso = ttk.Combobox(
            filtros_row1,
            values=[],
            state="readonly",
            width=12,
            font=("Segoe UI", 10),
        )
        self.combo_filtro_curso.pack(side="left", padx=(0, 15))
        self.combo_filtro_curso.bind(
            "<<ComboboxSelected>>", lambda e: self._on_curso_selected()
        )

        tk.Label(
            filtros_row1,
            text="Área:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(0, 5))
        self.combo_filtro_area = ttk.Combobox(
            filtros_row1,
            values=[],
            state="readonly",
            width=12,
            font=("Segoe UI", 10),
        )
        self.combo_filtro_area.pack(side="left", padx=(0, 15))
        self.combo_filtro_area.bind(
            "<<ComboboxSelected>>", lambda e: self._on_area_selected()
        )

        tk.Label(
            filtros_row1,
            text="Evaluación:",
            font=("Segoe UI", 10),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
        ).pack(side="left", padx=(0, 5))
        self.combo_filtro_evaluacion = ttk.Combobox(
            filtros_row1,
            values=[],
            state="readonly",
            width=12,
            font=("Segoe UI", 10),
        )
        self.combo_filtro_evaluacion.pack(side="left", padx=(0, 15))
        self.combo_filtro_evaluacion.bind(
            "<<ComboboxSelected>>", lambda e: self.cargar_datos()
        )

        # Botón para limpiar filtros
        tk.Button(
            filtros_row1,
            text="✖️  Limpiar Filtros",
            command=self._limpiar_filtros,
            font=("Segoe UI", 9),
            bg="#ff9500",
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
        ).pack(side="left", padx=5)

        self.btn_actualizar = tk.Button(
            filtros_row1,
            text="🔄 Actualizar Datos",
            command=self.cargar_datos,
            font=("Segoe UI", 9),
            bg=COLOR_PRIMARIO,
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.btn_actualizar.pack(side="left", padx=5)

        # Iniciar actualización automática para que el módulo docente sincronice cambios recientes
        self._auto_refresh_habilitado = True
        self._auto_refresh_job = None

        def _detener_auto_refresh(_event=None):
            self._auto_refresh_habilitado = False
            try:
                if self._auto_refresh_job:
                    self.ventana.after_cancel(self._auto_refresh_job)
                    self._auto_refresh_job = None
            except Exception:
                pass

        def _auto_refresh():
            if not self._auto_refresh_habilitado:
                return
            if not self.ventana.winfo_exists():
                return
            try:
                self.cargar_datos()
            except Exception:
                pass
            try:
                self._auto_refresh_job = self.ventana.after(5000, _auto_refresh)
            except tk.TclError:
                # La ventana ya se cerró; detener ciclo de auto-actualización.
                return
            except Exception:
                pass

        try:
            self.ventana.bind(
                "<Destroy>",
                lambda e: _detener_auto_refresh() if e.widget is self.ventana else None,
            )
        except Exception:
            pass

        _auto_refresh()

        # Crear la tabla siempre, independientemente de si hay datos
        self.crear_tabla()

        self._llenar_combo_grados()
        self._cargar_config_area()
        self.cargar_datos()
        crear_footer(self.ventana)

    def cargar_datos(self):
        # limpiar tabla
        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        self._fila_documento = {}

        # Obtener valores de filtros
        grado_sel = self.combo_filtro_grado.get()
        if grado_sel == "Todos":
            grado_sel = None

        curso_sel = self.combo_filtro_curso.get()
        if curso_sel == "Todos":
            curso_sel = None

        area_sel = self.combo_filtro_area.get()
        if area_sel == "Todos":
            area_sel = None

        evaluacion_sel = self.combo_filtro_evaluacion.get()
        if evaluacion_sel == "Todos":
            evaluacion_sel = None

        # Obtener estudiantes desde Excel filtrados por grado y curso
        try:
            # Obtener estudiantes desde SQLite filtrados por grado y curso
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Normalizar grado y curso seleccionados
            grado_sel_norm = normalizar_grado(grado_sel) if grado_sel else None
            curso_sel_norm = curso_sel.strip().upper() if curso_sel else None

            query = "SELECT documento, nombre, grado, curso FROM estudiantes WHERE estado = 'Activo'"
            params = []

            if grado_sel_norm:
                query += " AND grado = ?"
                params.append(grado_sel_norm)
            if curso_sel_norm:
                query += " AND UPPER(TRIM(curso)) = ?"
                params.append(curso_sel_norm)

            query += " ORDER BY grado, curso, nombre"
            cursor.execute(query, params)
            estudiantes_filtrados = cursor.fetchall()
        except Exception:
            estudiantes_filtrados = []

        # Para cada estudiante, buscar resultado en DB
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        for est in estudiantes_filtrados:
            documento, nombre, grado, curso = est
            documento = str(documento).strip()
            nombre = str(nombre).strip()
            grado = str(grado).strip()
            curso = str(curso).strip()

            # Buscar resultado para este estudiante, área y evaluación
            query = """
                SELECT nota, estado_examen, hora_inicio, hora_fin, evaluacion
                FROM resultados
                WHERE documento = ? AND estado_examen IN ('FINALIZADO','PRESENTADO')
            """
            params = [documento]
            if area_sel:
                query += " AND area = ?"
                params.append(area_sel)
            if evaluacion_sel:
                query += " AND evaluacion = ?"
                params.append(evaluacion_sel)
            query += " ORDER BY id DESC LIMIT 1"

            cursor.execute(query, params)
            resultado = cursor.fetchone()

            if resultado:
                nota, estado, hora_inicio, hora_fin, evaluacion = resultado
                nota_str = str(nota) if nota is not None else ""
                estado_str = estado.upper()
                fecha = hora_fin if hora_fin else hora_inicio
                evaluacion_str = evaluacion if evaluacion else ""
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
                except Exception:
                    duracion = ""
            else:
                nota_str = ""
                estado_str = "EXAMEN NO PRESENTADO"
                fecha = ""
                evaluacion_str = evaluacion_sel if evaluacion_sel else ""
                duracion = ""

            # Agregar fila a tabla
            item = self.tabla.insert(
                "",
                "end",
                values=(
                    grado,
                    curso,
                    nombre,
                    area_sel if area_sel else "",
                    evaluacion_str,
                    nota_str,
                    estado_str,
                    fecha,
                    duracion,
                ),
            )
            self._fila_documento[item] = documento

        conn.close()

    def _llenar_combos_filtros(self):
        """Llena los combos de filtros de estudiantes (Grado, Curso, Área, Evaluación)."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Llenar Grados
            cursor.execute(
                "SELECT DISTINCT grado FROM resultados WHERE estado_examen IN ('FINALIZADO','PRESENTADO') AND grado IS NOT NULL ORDER BY grado"
            )
            grados = [r[0] for r in cursor.fetchall() if r[0] is not None]
            self.combo_filtro_grado["values"] = ["Todos"] + grados

            # llenar Cursos
            cursor.execute(
                """
            SELECT DISTINCT curso
            FROM estudiantes
            WHERE estado = 'Activo'
            ORDER BY curso
            """
            )

            cursos = [str(r[0]).strip() for r in cursor.fetchall() if r[0]]

            self.combo_filtro_curso["values"] = ["Todos"] + cursos

            # Llenar Áreas
            cursor.execute(
                "SELECT DISTINCT area FROM resultados WHERE estado_examen IN ('FINALIZADO','PRESENTADO') AND area IS NOT NULL ORDER BY area"
            )
            areas = [r[0] for r in cursor.fetchall() if r[0] is not None]
            self.combo_filtro_area["values"] = ["Todos"] + (
                areas if areas else ["General"]
            )
            self.combo_filtro_area.current(0)

            # Llenar Evaluaciones
            cursor.execute(
                "SELECT DISTINCT evaluacion FROM resultados WHERE estado_examen IN ('FINALIZADO','PRESENTADO') AND evaluacion IS NOT NULL ORDER BY evaluacion"
            )
            evaluaciones = [r[0] for r in cursor.fetchall() if r[0] is not None]
            self.combo_filtro_evaluacion["values"] = ["Todos"] + evaluaciones

            conn.close()

            # Seleccionar "Todos" por defecto
            try:
                self.combo_filtro_grado.current(0)
                self.combo_filtro_curso.current(0)
                self.combo_filtro_area.current(0)
                self.combo_filtro_evaluacion.current(0)
            except Exception:
                pass
        except Exception:
            pass

    def _limpiar_filtros(self):
        """Limpia todos los filtros de estudiantes."""
        try:
            self.combo_filtro_grado.current(0)
            self.combo_filtro_curso.current(0)
            self.combo_filtro_area.current(0)
            self.combo_filtro_evaluacion.current(0)
            self.cargar_datos()
        except Exception:
            pass

    def _llenar_combo_grados(self):
        try:
            # Obtener grados y cursos desde SQLite (ahora es la fuente principal)
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Obtener grados desde la tabla estudiantes
            cursor.execute(
                "SELECT DISTINCT grado FROM estudiantes WHERE estado = 'Activo' AND grado IS NOT NULL ORDER BY grado"
            )
            grados = [r[0] for r in cursor.fetchall() if r[0]]
            grados = sorted([normalizar_grado(g) for g in grados])

            # Obtener cursos desde la tabla estudiantes
            cursor.execute(
                "SELECT DISTINCT curso FROM estudiantes WHERE estado = 'Activo' AND curso IS NOT NULL ORDER BY curso"
            )
            cursos = sorted(
                [str(r[0]).strip().upper() for r in cursor.fetchall() if r and r[0]]
            )

            conn.close()

            # Llenar combos de filtros
            self.combo_filtro_grado["values"] = ["Todos"] + [str(g) for g in grados]
            self.combo_filtro_grado.current(0)
            self.combo_filtro_curso["values"] = ["Todos"] + [str(c) for c in cursos]
            self.combo_filtro_curso.current(0)

            valores_cfg = ["Seleccione"] + [str(g) for g in grados]

            # Si existe el combo de grado en el panel de configuración, actualizarlo también
            try:
                self.combo_grado_cfg["values"] = valores_cfg
                self.combo_grado_cfg.current(0)
                self._llenar_combo_cursos_cfg()
            except Exception:
                pass
        except Exception:
            pass

    def _llenar_combo_areas(self):
        """Llena el combo de áreas desde el archivo de preguntas."""
        try:
            areas = cargar_areas()
            # Llenar combo de filtros con todas las áreas
            self.combo_filtro_area["values"] = ["Todos"] + (
                areas if areas else ["General"]
            )
            self.combo_filtro_area.current(0)

            # Para configuración
            valores_cfg = ["Seleccione"] + (areas if areas else ["General"])
            self.combo_area["values"] = valores_cfg
            self.combo_area.current(0)
        except Exception:
            pass

    def _on_grado_selected_filtro(self):
        """Actualiza cursos, áreas y evaluaciones cuando cambia el grado."""
        grado = self.combo_filtro_grado.get()
        if grado == "Todos":
            grado = None

        # Actualizar cursos por grado desde SQLite
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Normalizar grado seleccionado
            grado_norm = normalizar_grado(grado) if grado else None

            if grado_norm:
                # Filtrar cursos para el grado seleccionado
                cursor.execute(
                    "SELECT DISTINCT curso FROM estudiantes WHERE grado = ? AND estado = 'Activo' AND curso IS NOT NULL ORDER BY curso",
                    (grado_norm,),
                )
            else:
                # Mostrar todos los cursos disponibles
                cursor.execute(
                    "SELECT DISTINCT curso FROM estudiantes WHERE estado = 'Activo' AND curso IS NOT NULL ORDER BY curso"
                )

            cursos_filtrados = sorted(
                [str(c[0]).strip().upper() for c in cursor.fetchall() if c[0]]
            )
            conn.close()

            self.combo_filtro_curso["values"] = ["Todos"] + cursos_filtrados
            self.combo_filtro_curso.current(0)  # Resetear a "Todos"
        except Exception as e:
            print(f"[DEBUG] Error al actualizar cursos: {e}")
            # Fallback: mantener cursos existentes
            pass

        # Actualizar áreas por grado
        if grado:
            areas = cargar_areas_por_grado(grado)
        else:
            areas = cargar_areas()
        self.combo_filtro_area["values"] = ["Todos"] + (areas if areas else ["General"])
        self.combo_filtro_area.current(0)

        # Vaciar evaluaciones
        self.combo_filtro_evaluacion["values"] = ["Todos"]
        self.combo_filtro_evaluacion.current(0)

        self.cargar_datos()

    def _on_curso_selected(self):
        """Actualiza evaluaciones cuando cambia el curso y carga datos."""
        grado_sel = self.combo_filtro_grado.get()
        if grado_sel == "Todos":
            grado_sel = None

        # Cargar áreas por grado (independientemente del curso, ya que áreas dependen solo de grado)
        if grado_sel:
            areas = cargar_areas_por_grado(grado_sel)
        else:
            areas = cargar_areas()
        self.combo_filtro_area["values"] = ["Todos"] + (areas if areas else ["General"])
        self.combo_filtro_area.current(0)

        # Resetear evaluación
        self.combo_filtro_evaluacion["values"] = ["Todos"]
        self.combo_filtro_evaluacion.current(0)

        self.cargar_datos()

    def _llenar_combo_cursos_cfg(self, grado=None):
        """Carga cursos del panel de configuración según grado (sin opción 'Todos')."""
        try:
            if grado is None:
                grado = (
                    self.combo_grado_cfg.get()
                    if hasattr(self, "combo_grado_cfg")
                    else None
                )

            if not grado or grado == "Seleccione":
                self.combo_curso_cfg["values"] = ["Seleccione"]
                self.combo_curso_cfg.current(0)
                return

            grado_norm = normalizar_grado(grado)
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT curso FROM estudiantes WHERE estado = 'Activo' AND grado = ? AND curso IS NOT NULL ORDER BY curso",
                (grado_norm,),
            )
            cursos = sorted(
                [str(r[0]).strip().upper() for r in cursor.fetchall() if r and r[0]]
            )
            conn.close()

            valores = ["Seleccione"] + cursos if cursos else ["Seleccione"]
            self.combo_curso_cfg["values"] = valores
            self.combo_curso_cfg.current(0)
        except Exception:
            try:
                self.combo_curso_cfg["values"] = ["Seleccione"]
                self.combo_curso_cfg.current(0)
            except Exception:
                pass

    def _llenar_combo_areas_por_grado(self):
        """Llena el combo de áreas teniendo en cuenta el grado seleccionado.

        Si el grado es 'Todos' se muestran todas las áreas; si es específico,
        se usan las áreas disponibles para ese grado (cargar_areas_por_grado).
        """
        try:
            grado_sel = None
            # Preferir grado seleccionado en el panel de configuración si existe
            try:
                g = None
                if hasattr(self, "combo_grado_cfg"):
                    g = self.combo_grado_cfg.get()
                    if g and g not in ("Todos", "Seleccione"):
                        grado_sel = g
            except Exception:
                grado_sel = None

            if grado_sel:
                areas = cargar_areas_por_grado(normalizar_grado(grado_sel))
            else:
                areas = cargar_areas()

            valores = ["Seleccione"] + (areas if areas else ["General"])
            self.combo_area["values"] = valores
            self.combo_area.current(0)
            try:
                self.combo_area_cfg["values"] = valores
                self.combo_area_cfg.current(0)
            except Exception:
                pass
        except Exception:
            pass

    def _llenar_combo_evaluaciones_por_grado_area(self, grado=None, area=None):
        """Llena el combo de evaluaciones basado SOLO en grado y área seleccionados.

        Solo retorna evaluaciones donde grado == seleccionado AND area == seleccionado.
        Se resetea a "Seleccione" si no hay grado o área seleccionado.
        """
        try:
            # Usar parámetros si se proporcionan, sino obtener de combos de filtro
            if grado is None:
                if hasattr(self, "combo_filtro_grado"):
                    grado = self.combo_filtro_grado.get()
                    if grado == "Todos":
                        grado = None
                elif hasattr(self, "combo_grado_cfg"):
                    grado = self.combo_grado_cfg.get()
                    if grado in ("Todos", "Seleccione"):
                        grado = None
            if area is None:
                if hasattr(self, "combo_filtro_area"):
                    area = self.combo_filtro_area.get()
                    if area == "Todos":
                        area = None
                elif hasattr(self, "combo_area_cfg"):
                    area = self.combo_area_cfg.get()
                    if area in ("Todos", "General", "Seleccione"):
                        area = None

            print(
                f"[DEBUG] _llenar_combo_evaluaciones_por_grado_area: grado={repr(grado)}, area={repr(area)}"
            )

            # Si no hay grado o área seleccionado, resetear combo
            if not grado or not area:
                print(
                    f"[DEBUG] Sin grado o área seleccionado, reseteando combo evaluaciones"
                )
                if hasattr(self, "combo_filtro_evaluacion"):
                    self.combo_filtro_evaluacion["values"] = ["Todos"]
                    self.combo_filtro_evaluacion.current(0)
                return

            # Obtener evaluaciones para grado+area
            evaluaciones = cargar_evaluaciones_por_grado_y_area(grado, area)

            # Llenar combo
            valores = ["Todos"] + (evaluaciones if evaluaciones else [])
            if hasattr(self, "combo_filtro_evaluacion"):
                self.combo_filtro_evaluacion["values"] = valores
                self.combo_filtro_evaluacion.current(0)

            # También actualizar el combo de configuración (si existe)
            try:
                valores_cfg = ["Seleccione"] + (evaluaciones if evaluaciones else [])
                self.combo_evaluacion_cfg["values"] = valores_cfg
                self.combo_evaluacion_cfg.current(0)
            except Exception:
                pass

            print(f"[DEBUG] Combo evaluaciones actualizado: {valores}")

        except Exception as e:
            print(f"[DEBUG] Error en _llenar_combo_evaluaciones_por_grado_area: {e}")
            import traceback

            traceback.print_exc()
            # En caso de error, resetear
            try:
                self.combo_filtro_evaluacion["values"] = ["Todos"]
                self.combo_filtro_evaluacion.current(0)
            except Exception:
                pass

            # Fallback: leer evaluaciones desde SQLite
            evaluaciones = []
            try:
                grado_norm = normalizar_grado(grado) if grado else ""
                area_norm = str(area).strip().lower() if area else ""

                if grado_norm and area_norm:
                    with sqlite3.connect(DB_FILE) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            SELECT DISTINCT evaluacion
                            FROM banco_preguntas
                            WHERE LOWER(TRIM(grado)) = LOWER(TRIM(?))
                              AND LOWER(TRIM(area)) = LOWER(TRIM(?))
                              AND evaluacion IS NOT NULL
                              AND TRIM(evaluacion) <> ''
                            ORDER BY evaluacion
                            """,
                            (grado_norm, area_norm),
                        )
                        evaluaciones = [
                            str(r[0]).strip() for r in cursor.fetchall() if r and r[0]
                        ]

                print(
                    f"[DEBUG] Evaluaciones fallback SQLite para grado='{grado_norm}' área='{area_norm}': {evaluaciones}"
                )

            except Exception as e:
                print(f"[DEBUG] Error al consultar SQLite de evaluaciones: {e}")
                evaluaciones = []

            # Limpiar y filtrar evaluaciones inválidas
            evaluaciones = [
                str(e).strip()
                for e in evaluaciones
                if e and str(e).strip().lower() not in ["nan", "none", ""]
            ]
            evaluaciones = sorted(list(set(evaluaciones)))

            print(f"[DEBUG] Evaluaciones finales (después de limpiar): {evaluaciones}")

            # Actualizar combo
            valores = ["Seleccione"] + (evaluaciones if evaluaciones else [])
            try:
                self.combo_evaluacion_cfg["values"] = valores
                self.combo_evaluacion_cfg.current(0)
                print(
                    f"[DEBUG] Combo evaluación actualizado con {len(valores)} valores"
                )
            except Exception as e:
                print(f"[DEBUG] Error al actualizar combo evaluación: {e}")
                pass

        except Exception as e:
            print(
                f"[DEBUG] Error general en _llenar_combo_evaluaciones_por_grado_area: {e}"
            )
            try:
                self.combo_evaluacion_cfg["values"] = ["Seleccione"]
                self.combo_evaluacion_cfg.current(0)
            except Exception:
                pass

    def _on_grado_selected(self, event=None):
        """Callback cuando se selecciona un grado: actualiza áreas, evaluaciones y recarga datos."""
        try:
            self._llenar_combo_cursos_cfg()
        except Exception:
            pass
        try:
            self._llenar_combo_areas_por_grado()
        except Exception:
            pass
        # También actualizar el combo de evaluaciones del panel de configuración
        # (la evaluación depende de grado+área y puede cambiar al seleccionar un nuevo grado).
        try:
            self._on_area_selected_cfg()
        except Exception:
            pass
        try:
            # Resetear evaluaciones cuando cambia el grado en filtros
            self.cargar_datos()
        except Exception:
            pass

    def _on_area_selected(self):
        """Callback cuando se selecciona un área en filtros: actualiza evaluaciones y recarga datos."""
        grado = self.combo_filtro_grado.get()
        if grado == "Todos":
            grado = None
        area = self.combo_filtro_area.get()
        if area == "Todos":
            area = None
        self._llenar_combo_evaluaciones_por_grado_area(grado, area)
        self.cargar_datos()

    def _on_area_selected_cfg(self, event=None):
        """Callback cuando se selecciona un área en el panel de configuración.

        Carga evaluaciones basadas en grado+área y las muestra en el combo de Evaluación.
        Luego carga la configuración del área.
        """
        try:
            # Obtener grado y área seleccionados
            grado_sel = None
            try:
                g = self.combo_grado_cfg.get()
                if g and g.strip() and g != "Seleccione":
                    grado_sel = g
            except Exception:
                grado_sel = None

            area_sel = None
            try:
                a = self.combo_area_cfg.get()
                if a and a.strip() and a != "Seleccione":
                    area_sel = a
            except Exception:
                area_sel = None

            # Cargar evaluaciones usando la nueva función
            if grado_sel and area_sel:
                evaluaciones = cargar_evaluaciones_por_grado_y_area(grado_sel, area_sel)

                # Actualizar combo de evaluación
                valores = ["Seleccione"] + (evaluaciones if evaluaciones else [])
                try:
                    self.combo_evaluacion_cfg["values"] = valores
                    self.combo_evaluacion_cfg.current(0)
                    print(
                        f"[DEBUG] Combo evaluación actualizado con {len(valores)} valores: {valores}"
                    )
                except Exception as e:
                    print(f"[DEBUG] Error al actualizar combo evaluación: {e}")
            else:
                # Si no hay grado o área, resetear evaluaciones
                try:
                    self.combo_evaluacion_cfg["values"] = ["Seleccione"]
                    self.combo_evaluacion_cfg.current(0)
                except Exception:
                    pass

        except Exception as e:
            print(f"[DEBUG] Error en _on_area_selected_cfg: {e}")
            pass

        try:
            # Luego, cargar la configuración del área
            self._cargar_config_area()
        except Exception:
            pass

    def _cargar_config_area(self, event=None):
        """Carga la configuración actual del área seleccionada en los campos."""
        try:
            # Obtener valores seleccionados en el panel de configuración
            try:
                grado = self.combo_grado_cfg.get()
            except Exception:
                grado = None
            try:
                area = self.combo_area_cfg.get()
            except Exception:
                area = None
            try:
                evaluacion = self.combo_evaluacion_cfg.get()
            except Exception:
                evaluacion = None
            try:
                curso = self.combo_curso_cfg.get()
            except Exception:
                curso = None

            if not area:
                return

            # Normalizar selecciones 'Seleccione' a None
            if grado == "Seleccione":
                grado = None
            if area == "Seleccione":
                area = None
            if evaluacion == "Seleccione":
                evaluacion = None
            if curso == "Seleccione":
                curso = None

            duracion, cantidad, max_intentos, permitir_reintentos, examen_activo = (
                cargar_config_examen(area, grado, evaluacion, curso)
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
            try:
                self.var_examen_activo.set(bool(examen_activo))
            except Exception:
                self.var_examen_activo.set(False)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la configuración: {e}")

    def guardar_config(self):
        """Guarda la configuración de examen incluyendo límite de intentos."""
        try:
            # Obtener selección de grado/area/evaluacion desde el panel de configuración
            try:
                grado = self.combo_grado_cfg.get()
            except Exception:
                grado = None
            try:
                area = self.combo_area_cfg.get()
            except Exception:
                area = None
            try:
                evaluacion = self.combo_evaluacion_cfg.get()
            except Exception:
                evaluacion = None
            try:
                curso = self.combo_curso_cfg.get()
            except Exception:
                curso = None

            duracion_min = int(self.entry_duracion.get())
            cantidad = int(self.entry_cantidad.get())
            max_intentos = int(self.entry_max_intentos.get())
            permitir_reintentos = 1 if self.var_permitir_reintentos.get() else 0
            # Validaciones de campos obligatorios
            if not grado or grado == "Seleccione":
                messagebox.showerror("Error", "Debe seleccionar un grado.")
                return
            if not area or area == "Seleccione":
                messagebox.showerror("Error", "Debe seleccionar un área.")
                return
            if not evaluacion or evaluacion == "Seleccione":
                messagebox.showerror("Error", "Debe seleccionar una evaluación.")
                return
            if not curso or curso == "Seleccione":
                messagebox.showerror("Error", "Debe seleccionar un curso.")
                return

            if duracion_min <= 0 or cantidad <= 0 or max_intentos <= 0:
                messagebox.showwarning(
                    "Advertencia",
                    "Duración, cantidad e intentos deben ser mayores que 0.",
                )
                return

            duracion_seg = duracion_min * 60
            examen_activo = 1 if self.var_examen_activo.get() else 0

            if guardar_config_examen(
                grado,
                area,
                evaluacion,
                duracion_seg,
                cantidad,
                max_intentos,
                permitir_reintentos,
                examen_activo,
                curso=curso,
            ):
                reintentos_txt = "Sí" if permitir_reintentos else "No"
                messagebox.showinfo(
                    "Éxito",
                    f"Configuración guardada:\n"
                    f"- Grado: {grado}\n"
                    f"- Curso: {curso}\n"
                    f"- Área: {area}\n"
                    f"- Evaluación: {evaluacion}\n"
                    f"- Duración: {duracion_min} min\n"
                    f"- Preguntas: {cantidad}\n"
                    f"- Máx. Intentos: {max_intentos}\n"
                    f"- Permitir Reintentos: {reintentos_txt}\n- Habilitado: {'Sí' if examen_activo else 'No'}",
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
        # Frame contenedor para la tabla y scrollbar
        self.frame_tabla = tk.Frame(self.ventana)
        self.frame_tabla.pack(fill="both", expand=True, padx=20, pady=0)

        # Scrollbar vertical
        self.scrollbar = tk.Scrollbar(self.frame_tabla, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

        # Columnas: Grado | Curso | Nombre | Area | Evaluacion | Nota | Estado | Fecha | Duracion
        self.tabla = ttk.Treeview(
            self.frame_tabla,
            columns=(
                "Grado",
                "Curso",
                "Nombre",
                "Area",
                "Evaluacion",
                "Nota",
                "Estado",
                "Fecha",
                "Duracion",
            ),
            show="headings",
            yscrollcommand=self.scrollbar.set,
        )

        self.scrollbar.config(command=self.tabla.yview)

        self.tabla.heading("Grado", text="Grado")
        self.tabla.heading("Curso", text="Curso")
        self.tabla.heading("Nombre", text="Nombre")
        self.tabla.heading("Area", text="Area")
        self.tabla.heading("Evaluacion", text="Evaluacion")
        self.tabla.heading("Nota", text="Nota")
        self.tabla.heading("Estado", text="Estado")
        self.tabla.heading("Fecha", text="Fecha")
        self.tabla.heading("Duracion", text="Duración")

        self.tabla.pack(fill="both", expand=True)

        # Permitir que las columnas se estiren y ajustar al cambiar tamaño
        self.tabla.column("Grado", stretch=True)
        self.tabla.column("Curso", stretch=True)
        self.tabla.column("Nombre", stretch=True)
        self.tabla.column("Area", stretch=True)
        self.tabla.column("Evaluacion", stretch=True)
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
        # Recuperar documento desde diccionario privado
        documento = self._fila_documento.get(item)
        if not documento:
            messagebox.showerror(
                "Error", "No se pudo determinar el documento del registro seleccionado."
            )
            return

        vals = self.tabla.item(item, "values")
        nombre = vals[2] if len(vals) > 2 else ""
        area_sel = vals[3] if len(vals) > 3 else None

        pregunta = f"¿Desea resetear la nota de {nombre}?"
        if messagebox.askyesno("Confirmar", pregunta):
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
        # Recuperar documento desde diccionario privado
        documento = self._fila_documento.get(item)
        if not documento:
            messagebox.showerror(
                "Error", "No se pudo determinar el documento del registro seleccionado."
            )
            return

        vals = self.tabla.item(item, "values")
        area_sel = vals[3] if len(vals) > 3 else None

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
        # Recuperar documento desde diccionario privado
        documento = self._fila_documento.get(item)
        if not documento:
            messagebox.showerror(
                "Error", "No se pudo determinar el documento del registro seleccionado."
            )
            return

        vals = self.tabla.item(item, "values")
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
            # Obtener filtros de estudiantes (NO de configuración)
            grado_sel = None
            try:
                g = self.combo_filtro_grado.get()
                if g and g != "Todos":
                    grado_sel = g.strip()
            except Exception:
                pass

            curso_sel = None
            try:
                c = self.combo_filtro_curso.get()
                if c and c.lower() != "todos" and c != "":
                    curso_sel = c.strip()
            except Exception:
                pass

            area_sel = None
            try:
                a = self.combo_filtro_area.get()
                if a and a.lower() != "todos" and a != "":
                    area_sel = a.strip()
            except Exception:
                pass

            evaluacion_sel = None
            try:
                e = self.combo_filtro_evaluacion.get()
                if e and e.lower() != "todos" and e != "":
                    evaluacion_sel = e.strip()
            except Exception:
                pass

            # Exportar con los filtros de estudiantes
            exportar_reporte_por_filtros(grado_sel, curso_sel, area_sel, evaluacion_sel)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    def exportar_consolidado(self):
        try:
            # Obtener filtros: grado y área son obligatorios para consolidado
            grado_sel = None
            try:
                g = self.combo_filtro_grado.get()
                if g and g != "Todos":
                    grado_sel = g.strip()
            except Exception:
                pass

            curso_sel = None
            try:
                c = self.combo_filtro_curso.get()
                if c and c.lower() != "todos" and c != "":
                    curso_sel = c.strip()
            except Exception:
                pass

            area_sel = None
            try:
                a = self.combo_filtro_area.get()
                if a and a.lower() != "todos" and a != "":
                    area_sel = a.strip()
            except Exception:
                pass

            if not grado_sel:
                messagebox.showwarning(
                    "Filtro requerido",
                    "Seleccione un Grado para exportar el consolidado.",
                )
                return

            if not area_sel:
                messagebox.showwarning(
                    "Filtro requerido",
                    "Seleccione un Área para exportar el consolidado.",
                )
                return

            # Exportar consolidado del período (incluyendo curso si está seleccionado)
            exportar_consolidado_periodo(grado_sel, area_sel, curso_sel)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el consolidado: {e}")


def abrir_docente(nombre, cerrar_sesion_cb=None):
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

    ModuloDocente(ventana_docente, nombre, cerrar_sesion_cb=cerrar_sesion_cb)
    ventana_docente.mainloop()


# ================= MÓDULO ESTUDIANTE =================


class ModuloEstudiante:

    def __init__(
        self, ventana, documento, nombre, grado, curso=None, cerrar_sesion_cb=None
    ):
        self.ventana = ventana
        self.documento = documento
        self.nombre = nombre
        # Normalizar grado al instanciar el módulo
        self.grado = normalizar_grado(grado)
        self.curso = curso
        self.current_intento_id = None
        self.cerrar_sesion_cb = cerrar_sesion_cb

        self.ventana.title("Panel del Estudiante")
        self.ventana.configure(bg=COLOR_SECUNDARIO)

        header = tk.Frame(self.ventana, bg=COLOR_PRIMARIO, height=100)
        header.pack(fill="x")
        header.pack_propagate(False)

        if cerrar_sesion_cb:
            tk.Button(
                header,
                text="🚪 Cerrar sesión",
                font=("Segoe UI", 10, "bold"),
                bg="#cc3300",
                fg="white",
                relief="flat",
                cursor="hand2",
                padx=12,
                pady=6,
                command=cerrar_sesion_cb,
            ).pack(side="right", padx=15, pady=15)

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
        crear_footer(self.ventana)

    # ---------------------------------------------------

    def _mostrar_areas(self):
        for w in self.contenido.winfo_children():
            w.destroy()

        areas = cargar_areas_por_grado(self.grado)

        def on_area_click(a):
            print("CLICK OK")
            try:
                estado_info = obtener_estado_area(self.documento, a)
            except Exception as e:
                print("Error obteniendo estado del área:", e)
                estado_info = None
            # Verificar si el examen está habilitado por el docente
            try:
                activo = examen_esta_activo(a)
            except Exception:
                activo = False

            if not activo:
                # Si no está activo, permitir ver resultados si ya fue presentado
                if estado_info and estado_info[0] in ("PRESENTADO", "REVISION_ACTIVA"):
                    if estado_info[0] == "REVISION_ACTIVA":
                        self._ver_resultado(a)
                    else:
                        nota = estado_info[1]
                        messagebox.showinfo(
                            "Area presentada",
                            f"Ya presentaste esta área.\nNota: {nota}\nEl docente no ha autorizado la revisión.",
                        )
                else:
                    messagebox.showinfo(
                        "Examen cerrado",
                        "⛔ Examen no habilitado por el docente. Contacta con tu profesor.",
                    )
                return

            # Si está activo, comportamiento normal según estado
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

        # Crear botones de áreas con colores según estado y si el examen está activo
        for area in areas:
            estado_info = obtener_estado_area(self.documento, area)
            try:
                activo = examen_esta_activo(area)
            except Exception:
                activo = False

            # Determinar color y texto según estado y activación
            if not activo and (estado_info is None or estado_info[0] == "DISPONIBLE"):
                color_bg = "#999999"  # Gris - cerrado
                texto_estado = "🔒 Cerrado"
                icono = "🔒"
            elif activo and (estado_info is None or estado_info[0] == "DISPONIBLE"):
                color_bg = "#51cf66"  # Verde - disponible
                texto_estado = "🟢 Disponible"
                icono = "✓"
            elif estado_info and estado_info[0] == "REVISION_ACTIVA":
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

    def _iniciar_examen(self, area):
        print("INICIANDO EXAMEN ->", area)
        estado_info = obtener_estado_area(self.documento, area)

        # Obtener la evaluación seleccionada en combo_evaluacion_cfg, si está disponible
        evaluacion = None
        try:
            evaluacion = (
                self.combo_evaluacion_cfg.get()
                if hasattr(self, "combo_evaluacion_cfg")
                else None
            )
            if evaluacion and evaluacion.lower() in ["seleccione", "general", ""]:
                evaluacion = None
        except Exception:
            pass

        # Si no hay evaluación del combo, obtenerla de config_examenes (por grado/área/curso)
        if not evaluacion:
            try:
                curso = str(self.curso).strip() if self.curso is not None else ""
                if curso == "":
                    curso = "TODOS"

                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT evaluacion FROM config_examenes "
                    "WHERE grado = ? AND area = ? "
                    "AND (curso = ? OR curso = 'TODOS') "
                    "AND habilitado = 1 "
                    "ORDER BY (curso = 'TODOS') ASC LIMIT 1",
                    (str(self.grado), str(area), curso),
                )
                resultado = cursor.fetchone()
                conn.close()
                if resultado:
                    evaluacion = resultado[0]
            except Exception:
                pass

        # Normalizar evaluación para consistencia
        if evaluacion:
            evaluacion = str(evaluacion).strip().lower()
            if evaluacion.lower() in ["nan", "none", ""]:
                evaluacion = None

        print(f"[DEBUG] Evaluación obtenida: {repr(evaluacion)}")

        duracion, cantidad, max_intentos, permitir_reintentos, habilitado = (
            cargar_config_examen(area, self.grado, evaluacion, self.curso)
        )

        if not habilitado:
            # Si el examen está deshabilitado, no permitir iniciar (mantener historial)
            messagebox.showinfo(
                "Examen cerrado",
                "⛔ El docente ha deshabilitado este examen. Contacta con tu profesor.",
            )
            return

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM resultados WHERE documento=? AND area=? AND estado_examen IN ('FINALIZADO','PRESENTADO')",
            (self.documento, area),
        )
        intentos_previos = cursor.fetchone()[0]
        conn.close()

        print(
            "estado_info:",
            estado_info,
            "intentos_previos:",
            intentos_previos,
            "max_intentos:",
            max_intentos,
            "permitir_reintentos:",
            permitir_reintentos,
        )

        if estado_info and estado_info[0] in ["PRESENTADO", "REVISION_ACTIVA"]:
            if not permitir_reintentos or intentos_previos >= max_intentos:
                messagebox.showwarning(
                    "No disponible", "Ya alcanzaste el límite de intentos."
                )
                return

        try:
            # Obtener curso del estudiante desde la tabla estudiantes en SQLite
            curso = None
            try:
                estudiante = validar_estudiante(self.documento)
                if isinstance(estudiante, dict):
                    curso_val = estudiante.get("curso")
                    if _tiene_valor(curso_val):
                        curso = str(curso_val).strip()
            except Exception:
                pass

            intento_num, intento_id = registrar_inicio(
                self.documento, self.nombre, self.grado, area, evaluacion, curso
            )
            print("Registro de inicio exitoso:", intento_num, intento_id)
            self.current_intento_id = intento_id
        except Exception as e:
            # No silenciamos la excepción: la mostramos en consola y avisamos al usuario
            print("Error en registrar_inicio:", e)
            messagebox.showerror("Error", f"No fue posible iniciar el examen: {e}")
            return

        self._mostrar_pantalla_informativa(area, cantidad, duracion, evaluacion)

    # ---------------------------------------------------

    def _mostrar_pantalla_informativa(
        self, area, cantidad_preguntas, duracion_segundos, evaluacion=None
    ):
        print(
            "MOSTRANDO PANTALLA INFORMATIVA ->",
            area,
            cantidad_preguntas,
            duracion_segundos,
        )
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
            command=(
                lambda a=area, c=cantidad_preguntas, d=duracion_segundos, e=evaluacion: self._mostrar_examen(
                    a, c, d, e
                )
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
        self, area, cantidad_preguntas, duracion_segundos, evaluacion=None
    ):
        for w in self.contenido.winfo_children():
            w.destroy()

        print(f"\n[DEBUG] ====== _MOSTRAR_EXAMEN ======")
        print(
            f"[DEBUG] Parámetros: area={repr(area)}, grado={repr(self.grado)}, documento={repr(self.documento)}"
        )
        print(f"[DEBUG] Cantidad a cargar: {cantidad_preguntas}")

        todas = cargar_preguntas_filtradas(
            area=area, grado=self.grado, evaluacion=evaluacion, curso=self.curso
        )

        # Validar retorno de cargar_preguntas_filtradas
        if todas is None or not hasattr(todas, "empty"):
            print(
                f"[DEBUG] ❌ cargar_preguntas_filtradas devolvió valor inválido: {type(todas)}"
            )
            messagebox.showwarning(
                "Error al cargar preguntas",
                f"Error interno: la consulta de preguntas no retornó datos válidos.\n"
                f"Por favor, contacta al administrador.",
            )
            self._mostrar_areas()
            return

        if todas.empty:
            print(
                f"[DEBUG] ❌ DataFrame vacío - NO hay preguntas para area={repr(area)}, grado={repr(self.grado)}"
            )
            # Proveer información diagnóstica más detallada al usuario
            detalles_adicionales = ""
            try:
                # Consultar SQLite para mostrar ejemplos de áreas y grados disponibles
                with sqlite3.connect(DB_FILE) as conn:
                    df_all = pd.read_sql_query(
                        "SELECT area, grado FROM banco_preguntas", conn
                    )
                df_all.columns = df_all.columns.str.strip().str.lower()
                areas_disp = []
                grados_disp = []
                if "area" in df_all.columns:
                    areas_disp = sorted(
                        df_all["area"]
                        .astype(str)
                        .str.strip()
                        .str.lower()
                        .dropna()
                        .unique()
                        .tolist()
                    )
                if "grado" in df_all.columns:
                    grados_disp = sorted(
                        df_all["grado"]
                        .astype(str)
                        .str.strip()
                        .str.lower()
                        .dropna()
                        .unique()
                        .tolist()
                    )

                detalles_adicionales = (
                    "\n\nEjemplos disponibles en banco_preguntas (SQLite):\n"
                    f"- Áreas: {', '.join(areas_disp[:10]) if areas_disp else 'Ninguna encontrada'}\n"
                    f"- Grados: {', '.join(grados_disp[:10]) if grados_disp else 'Ninguno encontrado'}"
                )
            except Exception:
                detalles_adicionales = (
                    "\n\n(No se pudo consultar SQLite para mostrar ejemplos)"
                )

            messagebox.showwarning(
                "Sin preguntas disponibles",
                f"No hay preguntas para:\n"
                f"• Área: {area}\n"
                f"• Grado: {self.grado}\n\n"
                f"Verifica que:\n"
                f"• Existan preguntas para esta combinación en la base de datos\n"
                f"• Los campos 'area' y 'grado' estén correctamente configurados (formatos/valores)"
                f"{detalles_adicionales}",
            )
            self._mostrar_areas()
            return

        print(f"[DEBUG] Cargadas {len(todas)} preguntas")
        print(
            f"[DEBUG] Grados únicos en 'todas': {todas['grado'].unique().tolist() if 'grado' in todas.columns else 'SIN COLUMNA GRADO'}"
        )
        print(
            f"[DEBUG] Áreas únicas en 'todas': {todas['area'].unique().tolist() if 'area' in todas.columns else 'SIN COLUMNA AREA'}"
        )
        print(
            f"[DEBUG] IDs en 'todas': {todas['id'].tolist() if 'id' in todas.columns else 'SIN COLUMNA ID'}"
        )

        # VALIDACIÓN: Todas las preguntas deben ser del grado del estudiante
        if "grado" in todas.columns:
            grados_unicos = todas["grado"].unique().tolist()
            if (
                len(grados_unicos) != 1
                or grados_unicos[0] != str(self.grado).strip().lower()
            ):
                print(
                    f"[DEBUG] ⚠️ ADVERTENCIA: Las preguntas tienen múltiples grados o no coinciden con {repr(self.grado)}"
                )
                print(f"[DEBUG] Grados en preguntas: {grados_unicos}")

        # Seleccionar aleatoriamente y limitar a la cantidad requerida
        try:
            if cantidad_preguntas and int(cantidad_preguntas) > 0:
                n = int(cantidad_preguntas)
            else:
                n = len(todas)
        except Exception:
            n = len(todas)

        print(f"[DEBUG] Seleccionando {n} de {len(todas)} preguntas")
        if n >= len(todas):
            seleccion = todas.sample(frac=1).reset_index(drop=True)  # mezclar todo
        else:
            seleccion = todas.sample(n=n).reset_index(drop=True)

        print(f"[DEBUG] Después de sample():")
        print(
            f"  Grados en 'seleccion': {seleccion['grado'].unique().tolist() if 'grado' in seleccion.columns else 'ERROR'}"
        )
        print(
            f"  Áreas en 'seleccion': {seleccion['area'].unique().tolist() if 'area' in seleccion.columns else 'ERROR'}"
        )
        print(f"[DEBUG] ================================\n")

        # Construir lista de preguntas presentadas con opciones mezcladas y mapeo
        presentadas = []
        letras = ["A", "B", "C", "D"]
        for _, row in seleccion.iterrows():
            # Obtener textos de opciones originales
            opt_texts = [
                ("A", str(row.get("opcion_a", "")).strip()),
                ("B", str(row.get("opcion_b", "")).strip()),
                ("C", str(row.get("opcion_c", "")).strip()),
                ("D", str(row.get("opcion_d", "")).strip()),
            ]

            # Shuffle copy
            shuffled = opt_texts.copy()
            random.shuffle(shuffled)

            # Map shuffled options to letters A-D for display
            opciones_map = {}
            for i, pair in enumerate(shuffled):
                opciones_map[letras[i]] = pair[1]

            # Determinar letra correcta en el nuevo orden
            orig_correct = str(row.get("correcta", "")).strip().upper()
            correct_text = None
            if orig_correct in ["A", "B", "C", "D"]:
                correct_text = str(
                    row.get(f"opcion_{orig_correct.lower()}", "")
                ).strip()

            nueva_letra = ""
            if correct_text is not None:
                for letra, texto in opciones_map.items():
                    if texto == correct_text:
                        nueva_letra = letra
                        break

            presentadas.append(
                {
                    "id": (
                        int(row.get("id"))
                        if "id" in row and pd.notna(row.get("id"))
                        else None
                    ),
                    "enunciado": str(row.get("enunciado", "")),
                    "contexto": str(row.get("contexto", "")),
                    "imagen": (
                        str(row.get("imagen", ""))
                        if pd.notna(row.get("imagen", ""))
                        else None
                    ),
                    "opciones": opciones_map,
                    "correcta": nueva_letra if nueva_letra else orig_correct,
                    "grado": str(row.get("grado", "")),
                }
            )

        # mezclar orden de preguntas presentadas
        random.shuffle(presentadas)

        preguntas = presentadas

        contador = {
            "indice": 0,
            "correctas": 0,
            "tiempo": int(duracion_segundos),
            "timer_id": None,
        }
        respuestas = []

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

            preg = preguntas[contador["indice"]]

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

            # Mostrar contenido de la pregunta ya preparada
            label_contexto.config(
                text=str(preg.get("contexto", "")) if isinstance(preg, dict) else ""
            )
            label_enunciado.config(text=str(preg.get("enunciado", "")))

            # Configurar textos de opciones desde el mapeo
            opciones = preg.get("opciones", {})
            radios["A"].config(text="A. " + opciones.get("A", ""))
            radios["B"].config(text="B. " + opciones.get("B", ""))
            radios["C"].config(text="C. " + opciones.get("C", ""))
            radios["D"].config(text="D. " + opciones.get("D", ""))

            var.set("")
            canvas.yview_moveto(0)

        def siguiente():
            if var.get() == "":
                messagebox.showwarning("Advertencia", "Selecciona una respuesta.")
                return

            preg = preguntas[contador["indice"]]
            correcta = str(preg.get("correcta", "")).strip().upper()
            seleccion = var.get().strip().upper()
            es_corr = 1 if seleccion == correcta else 0

            if es_corr:
                contador["correctas"] += 1

            # Obtener id y datos para almacenar, incluyendo mapeo de opciones
            try:
                pregunta_id = (
                    int(preg.get("id")) if preg.get("id") is not None else None
                )
            except Exception:
                pregunta_id = None

            respuestas.append(
                {
                    "pregunta_id": pregunta_id,
                    "enunciado": str(preg.get("enunciado", "")),
                    "imagen": preg.get("imagen"),
                    "grado": preg.get("grado"),
                    "opciones_map": preg.get("opciones", {}),
                    "respuesta_dada": seleccion,
                    "respuesta_correcta": correcta,
                    "correcta": bool(es_corr),
                }
            )

            contador["indice"] += 1
            mostrar()

        def finalizar():
            try:
                if contador["timer_id"]:
                    self.ventana.after_cancel(contador["timer_id"])
            except Exception:
                pass

            total = len(preguntas)
            nota = round((contador["correctas"] / total) * 5, 2) if total > 0 else 0.0

            nivel_desempeno = "Sin clasificación"
            recomendacion = "Consulte al docente."
            try:
                conn_escala = sqlite3.connect(DB_FILE)
                cursor_escala = conn_escala.cursor()
                cursor_escala.execute(
                    """
                    SELECT
                        COALESCE(NULLIF(TRIM(desempeno), ''), NULLIF(TRIM(concepto), ''), 'Sin clasificación') AS nivel,
                        COALESCE(NULLIF(TRIM(recomendacion), ''), 'Consulte al docente.') AS recomendacion
                    FROM escala_valoracion
                    WHERE ? BETWEEN
                        MIN(
                            CAST(REPLACE(CAST(desde AS TEXT), ',', '.') AS REAL),
                            CAST(REPLACE(CAST(hasta AS TEXT), ',', '.') AS REAL)
                        )
                        AND
                        MAX(
                            CAST(REPLACE(CAST(desde AS TEXT), ',', '.') AS REAL),
                            CAST(REPLACE(CAST(hasta AS TEXT), ',', '.') AS REAL)
                        )
                    LIMIT 1
                    """,
                    (float(nota),),
                )
                fila_escala = cursor_escala.fetchone()
                if fila_escala:
                    nivel_desempeno = fila_escala[0] or "Sin clasificación"
                    recomendacion = fila_escala[1] or "Consulte al docente."
            except Exception:
                pass
            finally:
                try:
                    conn_escala.close()
                except Exception:
                    pass

            try:
                registrar_final(
                    self.documento,
                    nota,
                    area=area,
                    intento_id=self.current_intento_id,
                    respuestas=json.dumps(respuestas),
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
                f"Correctas: {contador['correctas']} de {total}\n"
                f"Nota: {nota}/5.0\n\n"
                f"Nivel: {nivel_desempeno}\n\n"
                f"Recomendación:\n{recomendacion}",
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
            opciones_map = r.get("opciones_map") or {}
            # Si hay mapeo guardado, mostrar texto junto a la letra
            if opciones_map and isinstance(opciones_map, dict):
                texto_sel = opciones_map.get(resp_sel, "")
                texto_corr = opciones_map.get(resp_corr, "")
                resp_sel_display = f"{resp_sel}. {texto_sel}" if resp_sel else ""
                resp_corr_display = f"{resp_corr}. {texto_corr}" if resp_corr else ""
            else:
                resp_sel_display = resp_sel
                resp_corr_display = resp_corr

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
                text=f"Tu respuesta: {resp_sel_display}",
                font=("Segoe UI", 11),
                bg=COLOR_SECUNDARIO,
                fg=("#2b8a3e" if correcta else "#d9534f"),
            ).pack(anchor="w", padx=10)
            tk.Label(
                frame_q,
                text=f"Respuesta correcta: {resp_corr_display}",
                font=("Segoe UI", 11),
                bg=COLOR_SECUNDARIO,
            ).pack(anchor="w", padx=10, pady=(0, 8))


def abrir_docente(nombre, cerrar_sesion_cb=None, parent=None):
    ventana_docente = tk.Toplevel(parent) if parent is not None else tk.Tk()
    # Maximizar la ventana al abrir (Windows: 'zoomed')
    try:
        ventana_docente.state("zoomed")
    except Exception:
        # Fallback a pantalla completa si 'zoomed' no está disponible
        try:
            ventana_docente.attributes("-fullscreen", True)
        except Exception:
            pass

    ModuloDocente(ventana_docente, nombre, cerrar_sesion_cb=cerrar_sesion_cb)
    if parent is None:
        ventana_docente.mainloop()
    return ventana_docente


# ================= LOGIN =================


def _restaurar_login():
    """Muestra nuevamente el login principal y limpia el campo de documento."""
    try:
        ventana.deiconify()
        ventana.lift()
        ventana.focus_force()
    except Exception:
        pass

    try:
        entry_documento.delete(0, tk.END)
        entry_documento.focus_set()
    except Exception:
        pass


def cerrar_modulo_y_mostrar_login(ventana_modulo):
    try:
        if ventana_modulo and ventana_modulo.winfo_exists():
            ventana_modulo.destroy()
    except Exception:
        pass
    _restaurar_login()


def confirmar_cerrar_sesion(ventana_modulo):
    confirmar = messagebox.askyesno(
        "Cerrar sesión",
        "¿Desea cerrar la sesión actual?",
        parent=ventana_modulo,
    )
    if confirmar:
        cerrar_modulo_y_mostrar_login(ventana_modulo)


def ingresar():
    documento = entry_documento.get()

    if documento == "":
        messagebox.showwarning("Advertencia", "Debe ingresar el documento.")
        return

    # Acceso SuperAdmin: usuario escribe 'admin' en login
    if str(documento).strip().lower() == "admin":
        msa = ModuloSuperAdmin(ventana, db_path=str(DB_FILE), base_dir=str(BASE_DIR))
        if msa.authenticate():
            ventana.withdraw()
            msa.parent = ventana
            msa.open_interface(
                cerrar_sesion_cb=lambda: confirmar_cerrar_sesion(msa.win)
            )
            try:
                msa.win.state("zoomed")
            except Exception:
                try:
                    msa.win.attributes("-fullscreen", True)
                except Exception:
                    pass
            msa.win.protocol(
                "WM_DELETE_WINDOW", lambda: cerrar_modulo_y_mostrar_login(msa.win)
            )
        return

    # Validar docente primero
    nombre_docente = validar_docente(documento)
    if nombre_docente:
        ventana.withdraw()
        ventana_docente = None
        cerrar_cb_docente = lambda: confirmar_cerrar_sesion(ventana_docente)
        ventana_docente = abrir_docente(
            nombre_docente,
            cerrar_sesion_cb=cerrar_cb_docente,
            parent=ventana,
        )
        ventana_docente.protocol(
            "WM_DELETE_WINDOW",
            lambda: cerrar_modulo_y_mostrar_login(ventana_docente),
        )
        return

    # Validar estudiante
    estudiante = validar_estudiante(documento)

    if estudiante is None:
        messagebox.showerror("Error", "Documento no encontrado.")
        return

    # Acceder al Módulo Estudiante
    ventana.withdraw()
    ventana_est = tk.Toplevel(ventana)
    # Maximizar la ventana del estudiante tras ingresar
    try:
        ventana_est.state("zoomed")
    except Exception:
        try:
            ventana_est.attributes("-fullscreen", True)
        except Exception:
            pass
    nombre = estudiante.get("nombre", estudiante.get("nombre_completo", ""))
    grado = estudiante.get("grado", "")
    curso = estudiante.get("curso", None)
    ModuloEstudiante(
        ventana_est,
        documento,
        nombre,
        grado,
        curso,
        cerrar_sesion_cb=lambda: confirmar_cerrar_sesion(ventana_est),
    )
    ventana_est.protocol(
        "WM_DELETE_WINDOW", lambda: cerrar_modulo_y_mostrar_login(ventana_est)
    )


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


def _iniciar_login():
    global ventana, entry_documento
    crear_base_datos()

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

    crear_footer(ventana)

    ventana.mainloop()


if __name__ == "__main__":
    _iniciar_login()
