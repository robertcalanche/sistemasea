from __future__ import annotations

from . import configuracion as core_configuracion


def _norm(txt):
    return str(txt or "").strip()


def resumen_seguridad():
    actual = _norm(core_configuracion.obtener_clave_maestra())
    return {
        "master_key_configurada": bool(actual),
        "longitud": len(actual),
    }


def cambiar_clave_maestra(actual, nueva, confirmar):
    actual_guardada = _norm(core_configuracion.obtener_clave_maestra())
    actual_in = _norm(actual)
    nueva_in = _norm(nueva)
    confirmar_in = _norm(confirmar)

    if not nueva_in:
        raise ValueError("nueva_clave_requerida")
    if len(nueva_in) < 6:
        raise ValueError("nueva_clave_muy_corta")
    if nueva_in != confirmar_in:
        raise ValueError("confirmacion_no_coincide")

    if actual_guardada and actual_in != actual_guardada:
        raise ValueError("clave_actual_incorrecta")

    core_configuracion.guardar_clave_maestra(nueva_in)
    return {
        "mensaje": "Clave maestra actualizada",
    }
