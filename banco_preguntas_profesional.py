# -*- coding: utf-8 -*-
"""
Modulo Banco de Preguntas Profesional.

Almacenamiento principal: SQLite.
Excel se usa solo para importacion/exportacion explicita.
"""

import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


def _runtime_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _leer_config_sistema(config_path: Path) -> Dict[str, str]:
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


def _resolver_db_path() -> str:
    runtime_dir = _runtime_dir()
    config_path = runtime_dir / "config_sistema"
    config = _leer_config_sistema(config_path)

    modo = str(config.get("modo", "local")).strip().lower()
    ruta_servidor = str(config.get("ruta_servidor", "")).strip().strip('"').strip("'")

    if modo == "red" and ruta_servidor:
        ruta = Path(ruta_servidor)
        if not ruta.is_absolute():
            ruta = (runtime_dir / ruta).resolve()
        if ruta.suffix.lower() == ".db":
            return str(ruta)
        return str(ruta / "sistema.db")

    return str(runtime_dir / "sistema.db")


class BancoPreguntasProfesional:

    AREA_CODIGOS = {
        "matemáticas": "MAT",
        "matematicas": "MAT",
        "lenguaje": "LEN",
        "sociales": "SOC",
        "ciencias": "CIE",
        "ética": "ETI",
        "etica": "ETI",
        # Agrega aquí más áreas según el catálogo real
    }

    TIPOS_PREGUNTA_VALIDOS = ("opcion_multiple", "abierta")
    COLUMNAS_REQUERIDAS = [
        "id",
        "id_evaluacion",
        "evaluacion",
        "area",
        "periodo",
        "grado",
        "id_contexto",
        "contexto",
        "enunciado",
        "opcion_a",
        "opcion_b",
        "opcion_c",
        "opcion_d",
        "correcta",
        "imagen",
        "tipo_pregunta",
        "docente_documento",
        "nombre",
        "fecha_registro",
    ]

    def _normalizar_area_codigo(self, area: str) -> str:
        area_norm = str(area or "").strip().lower()
        return self.AREA_CODIGOS.get(area_norm, area_norm[:3].upper())

    def __init__(self, preguntas_path: str = None, db_path: str = None):
        """Inicializa el gestor.

        Args:
            preguntas_path: Ruta por defecto para operaciones de import/export.
            db_path: Ruta SQLite. Si no se provee, usa config_sistema.
        """
        self.preguntas_path = preguntas_path or os.path.join(
            os.getcwd(), "preguntas.xlsx"
        )
        self.db_path = str(db_path or _resolver_db_path())
        self.df = pd.DataFrame(columns=self.COLUMNAS_REQUERIDAS)

        self._asegurar_tabla()
        self._cargar_preguntas()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _asegurar_tabla(self) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS banco_preguntas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_evaluacion TEXT,
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
                    tipo_pregunta TEXT DEFAULT '',
                    nombre TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

            # Migración: añadir columnas si no existen
            try:
                cur.execute(
                    "ALTER TABLE banco_preguntas ADD COLUMN tipo_pregunta TEXT DEFAULT ''"
                )
                conn.commit()
            except Exception:
                pass  # La columna ya existe
            try:
                cur.execute("ALTER TABLE banco_preguntas ADD COLUMN id_evaluacion TEXT")
                conn.commit()
            except Exception:
                pass  # La columna ya existe
            try:
                cur.execute(
                    "ALTER TABLE banco_preguntas ADD COLUMN docente_documento TEXT DEFAULT ''"
                )
                conn.commit()
            except Exception:
                pass
            try:
                cur.execute("ALTER TABLE banco_preguntas ADD COLUMN nombre TEXT")
                conn.commit()
            except Exception:
                pass
            try:
                cur.execute(
                    "ALTER TABLE banco_preguntas ADD COLUMN fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                )
                conn.commit()
            except Exception:
                pass

    def _normalizar_df(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None:
            df = pd.DataFrame(columns=self.COLUMNAS_REQUERIDAS)
        if df.empty:
            return pd.DataFrame(columns=self.COLUMNAS_REQUERIDAS)

        for col in self.COLUMNAS_REQUERIDAS:
            if col not in df.columns:
                df[col] = ""

        df = df[self.COLUMNAS_REQUERIDAS].copy()

        for col in [
            "evaluacion",
            "area",
            "periodo",
            "grado",
            "id_contexto",
            "contexto",
            "enunciado",
            "opcion_a",
            "opcion_b",
            "opcion_c",
            "opcion_d",
            "correcta",
            "imagen",
            "tipo_pregunta",
            "docente_documento",
            "nombre",
            "fecha_registro",
        ]:
            df[col] = df[col].fillna("").astype(str).str.strip()

        df["grado"] = df["grado"].apply(self._normalizar_grado)

        for col in ["grado", "area", "evaluacion"]:
            df[col] = df[col].str.lower()

        df["id"] = df["id"].fillna("").astype(str).str.strip()
        return df

    def _parse_id(self, id_pregunta: Any) -> Optional[int]:
        texto = str(id_pregunta).strip()
        if not texto:
            return None
        try:
            return int(float(texto))
        except Exception:
            return None

    def _normalizar_grado(self, grado_raw: Any) -> str:
        """Normaliza grado para evitar formatos como 8.0 al mostrar en tabla."""
        texto = str(grado_raw or "").strip()
        if not texto:
            return ""

        try:
            numero = float(texto)
            if numero.is_integer():
                return str(int(numero))
        except Exception:
            pass

        return texto

    def _normalizar_tipo_pregunta(
        self, tipo_raw: Any, fila: Dict[str, Any] = None
    ) -> str:
        tipo = str(tipo_raw or "").strip().lower()

        equivalencias = {
            "opcion_multiple": "opcion_multiple",
            "opcion multiple": "opcion_multiple",
            "seleccion_multiple": "opcion_multiple",
            "seleccion multiple": "opcion_multiple",
            "multiple": "opcion_multiple",
            "cerrada": "opcion_multiple",
            "abierta": "abierta",
            "abierto": "abierta",
            "texto": "abierta",
            "desarrollo": "abierta",
        }
        normalizado = equivalencias.get(tipo, "")
        if normalizado:
            return normalizado

        fila = fila or {}
        opciones = [
            str(fila.get("opcion_a", "")).strip(),
            str(fila.get("opcion_b", "")).strip(),
            str(fila.get("opcion_c", "")).strip(),
            str(fila.get("opcion_d", "")).strip(),
        ]
        correcta = str(fila.get("correcta", "")).strip()

        if not any(opciones) and not correcta:
            return "abierta"
        return "opcion_multiple"

    def _cargar_preguntas(self) -> bool:
        """Carga preguntas desde SQLite a memoria."""
        try:
            query = """
                SELECT
                    id,
                    id_evaluacion,
                    evaluacion,
                    area,
                    periodo,
                    grado,
                    id_contexto,
                    contexto,
                    enunciado,
                    opcion_a,
                    opcion_b,
                    opcion_c,
                    opcion_d,
                    correcta,
                    imagen,
                    tipo_pregunta,
                    docente_documento,
                    nombre,
                    fecha_registro
                FROM banco_preguntas
            """
            with self._connect() as conn:
                df = pd.read_sql_query(query, conn)

            self.df = self._normalizar_df(df)
            return True
        except Exception as e:
            print(f"Error cargando preguntas: {e}")
            self.df = pd.DataFrame(columns=self.COLUMNAS_REQUERIDAS)
            return False

    def guardar_preguntas(self) -> bool:
        """Sincroniza el DataFrame actual con SQLite."""
        try:
            self.df = self._normalizar_df(self.df)

            registros: List[Tuple[Any, ...]] = []
            ids_df: set = set()

            for _, fila in self.df.iterrows():
                id_int = self._parse_id(fila.get("id"))
                if id_int is None:
                    continue
                ids_df.add(id_int)
                registros.append(
                    (
                        id_int,
                        str(fila.get("id_evaluacion", "")).strip(),
                        str(fila.get("evaluacion", "")).strip(),
                        str(fila.get("area", "")).strip(),
                        str(fila.get("periodo", "")).strip(),
                        str(fila.get("grado", "")).strip(),
                        str(fila.get("id_contexto", "")).strip(),
                        str(fila.get("contexto", "")).strip(),
                        str(fila.get("enunciado", "")).strip(),
                        str(fila.get("opcion_a", "")).strip(),
                        str(fila.get("opcion_b", "")).strip(),
                        str(fila.get("opcion_c", "")).strip(),
                        str(fila.get("opcion_d", "")).strip(),
                        str(fila.get("correcta", "")).strip(),
                        str(fila.get("imagen", "")).strip(),
                        str(fila.get("tipo_pregunta", "")).strip(),
                        str(fila.get("docente_documento", "")).strip(),
                        str(fila.get("nombre", "")).strip(),
                        str(fila.get("fecha_registro", "")).strip(),
                    )
                )

            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT id FROM banco_preguntas")
                ids_db = {int(r[0]) for r in cur.fetchall() if r and r[0] is not None}

                sql_upsert = """
                    INSERT INTO banco_preguntas (
                        id, id_evaluacion, evaluacion, area, periodo, grado, id_contexto, contexto,
                        enunciado, opcion_a, opcion_b, opcion_c, opcion_d, correcta, imagen,
                        tipo_pregunta, docente_documento, nombre, fecha_registro
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        id_evaluacion=excluded.id_evaluacion,
                        evaluacion=excluded.evaluacion,
                        area=excluded.area,
                        periodo=excluded.periodo,
                        grado=excluded.grado,
                        id_contexto=excluded.id_contexto,
                        contexto=excluded.contexto,
                        enunciado=excluded.enunciado,
                        opcion_a=excluded.opcion_a,
                        opcion_b=excluded.opcion_b,
                        opcion_c=excluded.opcion_c,
                        opcion_d=excluded.opcion_d,
                        correcta=excluded.correcta,
                        imagen=excluded.imagen,
                        tipo_pregunta=excluded.tipo_pregunta,
                        docente_documento=excluded.docente_documento,
                        nombre=excluded.nombre,
                        fecha_registro=excluded.fecha_registro
                """
                for reg in registros:
                    cur.execute(sql_upsert, reg)

                ids_eliminar = ids_db - ids_df
                if ids_eliminar:
                    placeholders = ",".join(["?"] * len(ids_eliminar))
                    cur.execute(
                        f"DELETE FROM banco_preguntas WHERE id IN ({placeholders})",
                        tuple(ids_eliminar),
                    )

                conn.commit()

            return self._cargar_preguntas()
        except Exception as e:
            print(f"Error guardando preguntas: {e}")
            return False

    def obtener_todas_preguntas(self) -> pd.DataFrame:
        return (
            self.df.copy()
            if self.df is not None
            else pd.DataFrame(columns=self.COLUMNAS_REQUERIDAS)
        )

    def obtener_preguntas_filtradas(
        self,
        grado: str = None,
        area: str = None,
        evaluacion: str = None,
    ) -> pd.DataFrame:
        df = self.obtener_todas_preguntas()

        if grado:
            df = df[
                df["grado"].astype(str).str.lower().str.strip()
                == str(grado).lower().strip()
            ]
        if area:
            df = df[
                df["area"].astype(str).str.lower().str.strip()
                == str(area).lower().strip()
            ]
        if evaluacion:
            df = df[
                df["evaluacion"].astype(str).str.lower().str.strip()
                == str(evaluacion).lower().strip()
            ]

        return df.reset_index(drop=True)

    def obtener_grados_disponibles(self) -> List[str]:
        grados = (
            self.df["grado"]
            .astype(str)
            .str.strip()
            .str.lower()
            .dropna()
            .unique()
            .tolist()
        )
        return sorted([g for g in grados if g and g not in ("nan", "none", "")])

    def obtener_areas_disponibles(self, grado: str = None) -> List[str]:
        df_filtrado = (
            self.obtener_preguntas_filtradas(grado=grado) if grado else self.df
        )
        areas = (
            df_filtrado["area"]
            .astype(str)
            .str.strip()
            .str.lower()
            .dropna()
            .unique()
            .tolist()
        )
        return sorted([a for a in areas if a and a not in ("nan", "none", "")])

    def obtener_evaluaciones_disponibles(
        self, grado: str = None, area: str = None
    ) -> List[str]:
        df_filtrado = self.obtener_preguntas_filtradas(grado=grado, area=area)
        evals = (
            df_filtrado["evaluacion"]
            .astype(str)
            .str.strip()
            .str.lower()
            .dropna()
            .unique()
            .tolist()
        )
        return sorted([e for e in evals if e and e not in ("nan", "none", "")])

    def obtener_pregunta_por_id(self, id_pregunta) -> Optional[Dict[str, Any]]:
        try:
            filas = self.df[self.df["id"].astype(str) == str(id_pregunta).strip()]
            if filas.empty:
                return None
            return filas.iloc[0].to_dict()
        except Exception:
            return None

    def id_existe(self, id_pregunta) -> bool:
        try:
            return bool(
                len(self.df[self.df["id"].astype(str) == str(id_pregunta).strip()]) > 0
            )
        except Exception:
            return False

    def enunciado_existe(self, enunciado: str, excluir_id: str = None) -> bool:
        try:
            enun_norm = str(enunciado).strip().lower()
            df_busqueda = self.df[
                self.df["enunciado"].astype(str).str.lower().str.strip() == enun_norm
            ]
            if excluir_id is not None:
                df_busqueda = df_busqueda[
                    df_busqueda["id"].astype(str) != str(excluir_id).strip()
                ]
            return len(df_busqueda) > 0
        except Exception:
            return False

    def guardar_pregunta(
        self, id_pregunta: str, datos_pregunta: Dict[str, str], es_nueva: bool = False
    ) -> Tuple[bool, str]:
        try:
            tipo = str(datos_pregunta.get("tipo_pregunta", "")).strip().lower()
            tipo_normalizado = self._normalizar_tipo_pregunta(tipo, datos_pregunta)
            if tipo and tipo_normalizado not in self.TIPOS_PREGUNTA_VALIDOS:
                return False, "Tipo de pregunta invalido"

            es_abierta = tipo_normalizado == "abierta"

            campos_basicos = ["id", "evaluacion", "area", "enunciado"]
            campos_mc = ["opcion_a", "opcion_b", "opcion_c", "opcion_d", "correcta"]
            campos_requeridos = campos_basicos + ([] if es_abierta else campos_mc)
            for campo in campos_requeridos:
                if not str(datos_pregunta.get(campo, "")).strip():
                    return False, f"Campo requerido vacio: {campo}"

            id_nuevo = str(datos_pregunta.get("id", "")).strip()
            if self._parse_id(id_nuevo) is None:
                return False, "El ID debe ser numerico"

            if es_nueva:
                if self.id_existe(id_nuevo):
                    return False, f"El ID '{id_nuevo}' ya existe"
            else:
                if str(id_pregunta).strip() != id_nuevo and self.id_existe(id_nuevo):
                    return False, f"El ID '{id_nuevo}' ya existe"

            if self.enunciado_existe(
                datos_pregunta.get("enunciado", ""),
                excluir_id=id_pregunta if not es_nueva else None,
            ):
                return False, "Este enunciado ya existe en el banco"

            correcta = str(datos_pregunta.get("correcta", "")).upper().strip()
            if correcta not in ["A", "B", "C", "D"]:
                if not es_abierta:
                    return False, "La opcion correcta debe ser A, B, C o D"

            fila = {
                col: str(datos_pregunta.get(col, "")).strip()
                for col in self.COLUMNAS_REQUERIDAS
            }
            fila["tipo_pregunta"] = tipo_normalizado

            existente = (
                self.obtener_pregunta_por_id(id_pregunta) if not es_nueva else None
            )
            if existente:
                if not fila.get("docente_documento"):
                    fila["docente_documento"] = str(
                        existente.get("docente_documento", "")
                    ).strip()
                if not fila.get("nombre"):
                    fila["nombre"] = str(existente.get("nombre", "")).strip()
                if not fila.get("fecha_registro"):
                    fila["fecha_registro"] = str(
                        existente.get("fecha_registro", "")
                    ).strip()

            if not fila.get("fecha_registro"):
                fila["fecha_registro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if es_nueva:
                self.df = pd.concat([self.df, pd.DataFrame([fila])], ignore_index=True)
            else:
                idx = self.df[
                    self.df["id"].astype(str) == str(id_pregunta).strip()
                ].index.tolist()
                if not idx:
                    return False, f"Pregunta con ID '{id_pregunta}' no encontrada"
                for col, valor in fila.items():
                    self.df.at[idx[0], col] = valor

            if self.guardar_preguntas():
                return True, "Pregunta guardada exitosamente"
            return False, "Error al guardar en base de datos"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def actualizar_preguntas_filtradas(
        self,
        grado: str = None,
        area: str = None,
        evaluacion: str = None,
        cambios: Dict[str, str] = None,
        solo_contexto_vacio: bool = False,
    ) -> Tuple[bool, str, int]:
        """Actualiza de forma masiva preguntas que coinciden con filtros.

        Solo permite modificar campos de metadatos de la evaluación.
        """
        try:
            cambios = cambios or {}
            permitidos = [
                "evaluacion",
                "area",
                "periodo",
                "grado",
                "id_contexto",
                "contexto",
            ]

            cambios_norm = {}
            for campo in permitidos:
                if campo not in cambios:
                    continue
                valor = str(cambios.get(campo, "")).strip()
                if not valor:
                    continue
                if campo in ["evaluacion", "area"] and not valor:
                    return False, f"El campo {campo} no puede quedar vacío", 0
                if campo == "grado":
                    valor = self._normalizar_grado(valor)
                if campo in ["grado", "area", "evaluacion"]:
                    valor = valor.lower()
                cambios_norm[campo] = valor

            if not cambios_norm:
                return False, "No hay cambios para aplicar", 0

            def _norm_filtro(valor: str) -> Optional[str]:
                txt = str(valor or "").strip()
                return txt.lower() if txt else None

            grado_val = _norm_filtro(grado)
            area_val = _norm_filtro(area)
            eval_val = _norm_filtro(evaluacion)

            mask = pd.Series(True, index=self.df.index)
            if grado_val:
                mask &= (
                    self.df["grado"].astype(str).str.strip().str.lower() == grado_val
                )
            if area_val:
                mask &= self.df["area"].astype(str).str.strip().str.lower() == area_val
            if eval_val:
                mask &= (
                    self.df["evaluacion"].astype(str).str.strip().str.lower()
                    == eval_val
                )

            total_objetivo = int(mask.sum())
            if total_objetivo == 0:
                return False, "No hay preguntas para actualizar con esos filtros", 0

            for campo, valor in cambios_norm.items():
                if campo == "contexto" and solo_contexto_vacio:
                    mask_contexto = mask & (
                        self.df["contexto"].astype(str).str.strip() == ""
                    )
                    self.df.loc[mask_contexto, campo] = valor
                else:
                    self.df.loc[mask, campo] = valor

            if self.guardar_preguntas():
                return True, "Actualización masiva aplicada", total_objetivo
            return False, "No se pudo guardar la actualización masiva", 0
        except Exception as e:
            return False, f"Error en actualización masiva: {str(e)}", 0

    def eliminar_pregunta(self, id_pregunta: str) -> Tuple[bool, str]:
        try:
            if not self.id_existe(id_pregunta):
                return False, f"Pregunta con ID '{id_pregunta}' no encontrada"

            self.df = self.df[self.df["id"].astype(str) != str(id_pregunta).strip()]
            self.df = self.df.reset_index(drop=True)

            if self.guardar_preguntas():
                return True, "Pregunta eliminada exitosamente"
            return False, "Error al guardar en base de datos"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def importar_masivo(
        self, archivo_importacion: str, permitir_duplicados_id: bool = False
    ) -> Dict[str, Any]:
        resumen = {
            "exitosas": 0,
            "duplicadas_id": 0,
            "duplicadas_enunciado": 0,
            "rechazadas_validacion": 0,
            "total_procesadas": 0,
            "detalles": [],
        }

        try:
            if not os.path.exists(archivo_importacion):
                resumen["detalles"].append(
                    f"ERROR: Archivo no encontrado: {archivo_importacion}"
                )
                return resumen

            df_importar = pd.read_excel(archivo_importacion)
            if df_importar.empty:
                resumen["detalles"].append(
                    "ERROR: El archivo de importacion esta vacio"
                )
                return resumen

            df_importar.columns = df_importar.columns.str.strip().str.lower()

            # La columna "id" no es obligatoria: se ignora si existe
            columnas_criticas = ["evaluacion", "area", "enunciado"]
            faltantes = [c for c in columnas_criticas if c not in df_importar.columns]
            if faltantes:
                resumen["detalles"].append(
                    f"ERROR: Columnas faltantes: {', '.join(faltantes)}"
                )
                return resumen

            # Calcular el siguiente ID disponible (mayor existente + 1)
            ids_existentes = []
            if not self.df.empty and "id" in self.df.columns:
                for v in self.df["id"]:
                    parsed = self._parse_id(v)
                    if parsed is not None:
                        ids_existentes.append(parsed)
            next_id = (max(ids_existentes) + 1) if ids_existentes else 1

            # --- Generación automática de id_evaluacion por grupo ---
            def generar_id_evaluacion(evaluacion, area, periodo, grado, contador):
                fecha = datetime.now().strftime("%Y%m%d")
                base = f"EVAL-{fecha}-{str(evaluacion).strip().upper()}-{str(area).strip().upper()}-{str(periodo).strip().upper()}-{str(grado).strip().upper()}"
                return f"{base}-{contador:03d}"

            # Agrupar filas por (evaluacion, area, periodo, grado)
            # Agrupar por (area, grado, periodo, evaluacion) y generar id_evaluacion correcto
            grupos = {}
            for idx, fila in df_importar.iterrows():
                area_cod = self._normalizar_area_codigo(fila.get("area", ""))
                grado = str(fila.get("grado", "")).strip().upper()
                periodo = str(fila.get("periodo", "")).strip().upper()
                evaluacion = str(fila.get("evaluacion", "")).strip().upper()
                key = (area_cod, grado, periodo, evaluacion)
                if key not in grupos:
                    grupos[key] = []
                grupos[key].append(idx)

            id_evaluacion_por_grupo = {}
            # Conexión directa para consulta de consecutivo
            with self._connect() as conn:
                cur = conn.cursor()
                for key, indices in grupos.items():
                    area_cod, grado, periodo, evaluacion = key
                    # Buscar si ya existe un id_evaluacion para este grupo
                    cur.execute(
                        "SELECT id_evaluacion FROM banco_preguntas WHERE area=? AND grado=? AND periodo=? AND evaluacion=? AND id_evaluacion IS NOT NULL AND id_evaluacion != '' ORDER BY id_evaluacion DESC LIMIT 1",
                        (area_cod, grado, periodo, evaluacion),
                    )
                    row = cur.fetchone()
                    if row and row[0]:
                        id_eval = row[0]
                    else:
                        # Buscar último consecutivo para el grupo área-grado-periodo
                        cur.execute(
                            "SELECT id_evaluacion FROM banco_preguntas WHERE area=? AND grado=? AND periodo=? AND id_evaluacion IS NOT NULL AND id_evaluacion != '' ORDER BY id_evaluacion DESC LIMIT 1",
                            (area_cod, grado, periodo),
                        )
                        last = cur.fetchone()
                        if last and last[0]:
                            import re

                            m = re.match(
                                rf"^{area_cod}-{grado}-P{periodo}-E(\d{{2}})$", last[0]
                            )
                            n = int(m.group(1)) + 1 if m else 1
                        else:
                            n = 1
                        id_eval = f"{area_cod}-{grado}-P{periodo}-E{n:02d}"
                    # Validar formato
                    import re

                    if not re.match(r"^[A-Z]{3}-\d+-P\d+-E\d{2}$", id_eval):
                        id_eval = "SIN ID"
                    for idx in indices:
                        id_evaluacion_por_grupo[idx] = id_eval

            for idx, fila in df_importar.iterrows():
                resumen["total_procesadas"] += 1

                # Asignar ID automático, ignorando el que venga en el Excel
                id_pregunta = str(next_id)
                next_id += 1

                enunciado = str(fila.get("enunciado", "")).strip()
                if self.enunciado_existe(enunciado):
                    resumen["duplicadas_enunciado"] += 1
                    resumen["detalles"].append(f"Fila {idx + 2}: Enunciado duplicado")
                    next_id -= 1  # liberar el ID reservado
                    continue

                tipo_pregunta = self._normalizar_tipo_pregunta(
                    fila.get("tipo_pregunta", ""), fila
                )
                es_abierta = tipo_pregunta == "abierta"

                campos_requeridos = ["evaluacion", "area", "enunciado"]
                if not es_abierta:
                    campos_requeridos.extend(
                        ["opcion_a", "opcion_b", "opcion_c", "opcion_d", "correcta"]
                    )
                vacios = [
                    c for c in campos_requeridos if not str(fila.get(c, "")).strip()
                ]
                if vacios:
                    resumen["rechazadas_validacion"] += 1
                    resumen["detalles"].append(
                        f"Fila {idx + 2}: Campos vacios: {', '.join(vacios)}"
                    )
                    next_id -= 1  # liberar el ID reservado
                    continue

                correcta = str(fila.get("correcta", "")).upper().strip()
                if not es_abierta and correcta not in ["A", "B", "C", "D"]:
                    resumen["rechazadas_validacion"] += 1
                    resumen["detalles"].append(
                        f"Fila {idx + 2}: Opcion correcta invalida '{correcta}'"
                    )
                    next_id -= 1  # liberar el ID reservado
                    continue

                datos_insert = {
                    col: str(fila.get(col, "")).strip()
                    for col in self.COLUMNAS_REQUERIDAS
                }
                datos_insert["id"] = id_pregunta
                datos_insert["tipo_pregunta"] = tipo_pregunta
                # Asignar id_evaluacion automático
                datos_insert["id_evaluacion"] = id_evaluacion_por_grupo.get(
                    idx, "SIN ID"
                )
                self.df = pd.concat(
                    [self.df, pd.DataFrame([datos_insert])], ignore_index=True
                )

                resumen["exitosas"] += 1
                resumen["detalles"].append(
                    f"Fila {idx + 2}: Importada exitosamente (ID: {id_pregunta}, ID_EVAL: {datos_insert['id_evaluacion']})"
                )

            if resumen["exitosas"] > 0:
                self.guardar_preguntas()
                self._cargar_preguntas()  # Forzar recarga para reflejar todos los cambios

            return resumen
        except Exception as e:
            resumen["detalles"].append(f"ERROR GENERAL: {str(e)}")
            return resumen

    def generar_reporte_importacion(self, resumen: Dict[str, Any]) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lineas = [
            "=" * 60,
            f"REPORTE DE IMPORTACION - {timestamp}",
            "=" * 60,
            "",
            f"Total procesadas: {resumen['total_procesadas']}",
            f"  OK Importadas exitosamente: {resumen['exitosas']}",
            f"  WARN Duplicadas por ID: {resumen['duplicadas_id']}",
            f"  WARN Duplicadas por enunciado: {resumen['duplicadas_enunciado']}",
            f"  ERR Rechazadas por validacion: {resumen['rechazadas_validacion']}",
            "",
            "DETALLES:",
            "-" * 60,
        ]

        for detalle in resumen.get("detalles", [])[:50]:
            lineas.append(f"  - {detalle}")

        if len(resumen.get("detalles", [])) > 50:
            lineas.append(f"  ... y {len(resumen['detalles']) - 50} registros mas ...")

        lineas.extend(["", "=" * 60])
        return "\n".join(lineas)

    def obtener_estadisticas(self) -> Dict[str, Any]:
        df = (
            self.df
            if self.df is not None
            else pd.DataFrame(columns=self.COLUMNAS_REQUERIDAS)
        )
        if df.empty:
            return {
                "total_preguntas": 0,
                "grados_unicos": 0,
                "areas_unicas": 0,
                "evaluaciones_unicas": 0,
                "preguntas_sin_imagen": 0,
                "preguntas_con_imagen": 0,
            }

        return {
            "total_preguntas": len(df),
            "grados_unicos": len(self.obtener_grados_disponibles()),
            "areas_unicas": len(self.obtener_areas_disponibles()),
            "evaluaciones_unicas": len(self.obtener_evaluaciones_disponibles()),
            "preguntas_sin_imagen": len(df[df["imagen"].isna() | (df["imagen"] == "")]),
            "preguntas_con_imagen": len(
                df[df["imagen"].notna() & (df["imagen"] != "")]
            ),
        }

    def validar_integridad(self) -> Dict[str, List[str]]:
        advertencias = {
            "ids_duplicados": [],
            "enunciados_duplicados": [],
            "campos_vacios": [],
            "opciones_correctas_invalidas": [],
        }

        df = (
            self.df
            if self.df is not None
            else pd.DataFrame(columns=self.COLUMNAS_REQUERIDAS)
        )
        if df.empty:
            return advertencias

        ids_duplicados = df[df.duplicated(subset=["id"], keep=False)]["id"].tolist()
        if ids_duplicados:
            advertencias["ids_duplicados"] = list(set(ids_duplicados))

        enunciados_dup = df[df.duplicated(subset=["enunciado"], keep=False)][
            "enunciado"
        ].tolist()
        if enunciados_dup:
            advertencias["enunciados_duplicados"] = list(set(enunciados_dup))

        campos_basicos = ["id", "evaluacion", "area", "enunciado"]
        for col in campos_basicos:
            filas_vacias = df[
                df[col].isna() | (df[col].astype(str).str.strip() == "")
            ].index.tolist()
            if filas_vacias:
                advertencias["campos_vacios"].append(f"{col}: filas {filas_vacias}")

        if "tipo_pregunta" in df.columns:
            tipos_normalizados = df.apply(
                lambda row: self._normalizar_tipo_pregunta(
                    row.get("tipo_pregunta", ""), row.to_dict()
                ),
                axis=1,
            )
        else:
            tipos_normalizados = pd.Series(
                ["opcion_multiple"] * len(df), index=df.index
            )

        columnas_opciones = ["opcion_a", "opcion_b", "opcion_c", "opcion_d", "correcta"]
        for col in columnas_opciones:
            filas_vacias = df[
                (tipos_normalizados != "abierta")
                & (df[col].isna() | (df[col].astype(str).str.strip() == ""))
            ].index.tolist()
            if filas_vacias:
                advertencias["campos_vacios"].append(f"{col}: filas {filas_vacias}")

        correctas_invalidas = df[
            (tipos_normalizados != "abierta")
            & (~df["correcta"].astype(str).str.upper().isin(["A", "B", "C", "D"]))
        ]["correcta"].tolist()
        if correctas_invalidas:
            advertencias["opciones_correctas_invalidas"] = list(
                set(correctas_invalidas)
            )

        return advertencias


# ======== FUNCIONES STANDALONE ========


def cargar_preguntas_desde_excel(path: str = None, db_path: str = None) -> pd.DataFrame:
    """Compatibilidad: carga preguntas desde SQLite."""
    banco = BancoPreguntasProfesional(path, db_path=db_path)
    return banco.obtener_todas_preguntas()


def guardar_cambios_excel(
    df: pd.DataFrame, path: str = None, db_path: str = None
) -> bool:
    """Compatibilidad: guarda cambios en SQLite."""
    banco = BancoPreguntasProfesional(path, db_path=db_path)
    banco.df = df
    return banco.guardar_preguntas()


def eliminar_pregunta(
    id_pregunta: str, path: str = None, db_path: str = None
) -> Tuple[bool, str]:
    banco = BancoPreguntasProfesional(path, db_path=db_path)
    return banco.eliminar_pregunta(id_pregunta)


def importar_preguntas_masivo(
    archivo_importacion: str, path: str = None, db_path: str = None
) -> Dict[str, Any]:
    banco = BancoPreguntasProfesional(path, db_path=db_path)
    return banco.importar_masivo(archivo_importacion)


if __name__ == "__main__":
    banco = BancoPreguntasProfesional()
    print("Estadisticas:", banco.obtener_estadisticas())
    print("Grados:", banco.obtener_grados_disponibles())
