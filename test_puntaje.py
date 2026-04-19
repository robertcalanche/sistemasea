#!/usr/bin/env python3
import Admin
import sqlite3

# Obtener datos reales de un estudiante con respuestas
with sqlite3.connect("sistema.db") as conn:
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM respuestas_estudiantes WHERE documento = ?",
        ("1158467334",),
    )
    total = cur.fetchone()[0]

    print(f"Total de preguntas para documento 1158467334: {total}")
    print(f"Nota máxima: 5.0")

    if total > 0:
        valor_pregunta = 5.0 / total
        print(f"Valor por pregunta: {valor_pregunta:.1f}")

        # Obtener ejemplos
        respuestas = Admin.obtener_respuestas_estudiante("1158467334")
        correctas = sum(1 for r in respuestas if r.get("es_correcta"))
        print(f"\nRespuestas correctas: {correctas}/{total}")

        puntaje_esperado = correctas * valor_pregunta
        print(f"Puntaje esperado: {puntaje_esperado:.1f}")

        print("\n=== Primeras 3 preguntas ===")
        for i, r in enumerate(respuestas[:3], 1):
            puntaje = valor_pregunta if r.get("es_correcta") else 0
            estado = "✅ Correcta" if r.get("es_correcta") else "❌ Incorrecta"
            print(f"  P{i}: {estado} | Puntaje: {puntaje:.1f}")
