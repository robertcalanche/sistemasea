import sqlite3
import os
import traceback

DB = "resultados.db"
EXCEL_OUT = "reporte_prueba.xlsx"
PDF_OUT = "reporte_prueba.pdf"


def ensure_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS resultados (
        id INTEGER PRIMARY KEY,
        documento TEXT,
        nombre TEXT,
        grado TEXT,
        area TEXT,
        nota REAL,
        estado_examen TEXT,
        intento INTEGER,
        puede_revisar INTEGER
    )"""
    )
    conn.commit()
    # insert sample rows if table empty
    cur.execute("SELECT COUNT(*) FROM resultados")
    cnt = cur.fetchone()[0]
    if cnt == 0:
        sample = [
            (1, "1001", "Ana Perez", "5", "Matematicas", 4.5, "terminado", 1, 0),
            (2, "1002", "Luis Gomez", "5", "Ciencias", 3.8, "terminado", 1, 1),
            (3, "1003", "Marta Ruiz", "6", "Matematicas", 4.9, "terminado", 1, 1),
        ]
        cur.executemany(
            "INSERT OR REPLACE INTO resultados VALUES (?,?,?,?,?,?,?,?,?)", sample
        )
        conn.commit()
    conn.close()


def fetch_rows(grado=None, area=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    sql = "SELECT id, documento, nombre, grado, area, nota, estado_examen, intento, puede_revisar FROM resultados"
    conds = []
    params = []
    if grado:
        conds.append("grado=?")
        params.append(grado)
    if area:
        conds.append("area=?")
        params.append(area)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    conn.close()
    return rows


def export_excel(rows, path):
    try:
        import pandas as pd

        df = pd.DataFrame(
            rows,
            columns=[
                "id",
                "documento",
                "nombre",
                "grado",
                "area",
                "nota",
                "estado_examen",
                "intento",
                "puede_revisar",
            ],
        )
        df.to_excel(path, index=False)
        print("Excel guardado:", path)
        return True
    except Exception:
        try:
            from openpyxl import Workbook

            wb = Workbook()
            ws = wb.active
            ws.append(
                [
                    "id",
                    "documento",
                    "nombre",
                    "grado",
                    "area",
                    "nota",
                    "estado_examen",
                    "intento",
                    "puede_revisar",
                ]
            )
            for r in rows:
                ws.append(list(r))
            wb.save(path)
            print("Excel guardado (openpyxl):", path)
            return True
        except Exception:
            traceback.print_exc()
            return False


def export_pdf(rows, path):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        w, h = A4
        c = canvas.Canvas(path, pagesize=A4)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, h - 40, "Reporte de Calificaciones")
        c.setFont("Helvetica", 9)
        y = h - 70
        col_w = (w - 80) / 9
        headers = [
            "id",
            "documento",
            "nombre",
            "grado",
            "area",
            "nota",
            "estado_examen",
            "intento",
            "puede_revisar",
        ]
        for i, hh in enumerate(headers):
            c.drawString(40 + i * col_w, y, hh)
        y -= 14
        for r in rows:
            if y < 40:
                c.showPage()
                y = h - 40
            for i, cell in enumerate(r):
                c.drawString(40 + i * col_w, y, str(cell)[: int(col_w / 6)])
            y -= 12
        c.save()
        print("PDF guardado (reportlab):", path)
        return True
    except Exception:
        try:
            from PIL import Image, ImageDraw

            pw, ph = 595, 842
            pages = []
            for page_start in range(0, len(rows), 40):
                img = Image.new("RGB", (pw, ph), "white")
                d = ImageDraw.Draw(img)
                y = 30
                d.text((40, y), "Reporte de Calificaciones", fill="black")
                y += 24
                for r in rows[page_start : page_start + 40]:
                    line = " | ".join(str(x) for x in r)
                    d.text((40, y), line, fill="black")
                    y += 16
                pages.append(img.convert("RGB"))
            pages[0].save(path, save_all=True, append_images=pages[1:])
            print("PDF guardado (Pillow):", path)
            return True
        except Exception:
            traceback.print_exc()
            return False


if __name__ == "__main__":
    ensure_db()
    rows = fetch_rows()
    print("Filas en resultados:", len(rows))
    ok1 = export_excel(rows, EXCEL_OUT)
    ok2 = export_pdf(rows, PDF_OUT)
    print("Excel ok=", ok1, "PDF ok=", ok2)
