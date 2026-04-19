from pathlib import Path
import os
import sqlite3
import sys


def _runtime_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _leer_config_sistema(config_path):
    config = {"modo": "local", "ruta_servidor": ""}
    try:
        for raw_line in config_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip().lower()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return config


def resolver_db_path():
    # Prioridad 1: variable de entorno (útil para despliegue web)
    env_db = os.environ.get("SEA_DB_PATH", "").strip()
    if env_db:
        return Path(env_db)

    runtime_dir = _runtime_dir()
    config_path = runtime_dir / "config_sistema"
    config = _leer_config_sistema(config_path)

    modo = str(config.get("modo", "local")).strip().lower()
    ruta_servidor = str(config.get("ruta_servidor", "")).strip().strip('"').strip("'")

    if modo == "red" and ruta_servidor:
        ruta = Path(ruta_servidor)
        if not ruta.is_absolute():
            ruta = (runtime_dir / ruta).resolve()
        if ruta.suffix.lower() == ".db":
            return ruta
        return ruta / "sistema.db"

    return runtime_dir / "sistema.db"


def get_db_path():
    return resolver_db_path()


def get_connection(db_path=None, timeout=30):
    target = str(db_path or get_db_path())
    conn = sqlite3.connect(target, timeout=timeout)
    try:
        conn.execute("PRAGMA busy_timeout = 30000")
    except Exception:
        pass
    return conn


def ping_db():
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False
