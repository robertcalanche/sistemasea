import tkinter as tk
from tkinter import messagebox, ttk

from autoevaluacion import (
    ESCALA,
    autoevaluacion_ya_respondida,
    crear_tablas_autoevaluacion,
    guardar_respuesta_autoevaluacion,
    listar_autoevaluaciones_activas,
    obtener_respuesta_autoevaluacion,
)


class VentanaAutoevaluacionEstudiante(tk.Toplevel):
    def __init__(
        self,
        parent,
        estudiante_documento,
        estudiante_nombre,
        grado,
        curso,
        db_path="sistema.db",
    ):
        super().__init__(parent)
        self.estudiante_documento = str(estudiante_documento or "").strip()
        self.estudiante_nombre = str(estudiante_nombre or "").strip()
        self.grado = str(grado or "").strip()
        self.curso = str(curso or "").strip()
        self.db_path = db_path
        self.instrumentos = []
        self.instrumento_actual = None
        self.respuesta_vars = []

        crear_tablas_autoevaluacion(db_path=self.db_path)

        self.title("Autoevaluación")
        self.geometry("1100x720")
        self.minsize(980, 660)
        self.configure(bg="#f6f8fb")
        self.transient(parent)
        self.grab_set()
        self.focus_set()

        self._crear_estilos()
        self._construir_ui()
        self._cargar_instrumentos()

    def _crear_estilos(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("AE.TFrame", background="#f6f8fb")
        style.configure("AECard.TFrame", background="white")
        style.configure("AE.TLabel", background="#f6f8fb", foreground="#1f2937")
        style.configure(
            "AETitle.TLabel",
            background="#f6f8fb",
            foreground="#0f172a",
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "AECardTitle.TLabel",
            background="white",
            foreground="#0f172a",
            font=("Segoe UI", 11, "bold"),
        )

    def _construir_ui(self):
        container = ttk.Frame(self, style="AE.TFrame", padding=16)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=0)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(1, weight=1)

        header = ttk.Frame(container, style="AE.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ttk.Label(header, text="Autoevaluación", style="AETitle.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            header,
            text=f"Estudiante: {self.estudiante_nombre}  •  Grado {self.grado}  Curso {self.curso}",
            style="AE.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        left = ttk.Frame(container, style="AECard.TFrame", padding=14)
        left.grid(row=1, column=0, sticky="nsw", padx=(0, 12))
        right = ttk.Frame(container, style="AECard.TFrame", padding=14)
        right.grid(row=1, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        ttk.Label(
            left, text="Instrumentos habilitados", style="AECardTitle.TLabel"
        ).pack(anchor="w", pady=(0, 8))
        self.tree = ttk.Treeview(
            left,
            columns=("area", "periodo", "preguntas", "estado"),
            show="headings",
            height=18,
        )
        self.tree.pack(fill="both", expand=True)
        for col, title, width in (
            ("area", "Área", 150),
            ("periodo", "Periodo", 100),
            ("preguntas", "Preg.", 60),
            ("estado", "Estado", 110),
        ):
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="center")

        acciones = ttk.Frame(left, style="AECard.TFrame")
        acciones.pack(fill="x", pady=(8, 0))
        ttk.Button(acciones, text="Abrir", command=self._abrir_seleccionado).pack(
            side="left"
        )
        ttk.Button(acciones, text="Cerrar", command=self.destroy).pack(side="right")

        self.encabezado = ttk.Label(
            right,
            text="Seleccione un instrumento para responder.",
            style="AECardTitle.TLabel",
        )
        self.encabezado.grid(row=0, column=0, sticky="w")

        self.canvas = tk.Canvas(right, bg="white", highlightthickness=0)
        self.scroll = ttk.Scrollbar(right, orient="vertical", command=self.canvas.yview)
        self.form_frame = ttk.Frame(self.canvas, style="AECard.TFrame")
        self.form_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=(10, 10))
        self.scroll.grid(row=1, column=1, sticky="ns", pady=(10, 10))

        footer = ttk.Frame(right, style="AECard.TFrame")
        footer.grid(row=2, column=0, sticky="ew")
        self.lbl_estado = ttk.Label(footer, text="", style="AE.TLabel")
        self.lbl_estado.pack(side="left")
        ttk.Button(footer, text="Enviar", command=self._enviar).pack(side="right")

        self.tree.bind("<<TreeviewSelect>>", self._on_select_instrumento)

    def _cargar_instrumentos(self):
        self.instrumentos = listar_autoevaluaciones_activas(
            grado=self.grado,
            curso=self.curso,
            db_path=self.db_path,
        )
        for item in self.tree.get_children():
            self.tree.delete(item)
        for instrumento in self.instrumentos:
            ya_respondida = autoevaluacion_ya_respondida(
                instrumento.get("id"),
                self.estudiante_documento,
                db_path=self.db_path,
            )
            estado = "Respondida" if ya_respondida else "Pendiente"
            self.tree.insert(
                "",
                "end",
                iid=str(instrumento.get("id")),
                values=(
                    instrumento.get("area", ""),
                    instrumento.get("periodo", ""),
                    instrumento.get("total_preguntas", 0),
                    estado,
                ),
            )
        if not self.instrumentos:
            self.encabezado.config(
                text="No hay autoevaluaciones habilitadas para tu grupo."
            )
            self.lbl_estado.config(text="")

    def _buscar_instrumento(self, instrumento_id):
        for item in self.instrumentos:
            if int(item.get("id")) == int(instrumento_id):
                return item
        return None

    def _on_select_instrumento(self, event=None):
        self._abrir_seleccionado()

    def _limpiar_formulario(self):
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        self.respuesta_vars = []

    def _abrir_seleccionado(self):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        instrumento = self._buscar_instrumento(int(seleccion[0]))
        if not instrumento:
            return
        self.instrumento_actual = instrumento
        self._render_formulario()

    def _render_formulario(self):
        self._limpiar_formulario()
        instrumento = self.instrumento_actual
        if not instrumento:
            return

        docente = instrumento.get("docente_nombre") or instrumento.get("docente") or ""
        self.encabezado.config(
            text=(
                f"Área: {instrumento.get('area', '')}  •  Grado: {instrumento.get('grado', '')}  •  "
                f"Curso: {instrumento.get('curso', '')}  •  Periodo: {instrumento.get('periodo', '')}  •  Docente: {docente}"
            )
        )

        respuesta_prev = obtener_respuesta_autoevaluacion(
            instrumento.get("id"),
            self.estudiante_documento,
            db_path=self.db_path,
        )
        preguntas = instrumento.get("preguntas") or []
        grupos = {}
        for idx, pregunta in enumerate(preguntas):
            grupos.setdefault(pregunta.get("dimension", "Sin dimensión"), []).append(
                (idx, pregunta)
            )

        row = 0
        respuestas_previas = (
            respuesta_prev.get("respuestas", []) if respuesta_prev else []
        )
        self.respuesta_vars = [tk.IntVar(value=0) for _ in preguntas]
        for dimension, items in grupos.items():
            ttk.Label(self.form_frame, text=dimension, style="AECardTitle.TLabel").grid(
                row=row, column=0, sticky="w", pady=(6, 8)
            )
            row += 1
            for idx, pregunta in items:
                ttk.Label(
                    self.form_frame,
                    text=f"{idx + 1}. {pregunta.get('texto', '')}",
                    style="AE.TLabel",
                    wraplength=700,
                    justify="left",
                ).grid(row=row, column=0, sticky="w", pady=(4, 2))
                row += 1
                valores = ttk.Frame(self.form_frame, style="AECard.TFrame")
                valores.grid(row=row, column=0, sticky="w", pady=(0, 8))
                valor_actual = (
                    int(respuestas_previas[idx]) if idx < len(respuestas_previas) else 0
                )
                self.respuesta_vars[idx].set(valor_actual)
                for valor, texto in ESCALA:
                    ttk.Radiobutton(
                        valores,
                        text=f"{valor} {texto}",
                        value=valor,
                        variable=self.respuesta_vars[idx],
                    ).pack(side="left", padx=(0, 10))
                row += 1

        if respuesta_prev:
            self.lbl_estado.config(
                text=(
                    f"Ya respondida  •  Puntaje: {respuesta_prev.get('puntaje_total', 0)}/"
                    f"{respuesta_prev.get('puntaje_maximo', 0)}  •  Nota: {respuesta_prev.get('nota', 0)}  •  "
                    f"Nivel: {respuesta_prev.get('nivel', '')}"
                )
            )
        else:
            self.lbl_estado.config(text="Completa todas las preguntas antes de enviar.")

    def _enviar(self):
        instrumento = self.instrumento_actual
        if not instrumento:
            messagebox.showinfo(
                "Autoevaluación", "Seleccione una autoevaluación.", parent=self
            )
            return
        if autoevaluacion_ya_respondida(
            instrumento.get("id"),
            self.estudiante_documento,
            db_path=self.db_path,
        ):
            messagebox.showinfo(
                "Autoevaluación",
                "Esta autoevaluación ya fue respondida.",
                parent=self,
            )
            self._render_formulario()
            self._cargar_instrumentos()
            return

        respuestas = [var.get() for var in self.respuesta_vars]
        if not respuestas or any(valor not in (1, 2, 3, 4) for valor in respuestas):
            messagebox.showerror(
                "Autoevaluación",
                "Debes responder todas las preguntas con una opción de 1 a 4.",
                parent=self,
            )
            return

        try:
            nota, nivel = guardar_respuesta_autoevaluacion(
                instrumento.get("id"),
                self.estudiante_documento,
                respuestas,
                db_path=self.db_path,
            )
        except Exception as exc:
            messagebox.showerror(
                "Autoevaluación",
                f"No fue posible guardar la respuesta.\n{exc}",
                parent=self,
            )
            return

        puntaje_total = sum(respuestas)
        puntaje_maximo = len(respuestas) * 4
        self.lbl_estado.config(
            text=(
                f"Puntaje: {puntaje_total}/{puntaje_maximo}  •  Nota final: {nota}  •  Nivel: {nivel}"
            )
        )
        self._cargar_instrumentos()
        self._render_formulario()
        messagebox.showinfo(
            "Autoevaluación enviada",
            f"Puntaje total: {puntaje_total}\nNota final: {nota}\nNivel: {nivel}",
            parent=self,
        )
