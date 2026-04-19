from __future__ import annotations

import random
import zipfile
from datetime import datetime
from pathlib import Path

from banco_preguntas_profesional import BancoPreguntasProfesional
from multi_area_exam_pdf import write_multi_area_exam_pdf

from . import examenes_generacion as core_examenes_generacion
from . import matricula as core_matricula
from . import preguntas as core_preguntas
from .construir_nombre import construir_nombre


def catalogos_multi_area(grado=None, curso=None):
    grado_txt = str(grado or "").strip()
    curso_txt = str(curso or "").strip() or None
    if not grado_txt:
        return {"cursos": [], "areas": [], "estudiantes": []}

    cursos = core_matricula.listar_cursos_distintos(grado_txt)
    estudiantes = core_matricula.listar_estudiantes_por_grado(
        grado_txt,
        curso=curso_txt,
        solo_activos=False,
    )
    estudiantes_out = []
    for estudiante in estudiantes:
        documento = str(estudiante.get("documento") or "").strip()
        nombre = (
            construir_nombre(estudiante) or str(estudiante.get("nombre") or "").strip()
        )
        estudiantes_out.append(
            {
                "documento": documento,
                "nombre": nombre,
                "curso": str(estudiante.get("curso") or "").strip(),
                "label": f"{nombre} ({documento})" if documento else nombre,
            }
        )

    return {
        "cursos": cursos,
        "areas": core_preguntas.cargar_areas_por_grado(grado_txt),
        "estudiantes": estudiantes_out,
        "total_estudiantes": len(estudiantes_out),
    }


def disponibilidad_multi_area(grado=None, area=None, evaluacion=None):
    grado_txt = str(grado or "").strip()
    area_txt = str(area or "").strip().lower()
    evaluacion_txt = str(evaluacion or "").strip().lower()
    if not grado_txt:
        raise ValueError("grado_requerido")
    if not area_txt:
        raise ValueError("area_requerida")

    banco = BancoPreguntasProfesional()
    filtros = {"grado": grado_txt, "area": area_txt}
    if evaluacion_txt:
        filtros["evaluacion"] = evaluacion_txt
    df = banco.obtener_preguntas_filtradas(**filtros)
    textos = 0
    if not df.empty and "contexto" in df.columns:
        try:
            textos = int(
                df["contexto"]
                .fillna("")
                .astype(str)
                .str.strip()
                .replace("", None)
                .dropna()
                .nunique()
            )
        except Exception:
            textos = int(df["contexto"].nunique())
    return {
        "preguntas": int(len(df)),
        "textos": int(textos),
    }


def _seleccionar_preguntas_multi_area(banco, grado, area, evaluacion, cantidad):
    df = banco.obtener_preguntas_filtradas(
        grado=grado,
        area=area,
        evaluacion=evaluacion,
    )
    if len(df) < cantidad:
        df_area = banco.obtener_preguntas_filtradas(grado=grado, area=area)
        df_area_sola = banco.obtener_preguntas_filtradas(area=area)
        if len(df_area) > 0:
            raise ValueError(
                f"No hay suficientes preguntas para el area '{area}' y evaluacion '{evaluacion}'. "
                f"Disponibles para el area en este grado: {len(df_area)}."
            )
        if len(df_area_sola) > 0:
            raise ValueError(
                f"No hay preguntas para el area '{area}' en el grado y evaluacion seleccionados. "
                f"Pero existen {len(df_area_sola)} preguntas para esa area en otros grados o evaluaciones."
            )
        raise ValueError(f"No hay preguntas registradas para el area '{area}'.")
    return df.sample(n=cantidad, random_state=random.randint(1, 99999))


def _normalizar_estudiante(estudiante, grado, curso):
    if estudiante is None:
        return {
            "apellido1": "",
            "apellido2": "",
            "nombre1": "",
            "nombre2": "",
            "documento": "",
            "grado": grado,
            "curso": curso or "",
        }

    data = dict(estudiante)
    data.setdefault("apellido1", "")
    data.setdefault("apellido2", "")
    data.setdefault("nombre1", "")
    data.setdefault("nombre2", "")
    data.setdefault("documento", "")
    data.setdefault("grado", grado)
    data.setdefault("curso", curso or "")
    return data


def _safe_name(value, fallback):
    txt = str(value or "").strip()
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in txt)
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned or fallback


def generar_cuadernillo_multi_area(
    *,
    grado,
    curso=None,
    modo_generacion="individual",
    estudiante_documento=None,
    configuraciones_areas=None,
    output_dir=None,
):
    grado_txt = str(grado or "").strip()
    curso_txt = str(curso or "").strip() or None
    modo_txt = str(modo_generacion or "individual").strip().lower()
    if not grado_txt:
        raise ValueError("grado_requerido")
    if modo_txt not in {"individual", "todos", "todos_un_pdf"}:
        raise ValueError("modo_generacion_invalido")

    configuraciones = []
    for item in configuraciones_areas or []:
        area = str((item or {}).get("area") or "").strip().lower()
        evaluacion = str((item or {}).get("evaluacion") or "").strip().lower()
        try:
            cantidad = int((item or {}).get("cantidad_preguntas") or 0)
        except Exception:
            cantidad = 0
        if area and evaluacion and cantidad > 0:
            configuraciones.append(
                {
                    "area": area,
                    "evaluacion": evaluacion,
                    "cantidad_preguntas": cantidad,
                }
            )

    if not configuraciones:
        raise ValueError("areas_requeridas")

    if modo_txt == "individual":
        documento = str(estudiante_documento or "").strip()
        if not documento:
            raise ValueError("estudiante_documento_requerido")
        estudiante = core_matricula.buscar_estudiante(documento)
        if not estudiante:
            raise ValueError("estudiante_no_encontrado")
        estudiantes = [estudiante]
    else:
        estudiantes = core_matricula.listar_estudiantes_por_grado(
            grado_txt,
            curso=curso_txt,
            solo_activos=False,
        )
        if not estudiantes:
            raise ValueError("no_hay_estudiantes_para_filtro")

    banco = BancoPreguntasProfesional()
    evaluaciones_por_area = {
        item["area"]: item["evaluacion"] for item in configuraciones
    }
    preguntas_por_area = {
        item["area"]: item["cantidad_preguntas"] for item in configuraciones
    }
    areas_preguntas_dict = {
        item["area"]: _seleccionar_preguntas_multi_area(
            banco,
            grado_txt,
            item["area"],
            item["evaluacion"],
            item["cantidad_preguntas"],
        )
        for item in configuraciones
    }

    target_dir = Path(output_dir or Path.cwd()).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_paths = []

    for idx, estudiante in enumerate(estudiantes, start=1):
        estudiante_norm = _normalizar_estudiante(estudiante, grado_txt, curso_txt)
        nombre = _safe_name(construir_nombre(estudiante_norm), f"estudiante_{idx}")
        documento = _safe_name(estudiante_norm.get("documento"), f"doc_{idx}")
        pdf_path = (
            target_dir / f"cuadernillo_multi_area_{stamp}_{nombre}_{documento}.pdf"
        )
        evaluacion_pdf = " / ".join(
            f"{area}: {evaluacion}"
            for area, evaluacion in evaluaciones_por_area.items()
            if str(evaluacion).strip()
        )
        write_multi_area_exam_pdf(
            areas_preguntas_dict=areas_preguntas_dict,
            estudiante=estudiante_norm,
            path=str(pdf_path),
            evaluacion=evaluacion_pdf,
            version="A",
            config_numeracion="por_area",
            preguntas_por_area=preguntas_por_area,
            instrucciones_generales=None,
        )
        pdf_paths.append(pdf_path)

    if modo_txt == "individual":
        path = pdf_paths[0]
        return {"tipo": "pdf", "path": path, "filename": path.name}

    if modo_txt == "todos_un_pdf":
        merged = target_dir / f"cuadernillo_multi_area_consolidado_{stamp}.pdf"
        core_examenes_generacion.unir_pdfs(
            [str(path) for path in pdf_paths], str(merged)
        )
        return {"tipo": "pdf", "path": merged, "filename": merged.name}

    zip_path = target_dir / f"cuadernillos_multi_area_{stamp}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for path in pdf_paths:
            zip_file.write(path, arcname=path.name)
    return {"tipo": "zip", "path": zip_path, "filename": zip_path.name}
