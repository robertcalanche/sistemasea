def construir_nombre(est):
    """
    Construye el nombre completo del estudiante usando los campos estructurados.
    Siempre usa apellido1, apellido2, nombre1, nombre2 (en ese orden), quitando espacios extra.
    Permite tanto dict como objeto con atributos.
    """
    get = est.get if hasattr(est, "get") else lambda k, d=None: getattr(est, k, d)
    nombre1 = get("nombre1", "").strip()
    nombre2 = get("nombre2", "").strip()
    apellido1 = get("apellido1", "").strip()
    apellido2 = get("apellido2", "").strip()
    partes = [apellido1, apellido2, nombre1, nombre2]
    return " ".join([p for p in partes if p]).strip()
