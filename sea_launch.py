"""
sea_launch.py
-------------
Lanzador híbrido del sistema SEA.

Modos de uso:
  python sea_launch.py              → Inicia AMBOS: escritorio (Tkinter) + servidor web (Flask)
  python sea_launch.py --desktop    → Solo aplicación de escritorio
  python sea_launch.py --web        → Solo servidor web en red local
  python sea_launch.py --web --port 8080   → Servidor web en puerto personalizado
    python sea_launch.py --web --debug → Fuerza debug web cuando aplica

En modo híbrido, el servidor Flask corre en un hilo daemon y el escritorio se
ejecuta en el hilo principal con Tkinter.
"""

from __future__ import annotations

import argparse
import subprocess
import socket
import threading
import sys
import os
import tkinter as tk
from pathlib import Path

# ---------------------------------------------------------------------------
# Directorio base
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
DEFAULT_LOCAL_DOMAINS = ("sea.local", "evaluaciones.local", "admin.local")


def _python_candidates() -> list[Path]:
    current = Path(sys.executable).resolve()
    candidates: list[Path] = []
    for env_name in (".venv", "venv"):
        candidate = (BASE_DIR / env_name / "Scripts" / "python.exe").resolve()
        if candidate.exists() and candidate != current:
            candidates.append(candidate)
    return candidates


def _python_has_module(python_path: Path, module_name: str) -> bool:
    try:
        result = subprocess.run(
            [str(python_path), "-c", f"import {module_name}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception:
        return False
    return result.returncode == 0


def ensure_web_runtime() -> None:
    """Reintenta con el entorno correcto si Flask no está en el intérprete actual."""
    try:
        import flask  # noqa: F401

        return
    except ModuleNotFoundError as exc:
        if exc.name != "flask":
            raise

    for candidate in _python_candidates():
        if _python_has_module(candidate, "flask"):
            print(f"[INFO] Flask no está disponible en {sys.executable}")
            print(f"[INFO] Reintentando con {candidate}")
            os.execv(
                str(candidate),
                [str(candidate), str(Path(__file__).resolve()), *sys.argv[1:]],
            )

    raise ModuleNotFoundError(
        "No se encontró Flask en el intérprete actual ni en los entornos locales venv/.venv. "
        "Instala dependencias en el entorno correcto o ejecuta .venv\\Scripts\\python.exe sea_launch.py --web"
    )


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_local_domains() -> list[str]:
    raw = str(
        os.environ.get("SEA_LOCAL_DOMAINS", ",".join(DEFAULT_LOCAL_DOMAINS))
    ).strip()
    domains: list[str] = []
    for item in raw.split(","):
        domain = str(item or "").strip().lower()
        if domain and domain not in domains:
            domains.append(domain)
    return domains or [DEFAULT_LOCAL_DOMAINS[0]]


def build_url(host: str, port: int, path: str = "", scheme: str = "http") -> str:
    suffix = path if path.startswith("/") or not path else f"/{path}"
    if int(port) == 80:
        return f"{scheme}://{host}{suffix}"
    return f"{scheme}://{host}:{port}{suffix}"


# ---------------------------------------------------------------------------
# Servidor Flask en hilo separado
# ---------------------------------------------------------------------------


def iniciar_web(
    host: str = "0.0.0.0",
    port: int = 5000,
    debug: bool = False,
    use_reloader: bool = False,
) -> threading.Thread:
    """Lanza Flask en un hilo daemon (no bloquea el hilo principal)."""

    def _run():
        # Importar aquí para no cargar Flask si no se necesita
        from web_app import run_web_server

        # Silenciar el banner de Werkzeug en modo híbrido
        import logging

        log = logging.getLogger("werkzeug")
        log.setLevel(logging.WARNING)
        run_web_server(
            host=host,
            port=port,
            debug=debug,
            use_reloader=use_reloader,
            threaded=True,
        )

    t = threading.Thread(target=_run, daemon=True, name="SEA-WebServer")
    t.start()
    return t


def _sea_env_mode() -> str:
    """Resuelve entorno desde variable SEA_ENV (dev/prod)."""
    # Forzar siempre modo desarrollo
    return "dev"


def run_web(port: int, local_ip: str, web_only: bool, force_debug: bool = False):
    """Arranca servidor web según SEA_ENV, con híbrido seguro.

    - SEA_ENV=dev  -> debug y reloader activos (solo en web_only).
    - SEA_ENV=prod -> debug/reloader desactivados.
    - En modo híbrido nunca usa reloader para evitar doble ejecución.
    """
    from web_app import get_access_scheme, run_web_server

    runtime_mode = _sea_env_mode()
    debug_web = runtime_mode == "dev" or bool(force_debug)
    reloader_web = runtime_mode == "dev"

    if runtime_mode == "dev":
        print("MODO DESARROLLO ACTIVADO")
    else:
        print("MODO PRODUCCIÓN")

    if not web_only and reloader_web:
        print(
            "[WARN] Modo híbrido detectado: reloader desactivado para evitar doble ejecución."
        )
        reloader_web = False
        debug_web = False

    scheme = get_access_scheme()
    local_domains = get_local_domains()
    print(f"  Runtime: {'DESARROLLO' if runtime_mode == 'dev' else 'PRODUCCIÓN'}")
    print(f"  Web debug:     {'ON' if debug_web else 'OFF'}")
    print(f"  Web reloader:  {'ON' if reloader_web else 'OFF'}")
    print(f"  Acceso local:  {build_url(local_domains[0], port, scheme=scheme)}")
    if len(local_domains) > 1:
        print(
            "  Alias locales: "
            + " | ".join(
                build_url(item, port, scheme=scheme) for item in local_domains[1:]
            )
        )
    print(f"  Red local:     {build_url(local_ip, port, scheme=scheme)}")
    print(f"  Escáner OMR:   {build_url(local_ip, port, '/escanear', scheme=scheme)}")
    print(f"  API:           {build_url(local_ip, port, '/api/info', scheme=scheme)}")
    if scheme == "https":
        print(
            "  Nota:          HTTPS activo para contexto seguro de cámara en navegadores que lo exijan."
        )
    else:
        print("  Hosts Windows: C:\\Windows\\System32\\drivers\\etc\\hosts")
        print(
            "  Nota:          Los dominios .local funcionan en este PC; en celulares usa la IP local o habilita HTTPS si el navegador bloquea la cámara en HTTP."
        )
    print("-" * 60)

    if web_only:
        run_web_server(
            host="0.0.0.0",
            port=port,
            debug=debug_web,
            use_reloader=reloader_web,
            threaded=True,
        )
        return

    iniciar_web(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
    )


# ---------------------------------------------------------------------------
# Aplicación de escritorio
# ---------------------------------------------------------------------------


def iniciar_escritorio() -> None:
    """Lanza la aplicación de escritorio (Tkinter) en el hilo principal."""
    try:
        from modulo_superadmin import BASE_DIR as MSA_BASE_DIR
        from modulo_superadmin import DB_FILE, ModuloSuperAdmin
    except ImportError as exc:
        print(f"[ERROR] No se pudo importar modulo_superadmin: {exc}")
        sys.exit(1)

    root = tk.Tk()
    root.withdraw()
    msa = ModuloSuperAdmin(root, db_path=str(DB_FILE), base_dir=str(MSA_BASE_DIR))
    if msa.authenticate():
        msa.open_interface()
        root.mainloop()
        return

    root.destroy()


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------


def main() -> None:

    # --- AUTO-MIGRACIÓN GLOBAL ANTES DE INICIAR SERVIDOR ---
    try:
        import Admin

        Admin.crear_base_datos()
        Admin.crear_tabla_banco_preguntas()
        Admin.crear_tabla_config()
        print("[INFO] Migración automática de base de datos completada.")
    except Exception as e:
        print(f"[WARN] Auto-migración: {e}")
    # ---

    parser = argparse.ArgumentParser(
        description="SEA — Lanzador híbrido (Escritorio + Web + API)"
    )
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Iniciar solo la aplicación de escritorio Tkinter",
    )
    parser.add_argument(
        "--web", action="store_true", help="Iniciar solo el servidor web Flask"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Puerto del servidor web (por defecto: 5000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Activar modo debug de Flask (solo en desarrollo)",
    )
    args = parser.parse_args()

    if args.web or (not args.desktop and not args.web):
        ensure_web_runtime()

    # Si no se especifica nada → modo híbrido (ambos)
    modo_hibrido = (not args.desktop and not args.web) or (args.desktop and args.web)
    modo_web_solo = args.web and not args.desktop
    modo_desktop_solo = args.desktop and not args.web

    runtime_mode = _sea_env_mode()
    local_ip = get_local_ip()

    print("=" * 60)
    print("  SEA — Sistema de Evaluación Automatizada")
    print("  Arquitectura Híbrida: Escritorio + Web + API Móvil")
    print("=" * 60)

    if modo_web_solo or modo_hibrido:
        run_web(
            port=args.port,
            local_ip=local_ip,
            web_only=modo_web_solo,
            force_debug=args.debug,
        )
        if modo_web_solo:
            return

    if modo_desktop_solo or modo_hibrido:
        print("  Iniciando aplicación de escritorio...")
        print("=" * 60)
        iniciar_escritorio()

    elif modo_web_solo:
        # Solo web: mantener el proceso vivo
        print("=" * 60)
        print("  Servidor web corriendo. Presiona Ctrl+C para detener.")
        print("=" * 60)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            print("\n  Servidor detenido.")


if __name__ == "__main__":
    main()
