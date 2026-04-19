#!/usr/bin/env python3
import Admin
import sqlite3

# Obtener datos reales
with sqlite3.connect("sistema.db") as conn:
    cur = conn.cursor()
    cur.execute("SELECT documento FROM resultados LIMIT 1")
    doc_row = cur.fetchone()
    if doc_row:
        doc = doc_row[0]
        print(f"Probando con documento: {doc}")

        # Obtener respuestas
        respuestas = Admin.obtener_respuestas_estudiante(doc)
        if respuestas:
            nombre = respuestas[0].get("nombre", "Estudiante")
            area = respuestas[0].get("area", "General")

            print(f"Total de respuestas: {len(respuestas)}")
            print(f"Generando PDF...")

            # Generar PDF
            pdf_content = Admin._generar_pdf_reporte_respuestas(
                respuestas, doc, nombre, area, 1
            )

            if pdf_content:
                # Guardar para verificar
                pdf_path = "test_reporte.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(pdf_content)
                print(f"✓ PDF generado exitosamente: {pdf_path}")
                print(f"  Tamaño: {len(pdf_content)} bytes")
            else:
                print("✗ No se generó PDF")
        else:
            print("Sin respuestas para este documento")
    else:
        print("No hay documentos en resultados")
