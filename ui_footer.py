import tkinter as tk


FOOTER_TEXT = "Diseñador: Robert Calanche Villa | Versión 1.0 | 2026 | Todos los derechos reservados."


def crear_footer(ventana):
    """Crea un footer institucional fijo en la parte inferior de la ventana."""
    bg_color = "#f5f7fa"
    try:
        bg_color = ventana.cget("bg")
    except Exception:
        pass

    footer = tk.Frame(ventana, bg=bg_color)
    footer.pack(side="bottom", fill="x", pady=5)

    tk.Label(
        footer,
        text=FOOTER_TEXT,
        font=("Segoe UI", 9),
        bg=bg_color,
        fg="#999999",
    ).pack()

    return footer
