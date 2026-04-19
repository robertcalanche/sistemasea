from core.construir_nombre import construir_nombre

def obtener_respuestas_correctas_por_version(grado, area, evaluacion):
    """
    Devuelve un diccionario {version: [respuestas_correctas]} para el examen filtrado.
    """
    asegurar_tablas_generacion()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT eg.version, de.numero_pregunta, de.respuesta_correcta
            FROM examenes_generados eg
            JOIN detalle_examen de ON eg.exam_code = de.id_examen
            WHERE eg.grado = ? AND eg.area = ? AND eg.evaluacion = ?
            ORDER BY eg.version, de.numero_pregunta
            """,
            (str(grado), str(area), str(evaluacion or "")),
        )
        datos = cur.fetchall()
    respuestas = {}
    for version, num, resp in datos:
        if version not in respuestas:
            respuestas[version] = []
        respuestas[version].append(resp)
    return respuestas


def obtener_relacion_estudiantes_version(grado, area, evaluacion):
    """
    Devuelve una lista de dicts con documento, nombre estructurado y versión para el examen filtrado.
    """
    asegurar_tablas_generacion()

    def _partes_desde_texto(nombre_legado):
        partes = [p for p in str(nombre_legado or "").strip().split() if p]
        while len(partes) < 4:
            partes.append("")
        return {
            "apellido1": partes[0],
            "apellido2": partes[1],
            "nombre1": partes[2],
            "nombre2": " ".join(partes[3:]).strip(),
        }

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                COALESCE(NULLIF(TRIM(eg.estudiante_documento), ''), ''),
                COALESCE(NULLIF(TRIM(e.apellido1), ''), ''),
                COALESCE(NULLIF(TRIM(e.apellido2), ''), ''),
                COALESCE(NULLIF(TRIM(e.nombre1), ''), ''),
                COALESCE(NULLIF(TRIM(e.nombre2), ''), ''),
                COALESCE(NULLIF(TRIM(eg.version), ''), ''),
                COALESCE(NULLIF(TRIM(eg.estudiante_nombre), ''), '')
            FROM examenes_generados eg
            LEFT JOIN estudiantes e ON TRIM(CAST(e.documento AS TEXT)) = TRIM(CAST(eg.estudiante_documento AS TEXT))
            WHERE eg.grado = ? AND eg.area = ? AND eg.evaluacion = ?
            ORDER BY eg.version, COALESCE(NULLIF(TRIM(e.apellido1), ''), NULLIF(TRIM(eg.estudiante_nombre), ''))
            """,
            (str(grado), str(area), str(evaluacion or "")),
        )
        filas = []
        for documento, apellido1, apellido2, nombre1, nombre2, version, nombre_legado in cur.fetchall():
            estudiante = {
                "documento": str(documento or "").strip(),
                "apellido1": str(apellido1 or "").strip(),
                "apellido2": str(apellido2 or "").strip(),
                "nombre1": str(nombre1 or "").strip(),
                "nombre2": str(nombre2 or "").strip(),
                "version": str(version or "").strip(),
            }
            if not construir_nombre(estudiante):
                estudiante.update(_partes_desde_texto(nombre_legado))
            filas.append(estudiante)
        return filas


import random
import re
import uuid
import importlib
import os
import pandas as pd
from . import get_connection


# --- FUNCIÓN PRINCIPAL PARA GENERACIÓN DESDE LA WEB ---
def generar_examenes_web(
    grado=None,
    area=None,
    evaluacion=None,
    curso=None,
    versiones=1,
    n_preguntas=0,
    n_textos=0,
    docente=None,
    fecha=None,
    formato=None,
    hoja_respuestas=False,
    modo_hoja=None,
    estudiante=None,
    generar_pdf=True,
):
    """
    Orquesta la generación de exámenes desde la web.
    Devuelve un resumen de los exámenes generados y rutas de PDF si aplica.
    """
    # --- Validación básica ---
    versiones = int(versiones or 1)
    n_preguntas = int(n_preguntas or 0)
    n_textos = int(n_textos or 0)
    resultados = []

    # --- Carga real de preguntas desde el banco profesional ---
    try:
        from banco_preguntas_profesional import BancoPreguntasProfesional

        banco = BancoPreguntasProfesional()
        preguntas_df = None
        debug_log = []
        # Intentar filtrar por id_evaluacion si está presente
        if evaluacion and str(evaluacion).startswith("EVAL-"):
            debug_log.append(f"Intentando filtrar por id_evaluacion: {evaluacion}")
            df_all = banco.obtener_todas_preguntas()
            preguntas_df = df_all[
                df_all["id_evaluacion"].astype(str).str.strip()
                == str(evaluacion).strip()
            ]
            if preguntas_df.empty:
                debug_log.append(
                    f"No se encontraron preguntas con id_evaluacion={evaluacion}, fallback a filtros clásicos."
                )
                preguntas_df = None
        # Si no hay preguntas por id_evaluacion, usar filtros clásicos
        if preguntas_df is None:
            preguntas_df = banco.obtener_preguntas_filtradas(
                grado=grado, area=area, evaluacion=evaluacion
            )
            debug_log.append(
                f"Filtrado clásico: grado={grado}, area={area}, evaluacion={evaluacion}, preguntas={len(preguntas_df)}"
            )
        if preguntas_df.empty:
            raise ValueError(
                "No se encontraron preguntas para los filtros seleccionados."
            )
    except Exception as e:
        preguntas_df = pd.DataFrame(
            [
                {
                    "enunciado": f"Pregunta {i+1}",
                    "opcion_a": "A",
                    "opcion_b": "B",
                    "opcion_c": "C",
                    "opcion_d": "D",
                }
                for i in range(max(n_preguntas, 1))
            ]
        )
        resultados.append(
            {
                "error": f"No se pudo cargar el banco real: {e}",
            }
        )
        debug_log = [f"Excepción al cargar preguntas: {e}"]

    # Log de depuración (solo para desarrollador, no afecta resultado)
    if "debug_log" in locals() and debug_log:
        print("[DEBUG][generar_examenes_web]", *debug_log, sep="\n  ")

    for v in range(versiones):
        version_label = chr(65 + v) if versiones <= 26 else str(v + 1)
        exam_code = crear_codigo_examen(version_label)
        nombre_estudiante = construir_nombre(estudiante) if isinstance(estudiante, dict) else ""
        documento_estudiante = (
            estudiante.get("id") if isinstance(estudiante, dict) else ""
        )

        # --- Selección de preguntas (aquí debería ir la lógica real) ---
        preguntas_version = preguntas_df.sample(frac=1).reset_index(drop=True)

        # --- Generación de PDF si corresponde ---
        ruta_pdf = None
        if generar_pdf:
            pdf_dir = os.path.abspath("examenes_generados")
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(pdf_dir, f"examen_{exam_code}.pdf")
            try:
                # Importación dinámica para evitar dependencias circulares
                from _write_exam_pdf_new import _write_exam_pdf

                class Dummy:
                    def _get_config_plantel(self, key):
                        return ""

                    imagenes_dir = "imagenes"

                dummy = Dummy()
                _write_exam_pdf(
                    dummy,
                    preguntas_version,
                    estudiante or {},
                    pdf_path,
                    n_preguntas,
                    area,
                    evaluacion,
                )
                ruta_pdf = pdf_path
            except Exception as e:
                ruta_pdf = f"ERROR: {e}"

        # --- Guardar en base de datos (opcional) ---

        guardar_examen_generado(
            exam_code,
            grado,
            curso,
            area,
            evaluacion,
            version_label,
            nombre_estudiante,
            documento_estudiante,
            ruta_pdf or "",
        )
        # Guardar detalle de preguntas del examen generado
        guardar_detalle_examen(exam_code, preguntas_version)

        resultados.append(
            {
                "codigo": exam_code,
                "version": version_label,
                "pdf": ruta_pdf,
                "n_preguntas": len(preguntas_version),
                "estudiante": nombre_estudiante,
            }
        )

    return resultados


def generar_etiquetas_version(cantidad):
    try:
        total = int(cantidad)
    except Exception:
        total = 1
    total = max(1, total)

    etiquetas = []
    for i in range(total):
        x = i
        chars = []
        while True:
            x, rem = divmod(x, 26)
            chars.append(chr(ord("A") + rem))
            if x == 0:
                break
            x -= 1
        etiquetas.append("".join(reversed(chars)))
    return etiquetas


def construir_contenido_qr(documento, nombre, grado, curso, area, evaluacion, exam_id):
    return (
        f"SEA|{str(documento or '').strip()}|{str(nombre or '').strip()}|"
        f"{str(grado or '').strip()}|{str(curso or '').strip()}|"
        f"{str(area or '').strip()}|{str(evaluacion or '').strip()}|"
        f"ID:{str(exam_id or '').strip()}"
    )


def crear_codigo_examen(version=None):
    version_label = str(version or "A").strip().upper() or "A"
    return f"{version_label}{uuid.uuid4().hex[:5].upper()}"


def seleccionar_preguntas_por_textos(df_all, total_questions, num_texts, rnd_seed=None):
    if df_all is None or len(df_all) == 0:
        return pd.DataFrame()

    total_questions = max(1, int(total_questions or 1))
    rnd = random.Random()
    if rnd_seed is not None:
        rnd.seed(rnd_seed)

    if num_texts and int(num_texts) > 0:
        if "id_contexto" not in df_all.columns:
            raise ValueError(
                "No hay textos registrados para aplicar la cantidad de textos."
            )

        seen_ctx = []
        for contexto in df_all["id_contexto"]:
            if (
                str(contexto).strip()
                and str(contexto) != "nan"
                and contexto not in seen_ctx
            ):
                seen_ctx.append(contexto)

        if int(num_texts) > len(seen_ctx):
            raise ValueError(
                "No hay suficientes textos registrados para la cantidad solicitada."
            )

        ctx_choices = list(seen_ctx)
        rnd.shuffle(ctx_choices)
        selected_ctx = ctx_choices[: int(num_texts)]

        grupos = []
        for contexto in selected_ctx:
            grupo = df_all[df_all["id_contexto"] == contexto].copy()
            grupo = grupo.sample(frac=1, random_state=rnd.randint(0, 10**9))
            grupos.append((contexto, grupo))

        total_available = sum(len(grupo) for _, grupo in grupos)
        if total_available < total_questions:
            raise ValueError(
                "No hay suficientes preguntas disponibles para la combinación seleccionada."
            )

        n = len(grupos)
        base = total_questions // n
        rem = total_questions % n
        alloc = [base + (1 if i < rem else 0) for i in range(n)]
        capacities = [len(grupo) for _, grupo in grupos]

        while True:
            overflow = 0
            for i in range(n):
                if alloc[i] > capacities[i]:
                    overflow += alloc[i] - capacities[i]
                    alloc[i] = capacities[i]
            if overflow == 0:
                break

            remaining_idxs = [i for i in range(n) if alloc[i] < capacities[i]]
            if not remaining_idxs:
                break

            per = overflow // len(remaining_idxs)
            extra = overflow % len(remaining_idxs)
            for j, idx in enumerate(remaining_idxs):
                alloc[idx] += per + (1 if j < extra else 0)

        selected_rows = []
        for i, (_, grupo) in enumerate(grupos):
            take = alloc[i]
            if take <= 0:
                continue
            selected_rows.append(grupo.head(take).copy())

        rnd.shuffle(selected_rows)
        if not selected_rows:
            return pd.DataFrame(columns=df_all.columns)
        return pd.concat(selected_rows, ignore_index=True)

    if total_questions >= len(df_all):
        return df_all.sample(frac=1, random_state=rnd.randint(0, 10**9)).reset_index(
            drop=True
        )

    return df_all.sample(
        n=total_questions, random_state=rnd.randint(0, 10**9)
    ).reset_index(drop=True)


def normalizar_correcta_fila(row_data):
    letra = str(row_data.get("correcta", "") or "").strip().upper()[:1]
    if letra in ("A", "B", "C", "D"):
        return letra

    texto = str(
        row_data.get("respuesta_correcta", "")
        or row_data.get("respuesta_correcta_texto", "")
        or ""
    ).strip()
    if len(texto) == 1 and texto.upper() in ("A", "B", "C", "D"):
        return texto.upper()

    if texto:
        normalizado = re.sub(r"\s+", " ", texto).strip().lower()
        for letra_opcion, columna in (
            ("A", "opcion_a"),
            ("B", "opcion_b"),
            ("C", "opcion_c"),
            ("D", "opcion_d"),
        ):
            opcion = re.sub(
                r"\s+", " ", str(row_data.get(columna, "") or "").strip().lower()
            )
            if opcion and normalizado == opcion:
                return letra_opcion
    return ""


def asegurar_tablas_generacion():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS examenes_generados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_code TEXT,
                grado TEXT,
                curso TEXT,
                area TEXT,
                evaluacion TEXT,
                version TEXT,
                estudiante_nombre TEXT,
                estudiante_documento TEXT,
                ruta_pdf TEXT,
                fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(examenes_generados)")
            cols = {
                str(row[1]).lower() for row in cur.fetchall() if row and len(row) > 1
            }
            if "version" not in cols:
                conn.execute("ALTER TABLE examenes_generados ADD COLUMN version TEXT")
        except Exception:
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS detalle_examen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_examen TEXT,
                numero_pregunta INTEGER,
                respuesta_correcta TEXT,
                UNIQUE(id_examen, numero_pregunta)
            )
            """
        )
        conn.commit()


def guardar_examen_generado(
    exam_code,
    grado,
    curso,
    area,
    evaluacion,
    version,
    estudiante_nombre,
    estudiante_documento,
    ruta_pdf,
):
    asegurar_tablas_generacion()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO examenes_generados
                (exam_code, grado, curso, area, evaluacion, version,
                 estudiante_nombre, estudiante_documento, ruta_pdf)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            (
                str(exam_code or "").strip(),
                str(grado or "").strip(),
                str(curso or "").strip(),
                str(area or "").strip(),
                str(evaluacion or "").strip(),
                str(version or "").strip(),
                str(estudiante_nombre or "").strip(),
                str(estudiante_documento or "").strip(),
                str(ruta_pdf or "").strip(),
            ),
        )
        conn.commit()


def guardar_detalle_examen(id_examen, df_examen):
    if not id_examen or df_examen is None or len(df_examen) == 0:
        return

    asegurar_tablas_generacion()
    with get_connection() as conn:
        conn.execute("DELETE FROM detalle_examen WHERE id_examen = ?", (id_examen,))
        for idx_row, (_, row) in enumerate(df_examen.iterrows(), start=1):
            correcta = normalizar_correcta_fila(row)
            conn.execute(
                """
                INSERT OR REPLACE INTO detalle_examen
                    (id_examen, numero_pregunta, respuesta_correcta)
                VALUES (?,?,?)
                """,
                (str(id_examen).strip(), int(idx_row), correcta),
            )
        conn.commit()


def obtener_examen_generado_por_codigo(codigo):
    asegurar_tablas_generacion()
    codigo_norm = str(codigo or "").strip().upper()
    if not codigo_norm:
        return None

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT exam_code, grado, curso, area, evaluacion, version,
                   estudiante_nombre, estudiante_documento,
                   ruta_pdf, fecha_generacion
            FROM examenes_generados
            WHERE UPPER(exam_code) = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (codigo_norm,),
        )
        row = cur.fetchone()

    if not row:
        return None

    keys = [
        "exam_code",
        "grado",
        "curso",
        "area",
        "evaluacion",
        "version",
        "estudiante_nombre",
        "estudiante_documento",
        "ruta_pdf",
        "fecha_generacion",
    ]
    return dict(zip(keys, row))


def unir_pdfs(pdf_paths, output_path):
    rutas = [ruta for ruta in (pdf_paths or []) if ruta]
    if not rutas:
        raise ValueError("No hay archivos PDF para consolidar.")

    PdfReader = PdfWriter = None
    try:
        mod = importlib.import_module("pypdf")
        PdfReader = getattr(mod, "PdfReader", None)
        PdfWriter = getattr(mod, "PdfWriter", None)
    except Exception:
        PdfReader = PdfWriter = None

    if PdfReader is None or PdfWriter is None:
        try:
            mod_legacy = importlib.import_module("PyPDF2")
            PdfReader = getattr(mod_legacy, "PdfReader", None)
            PdfWriter = getattr(mod_legacy, "PdfWriter", None)
        except Exception:
            PdfReader = PdfWriter = None

    if PdfReader is None or PdfWriter is None:
        raise ValueError(
            "Para generar un solo PDF en modo Todos, instale pypdf (pip install pypdf)."
        )

    writer = PdfWriter()
    total_paginas = 0
    hojas_blanco = 0
    estudiantes = 0
    for pdf in rutas:
        reader = PdfReader(pdf)
        num_pages = len(reader.pages)
        estudiantes += 1
        total_paginas += num_pages
        # Si el número de páginas es impar, insertar hoja en blanco
        if num_pages % 2 != 0:
            for page in reader.pages:
                writer.add_page(page)
            # Insertar hoja en blanco (manteniendo tamaño)
            blank_page = PdfWriter().add_blank_page(
                width=reader.pages[0].mediabox.width,
                height=reader.pages[0].mediabox.height,
            )
            writer.add_page(blank_page)
            hojas_blanco += 1
            total_paginas += 1
        else:
            for page in reader.pages:
                writer.add_page(page)

    with open(output_path, "wb") as out_f:
        writer.write(out_f)

    # Retornar resumen para reporte
    return {
        "estudiantes": estudiantes,
        "total_paginas": total_paginas,
        "hojas_blanco": hojas_blanco,
    }
