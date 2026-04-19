"""
Test para verificar la funcionalidad de reanudacion automatica de examenes.
Simula un examen interrumpido y verifica que se pueda reanudar correctamente.
"""

import sqlite3
from pathlib import Path
import json
import sys

BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "sistema.db"


def test_reanudacion():
    """Verifica el flujo de reanudacion de examen."""

    print("=" * 70)
    print("TEST: REANUDACION AUTOMATICA DE EXAMENES")
    print("=" * 70)

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 1. Crear un examen EN_PROCESO simulado
        print("\n1. Creando examen EN_PROCESO simulado...")
        test_doc = "TEST_REANUDA_001"
        test_area = "LENGUAJE"
        test_grado = "DECIMO"

        cursor.execute(
            """
            SELECT COUNT(*) FROM resultados 
            WHERE documento = ? AND area = ? AND estado_examen = 'EN_PROCESO'
            """,
            (test_doc, test_area),
        )
        existe = cursor.fetchone()[0]

        if existe == 0:
            from datetime import datetime

            hora_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                """
                INSERT INTO resultados 
                (documento, nombre, grado, area, nota, estado_examen, hora_inicio, intento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    test_doc,
                    "Test Student",
                    test_grado,
                    test_area,
                    None,
                    "EN_PROCESO",
                    hora_inicio,
                    1,
                ),
            )
            intento_id = cursor.lastrowid
            intento_num = 1
            conn.commit()
            print(
                f"   [OK] Examen EN_PROCESO creado (ID: {intento_id}, Intento: {intento_num})"
            )
        else:
            print("   [AVISO] Examen EN_PROCESO ya existe")
            cursor.execute(
                """
                SELECT id, intento FROM resultados 
                WHERE documento = ? AND area = ? AND estado_examen = 'EN_PROCESO'
                """,
                (test_doc, test_area),
            )
            intento_id, intento_num = cursor.fetchone()

        # 2. Insertar respuestas parciales guardadas
        print(f"\n2. Guardando respuestas parciales (2 de 5)...")
        respuestas_test = [
            (
                test_doc,
                "Test Student",
                test_grado,
                test_area,
                intento_num,
                1,
                "Pregunta 1",
                "A",
                "A",
                1,
            ),
            (
                test_doc,
                "Test Student",
                test_grado,
                test_area,
                intento_num,
                2,
                "Pregunta 2",
                "B",
                "D",
                0,
            ),
        ]

        for resp in respuestas_test:
            cursor.execute(
                """
                INSERT OR IGNORE INTO respuestas_estudiantes 
                (documento, nombre, grado, area, intento, pregunta_id, enunciado, 
                 respuesta_seleccionada, respuesta_correcta, es_correcta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                resp,
            )

        conn.commit()

        # Verificar que se guardaron
        cursor.execute(
            """
            SELECT COUNT(*) FROM respuestas_estudiantes 
            WHERE documento = ? AND area = ? AND intento = ?
            """,
            (test_doc, test_area, intento_num),
        )
        respuestas_guardadas = cursor.fetchone()[0]
        print(f"   [OK] {respuestas_guardadas} respuestas guardadas")

        # 3. Simular busqueda de examen EN_PROCESO (como lo hace _obtener_examen_en_proceso)
        print(f"\n3. Simulando busqueda de examen EN_PROCESO...")
        cursor.execute(
            """
            SELECT intento, id FROM resultados 
            WHERE documento = ? AND area = ? AND estado_examen = 'EN_PROCESO'
            ORDER BY id DESC LIMIT 1
            """,
            (test_doc, test_area),
        )
        resultado = cursor.fetchone()

        if resultado:
            intento_recuperado, id_recuperado = resultado
            print(f"   [OK] Examen EN_PROCESO encontrado:")
            print(f"     - Intento: {intento_recuperado}")
            print(f"     - ID: {id_recuperado}")

            # Contar respuestas para determinar indice
            cursor.execute(
                """
                SELECT COUNT(*) FROM respuestas_estudiantes 
                WHERE documento = ? AND area = ? AND intento = ?
                """,
                (test_doc, test_area, intento_recuperado),
            )
            respuestas_count = cursor.fetchone()[0]
            print(
                f"   [OK] Indice de continuacion: {respuestas_count} (comenzar pregunta {respuestas_count + 1})"
            )

            # Contar respuestas correctas previas
            cursor.execute(
                """
                SELECT COUNT(*) FROM respuestas_estudiantes 
                WHERE documento = ? AND area = ? AND intento = ? AND es_correcta = 1
                """,
                (test_doc, test_area, intento_recuperado),
            )
            correctas_previas = cursor.fetchone()[0]
            print(f"   [OK] Respuestas correctas previas: {correctas_previas}")
        else:
            print("   [ERROR] No se encontro examen EN_PROCESO")
            return False

        # 4. Recuperar todas las respuestas (como lo hace obtener_todas_respuestas_desde_bd)
        print(f"\n4. Recuperando todas las respuestas guardadas...")
        cursor.execute(
            """
            SELECT pregunta_id, enunciado, respuesta_seleccionada, respuesta_correcta, es_correcta
            FROM respuestas_estudiantes
            WHERE documento = ? AND area = ? AND intento = ?
            ORDER BY rowid ASC
            """,
            (test_doc, test_area, intento_recuperado),
        )
        filas = cursor.fetchall()

        respuestas_recuperadas = []
        for pregunta_id, enunciado, resp_sel, resp_corr, es_corr in filas:
            respuestas_recuperadas.append(
                {
                    "pregunta_id": pregunta_id,
                    "enunciado": enunciado,
                    "respuesta_dada": resp_sel,
                    "respuesta_correcta": resp_corr,
                    "correcta": bool(es_corr),
                }
            )

        print(f"   [OK] {len(respuestas_recuperadas)} respuestas recuperadas")
        for r in respuestas_recuperadas:
            estado = "[CORRECTA]" if r["correcta"] else "[INCORRECTA]"
            print(
                f"     - P{r['pregunta_id']}: {r['respuesta_dada']} (Correcta: {r['respuesta_correcta']}) {estado}"
            )

        # 5. Verificar integridad de datos
        print(f"\n5. Verificando integridad de datos...")
        total_correctas = sum(1 for r in respuestas_recuperadas if r["correcta"])
        print(f"   [OK] Total correctas: {total_correctas}")

        if total_correctas == correctas_previas:
            print(f"   [OK] Contador de correctas coincide")
        else:
            print(
                f"   [ERROR] Contador no coincide ({total_correctas} vs {correctas_previas})"
            )
            return False

        conn.close()

        print("\n" + "=" * 70)
        print("[EXITO] TEST EXITOSO: Sistema de reanudacion funcionando correctamente")
        print("=" * 70)

        # Mostrar resumen
        print("\nRESUMEN:")
        print(f"  - Examen EN_PROCESO: SI")
        print(f"  - Respuestas guardadas: {respuestas_count}")
        print(f"  - Indice de continuacion: {respuestas_count}")
        print(f"  - Respuestas correctas previas: {correctas_previas}")
        print(f"  - Recuperacion de datos: COMPLETA")

        return True

    except Exception as e:
        print(f"\n[ERROR FATAL] Error en test: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_reanudacion()
    exit(0 if success else 1)
