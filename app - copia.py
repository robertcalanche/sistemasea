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
import Admin
from Admin import (
    ModuloDocente,
    abrir_docente,
    VistaHistorialExamenes,
    ModuloEstudiante,
    # data/file utilities
    crear_base_datos,
    crear_tabla_config,
    registrar_inicio,
    registrar_final,
    ya_presento,
    obtener_todas_respuestas_desde_bd,
    obtener_estado_area,
    obtener_intento_area,
    autorizar_revision,
    puede_revisar,
    obtener_respuestas_estudiante,
    resetear_examen,
    validar_estudiante,
    validar_docente,
    normalizar_grado,
    cargar_areas,
    cargar_areas_por_grado,
    cargar_grados,
    cargar_cursos_disponibles,
    cargar_evaluaciones_por_grado_y_area,
    cargar_preguntas,
    cargar_preguntas_filtradas,
    cargar_config_examen,
    guardar_config_examen,
    examen_esta_activo,
    exportar_reporte_por_filtros,
    exportar_consolidado_periodo,
    exportar_reporte_completo,
)

# alias antiguo para compatibilidad
## Alias para compatibilidad (mantener solo por si hay referencias antiguas)
cargar_evaluaciones = cargar_evaluaciones_por_grado_y_area

BASE_DIR = Path(__file__).resolve().parent
# ESTUDIANTES_FILE = BASE_DIR / "estudiantes.xlsx"  # Ahora se valida desde SQLite
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


# las funciones relacionadas con el historial, estado e intentos de examen se delegan a Admin
# se importan arriba y por claridad aquí se puede reafirmar la asignación (aunque no es estrictamente necesario)
ya_presento = Admin.ya_presento
obtener_estado_area = Admin.obtener_estado_area
obtener_intento_area = Admin.obtener_intento_area
autorizar_revision = Admin.autorizar_revision
puede_revisar = Admin.puede_revisar
obtener_respuestas_estudiante = Admin.obtener_respuestas_estudiante

# las funciones de validación y carga se importan desde Admin y no se definen aquí


## ================= FILTROS DOCENTE =================
# Corrección de filtros: Grado → carga cursos, Área → carga evaluaciones
def cargar_cursos_por_grado(grado):
    return Admin.cargar_cursos_disponibles(grado)


def cargar_evaluaciones_por_grado_y_area(grado, area):
    return Admin.cargar_evaluaciones_por_grado_y_area(grado, area)


# NOTA: No modificar ni eliminar funciones de reporte ni resultados.


# configuración de examen administrada por Admin.py; ver Admin.guardar_config_examen


# ================= VISTA HISTORIAL (Componente Reutilizable) =================
# implementación importada desde Admin.py

# ================= MÓDULO DOCENTE =================
# implementación importada desde Admin.py

# ================= MÓDULO ESTUDIANTE =================


class ModuloEstudiante:

    def __init__(self, ventana, documento, nombre, grado, curso):
        self.ventana = ventana
        self.documento = documento
        self.nombre = nombre
        self.grado = grado
        self.curso = curso
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
            text=f"Grado {grado} Curso {curso} • Mis Exámenes",
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

        # Detectar si hay examen en proceso
        self._detectar_examen_en_proceso()

        self._mostrar_areas()

    # ---------------------------------------------------

    def _detectar_examen_en_proceso(self):
        """Detecta si el estudiante tiene un examen en proceso y muestra mensaje."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT intento, area, evaluacion FROM resultados WHERE documento = ? AND estado_examen = 'EN_PROCESO' ORDER BY id DESC LIMIT 1",
                (self.documento,),
            )
            examen_proceso = cursor.fetchone()
            conn.close()

            if examen_proceso:
                intento, area, evaluacion = examen_proceso
                messagebox.showinfo(
                    "Examen en Progreso Detectado",
                    f"Se detectó un examen en progreso.\n\n"
                    f"Área: {area}\n"
                    f"Evaluación: {evaluacion or 'General'}\n"
                    f"Intento: {intento}\n\n"
                    f"El sistema continuará automáticamente desde la última pregunta respondida cuando selecciones esta área.",
                )
        except Exception as e:
            print(f"[INFO] Error detectando examen en proceso: {e}")

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
        Retorna: (intento_num, intento_id, max_pregunta_id, curso) o None si no existe.
        """
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Buscar registro EN_PROCESO más reciente
            cursor.execute(
                """
                SELECT intento, id, curso FROM resultados 
                WHERE documento = ? AND area = ? AND estado_examen = 'EN_PROCESO'
                ORDER BY id DESC LIMIT 1
                """,
                (self.documento, area),
            )
            resultado = cursor.fetchone()

            if not resultado:
                conn.close()
                return None

            intento_num, intento_id, curso = resultado

            # Obtener la última pregunta respondida
            cursor.execute(
                """
                SELECT MAX(pregunta_id) FROM respuestas_estudiantes 
                WHERE documento = ? AND area = ? AND intento = ?
                """,
                (self.documento, area, intento_num),
            )
            max_pregunta_id = cursor.fetchone()[0]
            if max_pregunta_id is None:
                max_pregunta_id = 0
            conn.close()

            return (intento_num, intento_id, max_pregunta_id, curso)
        except Exception as e:
            print(f"[ERROR] _obtener_examen_en_proceso: {e}")
            return None

    def _iniciar_examen(self, area):
        print(f"[DEBUG] INICIANDO EXAMEN -> {area}")
        estado_info = obtener_estado_area(self.documento, area)

        # Obtener evaluación activa de config_examenes para este grado+area+curso.
        # La configuración puede tener curso específico o aplicarse a TODOS.
        evaluacion = None
        try:
            curso = str(self.curso).strip() if self.curso is not None else ""
            if curso == "":
                curso = "TODOS"

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT evaluacion FROM config_examenes "
                "WHERE CAST(grado AS TEXT) = ? AND CAST(area AS TEXT) = ? "
                "AND (curso = ? OR curso = 'TODOS') "
                "AND habilitado = 1 "
                "ORDER BY (curso = 'TODOS') ASC LIMIT 1",
                (str(self.grado), str(area), curso),
            )
            resultado = cursor.fetchone()
            conn.close()
            if resultado and resultado[0]:
                evaluacion = resultado[0]
        except Exception as e:
            print(f"[DEBUG] Error al obtener evaluación de config_examenes: {e}")
            pass

        # Normalizar evaluación para consistencia
        if evaluacion:
            evaluacion = str(evaluacion).strip().lower()
            if evaluacion in ["nan", "none", ""]:
                evaluacion = None

        print(f"[DEBUG] Evaluación obtenida: {repr(evaluacion)}")

        # Cargar configuración usando grado + curso + area + evaluacion
        duracion, cantidad, max_intentos, permitir_reintentos, habilitado = (
            cargar_config_examen(area, self.grado, evaluacion, self.curso)
        )

        if not habilitado:
            messagebox.showwarning(
                "Examen no disponible",
                f"El examen de {area} aún no ha sido habilitado por el docente.",
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

        if estado_info and estado_info[0] in ["PRESENTADO", "REVISION_ACTIVA"]:
            if not permitir_reintentos or intentos_previos >= max_intentos:
                messagebox.showwarning(
                    "No disponible", "Ya alcanzaste el límite de intentos."
                )
                return

        # ============ VERIFICAR SI EXISTE EXAMEN EN_PROCESO (REANUDACIÓN) ============
        examen_reanudado = self._obtener_examen_en_proceso(area)

        # Obtener curso del estudiante
        curso = (
            self.curso if hasattr(self, "curso") and self.curso is not None else None
        )
        if not curso:
            try:
                estudiante = validar_estudiante(self.documento)
                if estudiante is not None and "curso" in estudiante.index:
                    curso_val = estudiante["curso"]
                    if not pd.isna(curso_val):
                        curso = str(curso_val).strip()
            except Exception:
                pass
        if not curso or curso == "":
            curso = "TODOS"

        if examen_reanudado:
            # Examen interrumpido encontrado - reanudarlo
            intento_num, intento_id, max_pregunta_id, curso_guardado = examen_reanudado
            if curso_guardado:
                curso = curso_guardado  # Usar el curso guardado en la BD
            self.current_intento_id = intento_id
            self.current_intento_num = intento_num
            es_reanudacion = True
            # indice_inicial se calculará después de cargar las preguntas
        else:
            # Nuevo examen
            intento_num, intento_id = registrar_inicio(
                self.documento, self.nombre, self.grado, area, evaluacion, curso
            )
            self.current_intento_id = intento_id
            self.current_intento_num = intento_num
            es_reanudacion = False
            indice_inicial = 0

        # antes de pasar a la pantalla informativa validamos que la evaluación
        # realmente exista y pertenezca al grado/área del estudiante
        if not evaluacion:
            messagebox.showwarning(
                "Evaluación indefinida",
                "No se encontró una evaluación habilitada para este examen.\n"
                "Contacta al docente para verificar la configuración.",
            )
            return

        try:
            df_eval = cargar_preguntas_filtradas(
                area=area, grado=self.grado, evaluacion=evaluacion
            )
            if df_eval.empty:
                messagebox.showwarning(
                    "Sin preguntas",
                    f"La evaluación '{evaluacion}' no contiene preguntas."
                    "\nVerifica el banco de preguntas.",
                )
                return

            # asegurarse de que todas las preguntas correspondan al grado
            mism = df_eval[
                df_eval["grado"].astype(str).str.strip().str.lower()
                != str(self.grado).strip().lower()
            ]
            if not mism.empty:
                messagebox.showwarning(
                    "Grado incompatible",
                    f"Las preguntas de la evaluación '{evaluacion}' no coinciden "
                    f"con el grado del estudiante ({self.grado}).",
                )
                return

            # también opcional: comprobar área
            mism_area = df_eval[
                df_eval["area"].astype(str).str.strip().str.lower()
                != str(area).strip().lower()
            ]
            if not mism_area.empty:
                messagebox.showwarning(
                    "Área incompatible",
                    f"Las preguntas de la evaluación '{evaluacion}' no coinciden "
                    f"con el área solicitada ({area}).",
                )
                return
        except Exception:
            # si algo falla aquí, dejamos que el flujo normal intente
            # cargar y mostrar las preguntas; esto no debería ocurrir
            pass

        # Calcular indice_inicial si es reanudación
        if es_reanudacion:
            preguntas = df_eval.head(cantidad).reset_index(drop=True)
            # Encontrar el índice de la pregunta siguiente a la última respondida
            indice_inicial = 0
            for idx, preg in preguntas.iterrows():
                preg_id = preg.get("id")
                if preg_id and pd.notna(preg_id):
                    if int(preg_id) <= max_pregunta_id:
                        indice_inicial = idx + 1
                    else:
                        break
        else:
            indice_inicial = 0

        self._mostrar_pantalla_informativa(
            area, cantidad, duracion, evaluacion, es_reanudacion, indice_inicial, curso
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
        curso=None,
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
                curso,
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
        curso=None,
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

            # Restaurar respuesta si es reanudación y ya fue respondida
            var.set("")
            if es_reanudacion:
                try:
                    pregunta_id = (
                        int(preg.get("id"))
                        if "id" in preg and pd.notna(preg.get("id"))
                        else None
                    )
                    if pregunta_id:
                        conn_resp = sqlite3.connect(DB_FILE)
                        cursor_resp = conn_resp.cursor()
                        cursor_resp.execute(
                            """
                            SELECT respuesta_seleccionada FROM respuestas_estudiantes 
                            WHERE documento = ? AND area = ? AND intento = ? AND pregunta_id = ?
                            """,
                            (
                                self.documento,
                                area,
                                self.current_intento_num,
                                pregunta_id,
                            ),
                        )
                        resp_guardada = cursor_resp.fetchone()
                        if resp_guardada and resp_guardada[0]:
                            var.set(resp_guardada[0])
                        conn_resp.close()
                except Exception as e:
                    print(
                        f"[INFO] No se pudo restaurar respuesta para pregunta {pregunta_id}: {e}"
                    )

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
                    (documento, nombre, grado, curso, area, evaluacion, intento, pregunta_id, enunciado, 
                     respuesta_seleccionada, respuesta_correcta, es_correcta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(documento, area, intento, pregunta_id) 
                    DO UPDATE SET 
                        respuesta_seleccionada = EXCLUDED.respuesta_seleccionada,
                        es_correcta = EXCLUDED.es_correcta
                    """,
                    (
                        self.documento,
                        self.nombre,
                        self.grado,
                        curso,
                        area,
                        evaluacion,
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


# abrir_docente importado desde Admin.py


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


# clase abrir_estudiante ahora proviene de Admin.py


# Nueva función que mantiene compatibilidad: redirige a abrir_estudiante
def abrir_examen(documento, nombre, grado):
    """Abre el módulo de estudiante (nuevo flujo unificado)."""
    abrir_estudiante(documento)


# ---------- usar implementaciones de Admin.py para componentes compartidos ----------
# clases (ModuloDocente y VistaHistorialExamenes se importan desde Admin)
# ModuloEstudiante se mantiene localizada en app.py para beneficiarse de mejoras
# de reanudación de examen que no están en admin.py
ModuloDocente = Admin.ModuloDocente
VistaHistorialExamenes = Admin.VistaHistorialExamenes
# NO sobreescribir ModuloEstudiante - mantener versión mejorada local de app.py

# abridores/constructores
abrir_docente = Admin.abrir_docente
abrir_estudiante = Admin.abrir_estudiante


# utilidades globales delegadas (exportar/filtrar y cálculo)
# `crear_base_datos` se mantiene en este módulo porque además de la
# implementación de Admin necesita las tablas `estudiantes` y `docentes`.
def crear_base_datos():
    # ejecutar la rutina principal ubicada en Admin
    Admin.crear_base_datos()
    # después, garantizar que existan las tablas específicas del ejecutable
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS estudiantes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_documento TEXT,
                    documento TEXT NOT NULL UNIQUE,
                    nombre_completo TEXT,
                    fecha_nacimiento TEXT,
                    sexo TEXT,
                    grupo_sanguineo TEXT,
                    telefono TEXT,
                    correo TEXT,
                    grado TEXT,
                    grupo TEXT,
                    jornada TEXT,
                    anio_lectivo TEXT,
                    estado TEXT DEFAULT 'Activo',
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS docentes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_documento TEXT,
                    documento TEXT NOT NULL UNIQUE,
                    nombre TEXT NOT NULL,
                    sexo TEXT,
                    fecha_nacimiento TEXT,
                    telefono TEXT,
                    correo TEXT,
                    cargo TEXT,
                    jornada TEXT,
                    sede TEXT,
                    estado TEXT DEFAULT 'Activo',
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            conn.commit()
    except Exception:
        pass


crear_tabla_config = Admin.crear_tabla_config
registrar_inicio = Admin.registrar_inicio
registrar_final = Admin.registrar_final
ya_presento = Admin.ya_presento
obtener_todas_respuestas_desde_bd = Admin.obtener_todas_respuestas_desde_bd
obtener_estado_area = Admin.obtener_estado_area
obtener_intento_area = Admin.obtener_intento_area
autorizar_revision = Admin.autorizar_revision
puede_revisar = Admin.puede_revisar
obtener_respuestas_estudiante = Admin.obtener_respuestas_estudiante
resetear_examen = Admin.resetear_examen
validar_estudiante = Admin.validar_estudiante
validar_docente = Admin.validar_docente
cargar_areas = Admin.cargar_areas
cargar_areas_por_grado = Admin.cargar_areas_por_grado
cargar_grados = Admin.cargar_grados
cargar_evaluaciones = Admin.cargar_evaluaciones_por_grado_y_area
cargar_preguntas = Admin.cargar_preguntas
cargar_preguntas_filtradas = Admin.cargar_preguntas_filtradas
exportar_reporte_por_filtros = Admin.exportar_reporte_por_filtros
exportar_consolidado_periodo = Admin.exportar_consolidado_periodo
exportar_reporte_completo = Admin.exportar_reporte_completo
# funciones de configuración también se delegan para mantener compatibilidad
cargar_config_examen = Admin.cargar_config_examen
guardar_config_examen = Admin.guardar_config_examen

## ================= INICIO =================

# Inicialización de la base de datos usando implementación actualizada
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
    text="📚 Sistema de Evaluación Automatizada",
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
    text="Todos los derechos reservados autor: Robert Calanche Villa 2026",
    font=("Segoe UI", 9),
    bg=COLOR_SECUNDARIO,
    fg="#999999",
).pack()

ventana.mainloop()
