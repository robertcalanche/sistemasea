# -*- coding: utf-8 -*-
"""
Interfaz Tkinter Mejorada - Banco de Preguntas
Integración con modulo_superadmin.py

Reemplaza _build_preguntas_tab() y funciones relacionadas
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from banco_preguntas_profesional import BancoPreguntasProfesional


class InterfazBancoPreguntasAvanzada:
    """Mixin para integrar en ModuloSuperAdmin."""

    def _preg_obtener_dataframe_base(self):
        try:
            return self.banco.obtener_todas_preguntas().copy()
        except Exception:
            return pd.DataFrame(columns=self.banco.COLUMNAS_REQUERIDAS)

    def _preg_puede_modificar_pregunta(self, pregunta, accion="editar"):
        return True

    def _preg_enriquecer_datos_guardado(
        self, datos_pregunta, es_nueva=False, pregunta_actual=None
    ):
        datos = dict(datos_pregunta or {})
        if pregunta_actual:
            if not str(datos.get("docente_documento", "")).strip():
                datos["docente_documento"] = str(
                    pregunta_actual.get("docente_documento", "")
                ).strip()
            if not str(datos.get("nombre", "")).strip():
                datos["nombre"] = str(pregunta_actual.get("nombre", "")).strip()
            if not str(datos.get("fecha_registro", "")).strip():
                datos["fecha_registro"] = str(
                    pregunta_actual.get("fecha_registro", "")
                ).strip()
        if es_nueva:
            if not str(datos.get("docente_documento", "")).strip():
                datos["docente_documento"] = "admin"
            if not str(datos.get("nombre", "")).strip():
                datos["nombre"] = "SuperAdmin"
        return datos

    def _preg_obtener_grados_disponibles_nueva_evaluacion(self):
        df_base = self._preg_obtener_dataframe_base()
        if df_base.empty:
            return []
        grados = []
        vistos = set()
        for valor in df_base.get("grado", pd.Series(dtype=str)).tolist():
            grado = str(valor).strip()
            clave = grado.lower()
            if not grado or clave in vistos:
                continue
            vistos.add(clave)
            grados.append(grado)
        return sorted(grados, key=lambda item: str(item).lower())

    def _preg_obtener_areas_disponibles_nueva_evaluacion(self, grado=None):
        df_base = self._preg_obtener_dataframe_base()
        if df_base.empty:
            return []
        if grado:
            df_base = df_base[
                df_base.get("grado", pd.Series(dtype=str))
                .astype(str)
                .str.strip()
                .str.lower()
                == str(grado).strip().lower()
            ]
        areas = []
        vistos = set()
        for valor in df_base.get("area", pd.Series(dtype=str)).tolist():
            area = self._preg_area_canonica(valor)
            clave = str(area).strip().lower()
            if not clave or clave in vistos:
                continue
            vistos.add(clave)
            areas.append(area)
        return sorted(areas, key=lambda item: str(item).lower())

    def _preg_dialog_agregar_evaluacion_completa(self):
        d = tk.Toplevel(self.win)
        d.transient(self.win)
        d.grab_set()
        d.title("Agregar evaluacion completa")
        d.geometry("980x720")

        bloques = []

        frame_meta = ttk.LabelFrame(d, text="Datos de la evaluacion", padding=(10, 8))
        frame_meta.pack(fill="x", padx=10, pady=(10, 6))

        ttk.Label(frame_meta, text="grado:").grid(
            row=0, column=0, sticky="e", padx=6, pady=4
        )
        cb_grado = ttk.Combobox(
            frame_meta,
            state="readonly",
            values=self._preg_obtener_grados_disponibles_nueva_evaluacion(),
            width=16,
        )
        cb_grado.grid(row=0, column=1, sticky="we", padx=6, pady=4)

        ttk.Label(frame_meta, text="area:").grid(
            row=0, column=2, sticky="e", padx=6, pady=4
        )
        cb_area = ttk.Combobox(frame_meta, state="readonly", values=[], width=22)
        cb_area.grid(row=0, column=3, sticky="we", padx=6, pady=4)

        ttk.Label(frame_meta, text="evaluacion:").grid(
            row=1, column=0, sticky="e", padx=6, pady=4
        )
        en_evaluacion = ttk.Entry(frame_meta)
        en_evaluacion.grid(row=1, column=1, sticky="we", padx=6, pady=4)

        ttk.Label(frame_meta, text="periodo:").grid(
            row=1, column=2, sticky="e", padx=6, pady=4
        )
        en_periodo = ttk.Entry(frame_meta)
        en_periodo.grid(row=1, column=3, sticky="we", padx=6, pady=4)

        frame_meta.columnconfigure(1, weight=1)
        frame_meta.columnconfigure(3, weight=1)

        controles = ttk.Frame(d)
        controles.pack(fill="x", padx=10, pady=(0, 6))

        lbl_total = ttk.Label(controles, text="0", font=("Arial", 10, "bold"))
        ttk.Label(controles, text="Preguntas:").pack(side="left", padx=(0, 6))
        lbl_total.pack(side="left", padx=(0, 10))

        contenedor_scroll = ttk.Frame(d)
        contenedor_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        canvas = tk.Canvas(contenedor_scroll, highlightthickness=0)
        scroll_y = ttk.Scrollbar(
            contenedor_scroll, orient="vertical", command=canvas.yview
        )
        frame_bloques = ttk.Frame(canvas)
        frame_bloques.bind(
            "<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        win_frame = canvas.create_window((0, 0), window=frame_bloques, anchor="nw")
        canvas.bind(
            "<Configure>", lambda e: canvas.itemconfigure(win_frame, width=e.width)
        )
        canvas.configure(yscrollcommand=scroll_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        def _scroll_rueda(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _scroll_rueda)
        d.bind("<MouseWheel>", _scroll_rueda)

        def _actualizar_areas(*_args):
            grado = cb_grado.get().strip()
            areas = self._preg_obtener_areas_disponibles_nueva_evaluacion(grado)
            cb_area["values"] = areas
            if areas:
                actual = cb_area.get().strip()
                if actual not in areas:
                    cb_area.set(areas[0])
            else:
                cb_area.set("")

        cb_grado.bind("<<ComboboxSelected>>", _actualizar_areas)
        if cb_grado["values"]:
            cb_grado.set(cb_grado["values"][0])
            _actualizar_areas()

        def _renumerar_bloques():
            for idx, bloque in enumerate(bloques, start=1):
                bloque["numero"] = idx
                bloque["titulo_var"].set(f"Pregunta {idx}")
                bloque["frame"].grid(row=idx - 1, column=0, sticky="we", pady=4)
            lbl_total.config(text=str(len(bloques)))

        def _toggle_bloque(bloque):
            if bloque.get("colapsado"):
                bloque["cuerpo"].grid()
                bloque["btn_colapsar"].configure(text="Colapsar")
                bloque["colapsado"] = False
            else:
                bloque["cuerpo"].grid_remove()
                bloque["btn_colapsar"].configure(text="Expandir")
                bloque["colapsado"] = True

        def _eliminar_bloque(bloque):
            try:
                bloque["frame"].destroy()
            except Exception:
                pass
            if bloque in bloques:
                bloques.remove(bloque)
            _renumerar_bloques()

        def _crear_bloque(datos_iniciales=None):
            datos_iniciales = datos_iniciales or {}

            frame = ttk.LabelFrame(frame_bloques)
            frame.grid(column=0, sticky="we", pady=4)
            frame.columnconfigure(0, weight=1)

            encabezado = ttk.Frame(frame)
            encabezado.grid(row=0, column=0, sticky="we", padx=6, pady=(4, 2))
            encabezado.columnconfigure(0, weight=1)

            titulo_var = tk.StringVar(value="Pregunta")
            ttk.Label(encabezado, textvariable=titulo_var).grid(
                row=0, column=0, sticky="w"
            )

            btn_colapsar = ttk.Button(encabezado, text="Colapsar", width=10)
            btn_colapsar.grid(row=0, column=1, sticky="e", padx=(0, 6))

            btn_eliminar = ttk.Button(encabezado, text="Eliminar", width=10)
            btn_eliminar.grid(row=0, column=2, sticky="e")

            cuerpo = ttk.Frame(frame)
            cuerpo.grid(row=1, column=0, sticky="we", padx=6, pady=(0, 6))
            cuerpo.columnconfigure(1, weight=1)

            ttk.Label(cuerpo, text="ID contexto:").grid(
                row=0, column=0, sticky="e", padx=4, pady=2
            )
            en_id_contexto = ttk.Entry(cuerpo)
            en_id_contexto.grid(row=0, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Tipo pregunta:").grid(
                row=1, column=0, sticky="e", padx=4, pady=2
            )
            cb_tipo_pregunta = ttk.Combobox(
                cuerpo,
                state="readonly",
                values=["opcion_multiple", "abierta"],
            )
            cb_tipo_pregunta.grid(row=1, column=1, sticky="w", padx=4, pady=2)

            ttk.Label(cuerpo, text="Contexto:").grid(
                row=2, column=0, sticky="ne", padx=4, pady=2
            )
            txt_contexto = tk.Text(cuerpo, height=3, width=80)
            txt_contexto.grid(row=2, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Enunciado:").grid(
                row=3, column=0, sticky="ne", padx=4, pady=2
            )
            txt_enunciado = tk.Text(cuerpo, height=3, width=80)
            txt_enunciado.grid(row=3, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Opción A:").grid(
                row=4, column=0, sticky="e", padx=4, pady=2
            )
            en_a = ttk.Entry(cuerpo)
            en_a.grid(row=4, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Opción B:").grid(
                row=5, column=0, sticky="e", padx=4, pady=2
            )
            en_b = ttk.Entry(cuerpo)
            en_b.grid(row=5, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Opción C:").grid(
                row=6, column=0, sticky="e", padx=4, pady=2
            )
            en_c = ttk.Entry(cuerpo)
            en_c.grid(row=6, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Opción D:").grid(
                row=7, column=0, sticky="e", padx=4, pady=2
            )
            en_d = ttk.Entry(cuerpo)
            en_d.grid(row=7, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Correcta:").grid(
                row=8, column=0, sticky="e", padx=4, pady=2
            )
            cb_correcta = ttk.Combobox(
                cuerpo, state="readonly", values=["A", "B", "C", "D"]
            )
            cb_correcta.grid(row=8, column=1, sticky="w", padx=4, pady=2)

            en_id_contexto.insert(0, str(datos_iniciales.get("id_contexto", "")))
            tipo_inicial = (
                str(datos_iniciales.get("tipo_pregunta", "opcion_multiple"))
                .strip()
                .lower()
            )
            if tipo_inicial not in ("opcion_multiple", "abierta"):
                tipo_inicial = "opcion_multiple"
            cb_tipo_pregunta.set(tipo_inicial)
            txt_contexto.insert("1.0", str(datos_iniciales.get("contexto", "")))
            txt_enunciado.insert("1.0", str(datos_iniciales.get("enunciado", "")))
            en_a.insert(0, str(datos_iniciales.get("opcion_a", "")))
            en_b.insert(0, str(datos_iniciales.get("opcion_b", "")))
            en_c.insert(0, str(datos_iniciales.get("opcion_c", "")))
            en_d.insert(0, str(datos_iniciales.get("opcion_d", "")))
            correcta = str(datos_iniciales.get("correcta", "")).upper().strip()
            if correcta in ("A", "B", "C", "D"):
                cb_correcta.set(correcta)

            bloque = {
                "frame": frame,
                "cuerpo": cuerpo,
                "titulo_var": titulo_var,
                "btn_colapsar": btn_colapsar,
                "numero": len(bloques) + 1,
                "colapsado": False,
                "widgets": {
                    "id_contexto": en_id_contexto,
                    "tipo_pregunta": cb_tipo_pregunta,
                    "contexto": txt_contexto,
                    "enunciado": txt_enunciado,
                    "opcion_a": en_a,
                    "opcion_b": en_b,
                    "opcion_c": en_c,
                    "opcion_d": en_d,
                    "correcta": cb_correcta,
                },
            }

            btn_colapsar.configure(command=lambda b=bloque: _toggle_bloque(b))
            btn_eliminar.configure(command=lambda b=bloque: _eliminar_bloque(b))
            bloques.append(bloque)
            _renumerar_bloques()

        def _leer_bloque(bloque):
            w = bloque["widgets"]
            return {
                "id_contexto": w["id_contexto"].get().strip(),
                "tipo_pregunta": w["tipo_pregunta"].get().strip().lower()
                or "opcion_multiple",
                "contexto": w["contexto"].get("1.0", "end").strip(),
                "enunciado": w["enunciado"].get("1.0", "end").strip(),
                "opcion_a": w["opcion_a"].get().strip(),
                "opcion_b": w["opcion_b"].get().strip(),
                "opcion_c": w["opcion_c"].get().strip(),
                "opcion_d": w["opcion_d"].get().strip(),
                "correcta": w["correcta"].get().strip().upper(),
            }

        def _guardar():
            grado = cb_grado.get().strip()
            area = cb_area.get().strip()
            evaluacion = en_evaluacion.get().strip()
            periodo = en_periodo.get().strip()

            if not grado or not area or not evaluacion:
                messagebox.showerror(
                    "Validación",
                    "Debe completar grado, área y evaluación.",
                    parent=d,
                )
                return

            if not bloques:
                messagebox.showerror(
                    "Validación", "Debe agregar al menos una pregunta.", parent=d
                )
                return

            payload = []
            for idx, bloque in enumerate(bloques, start=1):
                datos_bloque = _leer_bloque(bloque)
                tipo_pregunta = (
                    str(datos_bloque.get("tipo_pregunta", "opcion_multiple"))
                    .strip()
                    .lower()
                )

                if not datos_bloque.get("enunciado"):
                    messagebox.showerror(
                        "Validación",
                        f"Pregunta {idx}: el enunciado es obligatorio.",
                        parent=d,
                    )
                    return

                if tipo_pregunta == "opcion_multiple":
                    for campo in (
                        "opcion_a",
                        "opcion_b",
                        "opcion_c",
                        "opcion_d",
                        "correcta",
                    ):
                        if not datos_bloque.get(campo):
                            messagebox.showerror(
                                "Validación",
                                f"Pregunta {idx}: falta el campo '{campo}'.",
                                parent=d,
                            )
                            return
                    if datos_bloque["correcta"] not in ("A", "B", "C", "D"):
                        messagebox.showerror(
                            "Validación",
                            f"Pregunta {idx}: la correcta debe ser A, B, C o D.",
                            parent=d,
                        )
                        return
                else:
                    datos_bloque["opcion_a"] = ""
                    datos_bloque["opcion_b"] = ""
                    datos_bloque["opcion_c"] = ""
                    datos_bloque["opcion_d"] = ""
                    datos_bloque["correcta"] = ""

                payload.append(
                    {
                        "evaluacion": evaluacion,
                        "area": area,
                        "periodo": periodo,
                        "grado": grado,
                        **datos_bloque,
                    }
                )

            d.result = payload
            d.destroy()

        ttk.Button(controles, text="Agregar pregunta", command=_crear_bloque).pack(
            side="left", padx=(0, 4)
        )

        frame_btns = ttk.Frame(d)
        frame_btns.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(frame_btns, text="💾 Guardar", command=_guardar).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(frame_btns, text="Cancelar", command=d.destroy).pack(side="left")

        _crear_bloque()
        d.wait_window()
        return getattr(d, "result", None)

    # NOTA: Llamar a este método desde ModuloSuperAdmin para reemplazar _build_preguntas_tab
    def _build_preguntas_tab_mejorada(self):
        """Construye la interfaz mejorada del banco de preguntas."""
        frame = self.tab_preguntas
        mostrar_filtro_docente = bool(
            getattr(self, "_preg_mostrar_filtro_docente", False)
        )
        permitir_importar = bool(getattr(self, "_preg_permitir_importar", True))
        permitir_exportar = bool(getattr(self, "_preg_permitir_exportar", True))
        permitir_eliminar = bool(getattr(self, "_preg_permitir_eliminar", True))
        permitir_validar = bool(getattr(self, "_preg_permitir_validar", True))
        # self.banco ya está inicializado en ModuloSuperAdmin.__init__()
        # Así que aquí solo lo usamos, no lo recreamos

        # ============ PANEL DE FILTROS ============
        filtros_frame = ttk.Frame(frame, relief="sunken", padding=8)
        filtros_frame.pack(fill="x", padx=4, pady=4)

        ttk.Label(filtros_frame, text="Filtros:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky="w", padx=2
        )

        # Fila 1: Grado, Área, Evaluación
        ttk.Label(filtros_frame, text="Grado:").grid(
            row=1, column=0, sticky="e", padx=2
        )
        self.combo_grado_preg = ttk.Combobox(filtros_frame, state="readonly", width=15)
        self.combo_grado_preg.grid(row=1, column=1, sticky="we", padx=2)
        self.combo_grado_preg.bind("<<ComboboxSelected>>", self._preg_on_grado_cambio)

        ttk.Label(filtros_frame, text="Área:").grid(row=1, column=2, sticky="e", padx=2)
        self.combo_area_preg = ttk.Combobox(filtros_frame, state="readonly", width=15)
        self.combo_area_preg.grid(row=1, column=3, sticky="we", padx=2)
        self.combo_area_preg.bind("<<ComboboxSelected>>", self._preg_on_area_cambio)

        ttk.Label(filtros_frame, text="Evaluación:").grid(
            row=1, column=4, sticky="e", padx=2
        )
        self.combo_evaluacion_preg = ttk.Combobox(
            filtros_frame, state="readonly", width=15
        )
        self.combo_evaluacion_preg.grid(row=1, column=5, sticky="we", padx=2)
        self.combo_evaluacion_preg.bind(
            "<<ComboboxSelected>>", self._preg_cargar_datos_filtrados
        )

        # Botón de limpiar filtros
        ttk.Button(
            filtros_frame, text="Limpiar filtros", command=self._preg_limpiar_filtros
        ).grid(row=1, column=6, padx=2)

        if mostrar_filtro_docente:
            ttk.Label(filtros_frame, text="Docente:").grid(
                row=2, column=0, sticky="e", padx=2, pady=(4, 0)
            )
            self.combo_docente_preg = ttk.Combobox(
                filtros_frame, state="readonly", width=30
            )
            self.combo_docente_preg.grid(
                row=2, column=1, columnspan=3, sticky="we", padx=2, pady=(4, 0)
            )
            self.combo_docente_preg.bind(
                "<<ComboboxSelected>>", self._preg_cargar_datos_filtrados
            )

        # Estadísticas
        self.lbl_stats = ttk.Label(filtros_frame, text="", foreground="gray")
        self.lbl_stats.grid(
            row=3 if mostrar_filtro_docente else 2,
            column=0,
            columnspan=7,
            sticky="w",
            padx=2,
            pady=4,
        )

        filtros_frame.columnconfigure(1, weight=1)
        filtros_frame.columnconfigure(3, weight=1)
        filtros_frame.columnconfigure(5, weight=1)

        # ============ PANEL DE BOTONES ============
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", padx=4, pady=4)

        # Botones principales
        btn_agregar = ttk.Button(
            toolbar, text="➕ Agregar", command=self.pregunta_agregar
        )
        btn_agregar.pack(side="left", padx=2)

        btn_editar = ttk.Button(
            toolbar,
            text="✏️  Editar evaluación",
            command=self.pregunta_editar_evaluacion_filtrada,
        )
        btn_editar.pack(side="left", padx=2)

        if permitir_eliminar:
            btn_eliminar = ttk.Button(
                toolbar, text="🗑️  Eliminar", command=self.pregunta_eliminar
            )
            btn_eliminar.pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(
            side="left", fill="y", padx=(8, 4)
        )

        if permitir_importar:
            btn_importar = ttk.Button(
                toolbar,
                text="📥 Importar masivo",
                command=self.preguntas_importar_avanzado,
            )
            btn_importar.pack(side="left", padx=2)

        if permitir_exportar:
            btn_exportar = ttk.Button(
                toolbar, text="📤 Exportar", command=self.preguntas_exportar
            )
            btn_exportar.pack(side="left", padx=2)

        generar_plantilla = getattr(self, "generar_plantilla_excel_banco", None)
        if callable(generar_plantilla):
            ttk.Button(
                toolbar,
                text="🧾 Plantilla Excel",
                command=generar_plantilla,
            ).pack(side="left", padx=2)

        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=4)

        if permitir_validar:
            btn_validar = ttk.Button(
                toolbar,
                text="✓ Validar integridad",
                command=self._preg_validar_integridad,
            )
            btn_validar.pack(side="left", padx=2)

        self._preg_toolbar = toolbar

        # ============ TREEVIEW MEJORADO CON SCROLLS ============
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # Columnas: 15 total (incluye todas las necesarias)
        cols = (
            "id",
            "evaluacion",
            "id_evaluacion",  # NUEVA COLUMNA VISUAL
            "area",
            "periodo",
            "grado",
            "docente_documento",
            "nombre",
            "fecha_registro",
            "id_contexto",
            "contexto",
            "enunciado",
            "opcion_a",
            "opcion_b",
            "opcion_c",
            "opcion_d",
            "correcta",
            "tipo_pregunta",
            "imagen",
        )

        # Crear Treeview dentro del mismo frame que sus scrollbars
        self.tree_preg = ttk.Treeview(
            tree_frame, columns=cols, show="headings", height=15
        )

        # Configurar anchos de columnas según clasificación
        col_config = {
            # ===== COLUMNAS CORTAS (muy pequeñas) =====
            "id": {"width": 40, "anchor": "center"},
            "correcta": {"width": 35, "anchor": "center"},
            # ===== COLUMNAS CORTAS (pequeñas) =====
            "periodo": {"width": 50, "anchor": "center"},
            "grado": {"width": 50, "anchor": "center"},
            "imagen": {"width": 50, "anchor": "center"},
            "docente_documento": {"width": 110, "anchor": "w"},
            "nombre": {"width": 150, "anchor": "w"},
            "fecha_registro": {"width": 130, "anchor": "center"},
            # ===== COLUMNAS MEDIANAS =====
            "evaluacion": {"width": 90, "anchor": "w"},
            "id_evaluacion": {"width": 120, "anchor": "w"},  # Compacto, puede ser largo
            "area": {"width": 90, "anchor": "w"},
            "id_contexto": {"width": 80, "anchor": "center"},
            "tipo_pregunta": {"width": 110, "anchor": "center"},
            # ===== COLUMNAS LARGAS =====
            "contexto": {"width": 200, "anchor": "w"},
            "enunciado": {"width": 220, "anchor": "w"},
            "opcion_a": {"width": 180, "anchor": "w"},
            "opcion_b": {"width": 180, "anchor": "w"},
            "opcion_c": {"width": 180, "anchor": "w"},
            "opcion_d": {"width": 180, "anchor": "w"},
        }

        for col in cols:
            self.tree_preg.heading(
                col,
                text=col.upper(),
                command=lambda c=col: self._preg_ordenar_columna(c),
            )
            config = col_config.get(col, {})
            # stretch=True permite redimensionamiento manual de columnas
            self.tree_preg.column(
                col,
                width=config.get("width", 100),
                anchor=config.get("anchor", "w"),
                stretch=True,
            )

        # Scrollbar VERTICAL
        scrollbar_v = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.tree_preg.yview
        )

        # Scrollbar HORIZONTAL
        scrollbar_h = ttk.Scrollbar(
            tree_frame, orient="horizontal", command=self.tree_preg.xview
        )

        self.tree_preg.configure(yscroll=scrollbar_v.set, xscroll=scrollbar_h.set)

        # Empacar Treeview y scrollbars
        self.tree_preg.pack(side="left", fill="both", expand=True)
        scrollbar_v.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")

        # Configurar expansión del frame
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # ===== BINDINGS PARA INTERACCIÓN =====
        # Doble clic para editar
        self.tree_preg.bind("<Double-1>", self._preg_on_double_click_editar)
        # Clic derecho para menú contextual
        self.tree_preg.bind("<Button-3>", self._mostrar_menu_contextual)

        # Cargar datos iniciales
        self._preg_cargar_datos_iniciales()

    # ========== MÉTODOS DE FILTROS ==========

    def _preg_cargar_datos_iniciales(self):
        """Carga los datos iniciales en los combos de filtros."""
        df_base = self._preg_obtener_dataframe_base()
        grados = sorted(
            list(
                dict.fromkeys(
                    [
                        str(g).strip()
                        for g in df_base.get("grado", pd.Series(dtype=str)).tolist()
                        if str(g).strip()
                        and str(g).strip().lower() not in ("nan", "none")
                    ]
                )
            )
        )
        self.combo_grado_preg["values"] = ["(Todos)"] + grados
        self.combo_grado_preg.current(0)

        areas = self._preg_areas_canonicas(
            sorted(
                list(
                    dict.fromkeys(
                        [
                            str(a).strip()
                            for a in df_base.get("area", pd.Series(dtype=str)).tolist()
                            if str(a).strip()
                            and str(a).strip().lower() not in ("nan", "none")
                        ]
                    )
                )
            )
        )
        self.combo_area_preg["values"] = ["(Todos)"] + areas
        self.combo_area_preg.current(0)

        self.combo_evaluacion_preg["values"] = ["(Todos)"]
        self.combo_evaluacion_preg.current(0)

        if hasattr(self, "combo_docente_preg"):
            opciones_docente = sorted(
                list(
                    dict.fromkeys(
                        [
                            f"{str(row.get('nombre', '')).strip()} [{str(row.get('docente_documento', '')).strip()}]"
                            for _, row in df_base.iterrows()
                            if str(row.get("docente_documento", "")).strip()
                        ]
                    )
                )
            )
            self.combo_docente_preg["values"] = ["(Todos)"] + opciones_docente
            self.combo_docente_preg.current(0)

        self._preg_cargar_datos_filtrados()
        self._preg_actualizar_estadisticas()

    def _preg_mapa_areas_plan(self):
        """Devuelve mapa {area_lower: area_canonica} desde catálogo de áreas."""
        cache = getattr(self, "_preg_area_map_cache", None)
        if isinstance(cache, dict):
            return cache

        mapa = {}
        db_path = getattr(self, "db_path", None)
        if not db_path:
            self._preg_area_map_cache = mapa
            return mapa

        try:
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT nombre
                    FROM areas
                    WHERE nombre IS NOT NULL
                      AND TRIM(CAST(nombre AS TEXT)) <> ''
                    """
                )
                for row in cur.fetchall():
                    if not row:
                        continue
                    nombre = str(row[0]).strip()
                    if not nombre:
                        continue
                    mapa.setdefault(nombre.lower(), nombre)
        except Exception:
            mapa = {}

        self._preg_area_map_cache = mapa
        return mapa

    def _preg_area_canonica(self, area):
        area_txt = str(area or "").strip()
        if not area_txt:
            return ""
        return self._preg_mapa_areas_plan().get(area_txt.lower(), area_txt)

    def _preg_areas_canonicas(self, areas):
        unicas = {}
        for area in areas or []:
            area_canon = self._preg_area_canonica(area)
            if not area_canon:
                continue
            unicas.setdefault(area_canon.lower(), area_canon)
        return sorted(unicas.values(), key=lambda a: a.lower())

    def _preg_on_grado_cambio(self, *args):
        """Se ejecuta cuando cambia el grado."""
        grado_sel = self.combo_grado_preg.get()
        grado_val = None if grado_sel == "(Todos)" else grado_sel

        df_base = self._preg_obtener_dataframe_base()
        if grado_val:
            df_base = df_base[
                df_base["grado"].astype(str).str.strip().str.lower()
                == str(grado_val).strip().lower()
            ]
        areas = self._preg_areas_canonicas(
            df_base.get("area", pd.Series(dtype=str)).tolist()
        )
        self.combo_area_preg["values"] = ["(Todos)"] + areas
        self.combo_area_preg.current(0)

        self.combo_evaluacion_preg["values"] = ["(Todos)"]
        self.combo_evaluacion_preg.current(0)

        self._preg_cargar_datos_filtrados()

    def _preg_on_area_cambio(self, *args):
        """Se ejecuta cuando cambia el área."""
        grado_sel = self.combo_grado_preg.get()
        grado_val = None if grado_sel == "(Todos)" else grado_sel

        area_sel = self.combo_area_preg.get()
        area_val = None if area_sel == "(Todos)" else area_sel

        df_base = self._preg_obtener_dataframe_base()
        if grado_val:
            df_base = df_base[
                df_base["grado"].astype(str).str.strip().str.lower()
                == str(grado_val).strip().lower()
            ]
        if area_val:
            df_base = df_base[
                df_base["area"].astype(str).str.strip().str.lower()
                == str(area_val).strip().lower()
            ]
        evaluaciones = sorted(
            list(
                dict.fromkeys(
                    [
                        str(v).strip()
                        for v in df_base.get(
                            "evaluacion", pd.Series(dtype=str)
                        ).tolist()
                        if str(v).strip()
                        and str(v).strip().lower() not in ("nan", "none")
                    ]
                )
            )
        )
        self.combo_evaluacion_preg["values"] = ["(Todos)"] + evaluaciones
        self.combo_evaluacion_preg.current(0)

        self._preg_cargar_datos_filtrados()

    def _preg_limpiar_filtros(self):
        """Limpia todos los filtros."""
        self.combo_grado_preg.current(0)
        self.combo_area_preg.current(0)
        self.combo_evaluacion_preg.current(0)
        if hasattr(self, "combo_docente_preg"):
            self.combo_docente_preg.current(0)
        self._preg_cargar_datos_iniciales()

    def _preg_cargar_datos_filtrados(self, *args):
        """Alias ligero para aplicar los filtros.

        Se mantiene para que los *binds* existentes sigan funcionando, pero la
        lógica real está en ``aplicar_filtros``. De esta forma el método puede
        evolucionar sin tocar el resto del código que ya lo invoca.
        """
        self.aplicar_filtros()

    def _preg_actualizar_estadisticas(self):
        """Actualiza las estadísticas mostradas."""
        df_base = self._preg_obtener_dataframe_base()
        stats = {
            "total_preguntas": len(df_base),
            "grados_unicos": len(
                {
                    str(v).strip().lower()
                    for v in df_base.get("grado", pd.Series(dtype=str)).tolist()
                    if str(v).strip() and str(v).strip().lower() not in ("nan", "none")
                }
            ),
            "areas_unicas": len(
                {
                    str(v).strip().lower()
                    for v in df_base.get("area", pd.Series(dtype=str)).tolist()
                    if str(v).strip() and str(v).strip().lower() not in ("nan", "none")
                }
            ),
            "evaluaciones_unicas": len(
                {
                    str(v).strip().lower()
                    for v in df_base.get("evaluacion", pd.Series(dtype=str)).tolist()
                    if str(v).strip() and str(v).strip().lower() not in ("nan", "none")
                }
            ),
            "preguntas_con_imagen": (
                int(
                    (
                        df_base.get("imagen", pd.Series(dtype=str))
                        .astype(str)
                        .str.strip()
                        != ""
                    ).sum()
                )
                if not df_base.empty
                else 0
            ),
        }
        self.lbl_stats.config(
            text=f"Total: {stats['total_preguntas']} | "
            f"Grados: {stats['grados_unicos']} | "
            f"Áreas: {stats['areas_unicas']} | "
            f"Evaluaciones: {stats['evaluaciones_unicas']} | "
            f"Con imagen: {stats['preguntas_con_imagen']}"
        )

    # ========== NUEVA LÓGICA DE FILTRADO ROBUSTA ==========

    def aplicar_filtros(self):
        """Aplica filtros al banco de preguntas con normalizaciones.

        1. Normaliza los datos del Excel (strip + lower) en el DataFrame
           devuelto por el banco.
        2. Normaliza los valores seleccionados en los *combobox*.
        3. Convierte el grado a cadena para evitar comparaciones numéricas.
        4. Limpia y recarga el ``Treeview`` con las filas resultantes.
        5. Si no hay coincidencias muestra un mensaje informativo.

        Este método sustituye a la antigua ``_preg_cargar_datos_filtrados``
        (que ahora sólo hace de envoltorio) y se llama desde todos los
        controladores de eventos.
        """

        df_filtrado = self._preg_obtener_dataframe_filtrado_actual()

        # Limpiar espacios para evitar comparaciones/visualizaciones inconsistentes.
        for col in ("grado", "area", "evaluacion"):
            if col in df_filtrado.columns:
                df_filtrado[col] = df_filtrado[col].astype(str).str.strip()

        # --- repoblar treeview ---
        for iid in self.tree_preg.get_children():
            self.tree_preg.delete(iid)

        if df_filtrado.empty:
            messagebox.showinfo(
                "Filtros",
                "No hay preguntas que coincidan con los criterios seleccionados.",
                parent=self.win,
            )
            self._preg_actualizar_estadisticas()
            return

        for _, row in df_filtrado.iterrows():
            imagen_str = (
                "✓" if row.get("imagen") and str(row.get("imagen")).strip() else ""
            )

            # Obtener id_evaluacion visual
            id_eval = row.get("id_evaluacion", None)
            if id_eval is None or str(id_eval).strip().lower() in (
                "",
                "none",
                "nan",
                "null",
            ):
                id_eval_str = "SIN ID"
            else:
                id_eval_str = str(id_eval)

            valores = (
                row.get("id", ""),
                row.get("evaluacion", ""),
                id_eval_str,
                self._preg_area_canonica(row.get("area", "")),
                row.get("periodo", ""),
                row.get("grado", ""),
                row.get("docente_documento", ""),
                row.get("nombre", ""),
                row.get("fecha_registro", ""),
                row.get("id_contexto", ""),
                row.get("contexto", ""),
                row.get("enunciado", ""),
                row.get("opcion_a", ""),
                row.get("opcion_b", ""),
                row.get("opcion_c", ""),
                row.get("opcion_d", ""),
                row.get("correcta", ""),
                row.get("tipo_pregunta", ""),
                imagen_str,
            )
            item_id = self.tree_preg.insert("", "end", values=valores)
            # Tooltip opcional para id_evaluacion largo (handler global <Motion>)
            if id_eval_str not in ("", "SIN ID"):
                self.tree_preg.set(item_id, "id_evaluacion", id_eval_str)
                # El tooltip se maneja con un solo handler global <Motion> abajo

        # --- Handler global para tooltip de id_evaluacion ---
        def on_tree_motion(event):
            region = self.tree_preg.identify("region", event.x, event.y)
            if region == "cell":
                col = self.tree_preg.identify_column(event.x)
                if col == "#2":  # Asume que la columna 2 es id_evaluacion
                    row_id = self.tree_preg.identify_row(event.y)
                    val = self.tree_preg.set(row_id, "id_evaluacion") if row_id else ""
                    if val and val not in ("", "SIN ID"):
                        self._show_id_eval_tooltip(event, val)
                        return
            self._hide_id_eval_tooltip(event)

        self.tree_preg.bind("<Motion>", on_tree_motion)

    def _preg_obtener_dataframe_filtrado_actual(self):
        def _norm(val):
            if val is None:
                return None
            v = str(val).strip()
            if not v or v == "(Todos)":
                return None
            return v.lower()

        grado_sel = (
            self.combo_grado_preg.get() if hasattr(self, "combo_grado_preg") else None
        )
        area_sel = (
            self.combo_area_preg.get() if hasattr(self, "combo_area_preg") else None
        )
        eval_sel = (
            self.combo_evaluacion_preg.get()
            if hasattr(self, "combo_evaluacion_preg")
            else None
        )

        grado_val = _norm(grado_sel)
        area_val = _norm(area_sel)
        eval_val = _norm(eval_sel)

        if grado_val is not None:
            grado_val = str(grado_val)

        docente_val = None
        if hasattr(self, "combo_docente_preg"):
            docente_sel = self.combo_docente_preg.get().strip()
            if docente_sel and docente_sel != "(Todos)" and "[" in docente_sel:
                docente_val = docente_sel.rsplit("[", 1)[1].rstrip("]").strip()

        df_filtrado = self._preg_obtener_dataframe_base()
        if grado_val is not None:
            df_filtrado = df_filtrado[
                df_filtrado["grado"].astype(str).str.lower().str.strip() == grado_val
            ]
        if area_val is not None:
            df_filtrado = df_filtrado[
                df_filtrado["area"].astype(str).str.lower().str.strip() == area_val
            ]
        if eval_val is not None:
            df_filtrado = df_filtrado[
                df_filtrado["evaluacion"].astype(str).str.lower().str.strip()
                == eval_val
            ]
        if docente_val:
            df_filtrado = df_filtrado[
                df_filtrado.get("docente_documento", pd.Series(dtype=str))
                .astype(str)
                .str.strip()
                == docente_val
            ]
        return df_filtrado.copy()

    # Métodos para tooltip (opcional, seguro)
    def _show_id_eval_tooltip(self, event, value):
        x, y, _, _ = self.tree_preg.bbox(self.tree_preg.focus(), column="id_evaluacion")
        self._id_eval_tooltip = tk.Toplevel(self.tree_preg)
        self._id_eval_tooltip.wm_overrideredirect(True)
        self._id_eval_tooltip.wm_geometry(
            f"+{self.tree_preg.winfo_rootx() + x}+{self.tree_preg.winfo_rooty() + y + 20}"
        )
        label = tk.Label(
            self._id_eval_tooltip,
            text=value,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("Arial", 8),
        )
        label.pack()

    def _hide_id_eval_tooltip(self, event):
        if hasattr(self, "_id_eval_tooltip") and self._id_eval_tooltip:
            self._id_eval_tooltip.destroy()
            self._id_eval_tooltip = None

        self._preg_actualizar_estadisticas()

    def _preg_ordenar_columna(self, col):
        """Ordena el treeview por columna (implementación básica)."""
        pass  # Se puede implementar sorting si es necesario

    def _preg_on_double_click_editar(self, event):
        """Selecciona la fila bajo el cursor y abre el editor de pregunta."""
        iid = self.tree_preg.identify_row(event.y)
        if iid:
            self.tree_preg.selection_set(iid)
            self.tree_preg.focus(iid)
        self.pregunta_editar()

    def _mostrar_menu_contextual(self, event):
        """Muestra un menú contextual con opciones de editar, eliminar y ver detalles."""
        # Seleccionar la fila bajo el cursor
        item = self.tree_preg.selection()
        if item:
            self.tree_preg.selection_set(item)
        else:
            iid = self.tree_preg.identify("item", event.x, event.y)
            if iid:
                self.tree_preg.selection_set(iid)
            else:
                return

        # Crear menú contextual
        menu_contextual = tk.Menu(self.win, tearoff=False)
        menu_contextual.add_command(label="✏️  Editar", command=self.pregunta_editar)
        if bool(getattr(self, "_preg_permitir_eliminar", True)):
            menu_contextual.add_command(
                label="🗑️  Eliminar", command=self.pregunta_eliminar
            )
        menu_contextual.add_separator()
        menu_contextual.add_command(
            label="❌ Cerrar menú", command=menu_contextual.unpost
        )

        # Mostrar el menú en la posición del evento
        try:
            menu_contextual.tk_popup(event.x_root, event.y_root)
        finally:
            menu_contextual.grab_release()

    # ========== MÉTODOS DE OPERACIONES ==========

    def pregunta_editar_evaluacion_filtrada(self):
        """Abre diálogo para editar evaluación completa con bloques dinámicos."""
        grado_sel = (
            self.combo_grado_preg.get()
            if hasattr(self, "combo_grado_preg")
            else "(Todos)"
        )
        area_sel = (
            self.combo_area_preg.get()
            if hasattr(self, "combo_area_preg")
            else "(Todos)"
        )
        eval_sel = (
            self.combo_evaluacion_preg.get()
            if hasattr(self, "combo_evaluacion_preg")
            else "(Todos)"
        )

        if not eval_sel or eval_sel == "(Todos)":
            messagebox.showinfo(
                "Editar evaluación",
                "Seleccione una Evaluación en los filtros.",
                parent=self.win,
            )
            return

        grado_val = None if grado_sel == "(Todos)" else grado_sel
        area_val = None if area_sel == "(Todos)" else area_sel
        eval_val = None if eval_sel == "(Todos)" else eval_sel

        df_objetivo = self._preg_obtener_dataframe_filtrado_actual()
        if df_objetivo.empty:
            messagebox.showinfo(
                "Editar evaluación",
                "No hay preguntas para la evaluación seleccionada.",
                parent=self.win,
            )
            return

        for _, row in df_objetivo.iterrows():
            if not self._preg_puede_modificar_pregunta(row.to_dict(), accion="editar"):
                messagebox.showerror(
                    "Acceso denegado",
                    "La evaluación seleccionada contiene preguntas que no puede modificar.",
                    parent=self.win,
                )
                return

        # Convertir datos a lista de dicts para pasar al diálogo
        preguntas_datos = []
        for _, row in df_objetivo.iterrows():
            preguntas_datos.append(row.to_dict())

        resultado = self._dialog_editar_evaluacion_completa(
            grado=grado_val,
            area=area_val,
            evaluacion=eval_val,
            periodo=str(df_objetivo["periodo"].iloc[0]) if len(df_objetivo) > 0 else "",
            preguntas_existentes=preguntas_datos,
        )

        if resultado:
            self._guardar_evaluacion_editada(resultado, grado_val, area_val, eval_val)

    def _dialog_editar_evaluacion_completa(
        self, grado, area, evaluacion, periodo, preguntas_existentes=None
    ):
        """Diálogo para editar evaluación con bloques dinámicos, igual a agregar."""
        d = tk.Toplevel(self.win)
        d.transient(self.win)
        d.grab_set()
        d.title(f"Editar evaluación: {evaluacion}")
        d.geometry("980x700")

        bloques = []

        # Metadata frame
        frame_meta = ttk.LabelFrame(d, text="Datos de la evaluación", padding=(10, 8))
        frame_meta.pack(fill="x", padx=10, pady=(10, 6))

        ttk.Label(frame_meta, text="Grado:").grid(
            row=0, column=0, sticky="e", padx=6, pady=4
        )
        ttk.Label(frame_meta, text=str(grado or "-"), relief="sunken").grid(
            row=0, column=1, sticky="we", padx=6, pady=4
        )

        ttk.Label(frame_meta, text="Área:").grid(
            row=0, column=2, sticky="e", padx=6, pady=4
        )
        ttk.Label(frame_meta, text=str(area or "-"), relief="sunken").grid(
            row=0, column=3, sticky="we", padx=6, pady=4
        )

        ttk.Label(frame_meta, text="Evaluación:").grid(
            row=1, column=0, sticky="e", padx=6, pady=4
        )
        ttk.Label(frame_meta, text=str(evaluacion or "-"), relief="sunken").grid(
            row=1, column=1, sticky="we", padx=6, pady=4
        )

        ttk.Label(frame_meta, text="Período:").grid(
            row=1, column=2, sticky="e", padx=6, pady=4
        )
        ttk.Label(frame_meta, text=str(periodo or "-"), relief="sunken").grid(
            row=1, column=3, sticky="we", padx=6, pady=4
        )

        frame_meta.columnconfigure(1, weight=1)
        frame_meta.columnconfigure(3, weight=1)

        # Controls frame
        controles = ttk.Frame(d)
        controles.pack(fill="x", padx=10, pady=(0, 6))

        lbl_total = ttk.Label(controles, text="0", font=("Arial", 10, "bold"))
        ttk.Label(controles, text="Preguntas:").pack(side="left", padx=(0, 6))
        lbl_total.pack(side="left", padx=(0, 10))

        # Scroll canvas
        contenedor_scroll = ttk.Frame(d)
        contenedor_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        canvas = tk.Canvas(contenedor_scroll, highlightthickness=0)
        scroll_y = ttk.Scrollbar(
            contenedor_scroll, orient="vertical", command=canvas.yview
        )
        frame_bloques = ttk.Frame(canvas)
        frame_bloques.bind(
            "<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        win_frame = canvas.create_window((0, 0), window=frame_bloques, anchor="nw")
        canvas.bind(
            "<Configure>", lambda e: canvas.itemconfigure(win_frame, width=e.width)
        )
        canvas.configure(yscrollcommand=scroll_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        def _scroll_rueda(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _scroll_rueda)
        d.bind("<MouseWheel>", _scroll_rueda)

        def _renumerar_bloques():
            for idx, bloque in enumerate(bloques, start=1):
                bloque["numero"] = idx
                bloque["titulo_var"].set(f"Pregunta {idx}")
                bloque["frame"].grid(row=idx - 1, column=0, sticky="we", pady=4)
            lbl_total.config(text=str(len(bloques)))

        def _toggle_bloque(bloque):
            if bloque.get("colapsado"):
                bloque["cuerpo"].grid()
                bloque["btn_colapsar"].configure(text="Colapsar")
                bloque["colapsado"] = False
            else:
                bloque["cuerpo"].grid_remove()
                bloque["btn_colapsar"].configure(text="Expandir")
                bloque["colapsado"] = True

        def _eliminar_bloque(bloque):
            try:
                bloque["frame"].destroy()
            except:
                pass
            if bloque in bloques:
                bloques.remove(bloque)
            _renumerar_bloques()

        def _crear_bloque(datos_iniciales=None):
            datos_iniciales = datos_iniciales or {}

            frame = ttk.LabelFrame(frame_bloques)
            frame.grid(column=0, sticky="we", pady=4)
            frame.columnconfigure(0, weight=1)

            encabezado = ttk.Frame(frame)
            encabezado.grid(row=0, column=0, sticky="we", padx=6, pady=(4, 2))
            encabezado.columnconfigure(0, weight=1)

            titulo_var = tk.StringVar(value="Pregunta")
            ttk.Label(encabezado, textvariable=titulo_var).grid(
                row=0, column=0, sticky="w"
            )

            btn_colapsar = ttk.Button(encabezado, text="Colapsar", width=10)
            btn_colapsar.grid(row=0, column=1, sticky="e", padx=(0, 6))

            btn_eliminar = ttk.Button(encabezado, text="Eliminar", width=10)
            btn_eliminar.grid(row=0, column=2, sticky="e")

            cuerpo = ttk.Frame(frame)
            cuerpo.grid(row=1, column=0, sticky="we", padx=6, pady=(0, 6))
            cuerpo.columnconfigure(1, weight=1)

            # Campos
            ttk.Label(cuerpo, text="ID contexto:").grid(
                row=0, column=0, sticky="e", padx=4, pady=2
            )
            en_id_contexto = ttk.Entry(cuerpo)
            en_id_contexto.grid(row=0, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Tipo pregunta:").grid(
                row=1, column=0, sticky="e", padx=4, pady=2
            )
            cb_tipo_pregunta = ttk.Combobox(
                cuerpo,
                state="readonly",
                values=["opcion_multiple", "abierta"],
            )
            cb_tipo_pregunta.grid(row=1, column=1, sticky="w", padx=4, pady=2)

            ttk.Label(cuerpo, text="Contexto:").grid(
                row=2, column=0, sticky="ne", padx=4, pady=2
            )
            txt_contexto = tk.Text(cuerpo, height=3, width=80)
            txt_contexto.grid(row=2, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Enunciado:").grid(
                row=3, column=0, sticky="ne", padx=4, pady=2
            )
            txt_enunciado = tk.Text(cuerpo, height=3, width=80)
            txt_enunciado.grid(row=3, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Opción A:").grid(
                row=4, column=0, sticky="e", padx=4, pady=2
            )
            en_a = ttk.Entry(cuerpo)
            en_a.grid(row=4, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Opción B:").grid(
                row=5, column=0, sticky="e", padx=4, pady=2
            )
            en_b = ttk.Entry(cuerpo)
            en_b.grid(row=5, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Opción C:").grid(
                row=6, column=0, sticky="e", padx=4, pady=2
            )
            en_c = ttk.Entry(cuerpo)
            en_c.grid(row=6, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Opción D:").grid(
                row=7, column=0, sticky="e", padx=4, pady=2
            )
            en_d = ttk.Entry(cuerpo)
            en_d.grid(row=7, column=1, sticky="we", padx=4, pady=2)

            ttk.Label(cuerpo, text="Correcta:").grid(
                row=8, column=0, sticky="e", padx=4, pady=2
            )
            cb_correcta = ttk.Combobox(
                cuerpo, state="readonly", values=["A", "B", "C", "D"]
            )
            cb_correcta.grid(row=8, column=1, sticky="w", padx=4, pady=2)

            # Poblar datos
            en_id_contexto.insert(0, str(datos_iniciales.get("id_contexto", "")))
            tipo_inicial = (
                str(datos_iniciales.get("tipo_pregunta", "opcion_multiple"))
                .strip()
                .lower()
            )
            if tipo_inicial not in ("opcion_multiple", "abierta"):
                tipo_inicial = "opcion_multiple"
            cb_tipo_pregunta.set(tipo_inicial)
            txt_contexto.insert("1.0", str(datos_iniciales.get("contexto", "")))
            txt_enunciado.insert("1.0", str(datos_iniciales.get("enunciado", "")))
            en_a.insert(0, str(datos_iniciales.get("opcion_a", "")))
            en_b.insert(0, str(datos_iniciales.get("opcion_b", "")))
            en_c.insert(0, str(datos_iniciales.get("opcion_c", "")))
            en_d.insert(0, str(datos_iniciales.get("opcion_d", "")))
            if str(datos_iniciales.get("correcta", "")).upper().strip() in (
                "A",
                "B",
                "C",
                "D",
            ):
                cb_correcta.set(
                    str(datos_iniciales.get("correcta", "")).upper().strip()
                )

            bloque = {
                "frame": frame,
                "cuerpo": cuerpo,
                "titulo_var": titulo_var,
                "btn_colapsar": btn_colapsar,
                "numero": len(bloques) + 1,
                "colapsado": False,
                "id_pregunta": str(datos_iniciales.get("id", "")),
                "widgets": {
                    "id_contexto": en_id_contexto,
                    "tipo_pregunta": cb_tipo_pregunta,
                    "contexto": txt_contexto,
                    "enunciado": txt_enunciado,
                    "opcion_a": en_a,
                    "opcion_b": en_b,
                    "opcion_c": en_c,
                    "opcion_d": en_d,
                    "correcta": cb_correcta,
                },
            }

            for _txt in (txt_contexto, txt_enunciado):
                _txt.bind(
                    "<MouseWheel>",
                    lambda e: (
                        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
                        "break",
                    )[1],
                )

            btn_colapsar.configure(command=lambda b=bloque: _toggle_bloque(b))
            btn_eliminar.configure(command=lambda b=bloque: _eliminar_bloque(b))

            bloques.append(bloque)
            _renumerar_bloques()

        def _leer_bloque(bloque):
            w = bloque["widgets"]
            return {
                "id_pregunta": bloque.get("id_pregunta", ""),
                "id_contexto": w["id_contexto"].get().strip(),
                "tipo_pregunta": w["tipo_pregunta"].get().strip().lower()
                or "opcion_multiple",
                "contexto": w["contexto"].get("1.0", "end").strip(),
                "enunciado": w["enunciado"].get("1.0", "end").strip(),
                "opcion_a": w["opcion_a"].get().strip(),
                "opcion_b": w["opcion_b"].get().strip(),
                "opcion_c": w["opcion_c"].get().strip(),
                "opcion_d": w["opcion_d"].get().strip(),
                "correcta": w["correcta"].get().strip().upper(),
            }

        def _anadir_bloque():
            _crear_bloque()

        def _guardar():
            if not bloques:
                messagebox.showerror(
                    "Validación", "Debe tener al menos una pregunta.", parent=d
                )
                return

            preguntas = []
            for idx, bloque in enumerate(bloques, start=1):
                datos_bloque = _leer_bloque(bloque)

                requeridos = ["tipo_pregunta", "enunciado"]
                for campo in requeridos:
                    if not datos_bloque.get(campo):
                        messagebox.showerror(
                            "Validación",
                            f"Pregunta {idx}: campo requerido '{campo}'.",
                            parent=d,
                        )
                        return

                tipo_pregunta = (
                    str(datos_bloque.get("tipo_pregunta", "opcion_multiple"))
                    .strip()
                    .lower()
                )
                if tipo_pregunta not in ("opcion_multiple", "abierta"):
                    messagebox.showerror(
                        "Validación",
                        f"Pregunta {idx}: tipo_pregunta debe ser 'opcion_multiple' o 'abierta'.",
                        parent=d,
                    )
                    return

                datos_bloque["tipo_pregunta"] = tipo_pregunta

                if tipo_pregunta == "opcion_multiple":
                    requeridos_om = [
                        "opcion_a",
                        "opcion_b",
                        "opcion_c",
                        "opcion_d",
                        "correcta",
                    ]
                    for campo in requeridos_om:
                        if not datos_bloque.get(campo):
                            messagebox.showerror(
                                "Validación",
                                f"Pregunta {idx}: campo requerido '{campo}' para opcion_multiple.",
                                parent=d,
                            )
                            return

                    correcta = str(datos_bloque.get("correcta", "")).upper().strip()
                    if correcta not in ("A", "B", "C", "D"):
                        messagebox.showerror(
                            "Validación",
                            f"Pregunta {idx}: la correcta debe ser A, B, C o D.",
                            parent=d,
                        )
                        return
                    datos_bloque["correcta"] = correcta
                else:
                    datos_bloque["opcion_a"] = ""
                    datos_bloque["opcion_b"] = ""
                    datos_bloque["opcion_c"] = ""
                    datos_bloque["opcion_d"] = ""
                    datos_bloque["correcta"] = ""

                preguntas.append(datos_bloque)

            d.result = preguntas
            d.destroy()

        ttk.Button(controles, text="Agregar pregunta", command=_anadir_bloque).pack(
            side="left", padx=(0, 4)
        )

        frame_btns = ttk.Frame(d)
        frame_btns.pack(fill="x", padx=10, pady=(0, 10))

        # Botón Guardar explícito
        ttk.Button(frame_btns, text="💾 Guardar", command=_guardar).pack(
            side="left", padx=(0, 6)
        )
        # Botón Cancelar
        ttk.Button(frame_btns, text="Cancelar", command=d.destroy).pack(side="left")

        # Cargar preguntas existentes
        if preguntas_existentes:
            for preg in preguntas_existentes:
                _crear_bloque(preg)

        d.wait_window()
        return getattr(d, "result", None)

    def _guardar_evaluacion_editada(self, preguntas_editadas, grado, area, evaluacion):
        """Guarda los cambios de la evaluación editada."""
        try:
            # Eliminar todas las preguntas de esta evaluación
            df_eliminar = self._preg_obtener_dataframe_base()
            df_eliminar = df_eliminar[
                df_eliminar.get("grado", pd.Series(dtype=str))
                .astype(str)
                .str.strip()
                .str.lower()
                == str(grado or "").strip().lower()
            ]
            df_eliminar = df_eliminar[
                df_eliminar.get("area", pd.Series(dtype=str))
                .astype(str)
                .str.strip()
                .str.lower()
                == str(area or "").strip().lower()
            ]
            df_eliminar = df_eliminar[
                df_eliminar.get("evaluacion", pd.Series(dtype=str))
                .astype(str)
                .str.strip()
                .str.lower()
                == str(evaluacion or "").strip().lower()
            ]
            for _, row in df_eliminar.iterrows():
                id_preg = str(row.get("id", "")).strip()
                if id_preg:
                    self.banco.eliminar_pregunta(id_preg)

            # Agregar preguntas editadas/nuevas
            for preg_datos in preguntas_editadas:
                id_preg = preg_datos.get("id_pregunta", "")
                datos_guardar = {
                    "id": id_preg,
                    "evaluacion": evaluacion,
                    "area": area,
                    "grado": grado,
                    "id_contexto": preg_datos.get("id_contexto", ""),
                    "contexto": preg_datos.get("contexto", ""),
                    "enunciado": preg_datos.get("enunciado", ""),
                    "opcion_a": preg_datos.get("opcion_a", ""),
                    "opcion_b": preg_datos.get("opcion_b", ""),
                    "opcion_c": preg_datos.get("opcion_c", ""),
                    "opcion_d": preg_datos.get("opcion_d", ""),
                    "correcta": preg_datos.get("correcta", ""),
                    "tipo_pregunta": preg_datos.get("tipo_pregunta", "opcion_multiple"),
                }
                try:
                    datos_guardar = self._preg_enriquecer_datos_guardado(
                        datos_guardar,
                        es_nueva=not id_preg,
                        pregunta_actual=(
                            self.banco.obtener_pregunta_por_id(id_preg)
                            if id_preg
                            else None
                        ),
                    )
                except ValueError as exc:
                    messagebox.showerror("Error", str(exc), parent=self.win)
                    return
                self.banco.guardar_pregunta(
                    id_pregunta=id_preg,
                    datos_pregunta=datos_guardar,
                    es_nueva=not id_preg,
                )

            messagebox.showinfo(
                "Éxito",
                f"Evaluación '{evaluacion}' actualizada exitosamente.",
                parent=self.win,
            )
            self._preg_cargar_datos_iniciales()
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al guardar: {str(e)}", parent=self.win
            )

    def pregunta_agregar(self):
        """Agrega una evaluación completa con una o varias preguntas."""
        payload = self._preg_dialog_agregar_evaluacion_completa()
        if not payload:
            return

        total_guardadas = 0
        for datos in payload:
            try:
                datos = self._preg_enriquecer_datos_guardado(datos, es_nueva=True)
            except ValueError as exc:
                messagebox.showerror("Error", str(exc), parent=self.win)
                return

            exitoso, mensaje = self.banco.guardar_pregunta(
                id_pregunta=datos.get("id"), datos_pregunta=datos, es_nueva=True
            )
            if not exitoso:
                messagebox.showerror("Error", mensaje, parent=self.win)
                return
            total_guardadas += 1

        if total_guardadas:
            messagebox.showinfo(
                "Éxito",
                f"Se agregaron {total_guardadas} preguntas en una sola evaluacion.",
                parent=self.win,
            )
            self._preg_cargar_datos_iniciales()

    def pregunta_editar(self):
        """Edita una pregunta seleccionada."""
        sel = self.tree_preg.selection()
        if not sel:
            messagebox.showinfo("Editar", "Seleccione una pregunta.", parent=self.win)
            return

        id_actual = self.tree_preg.item(sel[0])["values"][0]
        pregunta = self.banco.obtener_pregunta_por_id(id_actual)

        if not pregunta:
            messagebox.showerror(
                "Error", "No se pudo obtener la pregunta.", parent=self.win
            )
            return

        if not self._preg_puede_modificar_pregunta(pregunta, accion="editar"):
            messagebox.showerror(
                "Acceso denegado",
                "No tiene permisos para editar esta pregunta.",
                parent=self.win,
            )
            return

        datos_nuevos = self._dialog_pregunta_mejorado(pregunta)
        if not datos_nuevos:
            return

        try:
            datos_nuevos = self._preg_enriquecer_datos_guardado(
                datos_nuevos, es_nueva=False, pregunta_actual=pregunta
            )
        except ValueError as exc:
            messagebox.showerror("Error", str(exc), parent=self.win)
            return

        exitoso, mensaje = self.banco.guardar_pregunta(
            id_pregunta=id_actual, datos_pregunta=datos_nuevos, es_nueva=False
        )

        if exitoso:
            messagebox.showinfo("Éxito", mensaje, parent=self.win)
            self._preg_cargar_datos_filtrados()
        else:
            messagebox.showerror("Error", mensaje, parent=self.win)

    def pregunta_eliminar(self):
        """Elimina una pregunta seleccionada."""
        sel = self.tree_preg.selection()
        if not sel:
            messagebox.showinfo("Eliminar", "Seleccione una pregunta.", parent=self.win)
            return

        id_pregunta = self.tree_preg.item(sel[0])["values"][0]

        pregunta = self.banco.obtener_pregunta_por_id(id_pregunta)
        if pregunta and not self._preg_puede_modificar_pregunta(
            pregunta, accion="eliminar"
        ):
            messagebox.showerror(
                "Acceso denegado",
                "No tiene permisos para eliminar esta pregunta.",
                parent=self.win,
            )
            return

        if not messagebox.askyesno(
            "Confirmar",
            f"¿Está seguro de eliminar la pregunta ID {id_pregunta}?",
            parent=self.win,
        ):
            return

        exitoso, mensaje = self.banco.eliminar_pregunta(id_pregunta)

        if exitoso:
            messagebox.showinfo("Éxito", mensaje, parent=self.win)
            self._preg_cargar_datos_filtrados()
        else:
            messagebox.showerror("Error", mensaje, parent=self.win)

    def preguntas_importar_avanzado(self):
        """Importa preguntas masivamente con selección obligatoria de área."""
        # 1. Diálogo para seleccionar área
        area_win = tk.Toplevel(self.win)
        area_win.title("Seleccionar Área para Importación")
        area_win.geometry("400x160")
        area_win.transient(self.win)
        area_win.grab_set()

        ttk.Label(
            area_win,
            text="Seleccione el área a asociar a TODAS las preguntas:",
            font=("Arial", 11, "bold"),
        ).pack(pady=(18, 8))

        # Cargar catálogo oficial de áreas desde plan de estudios
        try:
            from core import plan_estudio_web

            catalogo_areas = plan_estudio_web.listar_areas(only_active=True)
            areas = [a["nombre"] for a in catalogo_areas if a.get("nombre")]
        except Exception:
            areas = []
        if not areas:
            messagebox.showerror(
                "Error",
                "No se encontraron áreas en el catálogo oficial (plan de estudios).",
                parent=area_win,
            )
            area_win.destroy()
            return

        area_var = tk.StringVar()
        area_combo = ttk.Combobox(
            area_win, textvariable=area_var, values=areas, state="readonly", width=30
        )
        area_combo.pack(pady=6)

        # Vista previa del área seleccionada
        preview_lbl = ttk.Label(
            area_win, text="", font=("Arial", 10, "italic"), foreground="#0078D7"
        )
        preview_lbl.pack(pady=(2, 0))

        def on_area_change(event=None):
            val = area_var.get()
            preview_lbl.config(text=f"Área seleccionada: {val}" if val else "")

        area_combo.bind("<<ComboboxSelected>>", on_area_change)

        # Botón continuar
        def continuar():
            area_sel = area_var.get()
            if not area_sel:
                messagebox.showwarning(
                    "Área requerida",
                    "Debe seleccionar un área antes de continuar.",
                    parent=area_win,
                )
                return
            # Confirmación
            if not messagebox.askyesno(
                "Confirmar área",
                f"¿Desea importar el archivo y asociar TODAS las preguntas al área: '{area_sel}'?",
                parent=area_win,
            ):
                return
            area_win.grab_release()
            area_win.destroy()
            self._importar_archivo_con_area(area_sel)

        btn = ttk.Button(
            area_win, text="Seleccionar archivo y continuar", command=continuar
        )
        btn.pack(pady=14)

    def _importar_archivo_con_area(self, area_sel):
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo Excel para importar",
            filetypes=[("Excel", "*.xlsx;*.xls")],
            parent=self.win,
        )
        if not archivo:
            return
        # Leer archivo y sobrescribir columna 'area' antes de importar
        try:
            df = pd.read_excel(archivo)
            df["area"] = area_sel  # Sobrescribe área en todas las filas
            # Guardar temporalmente
            temp_path = os.path.join(
                os.path.dirname(archivo), f"__import_temp_{os.path.basename(archivo)}"
            )
            df.to_excel(temp_path, index=False)
            resumen = self.banco.importar_masivo(temp_path)
            os.remove(temp_path)
        except Exception as ex:
            messagebox.showerror(
                "Error de importación",
                f"No se pudo procesar el archivo: {ex}",
                parent=self.win,
            )
            return
        # Mostrar reporte
        reporte = self.banco.generar_reporte_importacion(resumen)
        print(reporte)
        self._mostrar_reporte_importacion(reporte, resumen)
        self._preg_cargar_datos_filtrados()

    def _mostrar_reporte_importacion(self, reporte: str, resumen: dict):
        """Muestra el reporte de importación en un diálogo."""
        d = tk.Toplevel(self.win)
        d.title("Reporte de Importación")
        d.geometry("700x400")

        # Frame con scroll
        canvas = tk.Canvas(d, bg="white")
        scrollbar = ttk.Scrollbar(d, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)

        frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Mostrar reporte con colores
        texto = tk.Text(frame, width=80, height=20, wrap="word", relief="flat")
        texto.pack(fill="both", expand=True, padx=10, pady=10)

        # Insertir texto con estilos
        texto.insert("1.0", reporte)
        texto.config(state="disabled")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Botones
        btn_frame = ttk.Frame(d)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(
            btn_frame, text=f"Importadas: {resumen['exitosas']} ✓", foreground="green"
        ).pack(side="left", padx=5)
        ttk.Label(
            btn_frame,
            text=f"Duplicadas ID: {resumen['duplicadas_id']}",
            foreground="orange",
        ).pack(side="left", padx=5)
        ttk.Label(
            btn_frame,
            text=f"Duplicadas Enunciado: {resumen['duplicadas_enunciado']}",
            foreground="orange",
        ).pack(side="left", padx=5)
        ttk.Label(
            btn_frame,
            text=f"Rechazadas: {resumen['rechazadas_validacion']}",
            foreground="red",
        ).pack(side="left", padx=5)

        ttk.Button(btn_frame, text="Cerrar", command=d.destroy).pack(
            side="right", padx=5
        )

    def preguntas_exportar(self):
        """Exporta las preguntas filtradas a un Excel."""
        archivo = filedialog.asksaveasfilename(
            title="Guardar preguntas como...",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            parent=self.win,
        )

        if not archivo:
            return

        try:
            grado = self.combo_grado_preg.get()
            area = self.combo_area_preg.get()
            evaluacion = self.combo_evaluacion_preg.get()

            grado_val = None if grado == "(Todos)" else grado
            area_val = None if area == "(Todos)" else area
            eval_val = None if evaluacion == "(Todos)" else evaluacion

            df_export = self.banco.obtener_preguntas_filtradas(
                grado=grado_val, area=area_val, evaluacion=eval_val
            )

            columnas_exportacion = [
                "id",
                "grado",
                "area",
                "evaluacion",
                "periodo",
                "id_contexto",
                "contexto",
                "enunciado",
                "tipo_pregunta",
                "opcion_a",
                "opcion_b",
                "opcion_c",
                "opcion_d",
                "correcta",
                "imagen",
            ]
            columnas_presentes = [
                col for col in columnas_exportacion if col in df_export.columns
            ]
            if columnas_presentes:
                df_export = df_export[columnas_presentes]

            df_export.to_excel(archivo, index=False, engine="openpyxl")
            messagebox.showinfo(
                "Éxito",
                f"Exportadas {len(df_export)} preguntas a:\n{archivo}",
                parent=self.win,
            )
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al exportar: {str(e)}", parent=self.win
            )

    def _preg_validar_integridad(self):
        """Valida la integridad del banco de preguntas."""
        advertencias = self.banco.validar_integridad()

        d = tk.Toplevel(self.win)
        d.title("Validación de Integridad")
        d.geometry("600x400")

        canvas = tk.Canvas(d, bg="white")
        scrollbar = ttk.Scrollbar(d, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)

        frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        lineas = []
        if not any(advertencias.values()):
            lineas.append("✓ No se encontraron problemas de integridad")
        else:
            if advertencias["ids_duplicados"]:
                lineas.append(
                    f"⚠ IDs duplicados: {len(advertencias['ids_duplicados'])}"
                )
                for id_dup in advertencias["ids_duplicados"][:10]:
                    lineas.append(f"     - {id_dup}")
            if advertencias["enunciados_duplicados"]:
                lineas.append(
                    f"⚠ Enunciados duplicados: {len(advertencias['enunciados_duplicados'])}"
                )
            if advertencias["campos_vacios"]:
                lineas.append(
                    f"⚠ Campos vacíos encontrados: {len(advertencias['campos_vacios'])}"
                )
                for campo in advertencias["campos_vacios"][:5]:
                    lineas.append(f"     - {campo}")
            if advertencias["opciones_correctas_invalidas"]:
                lineas.append(
                    f"✗ Opciones correctas inválidas: {advertencias['opciones_correctas_invalidas']}"
                )

        texto = tk.Text(frame, width=70, height=20, wrap="word", relief="flat")
        texto.pack(fill="both", expand=True, padx=10, pady=10)
        texto.insert("1.0", "\n".join(lineas))
        texto.config(state="disabled")

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(d, text="Cerrar", command=d.destroy).pack(pady=10)

    def _dialog_pregunta_mejorado(self, inicial=None):
        """Diálogo mejorado para agregar/editar preguntas."""
        d = tk.Toplevel(self.win)
        d.transient(self.win)
        d.grab_set()
        d.title("Pregunta")
        d.geometry("700x600")

        # Canvas con scroll
        canvas = tk.Canvas(d, bg="white")
        scrollbar = ttk.Scrollbar(d, orient="vertical", command=canvas.yview)
        frame_scroll = ttk.Frame(canvas)

        frame_scroll.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame_scroll, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Campos
        campos = [
            ("id", "ID (único)", ttk.Entry),
            ("evaluacion", "Evaluación", ttk.Entry),
            ("area", "Área", ttk.Entry),
            ("periodo", "Período", ttk.Entry),
            ("grado", "Grado", ttk.Entry),
            ("id_contexto", "ID Contexto", ttk.Entry),
            (
                "contexto",
                "Contexto (opcional)",
                lambda p: tk.Text(p, height=3, width=60),
            ),
            ("enunciado", "Enunciado *", lambda p: tk.Text(p, height=4, width=60)),
            (
                "tipo_pregunta",
                "Tipo de Pregunta",
                lambda p: ttk.Combobox(
                    p, values=["opcion_multiple", "abierta"], width=20
                ),
            ),
            ("opcion_a", "Opción A *", ttk.Entry),
            ("opcion_b", "Opción B *", ttk.Entry),
            ("opcion_c", "Opción C *", ttk.Entry),
            ("opcion_d", "Opción D *", ttk.Entry),
            ("correcta", "Correcta (A/B/C/D) *", ttk.Entry),
            ("imagen", "Imagen (ruta o vacío)", ttk.Entry),
        ]

        entries = {}
        for i, (key, label, widget_type) in enumerate(campos):
            ttk.Label(frame_scroll, text=label + ":").grid(
                row=i, column=0, sticky="e", padx=5, pady=5
            )
            if callable(widget_type):
                w = widget_type(frame_scroll)
            else:
                w = widget_type(frame_scroll)
            w.grid(row=i, column=1, sticky="we", padx=5, pady=5)
            entries[key] = w

        # Llenar datos iniciales si existen
        if inicial:
            for key, widget in entries.items():
                valor = inicial.get(key, "")
                if isinstance(widget, tk.Text):
                    widget.insert("1.0", valor)
                elif isinstance(widget, ttk.Combobox):
                    widget.set(valor)
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, valor)

        # Botones
        def on_ok():
            datos = {}
            for key, widget in entries.items():
                if isinstance(widget, tk.Text):
                    datos[key] = widget.get("1.0", "end").strip()
                else:
                    datos[key] = widget.get().strip()
            d.result = datos
            d.destroy()

        btn_frame = ttk.Frame(frame_scroll)
        btn_frame.grid(row=len(campos), column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Guardar", command=on_ok).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=d.destroy).pack(
            side="left", padx=5
        )

        frame_scroll.columnconfigure(1, weight=1)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        d.wait_window()
        return getattr(d, "result", None)


# ========== RECORDATORIO PARA INTEGRACIÓN ==========
"""
En ModuloSuperAdmin.__init__(), reemplaza:
    self._build_preguntas_tab()
por:
    InterfazBancoPreguntasAvanzada._build_preguntas_tab_mejorada(self)

O mejor aún, hereda de ambas clases:
    class ModuloSuperAdmin(InterfazBancoPreguntasAvanzada):
        ...y luego llama a _build_preguntas_tab_mejorada() en lugar de _build_preguntas_tab()
"""
