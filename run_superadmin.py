import tkinter as tk
from pathlib import Path
import sys
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


def main():
    root = tk.Tk()
    ruta_icono = obtener_ruta_icono()
    if ruta_icono.exists():
        root.iconbitmap(str(ruta_icono))
    root.withdraw()
    # Usa DB_PATH y BASE_DIR resueltos desde config_sistema.
    msa = ModuloSuperAdmin(root)
    # Abrir interfaz directamente para demostración
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
