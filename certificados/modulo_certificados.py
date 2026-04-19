"""
Interfaz gráfica del Módulo de Certificados para el panel SuperAdmin.
Permite seleccionar estudiante, tipo de certificado y generar PDF oficial.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from core.construir_nombre import construir_nombre


class ModuloCertificados:
    def __init__(self, parent, db_path):
        self.parent = parent
        self.db_path = db_path
        self.win = parent  # El contenedor es el Frame de la pestaña
        # Detectar si la subpestaña es "Acta de grado"
        # FORZAR SIEMPRE LA INTERFAZ DE ACTA DE GRADO PARA DEPURACIÓN
        self._construir_interfaz_acta_grado()

    def _construir_interfaz_acta_grado(self):
        import os

        # Limpiar el contenedor antes de agregar widgets
        for widget in self.win.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.win, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Acta de Grado", font=("Segoe UI", 16, "bold")).pack(
            pady=(0, 20)
        )

        # Filtros: Jornada, Grado, Curso
        filtros_frame = ttk.Frame(frame)
        filtros_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(filtros_frame, text="Jornada:").grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        self.combo_jornada = ttk.Combobox(filtros_frame, state="readonly", width=12)
        self.combo_jornada.grid(row=0, column=1, padx=(0, 15))
        self.combo_jornada.bind(
            "<<ComboboxSelected>>", lambda e: self._actualizar_estudiantes()
        )

        ttk.Label(filtros_frame, text="Grado:").grid(
            row=0, column=2, sticky="w", padx=(0, 5)
        )
        self.combo_grado = ttk.Combobox(filtros_frame, state="readonly", width=8)
        self.combo_grado.grid(row=0, column=3, padx=(0, 15))
        self.combo_grado.bind(
            "<<ComboboxSelected>>", lambda e: self._actualizar_cursos_y_estudiantes()
        )

        ttk.Label(filtros_frame, text="Curso:").grid(
            row=0, column=4, sticky="w", padx=(0, 5)
        )
        self.combo_curso = ttk.Combobox(filtros_frame, state="readonly", width=10)
        self.combo_curso.grid(row=0, column=5, padx=(0, 15))
        self.combo_curso.bind(
            "<<ComboboxSelected>>", lambda e: self._actualizar_estudiantes()
        )

        # Selector de estudiante
        ttk.Label(frame, text="Estudiante:").pack(anchor="w")
        self.combo_estudiante = ttk.Combobox(frame, state="readonly")
        self.combo_estudiante.pack(fill="x", pady=5)

        # Editor del modelo institucional
        modelo_path = os.path.join(os.path.dirname(__file__), "modelo_acta_grado.txt")
        self.text_modelo = tk.Text(frame, height=18, width=100, wrap="word")
        self.text_modelo.pack(fill="both", expand=True, pady=(15, 5))
        try:
            with open(modelo_path, "r", encoding="utf-8") as f:
                self.text_modelo.insert("1.0", f.read())
        except Exception as e:
            self.text_modelo.insert(
                "1.0", "[No se pudo cargar el modelo institucional: %s]" % e
            )

        # Mejorar disposición visual de los botones
        btns_frame = ttk.Frame(frame)
        btns_frame.pack(fill="x", pady=(10, 10))

        self.btn_guardar_modelo = ttk.Button(
            btns_frame,
            text="💾 Guardar cambios al modelo",
            command=self._guardar_modelo_acta,
            style="Accent.TButton",
        )
        self.btn_guardar_modelo.pack(fill="x", padx=120, pady=(0, 10))

        self.btn_generar = ttk.Button(
            btns_frame,
            text="🖨️ Generar Acta de Grado (PDF)",
            command=self._generar_pdf_acta_grado,
            style="Accent.TButton",
        )
        self.btn_generar.pack(fill="x", padx=120, pady=(0, 0))

        self._cargar_filtros()
        self._actualizar_estudiantes()

    def _guardar_modelo_acta(self):
        import os

        modelo_path = os.path.join(os.path.dirname(__file__), "modelo_acta_grado.txt")
        texto = self.text_modelo.get("1.0", "end").strip()
        try:
            with open(modelo_path, "w", encoding="utf-8") as f:
                f.write(texto)
            messagebox.showinfo(
                "Guardado", "Modelo institucional guardado correctamente."
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el modelo: {e}")

    def _generar_pdf_acta_grado(self):
        import os

        # Validar selección de estudiante
        texto_combo = self.combo_estudiante.get()
        estudiante = self.estudiantes_map.get(texto_combo)
        if not estudiante:
            messagebox.showerror("Error", "Debe seleccionar un estudiante válido.")
            return
        # Obtener el texto del modelo institucional
        texto_modelo = self.text_modelo.get("1.0", "end").strip()
        # Preguntar dónde guardar el PDF
        nombre_estudiante = construir_nombre(estudiante).replace(" ", "_")
        nombre_sugerido = f"ActaGrado_{nombre_estudiante}_{estudiante.get('documento','')}.pdf"
        ruta_guardar = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialfile=nombre_sugerido,
            title="¿Dónde desea guardar el acta de grado?",
        )
        if not ruta_guardar:
            return
        try:
            from certificados.acta_grado import generar_acta_grado

            institucion = self._obtener_institucion()
            # Pasar el texto del modelo como argumento extra
            generar_acta_grado(estudiante, institucion, {}, ruta_guardar, texto_modelo)
            messagebox.showinfo(
                "Éxito", f"Acta de grado generada correctamente:\n{ruta_guardar}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error", f"Ocurrió un error al generar el acta de grado:\n{e}"
            )

    def _construir_interfaz(self):
        import sqlite3

        # Limpiar el contenedor antes de agregar widgets
        for widget in self.win.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.win, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame, text="Generar Certificado Académico", font=("Segoe UI", 16, "bold")
        ).pack(pady=(0, 20))

        # Filtros: Jornada, Grado, Curso
        filtros_frame = ttk.Frame(frame)
        filtros_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(filtros_frame, text="Jornada:").grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        self.combo_jornada = ttk.Combobox(filtros_frame, state="readonly", width=12)
        self.combo_jornada.grid(row=0, column=1, padx=(0, 15))
        self.combo_jornada.bind(
            "<<ComboboxSelected>>", lambda e: self._actualizar_estudiantes()
        )

        ttk.Label(filtros_frame, text="Grado:").grid(
            row=0, column=2, sticky="w", padx=(0, 5)
        )
        self.combo_grado = ttk.Combobox(filtros_frame, state="readonly", width=8)
        self.combo_grado.grid(row=0, column=3, padx=(0, 15))
        self.combo_grado.bind(
            "<<ComboboxSelected>>", lambda e: self._actualizar_cursos_y_estudiantes()
        )

        ttk.Label(filtros_frame, text="Curso:").grid(
            row=0, column=4, sticky="w", padx=(0, 5)
        )
        self.combo_curso = ttk.Combobox(filtros_frame, state="readonly", width=10)
        self.combo_curso.grid(row=0, column=5, padx=(0, 15))
        self.combo_curso.bind(
            "<<ComboboxSelected>>", lambda e: self._actualizar_estudiantes()
        )

        # Selector de estudiante (real)
        ttk.Label(frame, text="Estudiante:").pack(anchor="w")
        self.combo_estudiante = ttk.Combobox(frame, state="readonly")
        self.combo_estudiante.pack(fill="x", pady=5)

        # Botón generar
        self.btn_generar = ttk.Button(
            frame, text="Generar PDF", command=self._generar_pdf
        )
        self.btn_generar.pack(pady=30)

        self._cargar_filtros()
        self._actualizar_estudiantes()

    def _cargar_filtros(self):
        import sqlite3

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Jornadas
            cursor.execute(
                "SELECT DISTINCT jornada FROM estudiantes WHERE estado = 'Activo' AND jornada IS NOT NULL AND TRIM(jornada) <> '' ORDER BY jornada"
            )
            jornadas = [r[0] for r in cursor.fetchall() if r[0]]
            self.combo_jornada["values"] = ["Todas"] + jornadas
            self.combo_jornada.current(0)
            # Grados
            cursor.execute(
                "SELECT DISTINCT grado FROM estudiantes WHERE estado = 'Activo' AND grado IS NOT NULL AND TRIM(grado) <> '' ORDER BY grado"
            )
            grados = [r[0] for r in cursor.fetchall() if r[0]]
            self.combo_grado["values"] = ["Todos"] + grados
            self.combo_grado.current(0)
            # Cursos (inicialmente todos)
            cursor.execute(
                "SELECT DISTINCT curso FROM estudiantes WHERE estado = 'Activo' AND curso IS NOT NULL AND TRIM(curso) <> '' ORDER BY curso"
            )
            cursos = [r[0] for r in cursor.fetchall() if r[0]]
            self.combo_curso["values"] = ["Todos"] + cursos
            self.combo_curso.current(0)
            conn.close()
        except Exception as e:
            print(f"[ERROR] No se pudo cargar filtros: {e}")

    def _actualizar_cursos_y_estudiantes(self):
        import sqlite3

        grado_sel = self.combo_grado.get()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            if grado_sel and grado_sel != "Todos":
                cursor.execute(
                    "SELECT DISTINCT curso FROM estudiantes WHERE estado = 'Activo' AND grado = ? AND curso IS NOT NULL AND TRIM(curso) <> '' ORDER BY curso",
                    (grado_sel,),
                )
                cursos = [r[0] for r in cursor.fetchall() if r[0]]
                self.combo_curso["values"] = ["Todos"] + cursos
                self.combo_curso.current(0)
            else:
                cursor.execute(
                    "SELECT DISTINCT curso FROM estudiantes WHERE estado = 'Activo' AND curso IS NOT NULL AND TRIM(curso) <> '' ORDER BY curso"
                )
                cursos = [r[0] for r in cursor.fetchall() if r[0]]
                self.combo_curso["values"] = ["Todos"] + cursos
                self.combo_curso.current(0)
            conn.close()
        except Exception as e:
            print(f"[ERROR] No se pudo actualizar cursos: {e}")
        self._actualizar_estudiantes()

    def _actualizar_estudiantes(self):
        import sqlite3

        jornada_sel = self.combo_jornada.get()
        grado_sel = self.combo_grado.get()
        curso_sel = self.combo_curso.get()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT id, documento, nombre, grado, curso FROM estudiantes WHERE estado = 'Activo'"
            params = []
            if jornada_sel and jornada_sel != "Todas":
                query += " AND jornada = ?"
                params.append(jornada_sel)
            if grado_sel and grado_sel != "Todos":
                query += " AND grado = ?"
                params.append(grado_sel)
            if curso_sel and curso_sel != "Todos":
                query += " AND curso = ?"
                params.append(curso_sel)
            query += " ORDER BY grado, curso, nombre"
            cursor.execute(query, params)
            estudiantes = cursor.fetchall()
            conn.close()
        except Exception as e:
            estudiantes = []
            print(f"[ERROR] No se pudo filtrar estudiantes: {e}")
        # Diccionario: texto_combo -> objeto_estudiante
        self.estudiantes_map = {}
        values = []
        for id_, documento, nombre, grado, curso in estudiantes:
            texto_combo = f"{nombre} (G:{grado} C:{curso}) - {documento}"
            values.append(texto_combo)
            self.estudiantes_map[texto_combo] = {
                "id": id_,
                "nombre": nombre,
                "documento": documento,
                "grado": grado,
                "curso": curso,
            }
        self.combo_estudiante["values"] = values
        if values:
            self.combo_estudiante.current(0)
        else:
            self.combo_estudiante.set("")

    def _cargar_estudiantes(self):
        import sqlite3

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT documento, nombre, grado, curso FROM estudiantes WHERE estado = 'Activo' ORDER BY grado, curso, nombre"
            )
            estudiantes = cursor.fetchall()
            conn.close()
        except Exception as e:
            estudiantes = []
            print(f"[ERROR] No se pudo cargar estudiantes: {e}")
        self.estudiantes_lista = estudiantes
        # Mostrar en el combo: "nombre (grado curso) - documento"
        values = [
            f"{nombre} (G:{grado} C:{curso}) - {documento}"
            for documento, nombre, grado, curso in estudiantes
        ]
        self.combo_estudiante["values"] = values
        if values:
            self.combo_estudiante.current(0)

    def _generar_pdf(self):
        # Validar selección de estudiante
        texto_combo = self.combo_estudiante.get()
        estudiante = self.estudiantes_map.get(texto_combo)
        if not estudiante:
            messagebox.showerror("Error", "Debe seleccionar un estudiante válido.")
            return
        # Determinar tipo de certificado según la subpestaña activa
        tipo = "MATRICULA"
        if hasattr(self.parent, "winfo_parent"):
            try:
                nb = self.parent.master  # Notebook
                idx = nb.index(nb.select())
                tab_text = nb.tab(idx, "text").upper()
                if "CALIFICACION" in tab_text:
                    tipo = "CALIFICACIONES"
                elif "ACTA" in tab_text:
                    tipo = "ACTA"
                elif "DIPLOMA" in tab_text:
                    tipo = "DIPLOMA"
            except Exception:
                pass
        # Validación académica: diploma solo grado 11
        if tipo == "DIPLOMA" and str(estudiante.get("grado", "")).strip() != "11":
            messagebox.showerror(
                "Regla académica",
                "Solo los estudiantes de grado 11 pueden recibir diploma.",
            )
            return

        # Preguntar dónde guardar el PDF
        nombre_estudiante = construir_nombre(estudiante).replace(" ", "_")
        nombre_sugerido = f"{tipo.title()}_{nombre_estudiante}_{estudiante.get('documento','')}.pdf"
        ruta_guardar = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialfile=nombre_sugerido,
            title="¿Dónde desea guardar el certificado?",
        )
        if not ruta_guardar:
            return  # Usuario canceló

        try:
            from certificados.gestor_certificados import generar_documento

            institucion = self._obtener_institucion()
            ruta = generar_documento(tipo, estudiante, institucion, ruta_guardar)
            if ruta:
                messagebox.showinfo(
                    "Éxito", f"Documento generado correctamente:\n{ruta}"
                )
            else:
                messagebox.showerror("Error", "No se pudo generar el documento.")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Ocurrió un error al generar el documento:\n{e}"
            )

    def _obtener_institucion(self):
        # TODO: Obtener datos reales de la institución (nombre, nit, etc.)
        return {"nombre": "Institución Demo", "nit": "00000000"}
