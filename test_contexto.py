#!/usr/bin/env python3
import Admin
import sqlite3

# Leer un documento de ejemplo
with sqlite3.connect("sistema.db") as conn:
    cur = conn.cursor()
    cur.execute("SELECT documento FROM respuestas_estudiantes LIMIT 1")
    fila = cur.fetchone()
    if fila:
        doc = fila[0]
        print(f"Probando con documento: {doc}")
        respuestas = Admin.obtener_respuestas_estudiante(doc)
        if respuestas:
            r = respuestas[0]
            campos = list(r.keys())
            print(f"Campos: {campos}")
            if "id_contexto" in campos and "contexto" in campos:
                print("✓ id_contexto y contexto presentes")
            else:
                print("✗ Faltan campos")
        else:
            print("Sin respuestas")
    else:
        print("No hay documentos")
