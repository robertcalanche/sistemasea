import sqlite3


def main():
    db = "sistema.db"
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute(
        "SELECT COUNT(*) FROM banco_preguntas WHERE id_evaluacion IS NULL OR TRIM(id_evaluacion) = ?",
        ("",),
    )
    resultado = c.fetchone()[0]
    print(f"Preguntas sin id_evaluacion: {resultado}")
    conn.close()


if __name__ == "__main__":
    main()
