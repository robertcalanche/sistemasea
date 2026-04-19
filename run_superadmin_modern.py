import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys

try:
    # intentar usar ttkbootstrap si está instalado
    from ttkbootstrap import Style as TBStyle

    _HAS_TTB = True
except Exception:
    _HAS_TTB = False

try:
    import sv_ttk

    _HAS_SVTTK = True
except Exception:
    _HAS_SVTTK = False

from modulo_superadmin import ModuloSuperAdmin


def obtener_ruta_icono():
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            ruta_meipass = Path(meipass) / "sea_icon.ico"
            if ruta_meipass.exists():
                return ruta_meipass
        return Path(sys.executable).resolve().parent / "sea_icon.ico"
    return Path(__file__).resolve().parent / "sea_icon.ico"


def apply_fallback_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    # fuentes y paddings más modernas
    default_font = ("Segoe UI", 10)
    try:
        root.option_add("*Font", default_font)
    except Exception:
        pass
    accent = "#0d6efd"  # azul moderno
    bg = "#f6f8fb"
    fg = "#222222"
    style.configure(".", background=bg, foreground=fg, padding=6)
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", padding=6)
    style.configure("Accent.TButton", background=accent, foreground="white")
    style.map("Accent.TButton", background=[("active", "!disabled", "#0b5ed7")])
    style.configure(
        "Treeview", rowheight=28, fieldbackground="white", background="white"
    )
    style.configure("Treeview.Heading", font=(default_font[0], 10, "bold"))
    style.configure("TNotebook", background=bg)
    style.configure("TNotebook.Tab", padding=(12, 8))


def main():
    # Preferir ttkbootstrap -> sv_ttk -> fallback
    if _HAS_TTB:
        # ttkbootstrap recomienda crear Style antes de Tk
        TBStyle(theme="litera")
        root = tk.Tk()
    else:
        root = tk.Tk()
        if _HAS_SVTTK:
            try:
                sv_ttk.set_theme("light")
            except Exception:
                apply_fallback_style(root)
        else:
            apply_fallback_style(root)

    ruta_icono = obtener_ruta_icono()
    if ruta_icono.exists():
        root.iconbitmap(str(ruta_icono))
    root.withdraw()
    # Usa DB_PATH y BASE_DIR resueltos desde config_sistema.
    msa = ModuloSuperAdmin(root)
    if msa.authenticate():
        msa.open_interface()
        if ruta_icono.exists() and hasattr(msa, "win"):
            try:
                msa.win.iconbitmap(str(ruta_icono))
            except Exception:
                pass
        try:
            msa.win.state("zoomed")
        except Exception:
            try:
                msa.win.attributes("-fullscreen", True)
            except Exception:
                pass
        msa.win.mainloop()


if __name__ == "__main__":
    main()
