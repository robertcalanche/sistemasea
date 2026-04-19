import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from autoevaluacion import (
    ESCALA,
    DIMENSIONES,
    actualizar_autoevaluacion,
    crear_autoevaluacion,
    crear_tablas_autoevaluacion,
    detalle_resultado_autoevaluacion,
    habilitar_autoevaluacion,
    listar_filtros_resultados_autoevaluacion,
    listar_autoevaluaciones,
    consultar_resultados_autoevaluacion,
    obtener_formato_base_autoevaluacion,
    obtener_autoevaluacion,
    resumir_resultados_autoevaluacion,
    sincronizar_resultados_autoevaluacion,
)


class VentanaAutoevaluacionDocente(tk.Toplevel):
    def __init__(self, parent, modulo_docente, docente_documento, db_path="sistema.db"):
        super().__init__(parent)
        self.modulo_docente = modulo_docente
        self.docente_documento = str(docente_documento or "").strip()
        self.db_path = db_path
        self.instrumento_id = None
        self.preguntas = []

        crear_tablas_autoevaluacion(db_path=self.db_path)

        self.title("Autoevaluación Docente")
        self.geometry("1100x720")
        self.minsize(980, 660)
        self.configure(bg="#f5f7fa")
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        self._crear_estilos()
        self._construir_ui()
        self._cargar_fuentes_docente()
        self._recargar_instrumentos()

    def _crear_estilos(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Autoeval.TFrame", background="#f5f7fa")
        style.configure("AutoevalCard.TFrame", background="white")
        style.configure("Autoeval.TLabel", background="#f5f7fa", foreground="#1f2937")
        style.configure(
            "AutoevalTitle.TLabel",
            background="#f5f7fa",
            foreground="#0f172a",
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "AutoevalCardTitle.TLabel",
            background="white",
            foreground="#0f172a",
            font=("Segoe UI", 11, "bold"),
        )
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))

    def _construir_ui(self):
        container = ttk.Frame(self, style="Autoeval.TFrame", padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(1, weight=1)

        header = ttk.Frame(container, style="Autoeval.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ttk.Label(
            header, text="Autoevaluación Docente", style="AutoevalTitle.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            header,
            text=f"Docente: {self.modulo_docente.nombre}",
            style="Autoeval.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        left = ttk.Frame(container, style="AutoevalCard.TFrame", padding=14)
        left.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        right = ttk.Frame(container, style="AutoevalCard.TFrame", padding=14)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        ttk.Label(
            left, text="Configuración del instrumento", style="AutoevalCardTitle.TLabel"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self.var_area = tk.StringVar()
        self.var_grado = tk.StringVar()
        self.var_curso = tk.StringVar()
        self.var_periodo = tk.StringVar(value="Periodo 1")
        self.var_dimension = tk.StringVar(value=DIMENSIONES[0])
        self.var_habilitada = tk.BooleanVar(value=False)

        ttk.Label(left, text="Área", style="Autoeval.TLabel").grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.cb_area = ttk.Combobox(
            left, textvariable=self.var_area, state="readonly", width=26
        )
        self.cb_area.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        ttk.Label(left, text="Grado", style="Autoeval.TLabel").grid(
            row=3, column=0, sticky="w", pady=4
        )
        self.cb_grado = ttk.Combobox(
            left, textvariable=self.var_grado, state="readonly", width=12
        )
        self.cb_grado.grid(row=4, column=0, sticky="ew", pady=(0, 8), padx=(0, 6))

        ttk.Label(left, text="Curso", style="Autoeval.TLabel").grid(
            row=3, column=1, sticky="w", pady=4
        )
        self.cb_curso = ttk.Combobox(
            left, textvariable=self.var_curso, state="readonly", width=12
        )
        self.cb_curso.grid(row=4, column=1, sticky="ew", pady=(0, 8))

        ttk.Label(left, text="Periodo", style="Autoeval.TLabel").grid(
            row=5, column=0, sticky="w", pady=4
        )
        self.cb_periodo = ttk.Combobox(
            left,
            textvariable=self.var_periodo,
            state="readonly",
            values=["Periodo 1", "Periodo 2", "Periodo 3", "Periodo 4"],
            width=18,
        )
        self.cb_periodo.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Checkbutton(
            left,
            text="Habilitar autoevaluación al guardar",
            variable=self.var_habilitada,
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 12))

        ttk.Label(
            left, text="Instrumentos creados", style="AutoevalCardTitle.TLabel"
        ).grid(row=8, column=0, columnspan=2, sticky="w", pady=(6, 8))
        self.tree_instrumentos = ttk.Treeview(
            left,
            columns=("area", "grupo", "periodo", "preguntas", "estado"),
            show="headings",
            height=14,
        )
        self.tree_instrumentos.grid(row=9, column=0, columnspan=2, sticky="nsew")
        left.rowconfigure(9, weight=1)
        for col, title, width in (
            ("area", "Área", 140),
            ("grupo", "Grupo", 100),
            ("periodo", "Periodo", 90),
            ("preguntas", "Preg.", 60),
            ("estado", "Estado", 90),
        ):
            self.tree_instrumentos.heading(col, text=title)
            self.tree_instrumentos.column(col, width=width, anchor="center")

        acciones_lista = ttk.Frame(left, style="AutoevalCard.TFrame")
        acciones_lista.grid(row=10, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(acciones_lista, text="Nuevo", command=self._nuevo_formulario).pack(
            side="left"
        )
        ttk.Button(
            acciones_lista,
            text="Cargar formato base",
            command=self._cargar_formato_base,
        ).pack(side="left", padx=(6, 0))
        ttk.Button(
            acciones_lista, text="Cargar", command=self._cargar_seleccionado
        ).pack(side="left", padx=(6, 0))
        ttk.Button(
            acciones_lista,
            text="Ver Resultados",
            command=self._abrir_resultados,
        ).pack(side="left", padx=(6, 0))
        ttk.Button(
            acciones_lista, text="Alternar estado", command=self._alternar_habilitada
        ).pack(side="left", padx=(6, 0))

        ttk.Label(
            right, text="Constructor de preguntas", style="AutoevalCardTitle.TLabel"
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            right,
            text="Escala fija: 1 Nunca, 2 Algunas veces, 3 Casi siempre, 4 Siempre.",
            style="Autoeval.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 10))

        formulario = ttk.Frame(right, style="AutoevalCard.TFrame")
        formulario.grid(row=2, column=0, sticky="ew")
        formulario.columnconfigure(1, weight=1)

        ttk.Label(formulario, text="Dimensión", style="Autoeval.TLabel").grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.cb_dimension = ttk.Combobox(
            formulario,
            textvariable=self.var_dimension,
            values=DIMENSIONES,
            state="readonly",
            width=20,
        )
        self.cb_dimension.grid(row=0, column=1, sticky="w", pady=4)

        ttk.Label(formulario, text="Pregunta", style="Autoeval.TLabel").grid(
            row=1, column=0, sticky="nw", pady=4
        )
        self.txt_pregunta = tk.Text(formulario, height=4, width=60, wrap="word")
        self.txt_pregunta.grid(row=1, column=1, sticky="ew", pady=4)

        acciones_pregunta = ttk.Frame(formulario, style="AutoevalCard.TFrame")
        acciones_pregunta.grid(row=2, column=1, sticky="w", pady=(6, 10))
        ttk.Button(
            acciones_pregunta, text="Agregar pregunta", command=self._agregar_pregunta
        ).pack(side="left")
        ttk.Button(
            acciones_pregunta,
            text="Actualizar seleccionada",
            command=self._actualizar_pregunta,
        ).pack(side="left", padx=(6, 0))
        ttk.Button(
            acciones_pregunta,
            text="Eliminar seleccionada",
            command=self._eliminar_pregunta,
        ).pack(side="left", padx=(6, 0))

        self.tree_preguntas = ttk.Treeview(
            right,
            columns=("dimension", "texto"),
            show="headings",
            height=12,
        )
        self.tree_preguntas.grid(row=3, column=0, sticky="nsew", pady=(10, 10))
        self.tree_preguntas.heading("dimension", text="Dimensión")
        self.tree_preguntas.heading("texto", text="Pregunta")
        self.tree_preguntas.column("dimension", width=160, anchor="center")
        self.tree_preguntas.column("texto", width=600, anchor="w")

        footer = ttk.Frame(right, style="AutoevalCard.TFrame")
        footer.grid(row=4, column=0, sticky="ew")
        self.lbl_resumen = ttk.Label(
            footer, text="Preguntas registradas: 0", style="Autoeval.TLabel"
        )
        self.lbl_resumen.pack(side="left")
        ttk.Button(
            footer,
            text="Guardar instrumento",
            command=self._guardar_instrumento,
            style="Primary.TButton",
        ).pack(side="right")
        ttk.Button(footer, text="Cerrar", command=self.destroy).pack(
            side="right", padx=(0, 8)
        )

        self.tree_preguntas.bind("<<TreeviewSelect>>", self._on_select_pregunta)
        self.tree_instrumentos.bind("<<TreeviewSelect>>", self._on_select_instrumento)
        self.cb_grado.bind("<<ComboboxSelected>>", self._refrescar_cursos_por_grado)

    def _consultar_valores_docente(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT TRIM(COALESCE(area, '')) AS area,
                            TRIM(COALESCE(grado, '')) AS grado,
                            TRIM(COALESCE(curso, '')) AS curso
            FROM carga_academica
            WHERE TRIM(COALESCE(docente_documento, '')) = ?
              AND TRIM(COALESCE(estado, 'Activo')) = 'Activo'
            ORDER BY area, grado, curso
        """,
            (self.docente_documento,),
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def _cargar_fuentes_docente(self):
        rows = self._consultar_valores_docente()
        areas = []
        grados = []
        self._cursos_por_grado = {}
        for area, grado, curso in rows:
            area_txt = str(area or "").strip()
            grado_txt = str(grado or "").strip()
            curso_txt = str(curso or "").strip()
            if area_txt and area_txt not in areas:
                areas.append(area_txt)
            if grado_txt and grado_txt not in grados:
                grados.append(grado_txt)
            if grado_txt and curso_txt:
                self._cursos_por_grado.setdefault(grado_txt, [])
                if curso_txt not in self._cursos_por_grado[grado_txt]:
                    self._cursos_por_grado[grado_txt].append(curso_txt)

        self.cb_area["values"] = areas
        self.cb_grado["values"] = grados
        if areas:
            self.var_area.set(areas[0])
        if grados:
            self.var_grado.set(grados[0])
            self._refrescar_cursos_por_grado()

    def _refrescar_cursos_por_grado(self, event=None):
        grado = self.var_grado.get().strip()
        cursos = self._cursos_por_grado.get(grado, [])
        self.cb_curso["values"] = cursos
        if cursos:
            if self.var_curso.get().strip() not in cursos:
                self.var_curso.set(cursos[0])
        else:
            self.var_curso.set("")

    def _recargar_instrumentos(self):
        for item in self.tree_instrumentos.get_children():
            self.tree_instrumentos.delete(item)
        instrumentos = listar_autoevaluaciones(
            docente=self.docente_documento,
            db_path=self.db_path,
        )
        for item in instrumentos:
            grupo = f"{item.get('grado', '')}-{item.get('curso', '')}".strip("-")
            estado = "Habilitada" if int(item.get("habilitada") or 0) else "Borrador"
            self.tree_instrumentos.insert(
                "",
                "end",
                iid=str(item.get("id")),
                values=(
                    item.get("area", ""),
                    grupo,
                    item.get("periodo", ""),
                    item.get("total_preguntas", 0),
                    estado,
                ),
            )

    def _refrescar_preguntas_ui(self):
        for item in self.tree_preguntas.get_children():
            self.tree_preguntas.delete(item)
        for idx, pregunta in enumerate(self.preguntas):
            self.tree_preguntas.insert(
                "",
                "end",
                iid=str(idx),
                values=(pregunta.get("dimension", ""), pregunta.get("texto", "")),
            )
        self.lbl_resumen.config(text=f"Preguntas registradas: {len(self.preguntas)}")

    def _limpiar_editor_pregunta(self):
        self.var_dimension.set(DIMENSIONES[0])
        self.txt_pregunta.delete("1.0", "end")
        for item in self.tree_preguntas.selection():
            self.tree_preguntas.selection_remove(item)

    def _establecer_preguntas(self, preguntas):
        self.preguntas = [dict(item) for item in (preguntas or [])]
        self._limpiar_editor_pregunta()
        self._refrescar_preguntas_ui()

    def _nuevo_formulario(self):
        self.instrumento_id = None
        self.var_habilitada.set(False)
        self._establecer_preguntas([])

    def _cargar_formato_base(self):
        if self.preguntas:
            reemplazar = messagebox.askyesno(
                "Cargar formato base",
                "¿Desea reemplazar el formato actual?",
                parent=self,
            )
            if not reemplazar:
                return

        self._establecer_preguntas(obtener_formato_base_autoevaluacion())

    def _obtener_pregunta_editor(self):
        texto = self.txt_pregunta.get("1.0", "end").strip()
        dimension = self.var_dimension.get().strip()
        if not dimension:
            raise ValueError("Seleccione una dimensión.")
        if not texto:
            raise ValueError("Escriba el texto de la pregunta.")
        return {"dimension": dimension, "texto": texto}

    def _agregar_pregunta(self):
        try:
            pregunta = self._obtener_pregunta_editor()
        except ValueError as exc:
            messagebox.showerror("Autoevaluación", str(exc), parent=self)
            return
        self.preguntas.append(pregunta)
        self._establecer_preguntas(self.preguntas)

    def _actualizar_pregunta(self):
        seleccion = self.tree_preguntas.selection()
        if not seleccion:
            messagebox.showinfo(
                "Autoevaluación",
                "Seleccione una pregunta para actualizar.",
                parent=self,
            )
            return
        try:
            pregunta = self._obtener_pregunta_editor()
        except ValueError as exc:
            messagebox.showerror("Autoevaluación", str(exc), parent=self)
            return
        idx = int(seleccion[0])
        self.preguntas[idx] = pregunta
        self._establecer_preguntas(self.preguntas)

    def _eliminar_pregunta(self):
        seleccion = self.tree_preguntas.selection()
        if not seleccion:
            messagebox.showinfo(
                "Autoevaluación", "Seleccione una pregunta para eliminar.", parent=self
            )
            return
        idx = int(seleccion[0])
        self.preguntas.pop(idx)
        self._establecer_preguntas(self.preguntas)

    def _on_select_pregunta(self, event=None):
        seleccion = self.tree_preguntas.selection()
        if not seleccion:
            return
        idx = int(seleccion[0])
        pregunta = self.preguntas[idx]
        self.var_dimension.set(pregunta.get("dimension", DIMENSIONES[0]))
        self.txt_pregunta.delete("1.0", "end")
        self.txt_pregunta.insert("1.0", pregunta.get("texto", ""))

    def _on_select_instrumento(self, event=None):
        seleccion = self.tree_instrumentos.selection()
        if not seleccion:
            return
        self.instrumento_id = int(seleccion[0])

    def _cargar_seleccionado(self):
        seleccion = self.tree_instrumentos.selection()
        if not seleccion:
            messagebox.showinfo(
                "Autoevaluación", "Seleccione un instrumento para cargar.", parent=self
            )
            return
        data = obtener_autoevaluacion(int(seleccion[0]), db_path=self.db_path)
        if not data:
            messagebox.showerror(
                "Autoevaluación",
                "No se pudo cargar el instrumento seleccionado.",
                parent=self,
            )
            return
        self.instrumento_id = int(data.get("id"))
        self.var_area.set(data.get("area", ""))
        self.var_grado.set(data.get("grado", ""))
        self._refrescar_cursos_por_grado()
        self.var_curso.set(data.get("curso", ""))
        self.var_periodo.set(data.get("periodo", "Periodo 1"))
        self.var_habilitada.set(bool(int(data.get("habilitada") or 0)))
        self._establecer_preguntas(data.get("preguntas") or [])

    def _alternar_habilitada(self):
        seleccion = self.tree_instrumentos.selection()
        if not seleccion:
            messagebox.showinfo(
                "Autoevaluación",
                "Seleccione un instrumento para cambiar su estado.",
                parent=self,
            )
            return
        data = obtener_autoevaluacion(int(seleccion[0]), db_path=self.db_path)
        if not data:
            messagebox.showerror(
                "Autoevaluación",
                "No se encontró el instrumento seleccionado.",
                parent=self,
            )
            return
        nuevo_estado = not bool(int(data.get("habilitada") or 0))
        habilitar_autoevaluacion(
            int(seleccion[0]), habilitar=nuevo_estado, db_path=self.db_path
        )
        self.var_habilitada.set(nuevo_estado)
        self._recargar_instrumentos()

    def _abrir_resultados(self):
        VentanaResultadosAutoevaluacionDocente(
            self,
            docente_documento=self.docente_documento,
            docente_nombre=self.modulo_docente.nombre,
            db_path=self.db_path,
        )

    def _validar_formulario(self):
        if not self.var_area.get().strip():
            raise ValueError("Seleccione el área.")
        if not self.var_grado.get().strip():
            raise ValueError("Seleccione el grado.")
        if not self.var_curso.get().strip():
            raise ValueError("Seleccione el curso.")
        if not self.var_periodo.get().strip():
            raise ValueError("Seleccione el periodo.")
        if not self.preguntas:
            raise ValueError("Agregue al menos una pregunta.")

    def _guardar_instrumento(self):
        try:
            self._validar_formulario()
        except ValueError as exc:
            messagebox.showerror("Autoevaluación", str(exc), parent=self)
            return

        try:
            if self.instrumento_id is None:
                self.instrumento_id = crear_autoevaluacion(
                    docente=self.docente_documento,
                    area=self.var_area.get().strip(),
                    grado=self.var_grado.get().strip(),
                    curso=self.var_curso.get().strip(),
                    periodo=self.var_periodo.get().strip(),
                    preguntas=self.preguntas,
                    db_path=self.db_path,
                )
            actualizado = actualizar_autoevaluacion(
                autoevaluacion_id=self.instrumento_id,
                docente=self.docente_documento,
                area=self.var_area.get().strip(),
                grado=self.var_grado.get().strip(),
                curso=self.var_curso.get().strip(),
                periodo=self.var_periodo.get().strip(),
                preguntas=self.preguntas,
                habilitada=self.var_habilitada.get(),
                db_path=self.db_path,
            )
            if not actualizado:
                raise ValueError("No se pudo guardar el instrumento.")
        except Exception as exc:
            messagebox.showerror(
                "Autoevaluación",
                f"No fue posible guardar el instrumento.\n{exc}",
                parent=self,
            )
            return

        self._recargar_instrumentos()
        messagebox.showinfo(
            "Autoevaluación", "Instrumento guardado correctamente.", parent=self
        )


class VentanaResultadosAutoevaluacionDocente(tk.Toplevel):
    def __init__(self, parent, docente_documento, docente_nombre, db_path="sistema.db"):
        super().__init__(parent)
        self.docente_documento = str(docente_documento or "").strip()
        self.docente_nombre = str(docente_nombre or "").strip()
        self.db_path = db_path
        self.resultados_actuales = []

        self.title("Resultados de Autoevaluación")
        self.geometry("1180x760")
        self.minsize(1040, 680)
        self.configure(bg="#f5f7fa")
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        self._crear_estilos()
        self._construir_ui()
        self._cargar_filtros()
        self._consultar()

    def _crear_estilos(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Result.TFrame", background="#f5f7fa")
        style.configure("ResultCard.TFrame", background="white")
        style.configure("Result.TLabel", background="#f5f7fa", foreground="#1f2937")
        style.configure(
            "ResultTitle.TLabel",
            background="#f5f7fa",
            foreground="#0f172a",
            font=("Segoe UI", 15, "bold"),
        )
        style.configure(
            "ResultCardTitle.TLabel",
            background="white",
            foreground="#0f172a",
            font=("Segoe UI", 10, "bold"),
        )

    def _construir_ui(self):
        container = ttk.Frame(self, style="Result.TFrame", padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)

        header = ttk.Frame(container, style="Result.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(
            header,
            text="Resultados de Autoevaluación",
            style="ResultTitle.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            header,
            text=f"Docente: {self.docente_nombre}",
            style="Result.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        filtros = ttk.Frame(container, style="ResultCard.TFrame", padding=12)
        filtros.grid(row=1, column=0, sticky="ew")
        for idx in range(4):
            filtros.columnconfigure(idx, weight=1)

        self.var_area = tk.StringVar(value="Todos")
        self.var_grado = tk.StringVar(value="Todos")
        self.var_curso = tk.StringVar(value="Todos")
        self.var_periodo = tk.StringVar(value="Todos")

        ttk.Label(filtros, text="Área", style="Result.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.cb_area = ttk.Combobox(
            filtros, textvariable=self.var_area, state="readonly"
        )
        self.cb_area.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(2, 0))
        ttk.Label(filtros, text="Grado", style="Result.TLabel").grid(
            row=0, column=1, sticky="w"
        )
        self.cb_grado = ttk.Combobox(
            filtros, textvariable=self.var_grado, state="readonly"
        )
        self.cb_grado.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(2, 0))
        ttk.Label(filtros, text="Curso", style="Result.TLabel").grid(
            row=0, column=2, sticky="w"
        )
        self.cb_curso = ttk.Combobox(
            filtros, textvariable=self.var_curso, state="readonly"
        )
        self.cb_curso.grid(row=1, column=2, sticky="ew", padx=(0, 8), pady=(2, 0))
        ttk.Label(filtros, text="Periodo", style="Result.TLabel").grid(
            row=0, column=3, sticky="w"
        )
        self.cb_periodo = ttk.Combobox(
            filtros, textvariable=self.var_periodo, state="readonly"
        )
        self.cb_periodo.grid(row=1, column=3, sticky="ew", pady=(2, 0))

        acciones = ttk.Frame(filtros, style="ResultCard.TFrame")
        acciones.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        ttk.Button(acciones, text="Consultar", command=self._consultar).pack(
            side="left"
        )
        ttk.Button(acciones, text="Ver Detalle", command=self._ver_detalle).pack(
            side="left", padx=(6, 0)
        )
        ttk.Button(
            acciones, text="Exportar a Excel", command=self._exportar_excel
        ).pack(side="left", padx=(6, 0))
        ttk.Button(
            acciones,
            text="Sincronizar a planilla",
            command=self._sincronizar_planilla,
        ).pack(side="left", padx=(6, 0))
        ttk.Button(acciones, text="Cerrar", command=self.destroy).pack(side="right")

        resumen = ttk.Frame(container, style="ResultCard.TFrame", padding=12)
        resumen.grid(row=2, column=0, sticky="ew", pady=(10, 10))
        for idx in range(6):
            resumen.columnconfigure(idx, weight=1)
        ttk.Label(resumen, text="Resumen general", style="ResultCardTitle.TLabel").grid(
            row=0, column=0, sticky="w", columnspan=6
        )

        self.var_total = tk.StringVar(value="Total estudiantes evaluados: 0")
        self.var_promedio = tk.StringVar(value="Promedio del curso: 0.0")
        self.var_bajo = tk.StringVar(value="Bajo: 0")
        self.var_basico = tk.StringVar(value="Básico: 0")
        self.var_alto = tk.StringVar(value="Alto: 0")
        self.var_superior = tk.StringVar(value="Superior: 0")

        ttk.Label(resumen, textvariable=self.var_total, style="Result.TLabel").grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Label(resumen, textvariable=self.var_promedio, style="Result.TLabel").grid(
            row=1, column=1, sticky="w", pady=(8, 0)
        )
        ttk.Label(resumen, textvariable=self.var_bajo, style="Result.TLabel").grid(
            row=1, column=2, sticky="w", pady=(8, 0)
        )
        ttk.Label(resumen, textvariable=self.var_basico, style="Result.TLabel").grid(
            row=1, column=3, sticky="w", pady=(8, 0)
        )
        ttk.Label(resumen, textvariable=self.var_alto, style="Result.TLabel").grid(
            row=1, column=4, sticky="w", pady=(8, 0)
        )
        ttk.Label(resumen, textvariable=self.var_superior, style="Result.TLabel").grid(
            row=1, column=5, sticky="w", pady=(8, 0)
        )

        tabla_frame = ttk.Frame(container, style="ResultCard.TFrame", padding=12)
        tabla_frame.grid(row=3, column=0, sticky="nsew")
        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)

        columnas = ("documento", "nombre", "puntaje", "nota", "desempeno", "fecha")
        self.tree = ttk.Treeview(tabla_frame, columns=columnas, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=vsb.set)
        config_cols = {
            "documento": ("Documento", 120, "center"),
            "nombre": ("Nombre del estudiante", 280, "w"),
            "puntaje": ("Puntaje total", 110, "center"),
            "nota": ("Nota", 80, "center"),
            "desempeno": ("Desempeño", 100, "center"),
            "fecha": ("Fecha", 160, "center"),
        }
        for col in columnas:
            titulo, ancho, anchor = config_cols[col]
            self.tree.heading(col, text=titulo)
            self.tree.column(col, width=ancho, anchor=anchor)

    def _cargar_filtros(self):
        filtros = listar_filtros_resultados_autoevaluacion(
            docente=self.docente_documento,
            db_path=self.db_path,
        )
        self.cb_area["values"] = ["Todos"] + list(filtros.get("areas") or [])
        self.cb_grado["values"] = ["Todos"] + list(filtros.get("grados") or [])
        self.cb_curso["values"] = ["Todos"] + list(filtros.get("cursos") or [])
        self.cb_periodo["values"] = ["Todos"] + list(filtros.get("periodos") or [])
        self.var_area.set("Todos")
        self.var_grado.set("Todos")
        self.var_curso.set("Todos")
        self.var_periodo.set("Todos")

    def _consultar(self):
        self.resultados_actuales = consultar_resultados_autoevaluacion(
            docente=self.docente_documento,
            area=self.var_area.get(),
            grado=self.var_grado.get(),
            curso=self.var_curso.get(),
            periodo=self.var_periodo.get(),
            db_path=self.db_path,
        )
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.resultados_actuales:
            fecha = str(row.get("fecha") or "").strip()
            self.tree.insert(
                "",
                "end",
                iid=str(row.get("respuesta_id")),
                values=(
                    row.get("documento", ""),
                    row.get("nombre", ""),
                    f"{int(row.get('puntaje_total') or 0)}/{int(row.get('puntaje_maximo') or 0)}",
                    f"{float(row.get('nota') or 0):.2f}",
                    row.get("nivel_calculado", ""),
                    fecha,
                ),
            )

        resumen = resumir_resultados_autoevaluacion(self.resultados_actuales)
        conteos = resumen.get("conteos") or {}
        self.var_total.set(
            f"Total estudiantes evaluados: {int(resumen.get('total_estudiantes') or 0)}"
        )
        self.var_promedio.set(
            f"Promedio del curso: {float(resumen.get('promedio_curso') or 0):.2f}"
        )
        self.var_bajo.set(f"Bajo: {int(conteos.get('Bajo') or 0)}")
        self.var_basico.set(f"Básico: {int(conteos.get('Básico') or 0)}")
        self.var_alto.set(f"Alto: {int(conteos.get('Alto') or 0)}")
        self.var_superior.set(f"Superior: {int(conteos.get('Superior') or 0)}")

    def _resultado_seleccionado(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo(
                "Resultados",
                "Seleccione un estudiante para ver el detalle.",
                parent=self,
            )
            return None
        return int(seleccion[0])

    def _ver_detalle(self):
        respuesta_id = self._resultado_seleccionado()
        if respuesta_id is None:
            return
        detalle = detalle_resultado_autoevaluacion(respuesta_id, db_path=self.db_path)
        if not detalle:
            messagebox.showerror(
                "Resultados",
                "No se pudo obtener el detalle del resultado seleccionado.",
                parent=self,
            )
            return
        VentanaDetalleResultadoAutoevaluacion(self, detalle)

    def _exportar_excel(self):
        if not self.resultados_actuales:
            messagebox.showinfo(
                "Resultados",
                "No hay resultados para exportar con los filtros actuales.",
                parent=self,
            )
            return

        try:
            import pandas as pd
        except Exception:
            messagebox.showerror(
                "Resultados",
                "No se pudo exportar porque pandas no está disponible.",
                parent=self,
            )
            return

        ruta = filedialog.asksaveasfilename(
            title="Exportar resultados de autoevaluación",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            parent=self,
        )
        if not ruta:
            return

        filas = []
        for row in self.resultados_actuales:
            filas.append(
                {
                    "Documento": row.get("documento", ""),
                    "Nombre": row.get("nombre", ""),
                    "Área": row.get("area", ""),
                    "Grado": row.get("grado", ""),
                    "Curso": row.get("curso", ""),
                    "Periodo": row.get("periodo", ""),
                    "Puntaje total": int(row.get("puntaje_total") or 0),
                    "Puntaje máximo": int(row.get("puntaje_maximo") or 0),
                    "Nota": float(row.get("nota") or 0),
                    "Desempeño": row.get("nivel_calculado", ""),
                    "Fecha": row.get("fecha", ""),
                }
            )
        pd.DataFrame(filas).to_excel(ruta, index=False)
        messagebox.showinfo(
            "Resultados",
            "Archivo exportado correctamente.",
            parent=self,
        )

    def _sincronizar_planilla(self):
        confirmar = messagebox.askyesno(
            "Sincronizar a planilla",
            "Se sincronizarán a la planilla las notas de autoevaluación según los filtros actuales. ¿Desea continuar?",
            parent=self,
        )
        if not confirmar:
            return

        try:
            resumen = sincronizar_resultados_autoevaluacion(
                docente=self.docente_documento,
                area=None if self.var_area.get() == "Todos" else self.var_area.get(),
                grado=None if self.var_grado.get() == "Todos" else self.var_grado.get(),
                curso=None if self.var_curso.get() == "Todos" else self.var_curso.get(),
                periodo=(
                    None
                    if self.var_periodo.get() == "Todos"
                    else self.var_periodo.get()
                ),
                db_path=self.db_path,
            )
        except Exception as exc:
            messagebox.showerror(
                "Sincronización",
                f"No fue posible sincronizar la planilla.\n{exc}",
                parent=self,
            )
            return

        owner = getattr(self.master, "modulo_docente", None)
        if owner is not None:
            try:
                owner._llenar_combos_filtros()
                owner.cargar_datos()
            except Exception:
                pass

        messagebox.showinfo(
            "Sincronización",
            f"Registros procesados: {int(resumen.get('total') or 0)}\n"
            f"Insertados: {int(resumen.get('insertados') or 0)}\n"
            f"Actualizados: {int(resumen.get('actualizados') or 0)}",
            parent=self,
        )


class VentanaDetalleResultadoAutoevaluacion(tk.Toplevel):
    def __init__(self, parent, detalle):
        super().__init__(parent)
        self.detalle = detalle or {}
        self.title("Detalle de resultado")
        self.geometry("980x680")
        self.minsize(900, 620)
        self.configure(bg="#f5f7fa")
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        self._construir_ui()

    def _texto_respuesta(self, valor):
        for numero, texto in ESCALA:
            if int(numero) == int(valor or 0):
                return f"{numero} - {texto}"
        return "Sin respuesta"

    def _construir_ui(self):
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        encabezado = ttk.Frame(container)
        encabezado.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(
            encabezado,
            text="Detalle de Autoevaluación",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            encabezado,
            text=(
                f"Estudiante: {self.detalle.get('nombre', '')}  •  Documento: {self.detalle.get('documento', '')}  •  "
                f"Área: {self.detalle.get('area', '')}  •  Nota: {float(self.detalle.get('nota') or 0):.2f}  •  "
                f"Desempeño: {self.detalle.get('nivel_calculado', '')}"
            ),
        ).pack(anchor="w", pady=(4, 0))

        tabla_frame = ttk.Frame(container)
        tabla_frame.grid(row=1, column=0, sticky="nsew")
        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)

        columnas = ("dimension", "pregunta", "respuesta", "puntaje")
        tree = ttk.Treeview(tabla_frame, columns=columnas, show="headings")
        tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=vsb.set)

        config_cols = {
            "dimension": ("Dimensión", 160, "center"),
            "pregunta": ("Pregunta", 500, "w"),
            "respuesta": ("Respuesta seleccionada", 180, "center"),
            "puntaje": ("Puntaje por pregunta", 120, "center"),
        }
        for col in columnas:
            titulo, ancho, anchor = config_cols[col]
            tree.heading(col, text=titulo)
            tree.column(col, width=ancho, anchor=anchor)

        for item in self.detalle.get("detalle_preguntas") or []:
            tree.insert(
                "",
                "end",
                values=(
                    item.get("dimension", ""),
                    item.get("texto", ""),
                    self._texto_respuesta(item.get("respuesta", 0)),
                    item.get("puntaje", 0),
                ),
            )

        footer = ttk.Frame(container)
        footer.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(footer, text="Cerrar", command=self.destroy).pack(side="right")
