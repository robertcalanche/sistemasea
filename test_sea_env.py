import os
import builtins
import types
import pytest

import sea_launch


def test_sea_env_modes(monkeypatch):
    """
    Valida que run_web seleccione correctamente debug/reloader según SEA_ENV y modo híbrido.
    """
    resultados = []

    def fake_run_web_server(host, port, debug, use_reloader, threaded):
        resultados.append((debug, use_reloader, threaded))

    def fake_get_access_scheme():
        return "http"

    monkeypatch.setattr(sea_launch, "get_local_ip", lambda: "127.0.0.1")
    monkeypatch.setattr("web_app.run_web_server", fake_run_web_server)
    monkeypatch.setattr("web_app.get_access_scheme", fake_get_access_scheme)

    # Caso 1: SEA_ENV=dev, web_only=True
    monkeypatch.setenv("SEA_ENV", "dev")
    resultados.clear()
    sea_launch.run_web(5000, "127.0.0.1", web_only=True)
    assert resultados[-1][:2] == (True, True)  # debug ON, reloader ON

    # Caso 2: SEA_ENV=prod, web_only=True
    monkeypatch.setenv("SEA_ENV", "prod")
    resultados.clear()
    sea_launch.run_web(5000, "127.0.0.1", web_only=True)
    assert resultados[-1][:2] == (False, False)  # debug OFF, reloader OFF

    # Caso 3: SEA_ENV=dev, modo híbrido (web_only=False)
    monkeypatch.setenv("SEA_ENV", "dev")
    resultados.clear()
    sea_launch.run_web(5000, "127.0.0.1", web_only=False)
    # En híbrido: debug y reloader forzados a OFF
    assert resultados == []  # No llama run_web_server directo, solo inicia hilo

    # Si quieres validar el hilo, puedes mockear iniciar_web y comprobar llamada


if __name__ == "__main__":
    pytest.main([__file__])
