def mostrar_detalle_respuestas_estudiante(
    parent, area, intento, respuestas, base_dir=None
):
    """Muestra la revisión de evaluación para el estudiante, agrupando por contexto y mostrando puntaje y resultado."""
    import tkinter as tk
    from collections import OrderedDict
    from pathlib import Path

    COLOR_CORRECTA = "#51cf66"  # Verde Docente
    COLOR_INCORRECTA = "#ff6b6b"  # Rojo Docente
    COLOR_CTX = "#e8f4f8"  # Igual Docente
    COLOR_PREG = "#f9f9f9"  # Igual Docente
    COLOR_PRIMARIO = "#0078D7"
    COLOR_SECUNDARIO = "#ffffff"
    base_dir = Path(base_dir) if base_dir else Path(".")

    for w in parent.winfo_children():
        w.destroy()

    # Calcular nota y desempeño
    NOTA_MAXIMA = 5.0
    total_preguntas = len(respuestas)
    valor_pregunta = (NOTA_MAXIMA / total_preguntas) if total_preguntas > 0 else 0
    nota_final = sum(
        valor_pregunta if r.get("es_correcta", 0) else 0 for r in respuestas
    )
    desempeno = (nota_final / NOTA_MAXIMA * 100) if NOTA_MAXIMA > 0 else 0

    header = tk.Frame(parent, bg=COLOR_PRIMARIO)
    header.pack(fill="x")
    tk.Label(
        header,
        text=f"Detalle de Respuestas - Área: {area}",
        font=("Segoe UI", 14, "bold"),
        bg=COLOR_PRIMARIO,
        fg="white",
    ).pack(side="left", padx=20, pady=10)

    tk.Label(
        parent,
        text=f"Nota final: {nota_final:.2f} / {NOTA_MAXIMA}",
        font=("Segoe UI", 12, "bold"),
        fg=COLOR_PRIMARIO,
        pady=6,
    ).pack()
    tk.Label(
        parent,
        text=f"Desempeño: {desempeno:.0f}%",
        font=("Segoe UI", 12),
        fg=COLOR_PRIMARIO,
    ).pack()

    canvas_frame = tk.Frame(parent)
    canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
    canvas = tk.Canvas(canvas_frame, bg=COLOR_SECUNDARIO, highlightthickness=0)
    scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    frame_scroll = tk.Frame(canvas, bg=COLOR_SECUNDARIO)
    frame_scroll.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=frame_scroll, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Agrupar por contexto
    grupos_contexto = OrderedDict()
    for r in respuestas:
        ctx_id = r.get("id_contexto")
        if ctx_id not in grupos_contexto:
            grupos_contexto[ctx_id] = []
        grupos_contexto[ctx_id].append(r)

    pregunta_num = 1
    num_contexto = 1
    for ctx_id, preguntas_grupo in grupos_contexto.items():
        ctx_texto = preguntas_grupo[0].get("contexto", "").strip()
        if ctx_texto and ctx_texto.lower() != "nan":
            ctx_frame = tk.Frame(
                frame_scroll, bg=COLOR_CTX, relief="solid", borderwidth=1
            )
            ctx_frame.pack(fill="x", padx=8, pady=(12, 6))
            titulo_ctx = f"TEXTO {num_contexto}"
            tk.Label(
                ctx_frame,
                text=titulo_ctx,
                font=("Segoe UI", 11, "bold"),
                bg=COLOR_CTX,
            ).pack(anchor="w", padx=10, pady=(8, 4))
            tk.Label(
                ctx_frame,
                text=ctx_texto,
                font=("Segoe UI", 10),
                bg=COLOR_CTX,
                wraplength=800,
                justify="left",
            ).pack(anchor="w", padx=10, pady=(0, 8))
            tk.Label(
                ctx_frame,
                text="—" * 80,
                font=("Segoe UI", 9),
                bg=COLOR_CTX,
                fg="#999999",
            ).pack(anchor="w", padx=10, pady=(0, 4))
            num_contexto += 1

        for r in preguntas_grupo:
            qf = tk.Frame(frame_scroll, bg=COLOR_PREG, relief="solid", borderwidth=1)
            qf.pack(fill="x", padx=8, pady=6)
            enun = r.get("enunciado", f"Pregunta {r.get('pregunta_id', pregunta_num)}")
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
                text=f"Pregunta {pregunta_num}: {enun}",
                font=("Segoe UI", 10, "bold"),
                bg=COLOR_PREG,
                wraplength=800,
                justify="left",
            ).pack(anchor="w", padx=10, pady=6)

            # Imagen si existe
            try:
                imagen = r.get("imagen")
                if imagen:
                    ruta = base_dir / "imagenes_preguntas" / str(imagen)
                    if ruta.exists():
                        from PIL import Image, ImageTk

                        img = Image.open(ruta)
                        max_ancho = 500
                        w, h = img.size
                        if w > max_ancho:
                            ratio = max_ancho / float(w)
                            img = img.resize((int(w * ratio), int(h * ratio)))
                        img_tk = ImageTk.PhotoImage(img)
                        lbl = tk.Label(qf, image=img_tk, bg=COLOR_PREG)
                        lbl.image = img_tk
                        lbl.pack(anchor="w", padx=10, pady=(0, 6))
            except Exception:
                pass

            tk.Label(
                qf,
                text=f"Tu respuesta: {letra_sel} - {seleccion}",
                font=("Segoe UI", 10),
                bg=COLOR_PREG,
            ).pack(anchor="w", padx=20)
            tk.Label(
                qf,
                text=f"Respuesta correcta: {correcta}",
                font=("Segoe UI", 10),
                bg=COLOR_PREG,
                fg=COLOR_PRIMARIO,
            ).pack(anchor="w", padx=20, pady=(0, 6))

            puntaje = valor_pregunta if es_corr else 0.0
            estado_text = "✅ Correcta" if es_corr else "❌ Incorrecta"
            estado_text_completo = f"{estado_text} | Puntaje: {puntaje:.1f}"

            tk.Label(
                qf,
                text=estado_text_completo,
                font=("Segoe UI", 10, "bold"),
                bg=COLOR_PREG,
                fg=COLOR_CORRECTA if es_corr else COLOR_INCORRECTA,
            ).pack(anchor="w", padx=20, pady=(0, 8))

            pregunta_num += 1


class CalendarioAcademico:
    def _abrir_datepicker_planeacion(self, event):
        item = self.tree_planeacion.identify_row(event.y)
        col = self.tree_planeacion.identify_column(event.x)
        if not item or col not in ("#2", "#3"):
            return
        idx = int(item)
        campo = 1 if col == "#2" else 2
        self._abrir_selector_fecha_planeacion(idx, campo)

    def __init__(self, parent, anio_lectivo=None):
        self.parent = parent
        self.anio_lectivo = self._resolver_anio_lectivo(anio_lectivo)
        self._build_ui()

    def _resolver_anio_lectivo(self, anio_lectivo=None):
        valor = str(anio_lectivo or "").strip()
        if valor:
            return valor
        try:
            from core.configuracion import obtener_anio_lectivo

            valor = str(obtener_anio_lectivo() or "").strip()
            if valor:
                return valor
        except Exception:
            pass
        return str(datetime.now().year)

    def _build_ui(self):
        # Encabezado
        header = tk.Frame(self.parent, bg=COLOR_PRIMARIO, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        titulo = f"📅 Calendario Académico  —  Año lectivo: {self.anio_lectivo}"
        tk.Label(
            header,
            text=titulo,
            font=("Segoe UI", 20, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
            anchor="w",
        ).pack(side="left", padx=30, pady=20)

        # Descripción
        desc = tk.Label(
            self.parent,
            text="Permite configurar los períodos académicos y controlar su impacto en procesos como asistencia, evaluaciones y reportes.",
            font=("Segoe UI", 11),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
            wraplength=700,
            justify="left",
        )
        desc.pack(fill="x", padx=30, pady=(10, 10))

        # --- CONTENEDOR UNIFICADO CON SCROLL ---
        cont_frame = tk.Frame(self.parent, bg=COLOR_SECUNDARIO)
        cont_frame.pack(padx=30, pady=10, fill="both", expand=True)

        canvas = tk.Canvas(cont_frame, bg=COLOR_SECUNDARIO, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(cont_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame interior para todo el contenido scrolleable
        inner = tk.Frame(canvas, bg=COLOR_SECUNDARIO)
        canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner.bind("<Configure>", _on_configure)

        # Permitir scroll con rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Encabezado de sección: Periodos Académicos
        lbl_periodos = tk.Label(
            inner,
            text="Periodos Académicos",
            font=("Segoe UI", 15, "bold"),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_PRIMARIO,
            anchor="w",
        )
        lbl_periodos.pack(fill="x", pady=(0, 8))

        # Tabla de períodos
        tabla_frame = tk.Frame(inner, bg=COLOR_SECUNDARIO)
        tabla_frame.pack(pady=10, fill="x")

        columns = ("periodo", "inicio", "fin")
        self.tree = ttk.Treeview(
            tabla_frame, columns=columns, show="headings", height=4
        )
        self.tree.heading("periodo", text="Período académico")
        self.tree.heading("inicio", text="Fecha inicio")
        self.tree.heading("fin", text="Fecha fin")
        self.tree.column("periodo", width=180, anchor="center")
        self.tree.column("inicio", width=120, anchor="center")
        self.tree.column("fin", width=120, anchor="center")
        self.tree.pack(side="left", fill="x", expand=True)

        # Periodos fijos
        self.periodos = [
            ("Primer período",),
            ("Segundo período",),
            ("Tercer período",),
            ("Cuarto período",),
        ]
        # Fechas por defecto: día y mes fijos, año lectivo dinámico
        try:
            anio_lectivo_int = int(self.anio_lectivo)
        except Exception:
            from datetime import datetime

            anio_lectivo_int = datetime.now().year
        self.periodos_default = [
            (
                "Primer período",
                f"{anio_lectivo_int}-01-19",
                f"{anio_lectivo_int}-03-27",
            ),
            (
                "Segundo período",
                f"{anio_lectivo_int}-04-06",
                f"{anio_lectivo_int}-06-12",
            ),
            (
                "Tercer período",
                f"{anio_lectivo_int}-07-06",
                f"{anio_lectivo_int}-09-11",
            ),
            (
                "Cuarto período",
                f"{anio_lectivo_int}-09-14",
                f"{anio_lectivo_int}-11-29",
            ),
        ]
        self._date_vars = []
        self._load_periodos()

        # --- Planeación y Desarrollo Institucional ---
        lbl_planeacion = tk.Label(
            inner,
            text="Planeación y Desarrollo Institucional",
            font=("Segoe UI", 15, "bold"),
            bg=COLOR_SECUNDARIO,
            fg=COLOR_PRIMARIO,
            anchor="w",
        )
        lbl_planeacion.pack(fill="x", pady=(30, 8))

        planeacion_frame = tk.Frame(inner, bg=COLOR_SECUNDARIO)
        planeacion_frame.pack(pady=10, fill="x")

        columns_planeacion = ("actividad", "inicio", "fin")
        self.tree_planeacion = ttk.Treeview(
            planeacion_frame, columns=columns_planeacion, show="headings", height=5
        )
        self.tree_planeacion.heading("actividad", text="Actividad")
        self.tree_planeacion.heading("inicio", text="Inicia")
        self.tree_planeacion.heading("fin", text="Finaliza")
        self.tree_planeacion.column("actividad", width=350, anchor="w")
        self.tree_planeacion.column("inicio", width=120, anchor="center")
        self.tree_planeacion.column("fin", width=120, anchor="center")
        self.tree_planeacion.pack(side="left", fill="x", expand=True)

        # Botones para agregar y eliminar actividades
        acciones_planeacion = tk.Frame(inner, bg=COLOR_SECUNDARIO)
        acciones_planeacion.pack(pady=(0, 5))
        tk.Button(
            acciones_planeacion,
            text="➕ Nueva actividad",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_PRIMARIO,
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            command=self._agregar_actividad_planeacion,
        ).pack(side="left", padx=5)
        tk.Button(
            acciones_planeacion,
            text="🗑 Eliminar actividad",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_ADVERTENCIA,
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            command=self._eliminar_actividad_planeacion,
        ).pack(side="left", padx=5)

        # Datos editables de planeación (en memoria)
        # Fechas por defecto: día y mes fijos, año lectivo dinámico para planeación
        try:
            anio_lectivo_int = int(self.anio_lectivo)
        except Exception:
            from datetime import datetime

            anio_lectivo_int = datetime.now().year
        self.datos_planeacion_default = [
            (
                "Actividad de Desarrollo Institucional (Inicio Año Lectivo)",
                f"12/01/{anio_lectivo_int}",
                f"18/01/{anio_lectivo_int}",
            ),
            (
                "Actividad de Desarrollo Institucional (Semana Santa)",
                f"30/03/{anio_lectivo_int}",
                f"05/04/{anio_lectivo_int}",
            ),
            (
                "Actividad de Desarrollo Institucional (Receso Estudiantil)",
                f"15/06/{anio_lectivo_int}",
                f"05/07/{anio_lectivo_int}",
            ),
            (
                "Actividad de Desarrollo Institucional (Receso Estudiantil)",
                f"15/10/{anio_lectivo_int}",
                f"21/07/{anio_lectivo_int}",
            ),
            (
                "Actividad de Desarrollo Institucional (Finalización Año Lectivo)",
                f"30/11/{anio_lectivo_int}",
                f"04/12/{anio_lectivo_int}",
            ),
        ]

        # Cargar planeación desde BD (persistencia real)
        self._crear_tabla_planeacion_si_no_existe()
        self.datos_planeacion = self._leer_planeacion_bd()
        if not self.datos_planeacion:
            self.datos_planeacion = [list(row) for row in self.datos_planeacion_default]
        self._cargar_planeacion()
        self.tree_planeacion.bind("<Double-1>", self._editar_celda_planeacion)

        if not hasattr(self, "_acciones_finales"):
            self._acciones_finales = tk.Frame(self.parent, bg=COLOR_SECUNDARIO)
            self._acciones_finales.pack(fill="x", padx=30, pady=(0, 15))
            self._btn_guardar = tk.Button(
                self._acciones_finales,
                text="💾 Guardar",
                font=("Segoe UI", 11, "bold"),
                bg=COLOR_PRIMARIO,
                fg="white",
                relief="flat",
                padx=18,
                pady=8,
                command=self._guardar,
            )
            self._btn_guardar.pack(side="left", padx=10)
            self._btn_restablecer = tk.Button(
                self._acciones_finales,
                text="↩ Restablecer",
                font=("Segoe UI", 11, "bold"),
                bg=COLOR_ADVERTENCIA,
                fg="white",
                relief="flat",
                padx=18,
                pady=8,
                command=self._restablecer,
            )
            self._btn_restablecer.pack(side="left", padx=10)

    def _crear_tabla_planeacion_si_no_existe(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute(
                """CREATE TABLE IF NOT EXISTS planeacion_institucional (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actividad TEXT NOT NULL,
                    fecha_inicio TEXT NOT NULL,
                    fecha_fin TEXT NOT NULL
                )"""
            )
            conn.commit()
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _leer_planeacion_bd(self):
        datos = []
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute(
                "SELECT actividad, fecha_inicio, fecha_fin FROM planeacion_institucional ORDER BY id ASC"
            )
            for row in cur.fetchall():
                datos.append([row[0], row[1], row[2]])
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
        return datos

    def _editar_celda_planeacion(self, event):
        item = self.tree_planeacion.identify_row(event.y)
        col = self.tree_planeacion.identify_column(event.x)
        if not item or col not in ("#1", "#2", "#3"):
            return
        idx = int(item)
        if col == "#1":
            # Editar nombre de la actividad
            x, y, width, height = self.tree_planeacion.bbox(idx, "actividad")
            entry = tk.Entry(self.tree_planeacion)
            entry.place(x=x, y=y, width=width, height=height)
            entry.insert(0, self.datos_planeacion[idx][0])
            entry.focus_set()

            def on_entry_confirm(event=None):
                nombre = entry.get().strip()
                if nombre:
                    self.datos_planeacion[idx][0] = nombre
                    vals = list(self.tree_planeacion.item(idx, "values"))
                    vals[0] = nombre
                    self.tree_planeacion.item(idx, values=vals)
                entry.destroy()

            entry.bind("<Return>", on_entry_confirm)
            entry.bind("<FocusOut>", on_entry_confirm)
        else:
            # Editar fechas (ya implementado)
            campo = 1 if col == "#2" else 2
            self._abrir_selector_fecha_planeacion(idx, campo)

    def _agregar_actividad_planeacion(self):
        # Diálogo para nueva actividad
        nombre = simpledialog.askstring("Nueva actividad", "Nombre de la actividad:")
        if not nombre:
            return
        from datetime import datetime, timedelta

        hoy = datetime.now()
        inicio = hoy.strftime("%d/%m/%Y")
        fin = (hoy + timedelta(days=1)).strftime("%d/%m/%Y")
        self.datos_planeacion.append([nombre, inicio, fin])
        self._cargar_planeacion()
        # Activar automáticamente el selector de fecha de inicio para la nueva fila
        self.parent.after(
            150,
            lambda: self._abrir_selector_fecha_planeacion(
                len(self.datos_planeacion) - 1, 1
            ),
        )

    def _eliminar_actividad_planeacion(self):
        sel = self.tree_planeacion.selection()
        if not sel:
            messagebox.showinfo(
                "Eliminar actividad", "Seleccione una fila para eliminar."
            )
            return
        idx = int(sel[0])
        if messagebox.askyesno(
            "Eliminar actividad",
            f"¿Eliminar la actividad '{self.datos_planeacion[idx][0]}'?",
        ):
            self.datos_planeacion.pop(idx)
            self._cargar_planeacion()

        # (Eliminado: no debe crear botones aquí)

    def _cargar_planeacion(self):
        self.tree_planeacion.delete(*self.tree_planeacion.get_children())
        for idx, (actividad, inicio, fin) in enumerate(self.datos_planeacion):
            self.tree_planeacion.insert(
                "", "end", iid=idx, values=(actividad, inicio, fin)
            )

    def _abrir_selector_fecha_planeacion(self, idx, campo):
        # Mejorada: siempre muestra el DateEntry y asegura edición correcta
        from datetime import datetime as _dt
        import tkinter as tk
        import tkcalendar

        col_id = "inicio" if campo == 1 else "fin"
        x, y, width, height = self.tree_planeacion.bbox(idx, col_id)
        date_value = self.datos_planeacion[idx][campo]
        fecha_inicial = None
        # Intentar parsear la fecha en ambos formatos
        if date_value:
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    fecha_inicial = _dt.strptime(date_value, fmt)
                    break
                except Exception:
                    continue
        if not fecha_inicial:
            fecha_inicial = _dt.now()

        # Destruir cualquier widget DateEntry/Entry previo en la celda
        for widget in self.tree_planeacion.winfo_children():
            widget.destroy()

        cal = tkcalendar.DateEntry(
            self.tree_planeacion,
            date_pattern="dd/mm/yyyy",
            showweeknumbers=False,
            state="normal",
        )
        cal.set_date(fecha_inicial)
        cal.place(x=x, y=y, width=width, height=height)
        cal.focus_set()

        # Forzar apertura del calendario desplegable
        try:
            cal.after(
                100,
                lambda: cal.event_generate("<Button-1>", x=width - 10, y=height // 2),
            )
        except Exception:
            pass

        def set_fecha(event=None):
            fecha = cal.get()
            self.datos_planeacion[idx][campo] = fecha
            vals = list(self.tree_planeacion.item(idx, "values"))
            vals[campo] = fecha
            self.tree_planeacion.item(idx, values=vals)
            cal.destroy()

        cal.bind("<Return>", set_fecha)
        cal.bind("<FocusOut>", set_fecha)

        # Si el usuario presiona Escape, cancelar edición
        def cancelar(event=None):
            cal.destroy()

        cal.bind("<Escape>", cancelar)

    def _load_periodos(self):
        # Cargar de BD o inicializar con fechas por defecto
        self.tree.delete(*self.tree.get_children())
        self._date_vars.clear()
        datos = self._leer_periodos_bd()
        for idx, (nombre,) in enumerate(self.periodos):
            # Si hay datos en BD, usarlos; si no, usar fechas por defecto
            inicio = datos.get(nombre, {}).get("inicio", "")
            fin = datos.get(nombre, {}).get("fin", "")
            if not inicio or not fin:
                # Buscar en periodos_default
                for def_nombre, def_inicio, def_fin in getattr(
                    self, "periodos_default", []
                ):
                    if def_nombre == nombre:
                        inicio = def_inicio
                        fin = def_fin
                        break
            self.tree.insert("", "end", iid=idx, values=(nombre, inicio, fin))
            self._date_vars.append(
                {"inicio": tk.StringVar(value=inicio), "fin": tk.StringVar(value=fin)}
            )
        self.tree.bind("<Double-1>", self._abrir_datepicker)

    def _abrir_datepicker(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item or col not in ("#2", "#3"):
            return
        idx = int(item)
        campo = "inicio" if col == "#2" else "fin"
        self._abrir_selector_fecha(idx, campo)

    def _abrir_selector_fecha(self, idx, campo):
        try:
            import tkcalendar
            from datetime import datetime as _dt

            # Obtener posición y tamaño de la celda
            col_id = "inicio" if campo == "inicio" else "fin"
            x, y, width, height = self.tree.bbox(idx, col_id)
            # Crear DateEntry embebido en la celda
            date_var = self._date_vars[idx][campo]
            date_value = date_var.get()
            # Determinar fecha inicial: si hay valor previo, usarlo; si no, año lectivo 1 de enero
            fecha_inicial = None
            if date_value:
                try:
                    fecha_inicial = _dt.strptime(date_value, "%Y-%m-%d")
                except Exception:
                    fecha_inicial = None
            if not fecha_inicial:
                # Usar año lectivo configurado, día 1 de enero
                try:
                    anio = int(self.anio_lectivo)
                except Exception:
                    anio = _dt.now().year
                fecha_inicial = _dt(anio, 1, 1)
            cal = tkcalendar.DateEntry(
                self.tree,
                date_pattern="yyyy-mm-dd",
                showweeknumbers=False,
                state="normal",
            )
            cal.set_date(fecha_inicial)
            cal.place(x=x, y=y, width=width, height=height)
            cal.focus_set()

            # Forzar apertura del calendario desplegable al hacer doble clic
            try:
                cal.after(
                    100,
                    lambda: cal.event_generate(
                        "<Button-1>", x=width - 10, y=height // 2
                    ),
                )
            except Exception:
                pass

            def set_fecha(event=None):
                fecha = cal.get()
                self._date_vars[idx][campo].set(fecha)
                vals = list(self.tree.item(idx, "values"))
                vals[1 if campo == "inicio" else 2] = fecha
                self.tree.item(idx, values=vals)
                cal.destroy()

            cal.bind("<Return>", set_fecha)
            cal.bind("<FocusOut>", set_fecha)
        except Exception:
            # Fallback: edición manual con Entry
            col_id = "inicio" if campo == "inicio" else "fin"
            x, y, width, height = self.tree.bbox(idx, col_id)
            entry = tk.Entry(self.tree)
            entry.place(x=x, y=y, width=width, height=height)
            entry.insert(0, self._date_vars[idx][campo].get())
            entry.focus_set()

            def on_entry_confirm(event=None):
                fecha = entry.get().strip()
                self._date_vars[idx][campo].set(fecha)
                vals = list(self.tree.item(idx, "values"))
                vals[1 if campo == "inicio" else 2] = fecha
                self.tree.item(idx, values=vals)
                entry.destroy()

            entry.bind("<Return>", on_entry_confirm)
            entry.bind("<FocusOut>", on_entry_confirm)

    def _leer_periodos_bd(self):
        # Lee los periodos desde la BD
        datos = {}
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS calendario_academico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    periodo TEXT UNIQUE,
                    fecha_inicio TEXT,
                    fecha_fin TEXT
                )
            """
            )
            for (nombre,) in self.periodos:
                cur.execute(
                    "SELECT fecha_inicio, fecha_fin FROM calendario_academico WHERE periodo=?",
                    (nombre,),
                )
                row = cur.fetchone()
                if row:
                    datos[nombre] = {"inicio": row[0] or "", "fin": row[1] or ""}
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
        return datos

    def _guardar(self):
        # Validaciones Periodos Académicos
        fechas = []
        for idx, (nombre,) in enumerate(self.periodos):
            inicio = self._date_vars[idx]["inicio"].get().strip()
            fin = self._date_vars[idx]["fin"].get().strip()
            if not inicio or not fin:
                messagebox.showerror(
                    "Error de validación",
                    f"Debe ingresar ambas fechas para '{nombre}'.",
                )
                return
            try:
                dt_inicio = datetime.strptime(inicio, "%Y-%m-%d")
                dt_fin = datetime.strptime(fin, "%Y-%m-%d")
            except Exception:
                messagebox.showerror(
                    "Error de formato",
                    f"Formato de fecha inválido en '{nombre}'. Use AAAA-MM-DD.",
                )
                return
            if dt_inicio >= dt_fin:
                messagebox.showerror(
                    "Error de validación",
                    f"La fecha de inicio debe ser menor que la de fin en '{nombre}'.",
                )
                return
            fechas.append((dt_inicio, dt_fin, nombre))
        # Validar superposición
        fechas_ordenadas = sorted(fechas, key=lambda x: x[0])
        for i in range(1, len(fechas_ordenadas)):
            if fechas_ordenadas[i][0] <= fechas_ordenadas[i - 1][1]:
                messagebox.showerror(
                    "Error de validación",
                    f"Los períodos '{fechas_ordenadas[i-1][2]}' y '{fechas_ordenadas[i][2]}' se superponen.",
                )
                return
        # Guardar en BD
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            for idx, (nombre,) in enumerate(self.periodos):
                inicio = self._date_vars[idx]["inicio"].get().strip()
                fin = self._date_vars[idx]["fin"].get().strip()
                cur.execute(
                    """
                    INSERT INTO calendario_academico (periodo, fecha_inicio, fecha_fin)
                    VALUES (?, ?, ?)
                    ON CONFLICT(periodo) DO UPDATE SET fecha_inicio=excluded.fecha_inicio, fecha_fin=excluded.fecha_fin
                """,
                    (nombre, inicio, fin),
                )
            conn.commit()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el calendario.\n{e}")
            return
        finally:
            try:
                conn.close()
            except Exception:
                pass
        # Validaciones Planeación (solo formato y no vacío)
        for idx, row in enumerate(self.datos_planeacion):
            actividad, inicio, fin = row
            if not inicio or not fin:
                messagebox.showerror(
                    "Error de validación",
                    f"Debe ingresar ambas fechas para '{actividad}'.",
                )
                return
            # Validar formato dd/mm/yyyy
            try:
                dt_inicio = datetime.strptime(inicio, "%d/%m/%Y")
                dt_fin = datetime.strptime(fin, "%d/%m/%Y")
            except Exception:
                messagebox.showerror(
                    "Error de formato",
                    f"Formato de fecha inválido en '{actividad}'. Use DD/MM/AAAA.",
                )
                return
            if dt_inicio >= dt_fin:
                messagebox.showerror(
                    "Error de validación",
                    f"La fecha de inicio debe ser menor que la de fin en '{actividad}'.",
                )
                return
        # Guardar planeación en BD (persistencia real)
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("DELETE FROM planeacion_institucional")
            for actividad, inicio, fin in self.datos_planeacion:
                cur.execute(
                    "INSERT INTO planeacion_institucional (actividad, fecha_inicio, fecha_fin) VALUES (?, ?, ?)",
                    (actividad, inicio, fin),
                )
            conn.commit()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la planeación.\n{e}")
            return
        finally:
            try:
                conn.close()
            except Exception:
                pass
        messagebox.showinfo(
            "Éxito",
            "Cambios guardados en ambas tablas (periodos y planeación).",
        )

    def _restablecer(self):
        if messagebox.askyesno(
            "Restablecer",
            "¿Desea restablecer los valores del calendario a los guardados en la base de datos?\nSe perderán los cambios no guardados.",
        ):
            self._load_periodos()
            self.datos_planeacion = self._leer_planeacion_bd()
            if not self.datos_planeacion:
                self.datos_planeacion = [
                    list(row) for row in self.datos_planeacion_default
                ]
            self._cargar_planeacion()


import pandas as pd
from PIL import Image, ImageTk, ImageOps
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from tkinter import ttk
import os
import re

from ui_footer import crear_footer
import sqlite3
from pathlib import Path
import sys
from datetime import datetime, timedelta
import random
import json
from types import SimpleNamespace


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
from core import preguntas as core_preguntas
from core import examenes as core_examenes

from core import usuarios as core_usuarios


_MODULO_SUPERADMIN_CLASS = None
_RENDERIZAR_FORMULA_FN = None


def _cargar_recursos_superadmin():
    global _MODULO_SUPERADMIN_CLASS, _RENDERIZAR_FORMULA_FN
    if _MODULO_SUPERADMIN_CLASS is None or _RENDERIZAR_FORMULA_FN is None:
        from modulo_superadmin import ModuloSuperAdmin, renderizar_formula

        _MODULO_SUPERADMIN_CLASS = ModuloSuperAdmin
        _RENDERIZAR_FORMULA_FN = renderizar_formula
    return _MODULO_SUPERADMIN_CLASS, _RENDERIZAR_FORMULA_FN


def _obtener_modulo_superadmin():
    clase, _ = _cargar_recursos_superadmin()
    return clase


def renderizar_formula(*args, **kwargs):
    _, fn = _cargar_recursos_superadmin()
    return fn(*args, **kwargs)


_WRITE_MULTI_AREA_EXAM_PDF = None
_OBTENER_PREGUNTAS_MULTI_AREA = None
_MULTI_AREA_CARGADO = False


def _cargar_recursos_multi_area():
    global _WRITE_MULTI_AREA_EXAM_PDF, _OBTENER_PREGUNTAS_MULTI_AREA, _MULTI_AREA_CARGADO
    if not _MULTI_AREA_CARGADO:
        _MULTI_AREA_CARGADO = True
        try:
            from multi_area_exam_pdf import (
                write_multi_area_exam_pdf as _write_multi_area_exam_pdf,
                obtener_preguntas_multi_area_por_id_evaluacion as _obtener_preguntas_multi_area_por_id_evaluacion,
            )
        except ImportError:
            _WRITE_MULTI_AREA_EXAM_PDF = None
            _OBTENER_PREGUNTAS_MULTI_AREA = None
        else:
            _WRITE_MULTI_AREA_EXAM_PDF = _write_multi_area_exam_pdf
            _OBTENER_PREGUNTAS_MULTI_AREA = (
                _obtener_preguntas_multi_area_por_id_evaluacion
            )
    return _WRITE_MULTI_AREA_EXAM_PDF, _OBTENER_PREGUNTAS_MULTI_AREA


# --- Integración de cuadernillo multi-área tipo ICFES ---
# Los recursos se cargan bajo demanda para no ralentizar el arranque.


def write_multi_area_exam_pdf(*args, **kwargs):
    writer, _ = _cargar_recursos_multi_area()
    if writer is None:
        raise ImportError(
            "No se pudo importar multi_area_exam_pdf.write_multi_area_exam_pdf"
        )
    return writer(*args, **kwargs)


def obtener_preguntas_multi_area_por_id_evaluacion(*args, **kwargs):
    _, getter = _cargar_recursos_multi_area()
    if getter is None:
        raise ImportError(
            "No se pudo importar multi_area_exam_pdf.obtener_preguntas_multi_area_por_id_evaluacion"
        )
    return getter(*args, **kwargs)


# Ejemplo de uso (integración recomendada para generación de cuadernillo multi-área):
# if write_multi_area_exam_pdf:
#     try:
#         db_path = 'sistema.db'  # O la ruta correspondiente
#         evaluacion = 'Simulacro ICFES'
#         grado = '11'
#         periodo = '2024-1'
#         areas = ['Matemáticas', 'Lenguaje']
#         preguntas_por_area = {'Matemáticas': 20, 'Lenguaje': 20}
#         areas_preguntas_dict = obtener_preguntas_multi_area_por_id_evaluacion(
#             db_path, evaluacion, grado, periodo, areas, preguntas_por_area
#         )
#         write_multi_area_exam_pdf(
#             areas_preguntas_dict=areas_preguntas_dict,
#             estudiante={'nombre': 'Juan Pérez', 'grado': grado, 'curso': 'A'},
#             path='salida.pdf',
#             evaluacion=evaluacion,
#             version='A',
#             config_numeracion='continua',
#             preguntas_por_area=preguntas_por_area,
#             instrucciones_generales=None
#         )
#     except ValueError as e:
#         print(f"Error al generar cuadernillo: {e}")
#         config_numeracion='continua',
#         preguntas_por_area={'Matemáticas': 10, 'Lenguaje': 10},
#         instrucciones_generales='Lee atentamente y responde todas las preguntas.'
#     )
#
# Esto permite generar el cuadernillo multi-área desde cualquier parte del sistema.

# alias antiguo para compatibilidad
## Alias para compatibilidad (mantener solo por si hay referencias antiguas)
cargar_evaluaciones = cargar_evaluaciones_por_grado_y_area


def _runtime_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def obtener_ruta_icono():
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
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


def _mostrar_error_arranque(titulo, mensaje):
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(titulo, mensaje, parent=root)
        root.destroy()
    except Exception:
        print(f"{titulo}: {mensaje}")


def _obtener_config_plantel(clave, default=""):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS configuracion_plantel (clave TEXT PRIMARY KEY, valor TEXT)"
            )
            cur.execute(
                "SELECT valor FROM configuracion_plantel WHERE clave=?",
                (str(clave or "").strip(),),
            )
            row = cur.fetchone()
            valor = str(row[0] or "").strip() if row else ""
            return valor or default
    except Exception:
        return default


def _ensure_contenido_institucional_login():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute(
                """CREATE TABLE IF NOT EXISTS contenido_institucional (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       titulo TEXT,
                       mensaje TEXT NOT NULL,
                       ruta_imagen TEXT,
                       estado TEXT NOT NULL DEFAULT 'Activo',
                       orden INTEGER NOT NULL DEFAULT 1,
                       fecha_creacion TEXT NOT NULL
                   )"""
            )
            conn.commit()
    except Exception:
        pass


def _resolver_ruta_login_recurso(ruta_ref):
    txt = str(ruta_ref or "").strip()
    if not txt:
        return ""
    if os.path.isabs(txt):
        return txt
    return str((BASE_DIR / txt).resolve())


def _listar_contenido_institucional_activo_login():
    _ensure_contenido_institucional_login()
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, titulo, mensaje, ruta_imagen, estado, orden "
                "FROM contenido_institucional "
                "WHERE LOWER(COALESCE(estado, 'Activo'))=? "
                "ORDER BY COALESCE(orden, 0) ASC, id ASC",
                ("activo",),
            )
            items = []
            for row in cur.fetchall():
                items.append(
                    {
                        "id": row[0],
                        "titulo": str(row[1] or "").strip(),
                        "mensaje": str(row[2] or "").strip(),
                        "ruta_imagen": str(row[3] or "").strip(),
                        "ruta_imagen_abs": _resolver_ruta_login_recurso(row[3] or ""),
                        "estado": str(row[4] or "Activo").strip(),
                        "orden": row[5] if row[5] is not None else 0,
                    }
                )
            return items
    except Exception:
        return []


def _formatear_nombre_institucion_login(nombre):
    texto = " ".join(str(nombre or "").strip().split())
    if not texto:
        return ""

    palabras = texto.split()
    if len(palabras) <= 3:
        return texto

    total = len(texto)
    mejor_indice = 1
    mejor_diferencia = total
    acumulado = 0
    for indice, palabra in enumerate(palabras[:-1], start=1):
        acumulado += len(palabra) + (1 if indice > 1 else 0)
        diferencia = abs((total / 2.0) - acumulado)
        if diferencia < mejor_diferencia:
            mejor_diferencia = diferencia
            mejor_indice = indice

    linea_1 = " ".join(palabras[:mejor_indice]).strip()
    linea_2 = " ".join(palabras[mejor_indice:]).strip()
    if not linea_1 or not linea_2:
        return texto
    return f"{linea_1}\n{linea_2}"


def _validar_entorno_red_local():
    config = _leer_config_sistema(CONFIG_SISTEMA_FILE)
    mod12o = str(config.get("modo", "local")).strip().lower()
    ruta_servidor = str(config.get("ruta_servidor", "")).strip().strip('"').strip("'")

    if mod12o != "red":
        return True

    if not ruta_servidor:
        _mostrar_error_arranque(
            "Configuracion de red incompleta",
            "El archivo config_sistema esta en modo red pero no tiene ruta_servidor.\n"
            "Configura una ruta UNC valida, por ejemplo:\n"
            "\\\\SERVIDOR\\SistemaEvaluacion\\DatosCompartidos",
        )
        return False

    if not BASE_DIR.exists():
        _mostrar_error_arranque(
            "Servidor no disponible",
            "No se puede acceder a la carpeta compartida configurada.\n"
            f"Ruta: {BASE_DIR}\n\n"
            "Verifica red local, permisos SMB y nombre del servidor.",
        )
        return False

    if not DB_FILE.exists():
        _mostrar_error_arranque(
            "Base de datos no encontrada",
            "No se encontro sistema.db en la ruta compartida.\n"
            f"Ruta esperada: {DB_FILE}\n\n"
            "Ejecuta preparar_servidor_red_local.ps1 en el servidor y valida la carpeta DatosCompartidos.",
        )
        return False

    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("SELECT 1")
    except Exception as e:
        _mostrar_error_arranque(
            "Sin acceso a base de datos de red",
            "La aplicacion no pudo abrir sistema.db en la red local.\n"
            f"Ruta: {DB_FILE}\n"
            f"Detalle: {e}",
        )
        return False

    return True


def _tiene_valor(valor):
    if valor is None:
        return False
    if isinstance(valor, float) and valor != valor:
        return False
    texto = str(valor).strip()
    return texto != "" and texto.lower() not in {"nan", "none"}


# las funciones relacionadas con el historial, estado e intentos de examen se delegan a Admin
# se importan arriba y por claridad aquí se puede reafirmar la asignación (aunque no es estrictamente necesario)
ya_presento = core_examenes.ya_presento
obtener_estado_area = core_examenes.obtener_estado_area
obtener_intento_area = core_examenes.obtener_intento_area
autorizar_revision = core_examenes.autorizar_revision
puede_revisar = core_examenes.puede_revisar
obtener_respuestas_estudiante = core_examenes.obtener_respuestas_estudiante

# las funciones de validación y carga se importan desde Admin y no se definen aquí


## ================= FILTROS DOCENTE =================
# Corrección de filtros: Grado → carga cursos, Área → carga evaluaciones
def cargar_cursos_por_grado(grado):
    return core_usuarios.cargar_cursos_disponibles(grado)


def cargar_evaluaciones_por_grado_y_area(grado, area):
    return core_preguntas.cargar_evaluaciones_por_grado_y_area(grado, area)


# NOTA: No modificar ni eliminar funciones de reporte ni resultados.


# configuración de examen administrada por Admin.py; ver Admin.guardar_config_examen


# ================= VISTA HISTORIAL (Componente Reutilizable) =================
# implementación importada desde Admin.py

# ================= MÓDULO DOCENTE =================
# implementación importada desde Admin.py

# ================= MÓDULO ESTUDIANTE =================


def _limpiar_valor_pregunta(valor, defecto=""):
    """
    Limpia valores NaN de pandas y retorna string seguro.

    Previene que "nan", "None", etc. aparezcan en la interfaz.

    Args:
        valor: Valor que puede ser NaN, None, o válido
        defecto: Valor por defecto si es inválido (default "")

    Returns:
        string: Valor limpio o defecto
    """
    try:
        # Intentar con pandas.isna()
        import pandas as pd

        if pd.isna(valor):
            return defecto
    except (ImportError, AttributeError):
        pass

    # Fallback: comparar string
    str_valor = str(valor).strip() if valor is not None else ""
    if str_valor.lower() in ("nan", "none", "<na>", ""):
        return defecto

    return str_valor


from core.construir_nombre import construir_nombre


class ModuloEstudiante:

    def __init__(
        self,
        ventana,
        documento,
        apellido1,
        apellido2,
        nombre1,
        nombre2,
        grado,
        curso,
        cerrar_sesion_cb=None,
        tipo_documento=None,
    ):
        self.ventana = ventana
        self.documento = documento
        self.tipo_documento = str(tipo_documento or "").strip()
        self.apellido1 = apellido1
        self.apellido2 = apellido2
        self.nombre1 = nombre1
        self.nombre2 = nombre2
        self.nombre = construir_nombre(self)
        self.grado = grado
        self.curso = curso
        self.current_intento_id = None
        self.cerrar_sesion_cb = cerrar_sesion_cb
        self._math_image_cache = {}
        self._ui_est_bg = "#eef4fb"
        self._ui_panel_bg = "#ffffff"
        self._ui_primary = "#0f5db8"
        self._ui_primary_dark = "#0b4a92"
        self._ui_text = "#16324f"
        self._ui_muted = "#5f7287"
        self._ui_border = "#d6e2f0"
        self._ui_status = {
            "DISPONIBLE": {
                "accent": "#16a34a",
                "soft": "#dcfce7",
                "label": "Disponible",
                "description": "Lista para presentar",
                "action": "Presentar evaluación",
            },
            "EN_PROCESO": {
                "accent": "#d97706",
                "soft": "#fef3c7",
                "label": "En proceso",
                "description": "Tienes un intento iniciado y puedes continuarlo",
                "action": "Continuar examen",
            },
            "REVISION_ACTIVA": {
                "accent": "#0f5db8",
                "soft": "#dbeafe",
                "label": "Revisión habilitada",
                "description": "Puedes revisar tus respuestas",
                "action": "Ver revisión",
            },
            "PRESENTADO": {
                "accent": "#64748b",
                "soft": "#e2e8f0",
                "label": "Presentado sin revisión",
                "description": "Pendiente de autorización del docente",
                "action": "Ver estado",
            },
            "CERRADO": {
                "accent": "#991b1b",
                "soft": "#fee2e2",
                "label": "Cerrado",
                "description": "La evaluación no está publicada para presentación en este momento",
                "action": "Examen cerrado",
            },
        }
        self.metric_disponibles_var = tk.StringVar(value="0")
        self.metric_revision_var = tk.StringVar(value="0")
        self.metric_promedio_var = tk.StringVar(value="0.0")

        self.ventana.title("Panel del Estudiante")
        self.ventana.configure(bg=self._ui_est_bg)

        self.main_shell = tk.Frame(self.ventana, bg=self._ui_est_bg)
        self.main_shell.pack(fill="both", expand=True)

        header = tk.Frame(self.main_shell, bg=self._ui_primary, height=138)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_top = tk.Frame(header, bg=self._ui_primary)
        header_top.pack(fill="x", padx=24, pady=(18, 6))

        if cerrar_sesion_cb:
            tk.Button(
                header_top,
                text="🚪 Cerrar sesión",
                font=("Segoe UI", 9, "bold"),
                bg="#d9480f",
                fg="white",
                relief="flat",
                cursor="hand2",
                padx=10,
                pady=5,
                command=cerrar_sesion_cb,
            ).pack(side="right")

        identidad = tk.Frame(header_top, bg=self._ui_primary)
        identidad.pack(side="left", fill="x", expand=True)
        documento_label = str(self.documento or "").strip()
        tipo_label = self.tipo_documento or "Documento"
        identidad_texto = f"👤 {self.nombre}"
        if documento_label:
            identidad_texto = f"{identidad_texto}  •  {tipo_label}: {documento_label}"
        tk.Label(
            identidad,
            text=identidad_texto,
            font=("Segoe UI", 17, "bold"),
            bg=self._ui_primary,
            fg="white",
        ).pack(anchor="w")

        tk.Label(
            identidad,
            text=f"Grado {grado}  Curso {curso}  • Mis Exámenes",
            font=("Segoe UI", 10),
            bg=self._ui_primary,
            fg="#e0e0ff",
        ).pack(anchor="w", pady=(4, 0))

        # Barra de acciones (historial)
        acciones_frame = tk.Frame(
            self.main_shell,
            bg=self._ui_panel_bg,
            highlightthickness=1,
            highlightbackground=self._ui_border,
            padx=14,
            pady=10,
        )
        acciones_frame.pack(fill="x", padx=16, pady=(12, 8))

        tk.Button(
            acciones_frame,
            text="📋 Ver Historial de Calificaciones",
            font=("Segoe UI", 10, "bold"),
            bg=self._ui_primary,
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
            command=self._mostrar_historial,
        ).pack(side="left")

        tk.Button(
            acciones_frame,
            text="📝 Autoevaluación",
            font=("Segoe UI", 10, "bold"),
            bg="#00b894",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
            command=self._abrir_autoevaluacion,
        ).pack(side="left", padx=(8, 0))

        self.contenido = tk.Frame(self.main_shell, bg=self._ui_est_bg)
        self.contenido.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        # Detectar si hay examen en proceso
        self._detectar_examen_en_proceso()

        self._mostrar_areas()
        crear_footer(self.ventana)

    def _abrir_autoevaluacion(self):
        try:
            from autoevaluacion_estudiante_ui import VentanaAutoevaluacionEstudiante
        except ImportError:
            messagebox.showerror(
                "Autoevaluación",
                "No se encontró el módulo de autoevaluación para estudiantes.",
            )
            return

        VentanaAutoevaluacionEstudiante(
            self.ventana,
            estudiante_documento=self.documento,
            estudiante_nombre=self.nombre,
            grado=self.grado,
            curso=self.curso,
            db_path=str(DB_FILE),
        )

    # ---------------------------------------------------

    def _detectar_expresion_matematica_visual(self, texto):
        txt = _limpiar_valor_pregunta(texto).strip()
        if not txt:
            return False

        if re.search(r"\$[^$]+\$", txt):
            return True

        patrones = (
            r"\\sqrt|sqrt|√|\\frac",
            r"[a-zA-Z]\s*\^\s*-?\d+",
            r"\b\d+\s*/\s*\d+\b",
            r"[a-zA-Z0-9]\s*[+\-*/]\s*[a-zA-Z0-9]",
            r"[×÷]",
        )
        return any(re.search(pat, txt, flags=re.IGNORECASE) for pat in patrones)

    def _extraer_formula_para_visual(self, texto):
        txt = _limpiar_valor_pregunta(texto).strip()
        if not txt:
            return "", None

        m = re.search(r"\$([^$]+)\$", txt)
        if m:
            expr = str(m.group(1) or "").strip()
            resto = (txt[: m.start()] + " " + txt[m.end() :]).strip()
            resto = re.sub(r"\s+", " ", resto)
            return resto, expr if expr else None

        if not self._detectar_expresion_matematica_visual(txt):
            return txt, None

        # Solo renderizamos texto completo como fórmula cuando luce realmente
        # como expresión y no como oración larga para evitar falsos positivos.
        if len(txt) <= 80 and re.fullmatch(r"[0-9a-zA-Z\s\^+\-*/=().,:;×÷√\\]+", txt):
            expr = txt.replace("×", "*").replace("÷", "/")
            return "", expr

        return txt, None

    def _obtener_formula_img_tk(self, expr, max_width=760):
        clave = (str(expr or "").strip(), int(max_width or 760))
        if not clave[0]:
            return None

        if clave in self._math_image_cache:
            return self._math_image_cache.get(clave)

        try:
            rendered = renderizar_formula(clave[0], dpi=220)
            if rendered is None:
                return None

            buf, _dpi_math = rendered
            if hasattr(buf, "seek"):
                buf.seek(0)
            img = Image.open(buf).convert("RGBA")
            if img.width > clave[1]:
                escala = clave[1] / float(img.width)
                img = img.resize(
                    (int(img.width * escala), int(img.height * escala)),
                    Image.LANCZOS,
                )
            img_tk = ImageTk.PhotoImage(img)

            if len(self._math_image_cache) > 300:
                self._math_image_cache.clear()
            self._math_image_cache[clave] = img_tk
            return img_tk
        except Exception:
            return None

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

    def _obtener_publicacion_examen_area(self, area):
        try:
            curso = str(self.curso).strip() if self.curso is not None else ""
            if not curso:
                curso = "TODOS"

            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COALESCE(habilitado, 0), COALESCE(evaluacion, '')
                    FROM config_examenes
                    WHERE LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
                      AND LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT)))
                      AND (
                            UPPER(TRIM(CAST(curso AS TEXT))) = UPPER(TRIM(CAST(? AS TEXT)))
                            OR UPPER(TRIM(CAST(curso AS TEXT))) = 'TODOS'
                          )
                    ORDER BY (UPPER(TRIM(CAST(curso AS TEXT))) = 'TODOS') ASC, id DESC
                    LIMIT 1
                    """,
                    (str(self.grado), str(area), curso),
                )
                row = cursor.fetchone()
        except Exception:
            row = None

        if not row:
            return {"configurada": False, "habilitado": False, "evaluacion": None}

        evaluacion = str(row[1] or "").strip() or None
        return {
            "configurada": True,
            "habilitado": bool(row[0]),
            "evaluacion": evaluacion,
        }

    def _resolver_estado_estudiante_area(self, area):
        estado_info = obtener_estado_area(self.documento, area)
        nota = estado_info[1] if estado_info and len(estado_info) > 1 else None

        if estado_info:
            estado_base = str(estado_info[0] or "").strip().upper()
            if estado_base == "REVISION_ACTIVA":
                return "REVISION_ACTIVA", nota, estado_info
            if estado_base in {"FINALIZADO", "PRESENTADO"}:
                return "PRESENTADO", nota, estado_info
            if estado_base == "EN_PROCESO":
                return "EN_PROCESO", nota, estado_info

        publicacion = self._obtener_publicacion_examen_area(area)
        if publicacion.get("habilitado"):
            return "DISPONIBLE", nota, estado_info
        return "CERRADO", nota, estado_info

    def _estado_area_ui(self, area):
        estado, nota, estado_info = self._resolver_estado_estudiante_area(area)
        meta = self._ui_status[estado]
        return {
            "area": area,
            "estado": estado,
            "nota": nota,
            "estado_info": estado_info,
            "accent": meta["accent"],
            "soft": meta["soft"],
            "label": meta["label"],
            "description": meta["description"],
            "action": meta["action"],
        }

    def _actualizar_metricas_estudiante(self, estados):
        disponibles = sum(1 for item in estados if item["estado"] == "DISPONIBLE")
        revision = sum(1 for item in estados if item["estado"] == "REVISION_ACTIVA")
        notas = []
        for item in estados:
            try:
                if item["nota"] is not None:
                    notas.append(float(item["nota"]))
            except Exception:
                pass
        promedio = round(sum(notas) / len(notas), 1) if notas else 0.0

        self.metric_disponibles_var.set(str(disponibles))
        self.metric_revision_var.set(str(revision))
        self.metric_promedio_var.set(f"{promedio:.1f}")

    def _obtener_color_promedio(self, promedio, tiene_promedio):
        if not tiene_promedio:
            return {
                "bg": "#334155",
                "border": "#475569",
                "title_fg": "#cbd5e1",
                "value_fg": "#ffffff",
                "accent": "#64748b",
            }
        if promedio < 3.0:
            return {
                "bg": "#991b1b",
                "border": "#dc2626",
                "title_fg": "#fecaca",
                "value_fg": "#ffffff",
                "accent": "#dc2626",
            }
        if promedio < 4.0:
            return {
                "bg": "#9a3412",
                "border": "#ea580c",
                "title_fg": "#fed7aa",
                "value_fg": "#ffffff",
                "accent": "#ea580c",
            }
        return {
            "bg": "#166534",
            "border": "#16a34a",
            "title_fg": "#dcfce7",
            "value_fg": "#ffffff",
            "accent": "#16a34a",
        }

    # ---------------------------------------------------

    def _mostrar_areas(self):
        for w in self.contenido.winfo_children():
            w.destroy()

        # Mostrar solo áreas disponibles para el grado del estudiante
        areas = cargar_areas_por_grado(self.grado)
        estados = [self._estado_area_ui(area) for area in areas]
        self._actualizar_metricas_estudiante(estados)

        def on_area_click(a):
            estado, nota, _estado_info = self._resolver_estado_estudiante_area(a)
            if estado in {"DISPONIBLE", "EN_PROCESO"}:
                self._iniciar_examen(a)
            elif estado == "PRESENTADO":
                messagebox.showinfo(
                    "Área presentada",
                    f"Ya presentaste esta área.\nNota: {nota}\nEl docente no ha autorizado la revisión.",
                )
            elif estado == "REVISION_ACTIVA":
                self._ver_resultado(a)
            elif estado == "CERRADO":
                messagebox.showinfo(
                    "Examen cerrado",
                    f"La evaluación de {a} no está publicada para presentación en este momento.",
                )

        shell = tk.Frame(self.contenido, bg=self._ui_est_bg)
        shell.pack(fill="both", expand=True)

        panel_resumen = tk.Frame(
            shell,
            bg=self._ui_panel_bg,
            highlightthickness=1,
            highlightbackground=self._ui_border,
            padx=20,
            pady=10,
        )
        panel_resumen.pack(fill="x", pady=(0, 6))

        cabecera_resumen = tk.Frame(panel_resumen, bg=self._ui_panel_bg)
        cabecera_resumen.pack(fill="x")

        tk.Label(
            cabecera_resumen,
            text="Tus evaluaciones",
            font=("Segoe UI", 15, "bold"),
            bg=self._ui_panel_bg,
            fg=self._ui_text,
        ).pack(side="left", anchor="w")
        tk.Label(
            cabecera_resumen,
            text=f"{len(estados)} áreas asociadas a tu curso",
            font=("Segoe UI", 9, "bold"),
            bg=self._ui_panel_bg,
            fg=self._ui_muted,
        ).pack(side="right", anchor="e")

        tk.Label(
            panel_resumen,
            text="Selecciona un área para presentar una evaluación o revisar resultados autorizados.",
            font=("Segoe UI", 9),
            bg=self._ui_panel_bg,
            fg=self._ui_muted,
            wraplength=980,
            justify="left",
        ).pack(anchor="w", pady=(3, 6))

        resumen_filas = tk.Frame(panel_resumen, bg=self._ui_panel_bg)
        resumen_filas.pack(fill="x")
        resumen_data = [
            (
                "Disponibles para presentar",
                self.metric_disponibles_var.get(),
                "#16a34a",
            ),
            ("Con revisión habilitada", self.metric_revision_var.get(), "#0f5db8"),
            (
                "Promedio acumulado",
                self.metric_promedio_var.get(),
                self._obtener_color_promedio(
                    float(self.metric_promedio_var.get() or 0),
                    self.metric_promedio_var.get() not in {"0", "0.0", ""},
                )["accent"],
            ),
        ]
        for titulo, valor, color in resumen_data:
            caja = tk.Frame(
                resumen_filas,
                bg="#f8fbff",
                padx=12,
                pady=6,
                highlightthickness=1,
                highlightbackground="#e7eef7",
            )
            caja.pack(side="left", fill="x", expand=True, padx=(0, 8))
            fila_kpi = tk.Frame(caja, bg="#f8fbff")
            fila_kpi.pack(fill="x")
            tk.Label(
                fila_kpi,
                text=titulo,
                font=("Segoe UI", 8, "bold"),
                bg="#f8fbff",
                fg=self._ui_muted,
            ).pack(side="left", anchor="w")
            tk.Label(
                fila_kpi,
                text=valor,
                font=("Segoe UI", 15, "bold"),
                bg="#f8fbff",
                fg=color,
            ).pack(side="right", anchor="e")

        panel_tarjetas = tk.Frame(
            shell,
            bg=self._ui_panel_bg,
            highlightthickness=1,
            highlightbackground=self._ui_border,
        )
        panel_tarjetas.pack(fill="both", expand=True)

        # Canvas con scroll para las áreas
        canvas = tk.Canvas(panel_tarjetas, bg=self._ui_panel_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            panel_tarjetas, orient="vertical", command=canvas.yview
        )
        frame_areas = tk.Frame(canvas, bg=self._ui_panel_bg)

        frame_areas.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        frame_areas.grid_columnconfigure(0, weight=1, uniform="areas")
        frame_areas.grid_columnconfigure(1, weight=1, uniform="areas")

        canvas.create_window((0, 0), window=frame_areas, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _ajustar_ancho_tarjetas(event):
            try:
                canvas.itemconfigure("all", width=event.width)
            except Exception:
                pass

        canvas.bind("<Configure>", _ajustar_ancho_tarjetas)

        # Permitir scroll con rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not estados:
            vacio = tk.Frame(frame_areas, bg=self._ui_panel_bg, padx=26, pady=30)
            vacio.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=16)
            tk.Label(
                vacio,
                text="No hay áreas configuradas para este grado.",
                font=("Segoe UI", 13, "bold"),
                bg=self._ui_panel_bg,
                fg=self._ui_text,
            ).pack(anchor="w")
            tk.Label(
                vacio,
                text="Cuando el área académica esté disponible, aparecerá aquí para presentar o revisar evaluaciones.",
                font=("Segoe UI", 10),
                bg=self._ui_panel_bg,
                fg=self._ui_muted,
                wraplength=900,
                justify="left",
            ).pack(anchor="w", pady=(8, 0))
            return

        for indice, item in enumerate(estados):
            fila = indice // 2
            columna = indice % 2

            card = tk.Frame(
                frame_areas,
                bg="#ffffff",
                highlightthickness=1,
                highlightbackground=self._ui_border,
                padx=18,
                pady=16,
            )
            card.grid(row=fila, column=columna, sticky="nsew", padx=16, pady=10)

            top = tk.Frame(card, bg="#ffffff")
            top.pack(fill="x")
            tk.Label(
                top,
                text=item["area"].upper(),
                font=("Segoe UI", 15, "bold"),
                bg="#ffffff",
                fg=self._ui_text,
            ).pack(side="left", anchor="w")
            tk.Label(
                top,
                text=item["label"],
                font=("Segoe UI", 9, "bold"),
                bg=item["soft"],
                fg=item["accent"],
                padx=12,
                pady=5,
            ).pack(side="right")

            tk.Label(
                card,
                text=item["description"],
                font=("Segoe UI", 10),
                bg="#ffffff",
                fg=self._ui_muted,
                justify="left",
                wraplength=420,
            ).pack(anchor="w", pady=(8, 8))

            meta = tk.Frame(card, bg="#ffffff")
            meta.pack(fill="x", pady=(0, 10))
            detalle_principal = "Pendiente"
            if item["nota"] is not None:
                detalle_principal = f"Nota registrada: {item['nota']}"
            tk.Label(
                meta,
                text=detalle_principal,
                font=("Segoe UI", 10, "bold"),
                bg="#ffffff",
                fg=item["accent"],
            ).pack(anchor="w")
            tk.Label(
                meta,
                text=f"Curso {self.curso} • Grado {self.grado}",
                font=("Segoe UI", 9),
                bg="#ffffff",
                fg=self._ui_muted,
            ).pack(anchor="w", pady=(4, 0))

            tk.Button(
                card,
                text=item["action"],
                font=("Segoe UI", 10, "bold"),
                bg=item["accent"],
                fg="white",
                relief="flat",
                padx=14,
                pady=8,
                cursor="hand2",
                command=lambda a=item["area"]: on_area_click(a),
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
        mostrar_detalle_respuestas_estudiante(
            self.contenido, area, intento, respuestas, base_dir=BASE_DIR
        )

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
                "WHERE LOWER(TRIM(CAST(grado AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT))) "
                "AND LOWER(TRIM(CAST(area AS TEXT))) = LOWER(TRIM(CAST(? AS TEXT))) "
                "AND (UPPER(TRIM(CAST(curso AS TEXT))) = UPPER(TRIM(CAST(? AS TEXT))) OR UPPER(TRIM(CAST(curso AS TEXT))) = 'TODOS') "
                "AND COALESCE(habilitado, 0) = 1 "
                "ORDER BY (UPPER(TRIM(CAST(curso AS TEXT))) = 'TODOS') ASC, id DESC LIMIT 1",
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
            evaluacion = str(evaluacion).strip()
            if evaluacion.lower() in ["nan", "none", ""]:
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
                if isinstance(estudiante, dict):
                    curso_val = estudiante.get("curso")
                    if _tiene_valor(curso_val):
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
            # Buscar id_evaluacion correspondiente usando los mismos filtros que la generación
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_evaluacion FROM banco_preguntas WHERE evaluacion = ? AND area = ? AND grado = ? AND periodo IS NOT NULL LIMIT 1",
                (evaluacion, area, self.grado),
            )
            row = cursor.fetchone()
            id_evaluacion = row[0] if row and row[0] else None
            df_eval = None
            if id_evaluacion:
                df_eval = pd.read_sql_query(
                    "SELECT * FROM banco_preguntas WHERE id_evaluacion = ?",
                    conn,
                    params=[id_evaluacion],
                )
            else:
                df_eval = pd.DataFrame()
            if df_eval is not None and not df_eval.empty:
                # Validar grado, área y evaluación (ya filtrado por id_evaluacion)
                pass  # Ya está filtrado correctamente
            else:
                # No hay preguntas para la evaluación seleccionada
                messagebox.showwarning(
                    "Sin preguntas",
                    f"No hay suficientes preguntas en la evaluación seleccionada.\n\nVerifica el banco de preguntas.",
                )
                conn.close()
                return
            conn.close()
        except Exception as ex:
            print(f"[ERROR] Validación de preguntas por evaluación/área: {ex}")
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
                if _tiene_valor(preg_id):
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
        nombre_label = self.nombre
        info_items = [
            ("Total de preguntas:", str(cantidad_preguntas)),
            ("Tiempo disponible:", f"{minutos} minutos"),
            ("Área de evaluación:", area.upper()),
            ("Documento:", self.documento),
            ("Nombre:", nombre_label),
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
                f"• Existan preguntas cargadas en el banco (SQLite)\n"
                f"• Haya preguntas del área '{area}' para el grado configurado\n"
                f"• La evaluación esté correctamente filtrada y habilitada",
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

        label_contexto_formula = tk.Label(frame_scroll, bg=COLOR_SECUNDARIO)
        label_contexto_formula.pack(pady=(0, 8), padx=30)

        label_enunciado = tk.Label(
            frame_scroll,
            text="",
            wraplength=900,
            justify="left",
            font=("Segoe UI", 13, "bold"),
            bg=COLOR_SECUNDARIO,
        )
        label_enunciado.pack(pady=10, padx=30)

        label_enunciado_formula = tk.Label(frame_scroll, bg=COLOR_SECUNDARIO)
        label_enunciado_formula.pack(pady=(0, 10), padx=30)

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

        def _aplicar_texto_y_formula(label_texto, label_formula, texto, max_width=760):
            texto_limpio, expr = self._extraer_formula_para_visual(texto)
            label_texto.config(
                text=texto_limpio if expr else _limpiar_valor_pregunta(texto)
            )

            if expr:
                img_formula = self._obtener_formula_img_tk(expr, max_width=max_width)
                if img_formula is not None:
                    label_formula.config(image=img_formula)
                    label_formula.image = img_formula
                    return

            label_formula.config(image="")
            label_formula.image = None

        def _aplicar_opcion_math(rb, letra, texto_opt):
            txt = _limpiar_valor_pregunta(texto_opt)
            txt_limpio, expr = self._extraer_formula_para_visual(txt)
            if expr:
                img_formula = self._obtener_formula_img_tk(expr, max_width=640)
                if img_formula is not None:
                    prefijo = f"{letra}."
                    if txt_limpio:
                        prefijo = f"{prefijo} {txt_limpio}"
                    rb.config(
                        text=prefijo,
                        image=img_formula,
                        compound="left",
                        wraplength=900,
                    )
                    rb.image = img_formula
                    return

            rb.config(text=f"{letra}. {txt}", image="", compound="none", wraplength=900)
            rb.image = None

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
                if _tiene_valor(imagen_ref):
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

            _aplicar_texto_y_formula(
                label_contexto,
                label_contexto_formula,
                _limpiar_valor_pregunta(preg.get("contexto", "")),
                max_width=820,
            )
            _aplicar_texto_y_formula(
                label_enunciado,
                label_enunciado_formula,
                _limpiar_valor_pregunta(preg.get("enunciado", "")),
                max_width=820,
            )

            _aplicar_opcion_math(
                radios["A"], "A", _limpiar_valor_pregunta(preg.get("opcion_a", ""))
            )
            _aplicar_opcion_math(
                radios["B"], "B", _limpiar_valor_pregunta(preg.get("opcion_b", ""))
            )
            _aplicar_opcion_math(
                radios["C"], "C", _limpiar_valor_pregunta(preg.get("opcion_c", ""))
            )
            _aplicar_opcion_math(
                radios["D"], "D", _limpiar_valor_pregunta(preg.get("opcion_d", ""))
            )

            # Restaurar respuesta si es reanudación y ya fue respondida
            var.set("")
            if es_reanudacion:
                try:
                    pregunta_id = (
                        int(preg.get("id")) if _tiene_valor(preg.get("id")) else None
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
            enunciado = _limpiar_valor_pregunta(preg.get("enunciado", ""))

            if es_corr:
                contador["correctas"] += 1

            try:
                pregunta_id = (
                    int(preg.get("id")) if _tiene_valor(preg.get("id")) else None
                )
            except Exception:
                pregunta_id = None

            respuestas.append(
                {
                    "pregunta_id": pregunta_id,
                    "enunciado": enunciado,
                    "imagen": (
                        str(preg.get("imagen", ""))
                        if _tiene_valor(preg.get("imagen", ""))
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
                print(
                    f"[INFO] No se pudo guardar la respuesta en BD: P{pregunta_id} = {seleccion}. Error: {e}"
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

        # Convertir respuestas_list al formato esperado por mostrar_detalle_respuestas_estudiante
        respuestas_list = []
        try:
            if isinstance(respuestas_raw, str):
                respuestas_list = json.loads(respuestas_raw)
            elif isinstance(respuestas_raw, list):
                respuestas_list = respuestas_raw
        except Exception:
            respuestas_list = []

        # Adaptar claves si es necesario
        respuestas_convertidas = []
        for r in respuestas_list:
            # Compatibilidad: usar claves estándar si existen, si no, mapear
            respuestas_convertidas.append(
                {
                    "enunciado": r.get("enunciado", ""),
                    "respuesta_seleccionada": r.get(
                        "respuesta_dada", r.get("respuesta_seleccionada", "")
                    ),
                    "respuesta_seleccionada_texto": r.get(
                        "respuesta_dada", r.get("respuesta_seleccionada_texto", "")
                    ),
                    "respuesta_correcta": r.get("respuesta_correcta", ""),
                    "respuesta_correcta_texto": r.get("respuesta_correcta", ""),
                    "es_correcta": int(r.get("correcta", r.get("es_correcta", False))),
                    "id_contexto": r.get("id_contexto", 0),
                    "contexto": r.get("contexto", ""),
                    "pregunta_id": r.get("pregunta_id", None),
                    "imagen": r.get("imagen", None),
                }
            )

        if not respuestas_convertidas:
            tk.Label(
                self.contenido,
                text="No hay detalles de respuestas para revisar.",
                bg="#ffffff",
            ).pack(pady=20)
            return

        mostrar_detalle_respuestas_estudiante(
            self.contenido, area, intento, respuestas_convertidas, base_dir=BASE_DIR
        )


# abrir_docente importado desde Admin.py


# ================= LOGIN =================


# ================= CERRAR SESIÓN =================
_volver_al_login = False


def cerrar_sesion(ventana_actual):
    """Cierra la ventana del módulo activo y marca que se debe volver al login."""
    global _volver_al_login
    _volver_al_login = True
    try:
        ventana_actual.destroy()
    except Exception:
        pass


def confirmar_cerrar_sesion(ventana_actual):
    """Muestra un cuadro de confirmación antes de cerrar la sesión."""
    respuesta = messagebox.askyesno(
        "Cerrar sesión",
        "¿Desea cerrar la sesión actual?",
    )
    if respuesta:
        cerrar_sesion(ventana_actual)


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
                    apellido1 TEXT,
                    apellido2 TEXT,
                    nombre1 TEXT,
                    nombre2 TEXT,
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
registrar_inicio = core_examenes.registrar_inicio
registrar_final = core_examenes.registrar_final
ya_presento = core_examenes.ya_presento
obtener_todas_respuestas_desde_bd = core_examenes.obtener_todas_respuestas_desde_bd
obtener_estado_area = core_examenes.obtener_estado_area
obtener_intento_area = core_examenes.obtener_intento_area
autorizar_revision = core_examenes.autorizar_revision
puede_revisar = core_examenes.puede_revisar
obtener_respuestas_estudiante = core_examenes.obtener_respuestas_estudiante
resetear_examen = core_examenes.resetear_examen
validar_estudiante = core_usuarios.validar_estudiante
validar_docente = core_usuarios.validar_docente
cargar_areas = core_preguntas.cargar_areas
cargar_areas_por_grado = core_preguntas.cargar_areas_por_grado
cargar_grados = core_usuarios.cargar_grados
cargar_evaluaciones = core_preguntas.cargar_evaluaciones_por_grado_y_area
cargar_preguntas = core_preguntas.cargar_preguntas
cargar_preguntas_filtradas = core_preguntas.cargar_preguntas_filtradas
exportar_reporte_por_filtros = Admin.exportar_reporte_por_filtros
exportar_consolidado_periodo = Admin.exportar_consolidado_periodo
exportar_reporte_completo = Admin.exportar_reporte_completo
# funciones de configuración también se delegan para mantener compatibilidad
cargar_config_examen = core_examenes.cargar_config_examen
guardar_config_examen = core_examenes.guardar_config_examen

## ================= INICIO =================

# Validacion previa para despliegue cliente-servidor en red local
if not _validar_entorno_red_local():
    sys.exit(1)

# Inicialización de la base de datos usando implementación actualizada
crear_base_datos()

# Configuración de colores modernos
COLOR_PRIMARIO = "#0066cc"
COLOR_SECUNDARIO = "#f5f7fa"
COLOR_TEXTO = "#1a1a1a"
COLOR_BORDE = "#e0e0e0"
COLOR_EXITO = "#51cf66"
COLOR_ADVERTENCIA = "#ff6b6b"


def abrir_login():
    """Construye y muestra la ventana de login. Llamada al arranque y al cerrar sesión."""
    global _volver_al_login
    _volver_al_login = False

    ventana = tk.Tk()
    ventana.title("Sistema de Evaluación Automatizada")
    ruta_icono = obtener_ruta_icono()
    if ruta_icono.exists():
        ventana.iconbitmap(str(ruta_icono))
    ventana.configure(bg=COLOR_SECUNDARIO)
    ventana.resizable(True, True)
    try:
        ventana.state("zoomed")
    except Exception:
        try:
            ventana.attributes("-zoomed", True)
        except Exception:
            pass

    ventana._login_images = []
    nombre_institucion_login = _obtener_config_plantel(
        "nombre_institucion",
        default="Institución Educativa Departamental Dagoberto Orozco Borja",
    )
    nombre_institucion_login = _formatear_nombre_institucion_login(
        nombre_institucion_login
    )

    def _cargar_imagen_login(ruta, size, cover=False):
        try:
            ruta_path = Path(ruta)
            if not ruta_path.exists():
                return None
            img = Image.open(ruta_path).convert("RGBA")
            if cover:
                img = ImageOps.fit(img, size, Image.LANCZOS)
            else:
                img.thumbnail(size, Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            ventana._login_images.append(img_tk)
            return img_tk
        except Exception:
            return None

    footer = crear_footer(ventana)

    fondo = tk.Frame(ventana, bg="#eef4fb")
    fondo.pack(fill="both", expand=True, padx=16, pady=(16, 8))

    contenedor = tk.Frame(fondo, bg="#eef4fb")
    contenedor.pack(fill="both", expand=True)
    contenedor.grid_columnconfigure(0, weight=11, uniform="login")
    contenedor.grid_columnconfigure(1, weight=14, uniform="login")
    contenedor.grid_rowconfigure(0, weight=1)

    panel_login = tk.Frame(
        contenedor,
        bg="#ffffff",
        bd=0,
        highlightthickness=1,
        highlightbackground="#c9d8ea",
    )
    panel_login.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

    panel_info = tk.Frame(
        contenedor,
        bg="#0d4f8b",
        bd=0,
        highlightthickness=1,
        highlightbackground="#0d4f8b",
    )
    panel_info.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

    login_wrap = tk.Frame(panel_login, bg="#ffffff")
    login_wrap.pack(fill="both", expand=True, padx=44, pady=20)

    login_header = tk.Frame(login_wrap, bg="#ffffff")
    login_header.pack(fill="x", pady=(0, 14))

    ruta_logo_sistema = BASE_DIR / "ICONO SEA.jpeg"
    logo_sistema_img = _cargar_imagen_login(ruta_logo_sistema, (240, 240))
    if logo_sistema_img is not None:
        tk.Label(login_header, image=logo_sistema_img, bg="#ffffff").pack(
            anchor="center", pady=(0, 4)
        )
    else:
        tk.Label(
            login_header,
            text="SEA",
            font=("Segoe UI", 28, "bold"),
            bg="#ffffff",
            fg="#0d4f8b",
        ).pack(anchor="center", pady=(0, 4))

    tk.Label(
        login_header,
        text="Sistema de Evaluación Automatizada",
        font=("Segoe UI", 21, "bold"),
        bg="#ffffff",
        fg="#0d4f8b",
        justify="center",
    ).pack(anchor="center")

    tk.Frame(login_wrap, bg="#e2e8f0", height=1).pack(fill="x", pady=(10, 14))

    form_card = tk.Frame(
        login_wrap,
        bg="#f8fbff",
        highlightthickness=1,
        highlightbackground="#d7e4f1",
        padx=26,
        pady=18,
    )
    form_card.pack(fill="x")

    tk.Label(
        form_card,
        text="Acceso institucional con documento",
        font=("Segoe UI", 11, "bold"),
        bg="#f8fbff",
        fg="#1e293b",
    ).pack(anchor="w", pady=(0, 8))

    campo_documento = tk.Frame(
        form_card,
        bg="#ffffff",
        highlightthickness=1,
        highlightbackground="#bfd3ea",
        padx=14,
        pady=10,
    )
    campo_documento.pack(fill="x")

    tk.Label(
        campo_documento,
        text="ID",
        font=("Segoe UI", 10, "bold"),
        bg="#ffffff",
        fg="#0d4f8b",
        width=3,
    ).pack(side="left", padx=(0, 12))

    entry_documento = tk.Entry(
        campo_documento,
        font=("Segoe UI", 14),
        relief="flat",
        bd=0,
        bg="#ffffff",
        fg="#0f172a",
        insertbackground="#0f172a",
    )
    entry_documento.pack(side="left", fill="x", expand=True, ipady=5)
    entry_documento.focus_set()

    # Campo clave (se muestra solo para personal, no para estudiantes)

    campo_clave = tk.Frame(
        form_card,
        bg="#ffffff",
        highlightthickness=1,
        highlightbackground="#bfd3ea",
        padx=14,
        pady=10,
    )
    # Por defecto oculto
    campo_clave.pack_forget()

    label_clave = tk.Label(
        campo_clave,
        text="Clave",
        font=("Segoe UI", 10, "bold"),
        bg="#ffffff",
        fg="#0d4f8b",
        width=7,
        anchor="w",
    )
    label_clave.pack(side="left", padx=(0, 12), fill="y")

    entry_clave = tk.Entry(
        campo_clave,
        font=("Segoe UI", 14),
        relief="flat",
        bd=0,
        bg="#ffffff",
        fg="#0f172a",
        insertbackground="#0f172a",
        show="*",
    )
    entry_clave.pack(side="left", fill="x", expand=True, ipady=5)

    # Botón de ojo para mostrar/ocultar clave
    mostrar_clave = [False]  # mutable para usar en closure

    def toggle_clave():
        mostrar_clave[0] = not mostrar_clave[0]
        entry_clave.config(show="" if mostrar_clave[0] else "*")
        btn_ojo.config(text="👁️" if not mostrar_clave[0] else "🙈")

    btn_ojo = tk.Button(
        campo_clave,
        text="👁️",
        font=("Segoe UI", 11),
        bg="#ffffff",
        fg="#0d4f8b",
        relief="flat",
        bd=0,
        command=toggle_clave,
        cursor="hand2",
        activebackground="#e0e7ef",
        activeforeground="#0d4f8b",
        padx=4,
        pady=0,
    )
    btn_ojo.pack(side="right", padx=(8, 0))

    # Mejorar separación visual con pady
    def mostrar_campo_clave():
        campo_clave.pack(fill="x", pady=(8, 0))

    def ocultar_campo_clave():
        campo_clave.pack_forget()

    # Función para mostrar/ocultar campo clave según el tipo de usuario
    def actualizar_visibilidad_clave(event=None):
        doc = entry_documento.get().strip()
        # Si es admin, rector, secretaria, coordinador, orientador, tutor, docente → pide clave
        # Si es estudiante → NO pide clave
        # Se detecta por el cargo en la BD o por el documento "admin"
        mostrar = False
        if doc.lower() == "admin":
            mostrar = True
        else:
            try:
                import sqlite3

                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT cargo FROM docentes WHERE documento=?", (doc,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    cargo = str(row[0] or "").strip().lower()
                    # Cargos que requieren clave
                    cargos_clave = [
                        "docente",
                        "rector",
                        "rectora",
                        "secretaria",
                        "coordinador",
                        "coordinadora",
                        "orientador",
                        "orientador escolar",
                        "tutor",
                        "docente tutor pta",
                        "orientador escolar tutor pta",
                        "administrador web",
                    ]
                    for c in cargos_clave:
                        if c in cargo:
                            mostrar = True
                            break
            except Exception:
                pass
        if mostrar:
            mostrar_campo_clave()
        else:
            ocultar_campo_clave()
        entry_clave.delete(0, "end")

    entry_documento.bind("<KeyRelease>", actualizar_visibilidad_clave)
    entry_documento.bind("<FocusOut>", actualizar_visibilidad_clave)

    # Inicializar visibilidad
    actualizar_visibilidad_clave()

    def ingresar():
        # Siempre ocultar la clave al intentar ingresar
        mostrar_clave[0] = False
        entry_clave.config(show="*")
        btn_ojo.config(text="👁️")
        documento = entry_documento.get()

        if documento == "":
            messagebox.showwarning("Advertencia", "Debe ingresar el documento.")
            return

        # Tomar clave solo si el campo está visible
        clave = entry_clave.get() if campo_clave.winfo_ismapped() else None
        if campo_clave.winfo_ismapped() and (clave is None or clave == ""):
            messagebox.showwarning("Advertencia", "Debe ingresar la clave.")
            return

        identidad, error = core_usuarios.resolver_identidad_acceso(
            documento,
            clave_maestra=clave,
        )
        if error:
            mensajes = {
                "documento_requerido": "Debe ingresar el documento.",
                "clave_maestra_requerida": "Debe ingresar la clave.",
                "clave_personal_requerida": "Debe ingresar la clave.",
                "clave_maestra_invalida": "Clave incorrecta.",
                "clave_personal_invalida": "Clave incorrecta.",
                "documento_no_encontrado": "Documento no encontrado.",
            }
            titulo = "Acceso denegado"
            messagebox.showerror(
                titulo, mensajes.get(error, "No fue posible validar el acceso.")
            )
            return

        usuario_actual = SimpleNamespace(
            **core_usuarios.enriquecer_usuario_rbac(identidad)
        )

        rol_canonico = (
            str(getattr(usuario_actual, "rol_canonico", "") or "").strip().lower()
        )
        es_superadmin = rol_canonico == core_usuarios.ROL_SUPERADMIN
        es_directivo = rol_canonico in {
            core_usuarios.ROL_RECTOR,
            core_usuarios.ROL_SECRETARIA,
            core_usuarios.ROL_COORDINADOR,
        }

        # FORZAR: rector, secretaria y coordinador siempre entran a SuperAdmin
        if es_superadmin or es_directivo:
            ventana.destroy()
            admin_root = tk.Tk()
            admin_root.withdraw()
            ModuloSuperAdmin = _obtener_modulo_superadmin()

            msa = ModuloSuperAdmin(
                admin_root,
                db_path=str(DB_FILE),
                base_dir=str(BASE_DIR),
                usuario_actual=usuario_actual,
            )
            msa.open_interface(
                cerrar_sesion_cb=lambda: confirmar_cerrar_sesion(admin_root)
            )
            try:
                msa.win.state("zoomed")
            except Exception:
                try:
                    msa.win.attributes("-fullscreen", True)
                except Exception:
                    pass
            msa.win.protocol("WM_DELETE_WINDOW", admin_root.destroy)
            admin_root.mainloop()
            if _volver_al_login:
                abrir_login()
            return

        # Docente
        if core_usuarios.tiene_permiso(
            usuario_actual,
            "desktop.session.open.docente",
        ):
            ventana.destroy()
            ventana_doc = tk.Tk()
            try:
                ventana_doc.state("zoomed")
            except Exception:
                try:
                    ventana_doc.attributes("-fullscreen", True)
                except Exception:
                    pass
            Admin.ModuloDocente(
                ventana_doc,
                usuario_actual.nombre or "Docente",
                docente_documento=usuario_actual.documento or documento,
                cerrar_sesion_cb=lambda: confirmar_cerrar_sesion(ventana_doc),
                usuario_actual=usuario_actual,
            )
            ventana_doc.mainloop()
            if _volver_al_login:
                abrir_login()
            return

        # Estudiante
        if not core_usuarios.tiene_permiso(
            usuario_actual,
            "desktop.session.open.estudiante",
        ):
            messagebox.showerror(
                "Acceso denegado",
                "El usuario autenticado no tiene permisos para abrir una sesión en escritorio.",
            )
            return

        estudiante = validar_estudiante(usuario_actual.documento or documento)

        if estudiante is None:
            messagebox.showerror("Error", "Documento no encontrado.")
            return

        ventana.destroy()
        ventana_est = tk.Tk()
        try:
            ventana_est.state("zoomed")
        except Exception:
            try:
                ventana_est.attributes("-fullscreen", True)
            except Exception:
                pass
        apellido1 = estudiante.get("apellido1", "")
        apellido2 = estudiante.get("apellido2", "")
        nombre1 = estudiante.get("nombre1", "")
        nombre2 = estudiante.get("nombre2", "")
        grado = estudiante.get("grado", "")
        curso = estudiante.get("curso", None)
        tipo_documento = estudiante.get("tipo_documento", "")
        ModuloEstudiante(
            ventana_est,
            documento,
            apellido1,
            apellido2,
            nombre1,
            nombre2,
            grado,
            curso,
            cerrar_sesion_cb=lambda: confirmar_cerrar_sesion(ventana_est),
            tipo_documento=tipo_documento,
        )
        ventana_est.mainloop()
        if _volver_al_login:
            abrir_login()

    tk.Button(
        form_card,
        text="Ingresar",
        font=("Segoe UI", 12, "bold"),
        command=ingresar,
        bg="#0d4f8b",
        fg="white",
        relief="flat",
        bd=0,
        padx=20,
        pady=14,
        cursor="hand2",
        activebackground="#0a3d6b",
        activeforeground="white",
    ).pack(fill="x", pady=(14, 0))

    label_info_doc = tk.Label(
        form_card,
        text="Ingresa únicamente tu número de documento para continuar.",
        font=("Segoe UI", 10),
        bg="#f8fbff",
        fg="#64748b",
        justify="left",
        wraplength=340,
    )
    # Ocultar el label de info inferior de login sin romper layout
    label_info_doc.pack_forget()

    info_top = tk.Frame(panel_info, bg="#0d4f8b")
    info_top.pack(fill="both", expand=True, padx=42, pady=34)

    encabezado_institucion = tk.Frame(info_top, bg="#0d4f8b")
    encabezado_institucion.pack(anchor="w", fill="x")
    encabezado_institucion.grid_columnconfigure(1, weight=1)

    ruta_escudo = BASE_DIR / "imagenes_preguntas" / "logo_institucion.png"
    escudo_institucion_img = _cargar_imagen_login(ruta_escudo, (84, 84))
    if escudo_institucion_img is not None:
        tk.Label(
            encabezado_institucion,
            image=escudo_institucion_img,
            bg="#0d4f8b",
        ).grid(row=0, column=0, sticky="w")

    tk.Label(
        encabezado_institucion,
        text=nombre_institucion_login,
        font=("Segoe UI", 17, "bold"),
        bg="#0d4f8b",
        fg="white",
        justify="left",
        wraplength=360,
    ).grid(row=0, column=1, sticky="w", padx=(16, 0))

    tk.Label(
        info_top,
        text="Plataforma institucional para la gestión, aplicación y seguimiento de evaluaciones académicas.",
        font=("Segoe UI", 12),
        bg="#0d4f8b",
        fg="#dbeafe",
        justify="left",
        wraplength=500,
    ).pack(anchor="w", pady=(10, 16))

    contenido_items = _listar_contenido_institucional_activo_login()
    if not contenido_items:
        contenido_items = [
            {
                "id": 0,
                "titulo": "Bienvenidos",
                "mensaje": "Un entorno digital pensado para fortalecer la evaluación formativa, la toma de decisiones pedagógicas y el acceso ágil a la información académica.",
                "ruta_imagen_abs": "",
            }
        ]

    mensaje = tk.Frame(info_top, bg="#0b4377", padx=18, pady=16)
    mensaje.pack(fill="both", expand=True)
    contenido_titulo = tk.Label(
        mensaje,
        font=("Segoe UI", 14, "bold"),
        bg="#0b4377",
        fg="#ffffff",
        justify="left",
        wraplength=500,
    )
    contenido_visual = tk.Frame(mensaje, bg="#0b4377", height=280)
    contenido_visual.pack_propagate(False)
    contenido_imagen = tk.Label(contenido_visual, bg="#0b4377")
    contenido_imagen.pack(fill="both", expand=True)
    contenido_texto = tk.Label(
        mensaje,
        font=("Segoe UI", 11),
        bg="#0b4377",
        fg="#dbeafe",
        justify="left",
        wraplength=500,
    )
    contenido_indicador = tk.Label(
        mensaje,
        font=("Segoe UI", 9),
        bg="#0b4377",
        fg="#93c5fd",
    )
    login_carrusel_job = {"id": None}

    def _cancelar_carrusel_login(_event=None):
        job_id = login_carrusel_job.get("id")
        if job_id:
            try:
                ventana.after_cancel(job_id)
            except Exception:
                pass
            login_carrusel_job["id"] = None

    def mostrar_contenido_login(indice=0):
        item = contenido_items[indice]
        titulo = str(item.get("titulo", "") or "").strip()
        texto = str(item.get("mensaje", "") or "").strip()
        ruta_imagen_abs = str(item.get("ruta_imagen_abs", "") or "").strip()

        _cancelar_carrusel_login()
        contenido_visual.pack_forget()
        contenido_titulo.pack_forget()
        contenido_texto.pack_forget()
        contenido_indicador.pack_forget()

        if titulo:
            contenido_titulo.configure(text=titulo)
            contenido_titulo.pack(anchor="w", pady=(0, 10))

        hay_imagen = False
        if ruta_imagen_abs:
            imagen_item = _cargar_imagen_login(
                ruta_imagen_abs,
                (540, 280),
                cover=True,
            )
            if imagen_item is not None:
                contenido_imagen.configure(image=imagen_item, text="")
                contenido_imagen.image = imagen_item
                contenido_visual.pack(fill="both", expand=True)
                hay_imagen = True
            else:
                contenido_imagen.configure(image="", text="")
                contenido_imagen.image = None

        if not hay_imagen:
            contenido_texto.configure(text=texto)
            contenido_texto.pack(anchor="w", pady=(8 if titulo else 0, 0))

        if len(contenido_items) > 1:
            contenido_indicador.configure(
                text=f"Contenido {indice + 1} de {len(contenido_items)}"
            )
            contenido_indicador.pack(anchor="e", pady=(10, 0))
            siguiente = (indice + 1) % len(contenido_items)
            login_carrusel_job["id"] = ventana.after(
                4000, lambda: mostrar_contenido_login(siguiente)
            )

    ventana.bind("<Destroy>", _cancelar_carrusel_login, add="+")
    mostrar_contenido_login(0)

    # Atajo teclado: Enter para ingresar
    ventana.bind("<Return>", lambda event: ingresar())

    ventana.mainloop()


if __name__ == "__main__":
    try:
        abrir_login()
    except KeyboardInterrupt:
        # Permite cerrar la app desde terminal sin mostrar traceback.
        pass

# ...existing code...
