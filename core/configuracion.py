"""
Servicios centralizados de configuración del sistema.
Gestiona acceso a: config_sistema (clave, valor).
"""

from . import get_connection


def obtener_config(clave):
    """
    Obtiene el valor de una configuración del sistema.

    Args:
        clave: Clave de configuración (ej: 'master_key', 'anio_lectivo')

    Returns:
        str o None: El valor configurado, o None si no existe.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT valor FROM config_sistema WHERE clave=?", (clave,))
        row = cur.fetchone()

    return row[0] if row else None


def guardar_config(clave, valor):
    """
    Guarda o actualiza una configuración del sistema.

    Args:
        clave: Clave de configuración
        valor: Valor a guardar (se convierte a string)

    Returns:
        bool: True si fue exitoso
    """
    valor_str = str(valor) if valor is not None else ""

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM config_sistema WHERE clave=?", (clave,))
        existe = cur.fetchone() is not None

        if existe:
            cur.execute(
                "UPDATE config_sistema SET valor=? WHERE clave=?", (valor_str, clave)
            )
        else:
            cur.execute(
                "INSERT INTO config_sistema(clave,valor) VALUES(?,?)",
                (clave, valor_str),
            )

        conn.commit()

    return True


def obtener_clave_maestra():
    """Obtiene la clave maestra del sistema."""
    return obtener_config("master_key")


def guardar_clave_maestra(clave):
    """Guarda la clave maestra del sistema."""
    return guardar_config("master_key", clave)


def obtener_anio_lectivo():
    """Obtiene el año lectivo actual configurado."""
    return obtener_config("anio_lectivo")


def guardar_anio_lectivo(anio):
    """Guarda el año lectivo actual."""
    return guardar_config("anio_lectivo", anio)


def listar_todas_configuraciones():
    """
    Retorna todas las configuraciones como diccionario.

    Returns:
        dict: {clave: valor, ...}
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT clave, valor FROM config_sistema ORDER BY clave")
        rows = cur.fetchall()

    return {row[0]: row[1] for row in rows}


def eliminar_config(clave):
    """
    Elimina una configuración del sistema.

    Args:
        clave: Clave a eliminar

    Returns:
        bool: True si fue exitoso
    """
    with get_connection() as conn:
        conn.execute("DELETE FROM config_sistema WHERE clave=?", (clave,))
        conn.commit()

    return True
