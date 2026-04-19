#!/usr/bin/env python3
"""
Script simple para arrancar web_app sin SSL y con logging visible.
"""
import sys
import os

# Desactivar HTTPS
os.environ["SEA_DISABLE_HTTPS"] = "1"

# Importar después de setear env
from web_app import run_web_server

if __name__ == "__main__":
    print("[INFO] Iniciando servidor web en http://0.0.0.0:5000")
    print("[INFO] Acceso: http://localhost:5000/acceso")
    print("[INFO] Red local: http://192.168.1.4:5000/acceso")
    print("[INFO] Presiona Ctrl+C para detener\n")

    try:
        run_web_server(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n[INFO] Servidor detenido.")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
