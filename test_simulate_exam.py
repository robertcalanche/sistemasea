import sqlite3
from pathlib import Path
from datetime import datetime
import json

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "sistema.db"

print("Usando BD en:", DB_FILE)

with sqlite3.connect(DB_FILE) as conn:
    cur = conn.cursor()
    # Insertar intento EN_PROCESO
    hora_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO resultados (documento, nombre, grado, area, nota, estado_examen, hora_inicio, hora_fin, intento) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "999",
            "Alumno Prueba",
            "1",
            "Prueba",
            None,
            "EN_PROCESO",
            hora_inicio,
            None,
            1,
        ),
    )
    intento_id = cur.lastrowid
    print("Inserted resultados id:", intento_id)

    # Construir respuestas detalladas
    respuestas = [
        {
            "pregunta_id": 0,
            "enunciado": "¿2+2?",
            "imagen": None,
            "grado": "1",
            "area": "Prueba",
            "respuesta_dada": "A",
            "respuesta_correcta": "A",
            "correcta": True,
        },
        {
            "pregunta_id": 1,
            "enunciado": "¿3+3?",
            "imagen": None,
            "grado": "1",
            "area": "Prueba",
            "respuesta_dada": "B",
            "respuesta_correcta": "C",
            "correcta": False,
        },
    ]

    # Insertar en respuestas_estudiantes
    for r in respuestas:
        pregunta_id = r.get("pregunta_id")
        enun = r.get("enunciado")
        resp_sel = r.get("respuesta_dada")
        resp_corr = r.get("respuesta_correcta")
        es_corr = 1 if r.get("correcta") else 0
        # evitar duplicados segun UNIQUE
        cur.execute(
            "SELECT id FROM respuestas_estudiantes WHERE documento = ? AND area = ? AND intento = ? AND pregunta_id = ?",
            ("999", "Prueba", 1, pregunta_id),
        )
        if cur.fetchone():
            print("Ya existe respuesta para pregunta", pregunta_id)
        else:
            cur.execute(
                "INSERT INTO respuestas_estudiantes (documento, nombre, grado, area, intento, pregunta_id, enunciado, respuesta_seleccionada, respuesta_correcta, es_correcta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "999",
                    "Alumno Prueba",
                    "1",
                    "Prueba",
                    1,
                    pregunta_id,
                    enun,
                    resp_sel,
                    resp_corr,
                    es_corr,
                ),
            )
            print("Inserted respuesta pregunta", pregunta_id)

    # Finalizar intento: actualizar resultados por id
    hora_fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nota = 2.5
    cur.execute(
        "UPDATE resultados SET nota = ?, estado_examen = ?, hora_fin = ? WHERE id = ?",
        (nota, "FINALIZADO", hora_fin, intento_id),
    )
    print("Filas afectadas en resultados:", cur.rowcount)

    conn.commit()

    # Mostrar datos insertados
    cur.execute(
        "SELECT id, documento, nombre, grado, area, nota, estado_examen, hora_inicio, hora_fin, intento FROM resultados WHERE id = ?",
        (intento_id,),
    )
    print("Resultado final:", cur.fetchone())

    cur.execute(
        "SELECT id, documento, pregunta_id, respuesta_seleccionada, respuesta_correcta, es_correcta FROM respuestas_estudiantes WHERE documento = ?",
        ("999",),
    )
    rows = cur.fetchall()
    print("Respuestas guardadas:", rows)

print("Prueba completada")
