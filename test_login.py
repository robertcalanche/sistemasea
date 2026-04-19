import sqlite3
from pathlib import Path

import tkinter as tk

# make sure workspace path is importable
import sys

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app import validar_maestra, requerir_clave_maestra, DB_FILE


def setup_db(master_key="secret"):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # ensure config_sistema exists
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS config_sistema (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """
    )
    cur.execute(
        "REPLACE INTO config_sistema(clave,valor) VALUES(?,?)",
        ("master_key", master_key),
    )
    conn.commit()
    conn.close()


def test_validar_maestra(tmp_path, monkeypatch):
    # start with a known key
    setup_db("clave1")
    assert validar_maestra("clave1")
    assert not validar_maestra("otra")


def test_requerir_clave_maestra():
    assert requerir_clave_maestra("admin")
    assert requerir_clave_maestra("ADMIN")
    assert not requerir_clave_maestra("admin123")
    assert not requerir_clave_maestra("usuario")
